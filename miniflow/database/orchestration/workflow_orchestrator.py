"""
Workflow Orchestrator

This module provides high-level orchestration for workflow operations,
managing database sessions and coordinating complex workflow workflows.
"""

from typing import List, Optional, Dict, Any
from miniflow.database.models import Workflow, WorkflowStatus
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class WorkflowOrchestrator(BaseOrchestrator):
    """Workflow orchestrator for basic CRUD operations and workflow management."""

    def __init__(self, database_engine):
        """
        Initialize workflow orchestrator
        
        Args:
            database_engine: DatabaseEngine instance
        """
        super().__init__(database_engine)
        # Workflow CRUD instance is already initialized in BaseOrchestrator

    @with_session
    def create_workflow(self, session, name: str, **kwargs) -> Workflow:
        """
        Create a new workflow record.

        Args:
            session: Database session
            name (str): Name of the workflow
            **kwargs: Additional workflow attributes (description, priority, status, etc.)

        Returns:
            Workflow: Created workflow record

        Raises:
            OrchestrationError: If workflow creation fails
        """
        try:
            return self.workflow_crud.create_workflow(session, name=name, **kwargs)
        except Exception as e:
            context = self._create_error_context("create", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_workflow_by_id(self, session, workflow_id: str) -> Optional[Workflow]:
        """
        Get workflow by ID.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow

        Returns:
            Optional[Workflow]: Workflow if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.workflow_crud.get_workflow_by_id(session, workflow_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_workflow_by_name(self, session, name: str) -> Optional[Workflow]:
        """
        Get workflow by name.

        Args:
            session: Database session
            name (str): Name of the workflow

        Returns:
            Optional[Workflow]: Workflow if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.workflow_crud.find_by_name(session, name)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_workflow(self, session, workflow_id: str, **kwargs) -> Workflow:
        """
        Update workflow by ID.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow
            **kwargs: Fields to update (name, description, priority, status, etc.)

        Returns:
            Workflow: Updated workflow record

        Raises:
            OrchestrationError: If workflow not found or update fails
        """
        try:
            return self.workflow_crud.update_workflow(session, workflow_id, **kwargs)
        except Exception as e:
            context = self._create_error_context("update", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_workflow(self, session, workflow_id: str) -> bool:
        """
        Delete workflow by ID.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow

        Returns:
            bool: True if deletion successful

        Raises:
            OrchestrationError: If workflow not found or deletion fails
        """
        try:
            return self.workflow_crud.delete_workflow(session, workflow_id)
        except Exception as e:
            context = self._create_error_context("delete", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all_workflows(self, session) -> List[Workflow]:
        """
        Get all workflows.

        Args:
            session: Database session

        Returns:
            List[Workflow]: List of all workflows

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.workflow_crud.get_all_workflows(session)
        except Exception as e:
            context = self._create_error_context("get_all")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_workflows(self, session, **kwargs) -> List[Workflow]:
        """
        Filter workflows by various criteria.

        Args:
            session: Database session
            **kwargs: Filter criteria (status, priority, etc.)

        Returns:
            List[Workflow]: Filtered list of workflows

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            workflows = self.workflow_crud.get_all_workflows(session)
            
            # Apply filters
            if 'status' in kwargs:
                workflows = [w for w in workflows if w.status == kwargs['status']]
            
            if 'priority' in kwargs:
                workflows = [w for w in workflows if w.priority == kwargs['priority']]
            
            return workflows
        except Exception as e:
            context = self._create_error_context("filter", filters=kwargs)
            raise OrchestrationError(str(e), context=context) from e
