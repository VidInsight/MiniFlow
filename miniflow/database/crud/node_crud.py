from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from miniflow.database.models import Node
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorContext, ErrorSeverity


class NodeCRUD(BaseCRUD[Node]):
    """Node specific CRUD operations"""

    def __init__(self):
        super().__init__(Node)

    def create_node(self, session: Session, workflow_id: str, name: str, **kwargs) -> Node:
        """Create new node record with validation"""
        # Validate required inputs
        if not workflow_id or not workflow_id.strip():
            context = self._create_error_context("create_node", workflow_id=workflow_id)
            raise ValidationError("Workflow ID cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        if not name or not name.strip():
            context = self._create_error_context("create_node", name=name)
            raise ValidationError("Node name cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        # Check if name already exists in the same workflow
        existing = self.find_by_name_and_workflow(session, name.strip(), workflow_id)
        if existing:
            context = self._create_error_context("create_node", name=name, workflow_id=workflow_id)
            raise ValidationError(f"Node name '{name}' already exists in workflow '{workflow_id}'", context=context, severity=ErrorSeverity.MEDIUM)

        # Prepare data
        node_data = {
            'workflow_id': workflow_id.strip(),
            'name': name.strip(),
            'description': kwargs.get('description'),
            'script_id': kwargs.get('script_id'),
            'params': kwargs.get('params', {}),
            'max_retries': kwargs.get('max_retries', 3),
            'timeout_seconds': kwargs.get('timeout_seconds', 300)
        }

        return self.create(session, **node_data)

    def get_node_by_id(self, session: Session, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        return self.find_by_id(session, node_id)

    def update_node(self, session: Session, node_id: str, **kwargs) -> Node:
        """Update node by ID"""
        # Get existing node
        node = self.find_by_id(session, node_id)
        if not node:
            context = self._create_error_context("update_node", node_id=node_id)
            raise ValidationError(f"Node '{node_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)

        # Update fields if provided
        update_data = {}
        
        if 'name' in kwargs and kwargs['name']:
            new_name = kwargs['name'].strip()
            if new_name != node.name:
                # Check if new name already exists in the same workflow
                existing = self.find_by_name_and_workflow(session, new_name, node.workflow_id)
                if existing and existing.id != node_id:
                    context = self._create_error_context("update_node", node_id=node_id, new_name=new_name)
                    raise ValidationError(f"Node name '{new_name}' already exists in workflow", context=context, severity=ErrorSeverity.MEDIUM)
                update_data['name'] = new_name

        if 'description' in kwargs:
            update_data['description'] = kwargs['description']

        if 'script_id' in kwargs:
            update_data['script_id'] = kwargs['script_id']

        if 'params' in kwargs:
            update_data['params'] = kwargs['params']

        if 'max_retries' in kwargs:
            update_data['max_retries'] = kwargs['max_retries']

        if 'timeout_seconds' in kwargs:
            update_data['timeout_seconds'] = kwargs['timeout_seconds']

        # Apply updates
        for field, value in update_data.items():
            setattr(node, field, value)

        session.flush()
        return node

    def delete_node(self, session: Session, node_id: str) -> bool:
        """Delete node by ID"""
        node = self.find_by_id(session, node_id)
        if not node:
            context = self._create_error_context("delete_node", node_id=node_id)
            raise ValidationError(f"Node '{node_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)

        session.delete(node)
        session.flush()
        return True

    def get_all_nodes(self, session: Session) -> List[Node]:
        """Get all nodes"""
        return self.get_all(session)

    def get_nodes_by_workflow(self, session: Session, workflow_id: str) -> List[Node]:
        """Get all nodes for a specific workflow"""
        try:
            filters = {'workflow_id': workflow_id}
            return self.filter(session, filters)
        except Exception as e:
            context = self._create_error_context("get_nodes_by_workflow", workflow_id=workflow_id)
            raise DatabaseQueryError(f"Failed to get nodes for workflow '{workflow_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def find_by_name_and_workflow(self, session: Session, name: str, workflow_id: str) -> Optional[Node]:
        """Find node by name within a specific workflow"""
        try:
            filters = {'name': name, 'workflow_id': workflow_id}
            results = self.filter(session, filters, limit=1)
            return results[0] if results else None
        except Exception as e:
            context = self._create_error_context("find_by_name_and_workflow", name=name, workflow_id=workflow_id)
            raise DatabaseQueryError(f"Failed to find node by name and workflow: {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)
