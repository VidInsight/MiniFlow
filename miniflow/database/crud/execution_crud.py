from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorSeverity
from miniflow.database.models import Execution, ExecutionInput, ExecutionOutput, ExecutionStatus
from miniflow.database.crud.base_crud import BaseCRUD


class ExecutionCRUD(BaseCRUD[Execution]):
    def __init__(self):
        super().__init__(Execution)

    def _create_with_validation(self, session, workflow_id: str, **kwargs):
        if not workflow_id or not workflow_id.strip():
            raise ValidationError("Workflow ID cannot be empty", severity=ErrorSeverity.HIGH)

        workflow_id = workflow_id.strip()
        return self._create(session, workflow_id=workflow_id, **kwargs)

    def _delete_execution(self, session: Session, record_id: str) -> Execution:
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
            
            deleted_execution = self._delete(session, record_id)
            
            self.logger.info(f"Successfully deleted execution {record_id} and all related records")
            return deleted_execution
            
        except Exception as e:
            context = self._create_error_context("_delete_execution", record_id=record_id)
            if isinstance(e, (DatabaseQueryError, ValidationError)):
                raise e
            raise DatabaseQueryError(f"Failed to delete execution {record_id}: {str(e)}", context=context, severity=ErrorSeverity.HIGH) from e