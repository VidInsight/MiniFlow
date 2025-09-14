from miniflow.database.models import Workflow, WorkflowStatus, ExecutionStatus
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity
from datetime import datetime, timezone
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from typing import Dict, Any, List


class WorkflowCRUD(BaseCRUD[Workflow]):
    def __init__(self):
        super().__init__(Workflow)

    def _create(self, session, **kwargs):
        # Extract name parameter
        name = kwargs.get('name')
        if not name or not name.strip():
            raise ValidationError("Workflow name cannot be empty", severity=ErrorSeverity.HIGH)

        name = name.strip()
        existing_record = self._filter(session, filters={"name": name})
        if existing_record:
            raise ValidationError(f"Workflow with name '{name}' already exists", severity=ErrorSeverity.HIGH)

        if "status" not in kwargs:
            kwargs["status"] = WorkflowStatus.DRAFT

        # Update kwargs with normalized name
        kwargs["name"] = name
        return super()._create(session, **kwargs)

    def _update(self, session, record_id: str, **kwargs):
        if "name" in kwargs and kwargs["name"]:
            new_name = kwargs["name"].strip()
            if not new_name:
                raise ValidationError("Workflow name cannot be empty", severity=ErrorSeverity.HIGH)

            existing_record = self._filter(session, filters={"name": new_name})
            if existing_record and existing_record[0].id != record_id:
                raise ValidationError(f"Workflow with name '{new_name}' already exists", severity=ErrorSeverity.HIGH)

            kwargs["name"] = new_name

        return super()._update(session, record_id, **kwargs)

    def _update_stats(self, session, workflow_id: str, execution_status: ExecutionStatus, execution_duration: float = None) -> None:
        """Update workflow statistics when an execution completes"""
        workflow = self._get_by_id(session, workflow_id)
        if not workflow:
            raise ValidationError(f"Workflow '{workflow_id}' not found", severity=ErrorSeverity.HIGH)

        # Update execution counts
        workflow.total_executions += 1
        current_time = datetime.now(timezone.utc)
        workflow.last_executed_at = current_time

        # Update status-specific counts and timestamps
        if execution_status == ExecutionStatus.COMPLETED:
            workflow.successful_executions += 1
            workflow.last_successful_execution_at = current_time
        elif execution_status == ExecutionStatus.FAILED:
            workflow.failed_executions += 1
            workflow.last_failed_execution_at = current_time
        elif execution_status == ExecutionStatus.CANCELLED:
            workflow.cancelled_executions += 1

        # Update duration statistics if provided
        if execution_duration is not None and execution_duration > 0:
            if workflow.min_execution_duration is None or execution_duration < workflow.min_execution_duration:
                workflow.min_execution_duration = execution_duration
            
            if workflow.max_execution_duration is None or execution_duration > workflow.max_execution_duration:
                workflow.max_execution_duration = execution_duration
            
            # Calculate new average duration
            if workflow.avg_execution_duration is None:
                workflow.avg_execution_duration = execution_duration
            else:
                # Weighted average calculation
                total_previous_duration = workflow.avg_execution_duration * (workflow.total_executions - 1)
                workflow.avg_execution_duration = (total_previous_duration + execution_duration) / workflow.total_executions

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
            
            results = session.query(Workflow).filter(
                Workflow.last_executed_at.isnot(None)
            ).order_by(
                desc(Workflow.last_executed_at)
            ).limit(limit).all()
            
            return results
            
        except Exception as e:
            context = self._create_error_context("get_recently_executed", limit=limit)
            raise ValidationError(f"Failed to get recently executed workflows: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e