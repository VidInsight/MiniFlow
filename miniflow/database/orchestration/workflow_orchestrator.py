from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity
from miniflow.database.models import WorkflowStatus, ExecutionStatus


class WorkflowOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)

    def _get_primary_crud(self):
        return self.workflow_crud

    @with_session
    def create(self, session: Session, **kwargs) -> Dict[str, Any]:
        try:
            result = self.workflow_crud._create(session, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", name=kwargs.get("name"))
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, workflow_id: str, **kwargs) -> Dict[str, Any]:
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "update")

        try:
            result = self.workflow_crud._update(session, workflow_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, record_id: str) -> Dict[str, Any]:
        # VALIDATION - Deletion safety
        self.workflow_crud._validate_deletion_safety(session, record_id)

        try:
            # Check for active executions - use separate queries for each status
            running_executions = self.execution_crud._filter(session, {"workflow_id": record_id, "status": ExecutionStatus.RUNNING}, limit=1)
            pending_executions = self.execution_crud._filter(session, {"workflow_id": record_id, "status": ExecutionStatus.PENDING}, limit=1)
            
            if running_executions or pending_executions:
                context = self._create_error_context("delete_with_active_executions", workflow_id=record_id)
                raise OrchestrationError(f"Cannot delete workflow '{record_id}' - it has active executions", context=context)
            
            # Delete all executions for this workflow (this will handle inputs/outputs)
            executions = self.execution_crud._filter(session, {"workflow_id": record_id})
            for execution in executions:
                self.execution_crud._delete(session, execution.id)
            
            # Delete all edges first (before nodes)
            edges = self.edge_crud._filter(session, {"workflow_id": record_id})
            for edge in edges:
                self.edge_crud._delete(session, edge.id)
            
            # Delete all nodes
            nodes = self.node_crud._filter(session, {"workflow_id": record_id})
            for node in nodes:
                self.node_crud._delete(session, node.id)
            
            # Finally delete the workflow
            deleted_workflow = self.workflow_crud._delete(session, record_id)
            return self._serialize_single_result(deleted_workflow)
            
        except Exception as e:
            context = self._create_error_context("delete", workflow_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_by_name(self, session: Session, name: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        if not name:
            return None

        try:
            results = self.workflow_crud._filter(session, filters={"name": name.strip()}, limit=1)
            if not results:
                return None
            return self._serialize_single_result(results[0], include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_stats(self, session: Session, workflow_id: str, execution_status: ExecutionStatus, execution_duration: float = None) -> Dict[str, Any]:
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "update_stats")
        try:
            self.workflow_crud._update_stats(session, workflow_id, execution_status, execution_duration)
            return {"updated": True, "workflow_id": workflow_id, "operation": "stats_update"}
        except Exception as e:
            context = self._create_error_context("update_stats", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_stats(self, session: Session, workflow_id: str) -> Dict[str, Any]:
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "get_stats")
        try:
            return self.workflow_crud._get_stats(session, workflow_id)
        except Exception as e:
            context = self._create_error_context("get_stats", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_recently_executed(self, session: Session, limit: int = 10, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        try:
            results = self.workflow_crud._get_recently_executed(session, limit)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
            
        except Exception as e:
            context = self._create_error_context("get_recently_executed", limit=limit)
            raise OrchestrationError(f"Failed to get recently executed workflows: {str(e)}", context=context) from e

    @with_session
    def get_workflow_graph(self, session: Session, workflow_id: str) -> Dict[str, Any]:
        try:
            if not self.workflow_crud._exists(session, workflow_id):
                self._handle_not_found("Workflow", workflow_id, "get_workflow_graph")
            
            return self.workflow_crud._get_workflow_graph(session, workflow_id)
        except Exception as e:
            context = self._create_error_context("get_workflow_graph", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def validate_workflow_completeness(self, session: Session, workflow_id: str) -> Dict[str, Any]:
        try:
            if not self.workflow_crud._exists(session, workflow_id):
                self._handle_not_found("Workflow", workflow_id, "validate_workflow_completeness")
            
            validation_result = {
                "workflow_id": workflow_id,
                "is_complete": False,
                "has_minimum_nodes": False,
                "has_no_cycles": False,
                "all_nodes_connected": False,
                "validation_errors": []
            }
            
            # Get workflow graph
            graph_data = self.workflow_crud._get_workflow_graph(session, workflow_id)
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            # Check minimum nodes
            if len(nodes) >= 1:
                validation_result["has_minimum_nodes"] = True
            else:
                validation_result["validation_errors"].append("Workflow must have at least 1 node")
            
            # Check for cycles
            has_cycles = self.workflow_crud._detect_cycles(session, workflow_id)
            if not has_cycles:
                validation_result["has_no_cycles"] = True
            else:
                validation_result["validation_errors"].append("Workflow contains cycles")
            
            # Check node connectivity
            all_connected = self.workflow_crud._check_node_connectivity(session, workflow_id)
            if all_connected:
                validation_result["all_nodes_connected"] = True
            else:
                validation_result["validation_errors"].append("Not all nodes are connected")
            
            # Overall completeness
            validation_result["is_complete"] = (
                validation_result["has_minimum_nodes"] and
                validation_result["has_no_cycles"] and
                validation_result["all_nodes_connected"]
            )
            
            return validation_result
        except Exception as e:
            context = self._create_error_context("validate_workflow_completeness", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e