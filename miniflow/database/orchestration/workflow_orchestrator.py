from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity
from miniflow.database.models import Workflow, WorkflowStatus, ExecutionStatus


class WorkflowOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)

    def _get_primary_crud(self):
        """Return the Workflow CRUD instance."""
        return self.workflow_crud

    @with_session
    def create(self, session: Session, name: str, **kwargs) -> Dict[str, Any]:
        try:
            result = self.workflow_crud._create_with_validation(session, name, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_name(self, session: Session, name: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get workflow by name using filter."""
        if not name:
            return None
        
        try:
            results = self.workflow_crud._filter(session, filters={"name": name.strip()}, limit=1)
            return self._serialize_single_result(results[0] if results else None, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, workflow_id: str, **kwargs) -> Dict[str, Any]:
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "update")

        try:
            result = self.workflow_crud._update_with_validation(session, workflow_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, workflow_id: str) -> Dict[str, Any]:
        """Delete workflow with cascade operations."""
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "delete")
        
        try:
            # Check for active executions - use separate queries for each status
            running_executions = self.execution_crud._filter(session, {"workflow_id": workflow_id, "status": ExecutionStatus.RUNNING}, limit=1)
            pending_executions = self.execution_crud._filter(session, {"workflow_id": workflow_id, "status": ExecutionStatus.PENDING}, limit=1)
            
            if running_executions or pending_executions:
                raise OrchestrationError(f"Cannot delete workflow '{workflow_id}' - it has active executions", ErrorSeverity.HIGH)
            
            # Delete all executions for this workflow (this will handle inputs/outputs)
            executions = self.execution_crud._filter(session, {"workflow_id": workflow_id})
            for execution in executions:
                self.execution_crud._delete_execution(session, execution.id)
            
            # Delete all nodes (nodes will handle their own edge deletions)
            nodes = self.node_crud._filter(session, {"workflow_id": workflow_id})
            for node in nodes:
                self.node_crud._delete(session, node.id)
            
            # Finally delete the workflow
            self.workflow_crud._delete(session, workflow_id)
            return {"deleted": True, "workflow_id": workflow_id}
            
        except Exception as e:
            context = self._create_error_context("delete", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int