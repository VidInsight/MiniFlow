from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from miniflow.database.models import ExecutionOutput
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError
from miniflow.core.logger import get_logger


class ExecutionOutputOrchestrator(BaseOrchestrator):
    """ExecutionOutput orchestration logic (READ-ONLY)"""

    def __init__(self, database_engine):
        super().__init__(database_engine)
        self.logger = get_logger("execution_output_orchestrator")
    
    def _get_primary_crud(self):
        return self.execution_output_crud

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_by_execution(self, session: Session, execution_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution outputs by execution ID."""
        if not execution_id:
            return []
        try:
            results = self.execution_output_crud._filter(session, filters={"execution_id": execution_id}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_execution", execution_id=execution_id)
            raise OrchestrationError(f"Failed to get execution outputs by execution: {str(e)}", context=context) from e

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution outputs by workflow ID."""
        if not workflow_id:
            return []
        try:
            results = self.execution_output_crud._filter(session, filters={"workflow_id": workflow_id}, skip=skip,
                                                         limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(f"Failed to get execution outputs by workflow: {str(e)}", context=context) from e

    @with_session
    def get_by_node(self, session: Session, node_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution outputs by node ID."""
        if not node_id:
            return []
        try:
            results = self.execution_output_crud._filter(session, filters={"node_id": node_id}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_node", node_id=node_id)
            raise OrchestrationError(f"Failed to get execution outputs by node: {str(e)}", context=context) from e

    @with_session
    def get_by_status(self, session: Session, status: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution outputs by status."""
        if not status:
            return []
        try:
            results = self.execution_output_crud._filter(session, filters={"status": status}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_status", status=status)
            raise OrchestrationError(f"Failed to get execution outputs by status: {str(e)}", context=context) from e