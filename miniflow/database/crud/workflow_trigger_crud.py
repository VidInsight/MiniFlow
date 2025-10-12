from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext
import miniflow.database.validators as validators

from ..models import WorkflowTrigger
from .base_crud import BaseCRUD


class WorkflowTriggerCRUD(BaseCRUD[WorkflowTrigger]):
    """CRUD operations for WorkflowTrigger junction table."""
    
    def __init__(self):
        super().__init__(WorkflowTrigger)
        self.model_fields = {column.name for column in WorkflowTrigger.__table__.columns}
        self.required_fields = {'trigger_id', 'workflow_id'}
        self.protected_fields = {'trigger_id', 'workflow_id'}  # Can't change relationships after creation

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs) -> WorkflowTrigger:
        """
        Create a new workflow-trigger assignment.
        
        Args:
            session: Database session
            trigger_id: ID of the trigger
            workflow_id: ID of the workflow
            **kwargs: Additional fields (created_by, etc.)
            
        Returns:
            WorkflowTrigger: Created junction record
            
        Raises:
            ValidationError: If required fields missing or duplicate assignment exists
        """
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate trigger_id
        trigger_id = kwargs['trigger_id']
        kwargs['trigger_id'] = validators._validate_id(trigger_id)
        
        # Validate workflow_id
        workflow_id = kwargs['workflow_id']
        kwargs['workflow_id'] = validators._validate_id(workflow_id)
        
        # Check for duplicate assignment (same trigger + workflow)
        existing = self._get_by_trigger_and_workflow(session, trigger_id, workflow_id)
        if existing:
            context = ErrorContext(
                operation='create', 
                component=self.model_name,
                additional_info={'trigger_id': trigger_id, 'workflow_id': workflow_id}
            )
            raise ValidationError(
                f"Trigger {trigger_id} is already assigned to workflow {workflow_id}", 
                context=context, 
                severity=ErrorSeverity.MEDIUM
            )
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        workflow_trigger = super()._create(session, **kwargs)
        return workflow_trigger

    def _update(self, session: Session, record_id: str, **kwargs) -> WorkflowTrigger:
        """
        Update is restricted for junction tables - relationships cannot be changed.
        Only BaseModel fields (updated_by, etc.) can be modified.
        """
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        existing = self._get_by_id(session, record_id)
        if not existing:
            context = ErrorContext(
                operation='update', 
                component=self.model_name,
                additional_info={'record_id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found", 
                context=context, 
                severity=ErrorSeverity.MEDIUM
            )
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        workflow_trigger = super()._update(session, record_id, **kwargs)
        return workflow_trigger

    # ============================================================================================ QUERY OPERATIONS =====
    def _get_by_trigger_and_workflow(
        self, 
        session: Session, 
        trigger_id: str, 
        workflow_id: str
    ) -> Optional[WorkflowTrigger]:
        """
        Get workflow-trigger assignment by trigger_id and workflow_id.
        
        Args:
            session: Database session
            trigger_id: Trigger ID
            workflow_id: Workflow ID
            
        Returns:
            WorkflowTrigger or None if not found
        """
        query = session.query(self.model).filter(
            and_(
                self.model.trigger_id == trigger_id,
                self.model.workflow_id == workflow_id,
                self.model.is_deleted == False
            )
        )
        return query.first()
    
    def _get_by_trigger(
        self, 
        session: Session, 
        trigger_id: str, 
        include_deleted: bool = False
    ) -> List[WorkflowTrigger]:
        """
        Get all workflow assignments for a trigger.
        
        Args:
            session: Database session
            trigger_id: Trigger ID
            include_deleted: Include soft-deleted records
            
        Returns:
            List of WorkflowTrigger records
        """
        query = session.query(self.model).filter(self.model.trigger_id == trigger_id)
        
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        return query.all()
    
    def _get_by_workflow(
        self, 
        session: Session, 
        workflow_id: str, 
        include_deleted: bool = False
    ) -> List[WorkflowTrigger]:
        """
        Get all trigger assignments for a workflow.
        
        Args:
            session: Database session
            workflow_id: Workflow ID
            include_deleted: Include soft-deleted records
            
        Returns:
            List of WorkflowTrigger records
        """
        query = session.query(self.model).filter(self.model.workflow_id == workflow_id)
        
        if not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        return query.all()
    
    def _count_workflows_for_trigger(self, session: Session, trigger_id: str) -> int:
        """Count how many workflows use this trigger."""
        return session.query(self.model).filter(
            and_(
                self.model.trigger_id == trigger_id,
                self.model.is_deleted == False
            )
        ).count()
    
    def _count_triggers_for_workflow(self, session: Session, workflow_id: str) -> int:
        """Count how many triggers are assigned to this workflow."""
        return session.query(self.model).filter(
            and_(
                self.model.workflow_id == workflow_id,
                self.model.is_deleted == False
            )
        ).count()
    
    def _delete_by_trigger_and_workflow(
        self, 
        session: Session, 
        trigger_id: str, 
        workflow_id: str,
        deleted_by: str = None,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a specific trigger-workflow assignment.
        
        Args:
            session: Database session
            trigger_id: Trigger ID
            workflow_id: Workflow ID
            deleted_by: User performing deletion
            hard_delete: Permanently delete (vs soft delete)
            
        Returns:
            bool: True if deleted, False if not found
        """
        assignment = self._get_by_trigger_and_workflow(session, trigger_id, workflow_id)
        
        if not assignment:
            return False
        
        if hard_delete:
            session.delete(assignment)
        else:
            # Soft delete
            self._delete(session, assignment.id, deleted_by=deleted_by)
        
        return True

