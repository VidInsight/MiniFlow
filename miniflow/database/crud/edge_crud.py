from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Edge
from ..enums import ConditionType
from .base_crud import BaseCRUD


class EdgeCRUD(BaseCRUD[Edge]):
    def __init__(self):
        super().__init__(Edge)
        self.model_fields = {column.name for column in Edge.__table__.columns}
        self.required_fields = {'workflow_id', 'from_node_id', 'to_node_id'}
        self.protected_fields = {'workflow_id'}

    def _create(self, session: Session, **kwargs) -> Edge:
        """Create a new edge with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate workflow_id
        workflow_id = kwargs['workflow_id']
        kwargs['workflow_id'] = validators._validate_id(workflow_id)
        
        # Validate from_node_id
        from_node_id = kwargs['from_node_id']
        kwargs['from_node_id'] = validators._validate_id(from_node_id)
        
        # Validate to_node_id
        to_node_id = kwargs['to_node_id']
        kwargs['to_node_id'] = validators._validate_id(to_node_id)
        
        # CRITICAL: Validate self-loop (from_node_id != to_node_id)
        if from_node_id == to_node_id:
            context = ErrorContext(
                operation='create_edge',
                component=self.model_name,
                additional_info={
                    'workflow_id': workflow_id,
                    'node_id': from_node_id
                }
            )
            raise ValidationError(
                f"Self-loop detected: Edge cannot connect node {from_node_id} to itself",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        # Validate condition_type
        condition_type = kwargs.get("condition_type", ConditionType.SUCCESS)
        kwargs['condition_type'] = self._validate_condition_type(condition_type)
        
        # Check for duplicate edge (workflow_id + from_node_id + to_node_id + condition_type must be unique)
        self._validate_edge_uniqueness(
            session,
            kwargs['workflow_id'],
            kwargs['from_node_id'],
            kwargs['to_node_id'],
            kwargs['condition_type']
        )
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        edge = super()._create(session, **kwargs)
        return edge

    def _update(self, session: Session, record_id: str, **kwargs) -> Edge:
        """Update edge with validation."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Get existing edge
        edge = self._get_by_id(session, record_id)
        if not edge:
            context = ErrorContext(
                operation='update_edge',
                component=self.model_name,
                additional_info={'id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        # Get from_node_id and to_node_id (use existing if not being updated)
        from_node_id = kwargs.get('from_node_id', edge.from_node_id)
        to_node_id = kwargs.get('to_node_id', edge.to_node_id)
        condition_type = kwargs.get('condition_type', edge.condition_type)
        
        # Validate IDs if being updated
        if 'from_node_id' in kwargs:
            kwargs['from_node_id'] = validators._validate_id(from_node_id)
        if 'to_node_id' in kwargs:
            kwargs['to_node_id'] = validators._validate_id(to_node_id)
        
        # CRITICAL: Validate self-loop (from_node_id != to_node_id)
        if from_node_id == to_node_id:
            context = ErrorContext(
                operation='update_edge',
                component=self.model_name,
                additional_info={
                    'id': record_id,
                    'workflow_id': edge.workflow_id,
                    'node_id': from_node_id
                }
            )
            raise ValidationError(
                f"Self-loop detected: Edge cannot connect node {from_node_id} to itself",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        # Validate condition_type if being updated
        if 'condition_type' in kwargs:
            kwargs['condition_type'] = self._validate_condition_type(condition_type)
        
        # Check for duplicate edge if from/to/condition being changed
        if 'from_node_id' in kwargs or 'to_node_id' in kwargs or 'condition_type' in kwargs:
            self._validate_edge_uniqueness(
                session,
                edge.workflow_id,
                from_node_id,
                to_node_id,
                condition_type,
                exclude_edge_id=record_id  # Exclude current edge from uniqueness check
            )
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        edge = super()._update(session, record_id, **kwargs)
        return edge

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


    def _validate_edge_uniqueness(
        self, 
        session: Session, 
        workflow_id: str, 
        from_node_id: str, 
        to_node_id: str,
        condition_type: ConditionType,
        exclude_edge_id: Optional[str] = None
    ):
        """
        Validate that edge is unique in workflow.
        
        According to models.py UniqueConstraint:
        ('workflow_id', 'from_node_id', 'to_node_id', 'condition_type')
        
        Multiple edges with same from→to are allowed if they have different condition_type:
        - Edge 1: A→B (SUCCESS)
        - Edge 2: A→B (FAILURE)
        - Edge 3: A→B (ALWAYS)
        
        Args:
            session: Database session
            workflow_id: Workflow ID
            from_node_id: Source node ID
            to_node_id: Target node ID
            condition_type: Edge condition type
            exclude_edge_id: Edge ID to exclude from check (for updates)
        """
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
            context = ErrorContext(
                operation='validate_edge_uniqueness',
                component=self.model_name,
                additional_info={
                    'workflow_id': workflow_id,
                    'from_node_id': from_node_id,
                    'to_node_id': to_node_id,
                    'condition_type': condition_type.value if isinstance(condition_type, ConditionType) else condition_type,
                    'existing_edge_id': existing.id
                }
            )
            raise ValidationError(
                f"Duplicate edge: {from_node_id} → {to_node_id} with condition '{condition_type.value}' already exists",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )

    def _get_by_workflow(self, session: Session, workflow_id: str, 
                        skip: int = 0, limit: int = None) -> List[Edge]:
        """Get all edges for a workflow."""
        try:
            workflow_id = validators._validate_id(workflow_id)
            
            if not isinstance(skip, int) or skip < 0:
                raise ValueError("Offset must be a non-negative integer")
            
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise ValueError("Limit must be a positive integer or None")
            
            query = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.asc()
            ).offset(skip)
            
            if limit is not None:
                query = query.limit(limit)
            
            results = query.all()
            return results
            
        except Exception as e:
            context = ErrorContext(operation='get_by_workflow', component=self.model_name,
                                 additional_info={'workflow_id': workflow_id, 'offset': skip, 'limit': limit})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by workflow: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_from_node(self, session: Session, from_node_id: str) -> List[Edge]:
        """Get all outgoing edges from a node."""
        try:
            from_node_id = validators._validate_id(from_node_id)
            
            edges = session.query(self.model).filter(
                and_(
                    self.model.from_node_id == from_node_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.asc()
            ).all()
            
            return edges
            
        except Exception as e:
            context = ErrorContext(operation='get_by_from_node', component=self.model_name,
                                 additional_info={'from_node_id': from_node_id})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by from_node: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_by_to_node(self, session: Session, to_node_id: str) -> List[Edge]:
        """Get all incoming edges to a node."""
        try:
            to_node_id = validators._validate_id(to_node_id)
            
            edges = session.query(self.model).filter(
                and_(
                    self.model.to_node_id == to_node_id,
                    self.model.is_deleted == False
                )
            ).order_by(
                self.model.created_at.asc()
            ).all()
            
            return edges
            
        except Exception as e:
            context = ErrorContext(operation='get_by_to_node', component=self.model_name,
                                 additional_info={'to_node_id': to_node_id})
            raise DatabaseQueryError(f"Failed to get {self.model_name} by to_node: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_edge_between_nodes(self, session: Session, from_node_id: str, to_node_id: str) -> Optional[Edge]:
        """Get specific edge between two nodes."""
        try:
            from_node_id = validators._validate_id(from_node_id)
            to_node_id = validators._validate_id(to_node_id)
            
            edge = session.query(self.model).filter(
                and_(
                    self.model.from_node_id == from_node_id,
                    self.model.to_node_id == to_node_id,
                    self.model.is_deleted == False
                )
            ).first()
            
            return edge
            
        except Exception as e:
            context = ErrorContext(operation='get_edge_between_nodes', component=self.model_name,
                                 additional_info={'from_node_id': from_node_id, 'to_node_id': to_node_id})
            raise DatabaseQueryError(f"Failed to get {self.model_name} between nodes: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _count_by_workflow(self, session: Session, workflow_id: str) -> int:
        """Count edges in a workflow."""
        try:
            workflow_id = validators._validate_id(workflow_id)
            
            count = session.query(self.model).filter(
                and_(
                    self.model.workflow_id == workflow_id,
                    self.model.is_deleted == False
                )
            ).count()
            
            return count
            
        except Exception as e:
            context = ErrorContext(operation='count_by_workflow', component=self.model_name,
                                 additional_info={'workflow_id': workflow_id})
            raise DatabaseQueryError(f"Failed to count {self.model_name} by workflow: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _delete_all_by_workflow(self, session: Session, workflow_id: str) -> List[Edge]:
        """Delete all edges in a workflow (soft delete)."""
        try:
            workflow_id = validators._validate_id(workflow_id)
            
            edges = self._get_by_workflow(session, workflow_id)
            
            deleted = []
            for edge in edges:
                self._delete(session, edge.id)
                deleted.append(edge)
            
            return deleted
            
        except Exception as e:
            context = ErrorContext(operation='delete_all_by_workflow', component=self.model_name,
                                 additional_info={'workflow_id': workflow_id})
            raise DatabaseQueryError(f"Failed to delete {self.model_name} by workflow: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _delete_all_by_node(self, session: Session, node_id: str) -> List[Edge]:
        """Delete all edges connected to a node (soft delete)."""
        try:
            node_id = validators._validate_id(node_id)
            
            # Get all edges where node is source or target
            outgoing = self._get_by_from_node(session, node_id)
            incoming = self._get_by_to_node(session, node_id)
            
            all_edges = outgoing + incoming
            
            deleted = []
            for edge in all_edges:
                if edge.id not in [e.id for e in deleted]:  # Avoid duplicates
                    self._delete(session, edge.id)
                    deleted.append(edge)
            
            return deleted
            
        except Exception as e:
            context = ErrorContext(operation='delete_all_by_node', component=self.model_name,
                                 additional_info={'node_id': node_id})
            raise DatabaseQueryError(f"Failed to delete {self.model_name} by node: {str(e)}",
                                    context=context, severity=ErrorSeverity.HIGH)

    def _get_next_nodes(self, session: Session, from_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Edge]:
        """
        Get all outgoing edges from a node, optionally filtered by condition type.
        
        Args:
            session: Database session
            from_node_id: Source node ID
            condition_type: Optional condition type filter
            
        Returns:
            List of edges going out from the node
            
        Raises:
            DatabaseQueryError: If query fails
        """
        try:
            from_node_id = validators._validate_id(from_node_id)
            
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
            context = ErrorContext(
                operation='get_next_nodes',
                component=self.model_name,
                additional_info={'from_node_id': from_node_id, 'condition_type': condition_type}
            )
            raise DatabaseQueryError(
                f"Failed to get next nodes: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )

    def _get_previous_nodes(self, session: Session, to_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Edge]:
        """
        Get all incoming edges to a node, optionally filtered by condition type.
        
        Args:
            session: Database session
            to_node_id: Target node ID
            condition_type: Optional condition type filter
            
        Returns:
            List of edges coming into the node
            
        Raises:
            DatabaseQueryError: If query fails
        """
        try:
            to_node_id = validators._validate_id(to_node_id)
            
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
            context = ErrorContext(
                operation='get_previous_nodes',
                component=self.model_name,
                additional_info={'to_node_id': to_node_id, 'condition_type': condition_type}
            )
            raise DatabaseQueryError(
                f"Failed to get previous nodes: {str(e)}",
                context=context,
                severity=ErrorSeverity.HIGH
            )