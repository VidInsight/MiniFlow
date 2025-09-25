from typing import Optional, List, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_, or_

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity, ErrorContext
from ..models import Edge, Node, Workflow, ConditionType, WorkflowStatus
from ..crud.base_crud import BaseCRUD


class EdgeCRUD(BaseCRUD[Edge]):
    def __init__(self):
        super().__init__(Edge)
        self.required_fields = [
            "workflow_id", "from_node_id", "to_node_id", "condition_type"
        ]
        self.protected_fields = [
            'created_at', 'updated_at', 'id'
        ]
    
    def _validate_workflow_exists(self, session: Session, workflow_id: str) -> Workflow:
        workflow = session.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            context = ErrorContext(operation="validate_workflow_for_edge", additional_info={"workflow_id": workflow_id})
            raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.HIGH)
    
    def _validate_node_exists(self, session: Session, node_id: str, workflow_id: str) -> Node:
        node = session.query(Node).filter(and_(Node.id == node_id,Node.workflow_id == workflow_id)).first()
        if not node:
            context = ErrorContext(operation="validate_node", additional_info={"node_id": node_id, "workflow_id": workflow_id})
            raise ValidationError(f"Node '{node_id}' not found in workflow '{workflow_id}'", context=context,severity=ErrorSeverity.HIGH)
    
    def _validate_self_loop(self, from_node_id: str, to_node_id: str) -> None:
        if from_node_id == to_node_id:
            context = ErrorContext(operation="validate_self_loop", additional_info={"from_node_id": from_node_id, "to_node_id": to_node_id})
            raise ValidationError(f"Self-loops are not allowed: from_node_id '{from_node_id}' cannot be the same as to_node_id '{to_node_id}'", context=context, severity=ErrorSeverity.MEDIUM)    
    
    def _validate_duplicate_edge(self, session: Session, workflow_id: str, from_node_id: str, to_node_id: str, condition_type: ConditionType, exclude_id: Optional[str] = None) -> None:
        query = session.query(Edge).filter(and_(Edge.workflow_id == workflow_id, Edge.from_node_id == from_node_id, Edge.to_node_id == to_node_id, Edge.condition_type == condition_type))
        
        if exclude_id:
            query = query.filter(Edge.id != exclude_id)
        
        existing = query.first()
        if existing:
            context = ErrorContext(operation="validate_duplicate", additional_info={"workflow_id": workflow_id, "from_node_id": from_node_id, "to_node_id": to_node_id, "condition_type": condition_type.value, "exclude_id": exclude_id})
            raise ValidationError(f"Edge already exists between nodes '{from_node_id}' and '{to_node_id} with condition type '{condition_type.value}'", context=context, severity=ErrorSeverity.MEDIUM)
    
    def _validate_condition_type(self, condition_type: Any) -> ConditionType:
        if isinstance(condition_type, str):
            try:
                return ConditionType(condition_type)
            except ValueError:
                valid_types = [ct.value for ct in ConditionType]
                context = ErrorContext(operation="validate_condition_type", additional_info={"provided_type": condition_type, "valid_types": valid_types})
                raise ValidationError(f"Invalid condition type '{condition_type}'. Valid types: {valid_types}", context=context,severity=ErrorSeverity.MEDIUM)
        else:
            context = ErrorContext(operation="validate_condition_type", additional_info={"provided_type": str(type(condition_type))})
            raise ValidationError(f"Condition type must be a string or ConditionType enum, got {type(condition_type)}", context=context, severity=ErrorSeverity.MEDIUM)

    def _validate_deletion_safety(self, session: Session, edge_id: str) -> None:
        edge = self._get_by_id(session, edge_id)
        if not edge:
            context = ErrorContext(operation="validate_deletion", additional_info={"node_id": edge_id})
            raise ValidationError(f"Node '{edge_id}' not found", context=context, severity=ErrorSeverity.HIGH)
        
        workflow = session.query(Workflow).filter(Workflow.id == edge.workflow_id).first()
        if workflow and workflow.status == WorkflowStatus.ACTIVE:
            self.logger.warning(f"Deactivating workflow {workflow.id} before deleting node {edge_id}")
            workflow.status = WorkflowStatus.DEACTIVATED
            workflow.status_message = "Workflow automatically deactivated due to edge deletion"
            session.flush()  
            self.logger.info(f"Workflow {workflow.id} automatically deactivated due to node deletion")

    def _create(self, session: Session, **kwargs) -> Edge:
        try:
            self.logger.debug(f"Creating edge with data: {kwargs}")
            self._validate_required_fields(self.required_fields, kwargs)

            workflow_id = kwargs.get("workflow_id")
            from_node_id = kwargs.get("from_node_id")
            to_node_id = kwargs.get("to_node_id")
            condition_type = kwargs.get("condition_type", ConditionType.SUCCESS)
            
            self._validate_workflow_exists(session, workflow_id)
            self._validate_node_exists(session, from_node_id, workflow_id)
            self._validate_node_exists(session, to_node_id, workflow_id)
            self._validate_self_loop(from_node_id, to_node_id)
            self._validate_condition_type(condition_type)
            self._validate_duplicate_edge(session, workflow_id, from_node_id, to_node_id, condition_type)
            
            valid_fields, invalid_fields = self._validate_request_data(kwargs)
            edge = super()._create(session, **valid_fields)
            self.logger.info(f"Successfully created edge: {edge.id} ({from_node_id} -> {to_node_id})")
            return edge
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="create", additional_info={"edge_data": kwargs})
            self.logger.error(f"Failed to create edge: {str(e)}")
            raise ValidationError(f"Failed to create edge: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _update(self, session: Session, record_id: str, **kwargs) -> Edge:
        try:
            self.logger.debug(f"Updating edge {record_id} with data: {kwargs}")
            
            existing_edge = self._get_by_id(session, record_id)
            if not existing_edge:
                raise ValidationError(f"Edge '{record_id}' not found", severity=ErrorSeverity.HIGH)

            if "workflow_id" in kwargs:
                self._validate_workflow_exists(session, kwargs["workflow_id"])
            
            if "from_node_id" in kwargs:
                workflow_id = kwargs.get("workflow_id", existing_edge.workflow_id)
                self._validate_node_exists(session, kwargs["from_node_id"], workflow_id)
            
            if "to_node_id" in kwargs:
                workflow_id = kwargs.get("workflow_id", existing_edge.workflow_id)
                self._validate_node_exists(session, kwargs["to_node_id"], workflow_id)
            
            if "condition_type" in kwargs:
                condition_type = self._validate_condition_type(kwargs["condition_type"])
                kwargs["condition_type"] = condition_type
            else:
                condition_type = existing_edge.condition_type
            
            workflow_id = kwargs.get("workflow_id", existing_edge.workflow_id)
            from_node_id = kwargs.get("from_node_id", existing_edge.from_node_id)
            to_node_id = kwargs.get("to_node_id", existing_edge.to_node_id)
            self._validate_duplicate_edge(session, workflow_id, from_node_id, to_node_id, condition_type, exclude_id=record_id)
        
            protected_fields = self._validate_protected_fields(self.protected_fields, kwargs)
            valid_fields, invalid_fields = self._validate_request_data(protected_fields) 

            edge = super()._update(session, record_id, **valid_fields)
            self.logger.info(f"Successfully updated edge: {edge.id}")
            return edge
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="update", additional_info={"edge_id": record_id, "update_data": kwargs})
            self.logger.error(f"Failed to update edge {record_id}: {str(e)}")
            raise ValidationError(f"Failed to update edge: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _delete(self, session: Session, record_id: str) -> Edge:
        try:
            self.logger.debug(f"Attempting to delete edge: {record_id}")
            
            self._validate_deletion_safety(session, record_id)
            
            result = super()._delete(session, record_id)
            self.logger.info(f"Successfully deleted edge: {record_id}")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            context = ErrorContext(operation="delete", additional_info={"edge_id": record_id})
            self.logger.error(f"Failed to delete edge {record_id}: {str(e)}")
            raise ValidationError(f"Failed to delete edge: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _get_outgoing_edges(self, session: Session, node_id: str) -> List[Edge]:
        try:
            edges = session.query(Edge).filter(Edge.from_node_id == node_id).all()
            self.logger.debug(f"Found {len(edges)} outgoing edges from node {node_id}")
            return edges
            
        except Exception as e:
            context = ErrorContext(operation="get_outgoing_edges", additional_info={"node_id": node_id})
            self.logger.error(f"Failed to get outgoing edges for node {node_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get outgoing edges for node: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _get_incoming_edges(self, session: Session, node_id: str) -> List[Edge]:
        try:
            edges = session.query(Edge).filter(Edge.to_node_id == node_id).all()
            self.logger.debug(f"Found {len(edges)} incoming edges to node {node_id}")
            return edges
            
        except Exception as e:
            context = ErrorContext(operation="get_incoming_edges", additional_info={"node_id": node_id})
            self.logger.error(f"Failed to get incoming edges for node {node_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get incoming edges for node: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e
    
    def _get_workflow_edges(self, session: Session, workflow_id: str) -> List[Edge]:
        try:
            edges = session.query(Edge).filter(Edge.workflow_id == workflow_id).all()
            self.logger.debug(f"Found {len(edges)} edges in workflow {workflow_id}")
            return edges
            
        except Exception as e:
            context = ErrorContext(operation="get_workflow_edges", additional_info={"workflow_id": workflow_id})
            self.logger.error(f"Failed to get edges for workflow {workflow_id}: {str(e)}")
            raise DatabaseQueryError(f"Failed to get edges for workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e