from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from miniflow.database.models import ExecutionInput
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError
from miniflow.core.logger import get_logger


class ExecutionInputOrchestrator(BaseOrchestrator):
    """ExecutionInput orchestration logic (READ-ONLY)"""

    def __init__(self, database_engine):
        super().__init__(database_engine)
        self.logger = get_logger("execution_input_orchestrator")
    
    def _get_primary_crud(self):
        return self.execution_input_crud

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_by_priority(self, session: Session, priority: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution inputs by priority."""
        try:
            results = self.execution_input_crud._filter(session, filters={"priority": priority}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_priority", priority=priority)
            raise OrchestrationError(f"Failed to get execution inputs by priority: {str(e)}", context=context) from e

    @with_session
    def get_by_execution(self, session: Session, execution_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution inputs by execution ID."""
        try:
            results = self.execution_input_crud._filter(session, filters={"execution_id": execution_id}, skip=skip,
                                                        limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_execution", execution_id=execution_id)
            raise OrchestrationError(f"Failed to get execution inputs by execution: {str(e)}", context=context) from e

    @with_session
    def get_by_node(self, session: Session, node_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution inputs by node ID."""
        try:
            results = self.execution_input_crud._filter(session, filters={"node_id": node_id}, skip=skip, limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_node", node_id=node_id)
            raise OrchestrationError(f"Failed to get execution inputs by node: {str(e)}", context=context) from e

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution inputs by workflow ID."""
        try:
            results = self.execution_input_crud._filter(session, filters={"workflow_id": workflow_id}, skip=skip,
                                                        limit=limit)
            return self._serialize_multiple_results(results)
        except Exception as e:
            context = self._create_error_context("get_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(f"Failed to get execution inputs by workflow: {str(e)}", context=context) from e