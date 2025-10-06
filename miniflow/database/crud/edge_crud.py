from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Edge, Workflow
from ..enums import ConditionType
from .base_crud import BaseCRUD


class EdgeCRUD(BaseCRUD[Edge]):
    def __init__(self):
        super().__init__(Edge)
        self.model_fields = {column.name for column in Edge.__table__.columns}
        self.required_fields = {'workflow_id', 'from_node_id', 'to_node_id'}
        self.protected_fields = {'workflow_id'}

    # ========================================================================================= VALIDATION HELPERS =====
    def _validate_self_loop(self, from_node_id: str, to_node_id: str):
        """Validate that an edge does not create a self-loop."""
        if from_node_id == to_node_id:
            context = ErrorContext(operation='validate_self_loop',component=self.model_name,additional_info={'node_id': from_node_id})
            raise ValidationError(f"Self-loop detected: Edge cannot connect node {from_node_id} to itself",context=context,severity=ErrorSeverity.MEDIUM)

    def _validate_edge_uniqueness(self, session: Session, workflow_id: str, from_node_id: str, to_node_id: str,condition_type: ConditionType,exclude_edge_id: Optional[str] = None):
        query = session.query(self.model).filter(
            and_(
                self.model.workflow_id == workflow_id,
                self.model.from_node_id == from_node_id,
                self.model.to_node_id == to_node_id,
                self.model.condition_type == condition_type,
                self.model.is_deleted == False
            )
        )

        # Exclude current edge when updating
        if exclude_edge_id:
            query = query.filter(self.model.id != exclude_edge_id)

        existing = query.first()

        if existing:
            context = ErrorContext(operation='validate_edge_uniqueness',component=self.model_name,additional_info={'workflow_id': workflow_id,'existing_edge_id': existing.id})
            raise ValidationError(f"Duplicate edge: {from_node_id} → {to_node_id} with condition '{condition_type.value}' already exists",context=context,severity=ErrorSeverity.MEDIUM)

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> Edge:
        """Create a new edge with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)

        workflow_id = kwargs.get('workflow_id')
        from_node_id = kwargs.get('from_node_id')
        to_node_id = kwargs.get('to_node_id')
        condition_type = kwargs.get("condition_type")

        #  Validate self-loop (from_node_id != to_node_id)
        self._validate_self_loop(from_node_id=from_node_id, to_node_id=to_node_id)

        # Check for duplicate edge (workflow_id + from_node_id + to_node_id + condition_type must be unique)
        self._validate_edge_uniqueness(session, workflow_id, from_node_id, to_node_id, condition_type)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        edge = super()._create(session, **kwargs)
        return edge

    def _update(self, session: Session, record_id: str, **kwargs) -> Edge:
        """Update edge with validation."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        # Get existing edge
        edge = self._get_by_id(session, record_id)
        if not edge:
            self._raise_not_found_error(operation="_update", record_id=record_id)

        # Get from_node_id and to_node_id (use existing if not being updated)
        from_node_id = kwargs.get('from_node_id', edge.from_node_id)
        to_node_id = kwargs.get('to_node_id', edge.to_node_id)
        condition_type = kwargs.get('condition_type', edge.condition_type)

        # Validate self-loop (from_node_id != to_node_id)
        self._validate_self_loop(from_node_id=from_node_id, to_node_id=to_node_id)
        
        # Check for duplicate edge if from/to/condition being changed
        if 'from_node_id' in kwargs or 'to_node_id' in kwargs or 'condition_type' in kwargs:
            self._validate_edge_uniqueness(session, edge.workflow_id, from_node_id, to_node_id, condition_type, exclude_edge_id=record_id)
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        edge = super()._update(session, record_id, **kwargs)
        return edge

    # =================================================================================== ORCHESTRATION OPERATIONS =====
    def _get_next_nodes(self, session: Session, from_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Edge]:
        """Get all outgoing edges from a node, optionally filtered by condition type."""
        try:
            query = session.query(self.model).filter(
                and_(
                    self.model.from_node_id == from_node_id,
                    self.model.is_deleted == False
                )
            )
            
            if condition_type is not None:
                query = query.filter(self.model.condition_type == condition_type)
            
            edges = query.order_by(self.model.created_at.asc()).all()
            return edges
            
        except Exception as e:
            context = ErrorContext(operation='get_next_nodes', component=self.model_name, additional_info={'from_node_id': from_node_id, 'condition_type': condition_type})
            raise DatabaseQueryError(f"Failed to get next nodes: {str(e)}", context=context, severity=ErrorSeverity.HIGH)

    def _get_previous_nodes(self, session: Session, to_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Edge]:
        """Get all incoming edges to a node, optionally filtered by condition type."""
        try:

            query = session.query(self.model).filter(
                and_(
                    self.model.to_node_id == to_node_id,
                    self.model.is_deleted == False
                )
            )
            
            if condition_type is not None:
                query = query.filter(self.model.condition_type == condition_type)
            
            edges = query.order_by(self.model.created_at.asc()).all()
            return edges
            
        except Exception as e:
            context = ErrorContext(operation='get_previous_nodes', component=self.model_name, additional_info={'to_node_id': to_node_id, 'condition_type': condition_type})
            raise DatabaseQueryError( f"Failed to get previous nodes: {str(e)}", context=context, severity=ErrorSeverity.HIGH)

    def _get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[Edge]:
        return self._get_all(
            session,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted,
            workflow_id=workflow_id
        )