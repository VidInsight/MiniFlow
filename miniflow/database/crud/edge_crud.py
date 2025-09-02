from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from miniflow.database.models import Edge
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorContext, ErrorSeverity


class EdgeCRUD(BaseCRUD[Edge]):
    """Edge specific CRUD operations"""

    def __init__(self):
        super().__init__(Edge)

    def create_edge(self, session: Session, workflow_id: str, from_node_id: str, to_node_id: str, **kwargs) -> Edge:
        """Create new edge record with validation"""
        # Validate required inputs
        if not workflow_id or not workflow_id.strip():
            context = self._create_error_context("create_edge", workflow_id=workflow_id)
            raise ValidationError("Workflow ID cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        if not from_node_id or not from_node_id.strip():
            context = self._create_error_context("create_edge", from_node_id=from_node_id)
            raise ValidationError("From Node ID cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        if not to_node_id or not to_node_id.strip():
            context = self._create_error_context("create_edge", to_node_id=to_node_id)
            raise ValidationError("To Node ID cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        # Validate nodes are different
        if from_node_id.strip() == to_node_id.strip():
            context = self._create_error_context("create_edge", from_node_id=from_node_id, to_node_id=to_node_id)
            raise ValidationError("From node and to node cannot be the same", context=context, severity=ErrorSeverity.MEDIUM)

        # Check if edge already exists
        existing = self.find_edge_between_nodes(session, from_node_id, to_node_id)
        if existing:
            context = self._create_error_context("create_edge", from_node_id=from_node_id, to_node_id=to_node_id)
            raise ValidationError(f"Edge already exists between nodes '{from_node_id}' and '{to_node_id}'", context=context, severity=ErrorSeverity.MEDIUM)

        # Prepare data
        edge_data = {
            'workflow_id': workflow_id.strip(),
            'from_node_id': from_node_id.strip(),
            'to_node_id': to_node_id.strip(),
            'condition_type': kwargs.get('condition_type', 'SUCCESS')
        }

        return self.create(session, **edge_data)

    def get_edge_by_id(self, session: Session, edge_id: str) -> Optional[Edge]:
        """Get edge by ID"""
        return self.find_by_id(session, edge_id)

    def update_edge(self, session: Session, edge_id: str, **kwargs) -> Edge:
        """Update edge by ID"""
        # Get existing edge
        edge = self.find_by_id(session, edge_id)
        if not edge:
            context = self._create_error_context("update_edge", edge_id=edge_id)
            raise ValidationError(f"Edge '{edge_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)

        # Update fields if provided
        update_data = {}
        
        if 'condition_type' in kwargs:
            update_data['condition_type'] = kwargs['condition_type']

        # Apply updates
        for field, value in update_data.items():
            setattr(edge, field, value)

        session.flush()
        return edge

    def delete_edge(self, session: Session, edge_id: str) -> bool:
        """Delete edge by ID"""
        edge = self.find_by_id(session, edge_id)
        if not edge:
            context = self._create_error_context("delete_edge", edge_id=edge_id)
            raise ValidationError(f"Edge '{edge_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)

        session.delete(edge)
        session.flush()
        return True

    def get_all_edges(self, session: Session) -> List[Edge]:
        """Get all edges"""
        return self.get_all(session)

    def get_edges_by_workflow(self, session: Session, workflow_id: str) -> List[Edge]:
        """Get all edges for a specific workflow"""
        try:
            filters = {'workflow_id': workflow_id}
            return self.filter(session, filters)
        except Exception as e:
            context = self._create_error_context("get_edges_by_workflow", workflow_id=workflow_id)
            raise DatabaseQueryError(f"Failed to get edges for workflow '{workflow_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def get_edges_by_node(self, session: Session, node_id: str, direction: str = 'both') -> List[Edge]:
        """Get edges connected to a specific node"""
        try:
            if direction == 'outgoing':
                filters = {'from_node_id': node_id}
            elif direction == 'incoming':
                filters = {'to_node_id': node_id}
            else:  # both
                outgoing = self.filter(session, {'from_node_id': node_id})
                incoming = self.filter(session, {'to_node_id': node_id})
                return outgoing + incoming
            
            return self.filter(session, filters)
        except Exception as e:
            context = self._create_error_context("get_edges_by_node", node_id=node_id, direction=direction)
            raise DatabaseQueryError(f"Failed to get edges for node '{node_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def find_edge_between_nodes(self, session: Session, from_node_id: str, to_node_id: str) -> Optional[Edge]:
        """Find edge between two specific nodes"""
        try:
            filters = {'from_node_id': from_node_id, 'to_node_id': to_node_id}
            results = self.filter(session, filters, limit=1)
            return results[0] if results else None
        except Exception as e:
            context = self._create_error_context("find_edge_between_nodes", from_node_id=from_node_id, to_node_id=to_node_id)
            raise DatabaseQueryError(f"Failed to find edge between nodes: {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)
