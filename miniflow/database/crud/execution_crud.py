from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import Execution, ExecutionInput, ExecutionOutput, ExecutionStatus
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionCRUD(BaseCRUD[Execution]):
    def __init__(self):
        super().__init__(Execution)

    def _delete(self, session: Session, record_id: str) -> Execution:
        try:
            execution = self._get_by_id(session, record_id)
            if not execution:
                context = self._create_error_context("_delete_execution", record_id=record_id)
                raise DatabaseQueryError(f"Execution with ID '{record_id}' not found", context=context, severity=ErrorSeverity.HIGH)
            
            # Check execution status - prevent deletion of active executions
            if execution.status in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]:
                context = self._create_error_context("_delete_execution", record_id=record_id, status=execution.status.value)
                raise ValidationError(
                    f"Cannot delete execution '{record_id}' - execution is {execution.status.value}. "
                    f"Only COMPLETED, FAILED, or CANCELLED executions can be deleted.",
                    context=context,
                    severity=ErrorSeverity.HIGH
                )
            
            input_count = session.query(ExecutionInput).filter(ExecutionInput.execution_id == record_id).count()
            output_count = session.query(ExecutionOutput).filter(ExecutionOutput.execution_id == record_id).count()
            
            self.logger.info(f"Deleting execution {record_id} (status: {execution.status.value}) with {input_count} inputs and {output_count} outputs")
            
            if input_count > 0:
                session.query(ExecutionInput).filter(ExecutionInput.execution_id == record_id).delete()
                self.logger.info(f"Deleted {input_count} execution inputs for execution {record_id}")
            
            if output_count > 0:
                session.query(ExecutionOutput).filter(ExecutionOutput.execution_id == record_id).delete()
                self.logger.info(f"Deleted {output_count} execution outputs for execution {record_id}")
            
            deleted_execution = super()._delete(session, record_id)
            
            self.logger.info(f"Successfully deleted execution {record_id} and all related records")
            return deleted_execution
            
        except Exception as e:
            context = self._create_error_context("_delete_execution", record_id=record_id)
            if isinstance(e, (DatabaseQueryError, ValidationError)):
                raise e
            raise DatabaseQueryError(f"Failed to delete execution {record_id}: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def get_daily_execution_stats(self, session: Session, target_date: Optional[datetime] = None) -> Dict[str, Any]:
        try:
            # Use provided date or default to today
            if target_date is None:
                target_date = datetime.now(timezone.utc).date()
            elif isinstance(target_date, datetime):
                target_date = target_date.date()
            
            # Calculate date range for the target day
            start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Base query for executions on the target date
            base_query = session.query(Execution).filter(
                and_(
                    Execution.started_at >= start_of_day,
                    Execution.started_at < end_of_day
                )
            )
            
            # Count by status (only finished executions)
            completed_count = base_query.filter(Execution.status == ExecutionStatus.COMPLETED).count()
            failed_count = base_query.filter(Execution.status == ExecutionStatus.FAILED).count()
            cancelled_count = base_query.filter(Execution.status == ExecutionStatus.CANCELLED).count()
            
            # Total finished executions
            total_finished = completed_count + failed_count + cancelled_count
            
            return {
                'total_finished': total_finished,
                'completed': completed_count,
                'failed': failed_count, 
                'cancelled': cancelled_count
            }
            
        except Exception as e:
            context = self._create_error_context("get_daily_execution_stats", target_date=str(target_date))
            raise DatabaseQueryError(f"Failed to get daily execution stats: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e

    def _get_recent_by_workflow(self, session: Session, workflow_id: str, limit: int = 10) -> List[Execution]:
        try:
            limit = min(max(1, limit), 100)  # Between 1 and 100
            
            results = session.query(Execution).filter(
                Execution.workflow_id == workflow_id
            ).order_by(
                Execution.started_at.desc()
            ).limit(limit).all()
            
            return results
            
        except Exception as e:
            context = self._create_error_context("get_recent_by_workflow", workflow_id=workflow_id, limit=limit)
            raise DatabaseQueryError(f"Failed to get recent executions for workflow {workflow_id}: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e