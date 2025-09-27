from datetime import datetime, timezone
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from ..models import Workflow, WorkflowStatus, ExecutionStatus, Node, Edge, Execution, Trigger
from ..crud.base_crud import BaseCRUD

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError


class WorkflowCRUD(BaseCRUD[Workflow]):
    def __init__(self):
        super().__init__(Workflow)
        self.required_fields = [
            "name"
            ]
        self.protected_fields = [
            'total_executions', 'successful_executions', 'failed_executions', 'cancelled_executions', 
            'avg_execution_duration', 'min_execution_duration','max_execution_duration', 'last_executed_at', 
            'last_successful_execution_at','last_failed_execution_at', 'status'
            ]

    def _validate_name(self, session: Session, name: str, exclude_id: Optional[str] = None) -> str:
        if not name or not name.strip():
            context = ErrorContext(operation="validate_name", additional_info={"field": "name"})
            raise ValidationError("Workflow name cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        name = name.strip()
        
        if len(name) < 3:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name})
            raise ValidationError(f"Workflow name too short: {len(name)} chars (min 3)", context=context, severity=ErrorSeverity.MEDIUM)

        if len(name) > 100:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name})
            raise ValidationError(f"Workflow name too long: {len(name)} chars (max 100)", context=context, severity=ErrorSeverity.MEDIUM)
    
        existing = session.query(Workflow).filter(Workflow.name == name).first()
        if existing and existing.id != exclude_id:
            context = ErrorContext(operation="validate_name", additional_info={"field": "name", "value": name, "existing_id": existing.id})
            raise ValidationError(f"Workflow name '{name}' already exists", context=context, severity=ErrorSeverity.HIGH)
        
        return name
    
    def _validate_priority(self, priority: int) -> int:
        if priority < 0:
            context = ErrorContext(operation="validate_priority", additional_info={"field": "priority", "value": priority})
            raise ValidationError(f"Priority cannot be negative: {priority}", context=context, severity=ErrorSeverity.MEDIUM)
        
        if priority > 10:
            context = ErrorContext(operation="validate_priority", additional_info={"field": "priority", "value": priority})
            raise ValidationError(f"Priority too high: {priority} (max 10)", context=context, severity=ErrorSeverity.MEDIUM)

    def _validate_status_transition(self, session: Session, workflow_id: str, new_status: WorkflowStatus) -> bool:
        try:
            current_workflow = self._get_by_id(session, workflow_id)
            if not current_workflow:
                context = ErrorContext(operation="validate_status_transition", additional_info={"workflow_id": workflow_id})
                raise ValidationError(f"Workflow {workflow_id} not found", context=context, severity=ErrorSeverity.HIGH)
            
            current_status = current_workflow.status
            
            if current_status == new_status:
                self.logger.debug(f"Workflow {workflow_id} status unchanged: {current_status.value}")
                return True
            
            valid_status_transitions = {
                WorkflowStatus.DRAFT: [WorkflowStatus.ACTIVE, WorkflowStatus.DEACTIVATED],
                WorkflowStatus.ACTIVE: [WorkflowStatus.DEACTIVATED],
                WorkflowStatus.DEACTIVATED: [WorkflowStatus.ACTIVE]
            }
            
            allowed_transitions = valid_status_transitions.get(current_status, [])
            if new_status not in allowed_transitions:
                context = ErrorContext(operation="validate_status_transition", additional_info={"workflow_id": workflow_id, "current_status": current_status.value, "new_status": new_status.value,"allowed_transitions": [t.value for t in allowed_transitions]})
                raise ValidationError(f"Invalid status transition from {current_status.value} to {new_status.value}. Allowed transitions from {current_status.value}: {[t.value for t in allowed_transitions]}",context=context, severity=ErrorSeverity.HIGH)
            
            if new_status == WorkflowStatus.ACTIVE:
                self._validate_workflow_completeness(session, workflow_id)

            self.logger.info(f"Valid status transition for workflow {workflow_id}: {current_status.value} -> {new_status.value}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="validate_status_transition", additional_info={"workflow_id": workflow_id, "new_status": new_status.value})
            self.logger.error(f"Failed to validate status transition for workflow {workflow_id}: {str(e)}")
            raise ValidationError(f"Failed to validate status transition: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _validate_workflow_completeness(self, session: Session, workflow_id: str) -> bool:
        try:
            # Get all nodes and edges
            nodes = session.query(Node).filter(Node.workflow_id == workflow_id).all()
            edges = session.query(Edge).filter(Edge.workflow_id == workflow_id).all()
            
            node_count = len(nodes)
            edge_count = len(edges)
            
            # 1. Check minimum 1 node
            if node_count == 0:
                context = ErrorContext(operation="validate_completeness", additional_info={"workflow_id": workflow_id, "issue": "no_nodes"})
                raise ValidationError("Cannot activate workflow without nodes", context=context, severity=ErrorSeverity.HIGH)
            
            # For single node workflows, no further validation needed
            if node_count == 1:
                return True
            
            # 2. Check for cycles
            if edge_count > 0:
                self._detect_cycles(session, workflow_id)
            
            # 3. Check all nodes are connected
            if edge_count > 0:
                self._check_node_connectivity(session, workflow_id)
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="validate_completeness", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to validate workflow completeness for {workflow_id}: {str(e)}")
            raise ValidationError(f"Failed to validate workflow completeness: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _detect_cycles(self, session: Session, workflow_id: str) -> bool:
        try:
            # Get nodes and edges
            nodes = session.query(Node).filter(Node.workflow_id == workflow_id).all()
            edges = session.query(Edge).filter(Edge.workflow_id == workflow_id).all()
            
            # Build adjacency list
            graph = {node.id: [] for node in nodes}
            for edge in edges:
                graph[edge.from_node_id].append(edge.to_node_id)
            
            # DFS cycle detection
            visited = set()
            rec_stack = set()
            
            def has_cycle(node_id):
                if node_id in rec_stack:
                    return True
                if node_id in visited:
                    return False
                
                visited.add(node_id)
                rec_stack.add(node_id)
                
                for neighbor in graph[node_id]:
                    if has_cycle(neighbor):
                        return True
                
                rec_stack.remove(node_id)
                return False
            
            for node in nodes:
                if node.id not in visited:
                    if has_cycle(node.id):
                        context = ErrorContext(operation="detect_cycles", additional_info={"workflow_id": workflow_id, "issue": "cycle_detected"})
                        raise ValidationError("Workflow contains cycles which are not allowed", context=context, severity=ErrorSeverity.HIGH)
            
            return False  # No cycles found
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="detect_cycles", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to detect cycles for workflow {workflow_id}: {str(e)}")
            raise ValidationError(f"Failed to detect cycles: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _check_node_connectivity(self, session: Session, workflow_id: str) -> bool:
        try:
            # Get nodes and edges
            nodes = session.query(Node).filter(Node.workflow_id == workflow_id).all()
            edges = session.query(Edge).filter(Edge.workflow_id == workflow_id).all()
            
            # Build adjacency list for both directions
            outgoing = {node.id: [] for node in nodes}
            incoming = {node.id: [] for node in nodes}
            
            for edge in edges:
                outgoing[edge.from_node_id].append(edge.to_node_id)
                incoming[edge.to_node_id].append(edge.from_node_id)
            
            # Find isolated nodes (no incoming or outgoing edges)
            isolated_nodes = []
            for node in nodes:
                if len(outgoing[node.id]) == 0 and len(incoming[node.id]) == 0:
                    isolated_nodes.append(node.id)
            
            if isolated_nodes:
                context = ErrorContext(operation="check_connectivity", additional_info={"workflow_id": workflow_id, "issue": "isolated_nodes", "isolated_nodes": isolated_nodes})
                raise ValidationError(f"Workflow has isolated nodes: {isolated_nodes}. All nodes must be connected.", context=context, severity=ErrorSeverity.HIGH)
            
            return True  # All nodes connected
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="check_connectivity", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to check node connectivity for workflow {workflow_id}: {str(e)}")
            raise ValidationError(f"Failed to check node connectivity: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _get_workflow_nodes(self, session: Session, workflow_id: str) -> List[Node]:
        try:
            nodes = session.query(Node).filter(Node.workflow_id == workflow_id).all()
            return nodes
        except Exception as e:
            context = ErrorContext(operation="get_workflow_nodes", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to get workflow nodes for {workflow_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get workflow nodes: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _get_workflow_edges(self, session: Session, workflow_id: str) -> List[Edge]:
        try:
            edges = session.query(Edge).filter(Edge.workflow_id == workflow_id).all()
            return edges
        except Exception as e:
            context = ErrorContext(operation="get_workflow_edges", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to get workflow edges for {workflow_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get workflow edges: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _get_workflow_triggers(self, session: Session, workflow_id: str) -> List[Trigger]:
        try:
            triggers = session.query(Trigger).filter(Trigger.workflow_id == workflow_id).all()
            return triggers
        except Exception as e:
            context = ErrorContext(operation="get_workflow_triggers", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to get workflow triggers for {workflow_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get workflow triggers: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _validate_deletion_safety(self, session: Session, workflow_id: str) -> Dict[str, Any]:
        workflow = self._get_by_id(session, workflow_id)
        
        if not workflow:
            raise ValidationError(f"Workflow {workflow_id} not found", severity=ErrorSeverity.HIGH)
        
        active_executions = session.query(func.count(Execution.id)).filter(
             and_(
                Execution.workflow_id == workflow_id,
                Execution.status.in_([ExecutionStatus.PENDING, ExecutionStatus.RUNNING])
            )
        ).scalar()
        
        if active_executions > 0:
            context = ErrorContext(operation="validate_deletion", additional_info={"workflow_id": workflow_id, "active_executions": active_executions})
            raise ValidationError(f"Cannot delete workflow with {active_executions} active executions",context=context, severity=ErrorSeverity.HIGH)
        
    def _create(self, session: Session, **kwargs) -> Workflow:
        try:
            self.logger.debug(f"Creating workflow with data: {kwargs}")
            
            # VALIDATION - Required fields
            self._validate_required_fields(self.required_fields, kwargs)
        
            # VALIDATION - Name
            name = kwargs.get('name')
            kwargs['name'] = self._validate_name(session, name)
            
            # VALIDATION - Priority
            priority = kwargs.get('priority', 0)
            self._validate_priority(priority)

            # VALIDATION - Status (Set to DRAFT)
            if "status" in kwargs:
                kwargs["status"] = WorkflowStatus.DRAFT

            # VALIDATION - Protected fields
            protected_fields = self._validate_protected_fields(self.protected_fields, kwargs)

            # VALIDATION - Request data
            valid_fields, invalid_fields = self._validate_request_data(protected_fields)

            # OPERATION - Create workflow
            workflow = super()._create(session, **valid_fields)
            self.logger.info(f"Successfully created workflow: {workflow.name} ({workflow.id})")
            return workflow
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="create", additional_info={"workflow_data": kwargs})
            self.logger.error(f"Failed to create workflow: {str(e)}")
            raise ValidationError(f"Failed to create workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _update(self, session: Session, record_id: str, **kwargs) -> Workflow:
        try:
            self.logger.debug(f"Updating workflow {record_id} with data: {kwargs}")
            
            # VALIDATION - Name
            if "name" in kwargs:
                kwargs['name'] = self._validate_name(session, kwargs['name'], exclude_id=record_id)
            
            # VALIDATION - Priority
            if "priority" in kwargs:
                priority = kwargs['priority']
                self._validate_priority(priority)

            # VALIDATION - Protected fields
            protected_fields = self._validate_protected_fields(self.protected_fields, kwargs)   

            # VALIDATION - Request data
            valid_fields, invalid_fields = self._validate_request_data(protected_fields) 
            
            # OPERATION - Update workflow
            workflow = super()._update(session, record_id, **valid_fields)
            self.logger.info(f"Successfully updated workflow: {workflow.name} ({workflow.id})")
            return workflow
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="update", additional_info={"workflow_id": record_id, "update_data": kwargs})
            self.logger.error(f"Failed to update workflow {record_id}: {str(e)}")
            raise ValidationError(f"Failed to update workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _delete(self, session: Session, record_id: str) -> bool:
        try:
            self.logger.debug(f"Attempting to delete workflow: {record_id}")

            # OPERATION - Delete workflow
            result = super()._delete(session, record_id)
            self.logger.info(f"Successfully deleted workflow: {record_id}")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="delete", additional_info={"workflow_id": record_id})
            self.logger.error(f"Failed to delete workflow {record_id}: {str(e)}")
            raise ValidationError(f"Failed to delete workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _update_stats(self, session, workflow_id: str, execution_status: ExecutionStatus, execution_duration: float = None) -> None:
        try:
            self.logger.debug(f"Updating stats for workflow {workflow_id}, status: {execution_status.value}")
            
            # Get current workflow
            current_workflow = self._get_by_id(session, workflow_id)
            if not current_workflow:
                context = ErrorContext(operation="update_stats", additional_info={"workflow_id": workflow_id})
                raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.HIGH)

            # Prepare update data
            current_time = datetime.now(timezone.utc)
            update_data = {
                "total_executions": current_workflow.total_executions + 1,
                "last_executed_at": current_time
            }

            # Update status-specific counts and timestamps
            if execution_status == ExecutionStatus.COMPLETED:
                update_data["successful_executions"] = current_workflow.successful_executions + 1
                update_data["last_successful_execution_at"] = current_time
            elif execution_status == ExecutionStatus.FAILED:
                update_data["failed_executions"] = current_workflow.failed_executions + 1
                update_data["last_failed_execution_at"] = current_time
            elif execution_status == ExecutionStatus.CANCELLED:
                update_data["cancelled_executions"] = current_workflow.cancelled_executions + 1

            # Update duration statistics if provided
            if execution_duration is not None and execution_duration > 0:
                if current_workflow.min_execution_duration is None or execution_duration < current_workflow.min_execution_duration:
                    update_data["min_execution_duration"] = execution_duration
                
                if current_workflow.max_execution_duration is None or execution_duration > current_workflow.max_execution_duration:
                    update_data["max_execution_duration"] = execution_duration
                
                # Calculate new average duration
                if current_workflow.avg_execution_duration is None:
                    update_data["avg_execution_duration"] = execution_duration
                else:
                    # Weighted average calculation
                    total_previous_duration = current_workflow.avg_execution_duration * (current_workflow.total_executions - 1)
                    update_data["avg_execution_duration"] = (total_previous_duration + execution_duration) / (current_workflow.total_executions + 1)

            # OPERATION - Update stats
            super()._update(session, workflow_id, **update_data)
            
            self.logger.info(f"Successfully updated stats for workflow {workflow_id}")
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="update_stats", additional_info={"workflow_id": workflow_id, "execution_status": execution_status.value})
            self.logger.error(f"Failed to update stats for workflow {workflow_id}: {str(e)}")
            raise ValidationError(f"Failed to update workflow stats: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _get_stats(self, session, workflow_id: str) -> Dict[str, Any]:
        workflow = self._get_by_id(session, workflow_id)
        if not workflow:
            raise ValidationError(f"Workflow '{workflow_id}' not found", severity=ErrorSeverity.HIGH)

        return {
            "total_executions": workflow.total_executions,
            "successful_executions": workflow.successful_executions,
            "failed_executions": workflow.failed_executions,
            "cancelled_executions": workflow.cancelled_executions,
            "avg_execution_duration": workflow.avg_execution_duration,
            "min_execution_duration": workflow.min_execution_duration,
            "max_execution_duration": workflow.max_execution_duration,
            "last_executed_at": workflow.last_executed_at,
            "last_successful_execution_at": workflow.last_successful_execution_at,
            "last_failed_execution_at": workflow.last_failed_execution_at,
        }

    def _get_recently_executed(self, session: Session, limit: int = 10) -> List[Workflow]:
        try:
            limit = min(max(1, limit), 100)  # Between 1 and 100     
            results = session.query(Workflow).filter(Workflow.last_executed_at.isnot(None)).order_by(desc(Workflow.last_executed_at)).limit(limit).all()
            return results    
        except Exception as e:
            context = self._create_error_context("get_recently_executed", limit=limit)
            raise ValidationError(f"Failed to get recently executed workflows: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _update_status(self, session: Session, workflow_id: str, status: WorkflowStatus) -> Workflow:
        try:
            self.logger.debug(f"Updating workflow {workflow_id} status to {status.value}")
            
            current_workflow = self._get_by_id(session, workflow_id)
            if not current_workflow:
                context = ErrorContext(operation="update_status", additional_info={"workflow_id": workflow_id})
                raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.HIGH)
            
            old_status = current_workflow.status

            # VALIDATION - Status transition
            self._validate_status_transition(session, workflow_id, status)
            
            # OPERATION - Update status
            workflow = super()._update(session, workflow_id, status=status)
            
            self.logger.info(f"Successfully updated workflow {workflow_id} status: {old_status.value} -> {status.value}")
            return workflow
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="update_status", additional_info={"workflow_id": workflow_id, "new_status": status.value})
            self.logger.error(f"Failed to update workflow {workflow_id} status: {str(e)}")
            raise ValidationError(f"Failed to update workflow status: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _get_workflow_graph(self, session: Session, workflow_id: str) -> Dict[str, Any]:
        try:
            self.logger.debug(f"Building complete graph for workflow {workflow_id}")
            
            nodes = session.query(Node).filter(Node.workflow_id == workflow_id).all()
            edges = self._get_workflow_edges(session, workflow_id)
            triggers = session.query(Trigger).filter(Trigger.workflow_id == workflow_id).all()
            
            outgoing = {node.id: [] for node in nodes}
            incoming = {node.id: [] for node in nodes}
            
            for edge in edges:
                outgoing[edge.from_node_id].append({
                    "to_node_id": edge.to_node_id,
                    "condition_type": edge.condition_type.value,
                    "edge_id": edge.id
                })
                incoming[edge.to_node_id].append({
                    "from_node_id": edge.from_node_id,
                    "condition_type": edge.condition_type.value,
                    "edge_id": edge.id
                })
            
            graph_info = {
                "workflow_id": workflow_id,
                "metadata": {
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "trigger_count": len(triggers),
                    "has_triggers": len(triggers) > 0
                },
                "nodes": [
                    {
                        "id": node.id, 
                        "name": node.name,
                        "description": node.description,
                        "script_id": node.script_id,
                        "input_params": node.input_params,
                        "output_params": node.output_params,
                        "meta_data": node.meta_data,
                        "max_retries": node.max_retries,
                        "timeout_seconds": node.timeout_seconds,
                        "created_at": node.created_at.isoformat() if node.created_at else None,
                        "updated_at": node.updated_at.isoformat() if node.updated_at else None
                    } 
                    for node in nodes
                ],
                "edges": [
                    {
                        "id": edge.id, 
                        "workflow_id": edge.workflow_id,
                        "from": edge.from_node_id, 
                        "to": edge.to_node_id, 
                        "condition_type": edge.condition_type.value,
                        "created_at": edge.created_at.isoformat() if edge.created_at else None,
                        "updated_at": edge.updated_at.isoformat() if edge.updated_at else None
                    } 
                    for edge in edges
                ],
                "triggers": [
                    {
                        "id": trigger.id,
                        "name": trigger.name,
                        "description": trigger.description,
                        "trigger_type": trigger.trigger_type.value,
                        "status": trigger.status.value,
                        "config": trigger.config,
                        "input_mapping": trigger.input_mapping,
                        "created_at": trigger.created_at.isoformat() if trigger.created_at else None,
                        "updated_at": trigger.updated_at.isoformat() if trigger.updated_at else None
                    }
                    for trigger in triggers
                ],
                "adjacency": {
                    "outgoing": outgoing,
                    "incoming": incoming
                },
                "graph_analysis": {
                    "has_cycles": self._detect_cycles(session, workflow_id),
                    "is_connected": self._check_node_connectivity(session, workflow_id),
                    "entry_points": [node.id for node in nodes if not incoming[node.id]],
                    "exit_points": [node.id for node in nodes if not outgoing[node.id]],
                    "trigger_types": list(set([t.trigger_type.value for t in triggers]))
                }
            }
            
            self.logger.info(f"Built complete graph for workflow {workflow_id}: {len(nodes)} nodes, {len(edges)} edges, {len(triggers)} triggers")
            return graph_info
            
        except Exception as e:
            context = ErrorContext(operation="get_workflow_graph", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to get workflow graph for {workflow_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get workflow graph: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e