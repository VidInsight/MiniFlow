"""
Execution Orchestrator

This module provides high-level orchestration for execution operations,
managing database sessions and coordinating execution queries.
"""

from typing import List, Optional, Dict, Any
from miniflow.database.models import Execution
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class ExecutionOrchestrator(BaseOrchestrator):
    """Execution orchestrator for READ-ONLY operations and execution monitoring."""

    def __init__(self, database_engine):
        """
        Initialize execution orchestrator
        
        Args:
            database_engine: DatabaseEngine instance
        """
        super().__init__(database_engine)
        # Execution CRUD instance is already initialized in BaseOrchestrator

    @with_session
    def get_execution_by_id(self, session, execution_id: str) -> Optional[Execution]:
        """
        Get execution by ID.

        Args:
            session: Database session
            execution_id (str): ID of the execution

        Returns:
            Optional[Execution]: Execution if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.execution_crud.get_execution_by_id(session, execution_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", execution_id=execution_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all_executions(self, session, skip: int = 0, limit: int = 100) -> List[Execution]:
        """
        Get all executions with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Execution]: List of executions

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.execution_crud.get_all_executions(session, skip=skip, limit=limit)
        except Exception as e:
            context = self._create_error_context("get_all", skip=skip, limit=limit)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_executions_by_workflow(self, session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[Execution]:
        """
        Get executions for a specific workflow.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Execution]: List of executions for the workflow

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.execution_crud.get_executions_by_workflow(session, workflow_id, skip=skip, limit=limit)
        except Exception as e:
            context = self._create_error_context("get_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_executions_by_status(self, session, status: str, skip: int = 0, limit: int = 100) -> List[Execution]:
        """
        Get executions with specific status.

        Args:
            session: Database session
            status (str): Execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Execution]: List of executions with the specified status

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.execution_crud.get_executions_by_status(session, status, skip=skip, limit=limit)
        except Exception as e:
            context = self._create_error_context("get_by_status", status=status)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_executions(self, session, workflow_id: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Execution]:
        """
        Filter executions by various criteria.

        Args:
            session: Database session
            workflow_id: Optional workflow ID filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[Execution]: Filtered list of executions

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            # Handle combined filters
            if workflow_id and status:
                return self.execution_crud.get_executions_by_workflow_and_status(session, workflow_id, status, skip=skip, limit=limit)
            elif workflow_id:
                return self.execution_crud.get_executions_by_workflow(session, workflow_id, skip=skip, limit=limit)
            elif status:
                return self.execution_crud.get_executions_by_status(session, status, skip=skip, limit=limit)
            else:
                return self.execution_crud.get_all_executions(session, skip=skip, limit=limit)
        except Exception as e:
            context = self._create_error_context("filter", workflow_id=workflow_id, status=status)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def count_executions(self, session, workflow_id: Optional[str] = None, status: Optional[str] = None) -> int:
        """
        Count executions with optional filters.

        Args:
            session: Database session
            workflow_id: Optional workflow ID filter
            status: Optional status filter

        Returns:
            int: Number of executions matching the criteria

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            if workflow_id:
                return self.execution_crud.count_executions_by_workflow(session, workflow_id)
            elif status:
                return self.execution_crud.count_executions_by_status(session, status)
            else:
                return self.execution_crud.count(session)
        except Exception as e:
            context = self._create_error_context("count", workflow_id=workflow_id, status=status)
            raise OrchestrationError(str(e), context=context) from e
