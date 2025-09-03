from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.models import Execution
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class ExecutionOrchestrator(BaseOrchestrator):
    """Execution orchestrator for READ-ONLY operations and execution monitoring."""

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        return self.execution_crud

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get executions for a specific workflow."""
        try:
            results = self.execution_crud._filter(session, filters={"workflow_id": workflow_id}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_executions_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_status(self, session: Session, status: str, skip: int = 0, limit: int = 100, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get executions by status."""
        try:
            results = self.execution_crud._filter(session, filters={"status": status}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_executions_by_status", status=status)
            raise OrchestrationError(str(e), context=context) from e