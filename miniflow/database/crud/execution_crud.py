from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from miniflow.database.models import Execution
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorContext, ErrorSeverity


class ExecutionCRUD(BaseCRUD[Execution]):
    """Execution specific CRUD operations (READ-ONLY)"""

    def __init__(self):
        super().__init__(Execution)

    def get_execution_by_id(self, session: Session, execution_id: str) -> Optional[Execution]:
        """Get execution by ID"""
        return self.find_by_id(session, execution_id)

    def get_all_executions(self, session: Session, skip: int = 0, limit: int = 100) -> List[Execution]:
        """Get all executions with pagination"""
        return self.get_all(session, skip=skip, limit=limit, order_by="started_at")

    def get_executions_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[Execution]:
        """Get all executions for a specific workflow"""
        try:
            filters = {'workflow_id': workflow_id}
            return self.filter(session, filters, skip=skip, limit=limit, order_by_field="started_at")
        except Exception as e:
            context = self._create_error_context("get_executions_by_workflow", workflow_id=workflow_id)
            raise DatabaseQueryError(f"Failed to get executions for workflow '{workflow_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def get_executions_by_status(self, session: Session, status: str, skip: int = 0, limit: int = 100) -> List[Execution]:
        """Get all executions with specific status"""
        try:
            filters = {'status': status}
            return self.filter(session, filters, skip=skip, limit=limit, order_by_field="started_at")
        except Exception as e:
            context = self._create_error_context("get_executions_by_status", status=status)
            raise DatabaseQueryError(f"Failed to get executions with status '{status}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def get_executions_by_workflow_and_status(self, session: Session, workflow_id: str, status: str, skip: int = 0, limit: int = 100) -> List[Execution]:
        """Get executions filtered by both workflow and status"""
        try:
            filters = {'workflow_id': workflow_id, 'status': status}
            return self.filter(session, filters, skip=skip, limit=limit, order_by_field="started_at")
        except Exception as e:
            context = self._create_error_context("get_executions_by_workflow_and_status", workflow_id=workflow_id, status=status)
            raise DatabaseQueryError(f"Failed to get executions for workflow '{workflow_id}' with status '{status}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def count_executions_by_workflow(self, session: Session, workflow_id: str) -> int:
        """Count executions for a specific workflow"""
        try:
            filters = {'workflow_id': workflow_id}
            return self.count_filtered(session, filters)
        except Exception as e:
            context = self._create_error_context("count_executions_by_workflow", workflow_id=workflow_id)
            raise DatabaseQueryError(f"Failed to count executions for workflow '{workflow_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)

    def count_executions_by_status(self, session: Session, status: str) -> int:
        """Count executions with specific status"""
        try:
            filters = {'status': status}
            return self.count_filtered(session, filters)
        except Exception as e:
            context = self._create_error_context("count_executions_by_status", status=status)
            raise DatabaseQueryError(f"Failed to count executions with status '{status}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)
