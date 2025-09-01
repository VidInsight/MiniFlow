from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from miniflow.database.models import Workflow, WorkflowStatus
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorContext, ErrorSeverity


class WorkflowCRUD(BaseCRUD[Workflow]):
    """Workflow specific CRUD operations"""

    def __init__(self):
        super().__init__(Workflow)

    def create_workflow(self, session: Session, name: str, **kwargs) -> Workflow:
        """Create new workflow record with validation"""
        # Validate inputs
        if not name or not name.strip():
            context = self._create_error_context("create_workflow", name=name)
            raise ValidationError("Workflow name cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        # Check if name already exists
        existing = self.find_by_name(session, name.strip())
        if existing:
            context = self._create_error_context("create_workflow", name=name)
            raise ValidationError(f"Workflow name '{name}' already exists", context=context, severity=ErrorSeverity.MEDIUM)

        # Prepare data
        workflow_data = {
            'name': name.strip(),
            'description': kwargs.get('description'),
            'priority': kwargs.get('priority', 0),
            'status': kwargs.get('status', WorkflowStatus.DRAFT),
            'status_message': kwargs.get('status_message')
        }

        return self.create(session, **workflow_data)

    def get_workflow_by_id(self, session: Session, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.find_by_id(session, workflow_id)

    def update_workflow(self, session: Session, workflow_id: str, **kwargs) -> Workflow:
        """Update workflow by ID"""
        # Get existing workflow
        workflow = self.find_by_id(session, workflow_id)
        if not workflow:
            context = self._create_error_context("update_workflow", workflow_id=workflow_id)
            raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)

        # Update fields if provided
        update_data = {}
        if 'name' in kwargs and kwargs['name']:
            new_name = kwargs['name'].strip()
            if new_name != workflow.name:
                # Check if new name already exists
                existing = self.find_by_name(session, new_name)
                if existing and existing.id != workflow_id:
                    context = self._create_error_context("update_workflow", workflow_id=workflow_id, new_name=new_name)
                    raise ValidationError(f"Workflow name '{new_name}' already exists", context=context, severity=ErrorSeverity.MEDIUM)
                update_data['name'] = new_name

        if 'description' in kwargs:
            update_data['description'] = kwargs['description']

        if 'priority' in kwargs:
            update_data['priority'] = kwargs['priority']

        if 'status' in kwargs:
            update_data['status'] = kwargs['status']

        if 'status_message' in kwargs:
            update_data['status_message'] = kwargs['status_message']

        # Apply updates
        for field, value in update_data.items():
            setattr(workflow, field, value)

        session.flush()
        return workflow

    def delete_workflow(self, session: Session, workflow_id: str) -> bool:
        """Delete workflow by ID"""
        workflow = self.find_by_id(session, workflow_id)
        if not workflow:
            context = self._create_error_context("delete_workflow", workflow_id=workflow_id)
            raise ValidationError(f"Workflow '{workflow_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)

        session.delete(workflow)
        session.flush()
        return True

    def get_all_workflows(self, session: Session) -> List[Workflow]:
        """Get all workflows"""
        return self.get_all(session)

    def find_by_name(self, session: Session, name: str) -> Optional[Workflow]:
        """Find workflow by name"""
        return super().find_by_name(session, name)
