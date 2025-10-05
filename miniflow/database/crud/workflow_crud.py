from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timezone

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext, DatabaseQueryError
import miniflow.database.validators as validators

from ..models import Workflow
from ..enums import WorkflowStatus
from .base_crud import BaseCRUD


class WorkflowCRUD(BaseCRUD[Workflow]):
    def __init__(self):
        super().__init__(Workflow)
        self.model_fields = {column.name for column in Workflow.__table__.columns}
        self.required_fields = {'name'}
        self.protected_fields = {'total_executions', 'successful_executions', 'failed_executions',
                                'cancelled_executions', 'avg_execution_duration', 'min_execution_duration',
                                'max_execution_duration', 'last_executed_at', 
                                'last_successful_execution_at', 'last_failed_execution_at'}

    def _create(self, session: Session, **kwargs) -> Workflow:
        """Create a new workflow with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)
        
        # Validate name
        name = kwargs['name']
        kwargs['name'] = validators._validate_name(name)
        
        # Validate priority if provided (integer 1-5)
        priority = kwargs.get('priority')
        if priority is not None:
            if not isinstance(priority, int) or priority < 1 or priority > 5:
                raise ValueError("Priority must be an integer between 1 and 5")

        if 'status' in kwargs:
            kwargs.pop('status')
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        workflow = super()._create(session, **kwargs)
        return workflow

    def _update(self, session: Session, record_id: str, **kwargs) -> Workflow:
        """Update workflow with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)
        
        # Validate name if being updated
        if 'name' in kwargs and kwargs['name']:
            kwargs['name'] = validators._validate_name(kwargs['name'])
        
        # Validate priority if being updated (integer 1-5)
        if 'priority' in kwargs and kwargs['priority'] is not None:
            priority = kwargs['priority']
            if not isinstance(priority, int) or priority < 1 or priority > 5:
                raise ValueError("Priority must be an integer between 1 and 5")
        
        # Validate status if being updated
        if 'status' in kwargs:
            kwargs.pop('status')
        
        self._validate_no_extra_fields(self.model_fields, kwargs)
        workflow = super()._update(session, record_id, **kwargs)
        return workflow

    def _activate(self, session: Session, record_id: str) -> Workflow:
        """Activate a workflow."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(operation='activate_workflow', component=self.model_name,additional_info={'id': record_id})
            raise ValidationError(f"{self.model_name} with ID {record_id} not found", context=context ,severity=ErrorSeverity.MEDIUM)
        
        workflow.status = WorkflowStatus.ACTIVE
        session.add(workflow)
        session.flush()
        return workflow

    def _deactivate(self, session: Session, record_id: str) -> Workflow:
        """Deactivate a workflow."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(operation='deactivate_workflow', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"{self.model_name} with ID {record_id} not found", severity=ErrorSeverity.MEDIUM)
        
        workflow.status = WorkflowStatus.DEACTIVATED
        session.add(workflow)
        session.flush()
        return workflow

    def _increment_successful_executions(self, session: Session, record_id: str) -> Workflow:
        """Increment successful executions counter."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(
                operation='increment_successful_executions',
                component=self.model_name,
                additional_info={'id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        workflow.total_executions = (workflow.total_executions or 0) + 1
        workflow.successful_executions = (workflow.successful_executions or 0) + 1
        workflow.last_executed_at = datetime.now(timezone.utc)
        workflow.last_successful_execution_at = datetime.now(timezone.utc)
        
        session.add(workflow)
        session.flush()
        return workflow
    
    def _increment_failed_executions(self, session: Session, record_id: str) -> Workflow:
        """Increment failed executions counter."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(
                operation='increment_failed_executions',
                component=self.model_name,
                additional_info={'id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        workflow.total_executions = (workflow.total_executions or 0) + 1
        workflow.failed_executions = (workflow.failed_executions or 0) + 1
        workflow.last_executed_at = datetime.now(timezone.utc)
        workflow.last_failed_execution_at = datetime.now(timezone.utc)
        
        session.add(workflow)
        session.flush()
        return workflow

    def _increment_cancelled_executions(self, session: Session, record_id: str) -> Workflow:
        """Increment cancelled executions counter."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(
                operation='increment_cancelled_executions',
                component=self.model_name,
                additional_info={'id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )
        
        workflow.total_executions = (workflow.total_executions or 0) + 1
        workflow.cancelled_executions = (workflow.cancelled_executions or 0) + 1
        workflow.last_executed_at = datetime.now(timezone.utc)
        
        session.add(workflow)
        session.flush()
        return workflow

    def _update_execution_durations(self, session: Session, record_id: str, duration: float) -> Workflow:
        """Update execution duration statistics."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(
                operation='update_execution_durations',
                component=self.model_name,
                additional_info={'id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )

        if duration < 0:
            raise ValueError("Duration must be a non-negative float")

        # Update average duration
        total_exec = workflow.total_executions or 0
        current_avg = workflow.avg_execution_duration or 0.0
        new_avg = ((current_avg * (total_exec - 1)) + duration) / total_exec if total_exec > 0 else duration
        workflow.avg_execution_duration = new_avg

        # Update min duration
        if workflow.min_execution_duration is None or duration < workflow.min_execution_duration:
            workflow.min_execution_duration = duration

        # Update max duration
        if workflow.max_execution_duration is None or duration > workflow.max_execution_duration:
            workflow.max_execution_duration = duration

        session.add(workflow)
        session.flush()
        return workflow

    def _get_execution_stats(self, session: Session, record_id: str) -> Optional[dict]:
        """Retrieve execution statistics for a workflow."""
        workflow = self._get_by_id(session, record_id)
        if not workflow:
            context = ErrorContext(
                operation='get_execution_stats',
                component=self.model_name,
                additional_info={'id': record_id}
            )
            raise ValidationError(
                f"{self.model_name} with ID {record_id} not found",
                context=context,
                severity=ErrorSeverity.MEDIUM
            )

        stats = {
            'total_executions': workflow.total_executions,
            'successful_executions': workflow.successful_executions,
            'failed_executions': workflow.failed_executions,
            'cancelled_executions': workflow.cancelled_executions,
            'avg_execution_duration': workflow.avg_execution_duration,
            'min_execution_duration': workflow.min_execution_duration,
            'max_execution_duration': workflow.max_execution_duration,
            'last_executed_at': workflow.last_executed_at,
            'last_successful_execution_at': workflow.last_successful_execution_at,
            'last_failed_execution_at': workflow.last_failed_execution_at
        }
        return stats

