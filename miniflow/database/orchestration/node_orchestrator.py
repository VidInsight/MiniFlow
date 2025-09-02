"""
Node Orchestrator

This module provides high-level orchestration for node operations,
managing database sessions and coordinating complex node workflows.
"""

from typing import List, Optional, Dict, Any
from miniflow.database.models import Node
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class NodeOrchestrator(BaseOrchestrator):
    """Node orchestrator for basic CRUD operations and node management."""

    def __init__(self, database_engine):
        """
        Initialize node orchestrator
        
        Args:
            database_engine: DatabaseEngine instance
        """
        super().__init__(database_engine)
        # Node CRUD instance is already initialized in BaseOrchestrator

    @with_session
    def create_node(self, session, workflow_id: str, name: str, **kwargs) -> Node:
        """
        Create a new node record.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow this node belongs to
            name (str): Name of the node
            **kwargs: Additional node attributes (description, script_id, params, etc.)

        Returns:
            Node: Created node record

        Raises:
            OrchestrationError: If node creation fails
        """
        try:
            return self.node_crud.create_node(session, workflow_id=workflow_id, name=name, **kwargs)
        except Exception as e:
            context = self._create_error_context("create", workflow_id=workflow_id, name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_node_by_id(self, session, node_id: str) -> Optional[Node]:
        """
        Get node by ID.

        Args:
            session: Database session
            node_id (str): ID of the node

        Returns:
            Optional[Node]: Node if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.node_crud.get_node_by_id(session, node_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", node_id=node_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_node_by_name_and_workflow(self, session, name: str, workflow_id: str) -> Optional[Node]:
        """
        Get node by name within a specific workflow.

        Args:
            session: Database session
            name (str): Name of the node
            workflow_id (str): ID of the workflow

        Returns:
            Optional[Node]: Node if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.node_crud.find_by_name_and_workflow(session, name, workflow_id)
        except Exception as e:
            context = self._create_error_context("get_by_name_and_workflow", name=name, workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_nodes_by_workflow(self, session, workflow_id: str) -> List[Node]:
        """
        Get all nodes for a specific workflow.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow

        Returns:
            List[Node]: List of nodes in the workflow

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.node_crud.get_nodes_by_workflow(session, workflow_id)
        except Exception as e:
            context = self._create_error_context("get_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_node(self, session, node_id: str, **kwargs) -> Node:
        """
        Update node by ID.

        Args:
            session: Database session
            node_id (str): ID of the node
            **kwargs: Fields to update (name, description, script_id, params, etc.)

        Returns:
            Node: Updated node record

        Raises:
            OrchestrationError: If node not found or update fails
        """
        try:
            return self.node_crud.update_node(session, node_id, **kwargs)
        except Exception as e:
            context = self._create_error_context("update", node_id=node_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_node(self, session, node_id: str) -> bool:
        """
        Delete node by ID.

        Args:
            session: Database session
            node_id (str): ID of the node

        Returns:
            bool: True if deletion successful

        Raises:
            OrchestrationError: If node not found or deletion fails
        """
        try:
            return self.node_crud.delete_node(session, node_id)
        except Exception as e:
            context = self._create_error_context("delete", node_id=node_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all_nodes(self, session) -> List[Node]:
        """
        Get all nodes.

        Args:
            session: Database session

        Returns:
            List[Node]: List of all nodes

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.node_crud.get_all_nodes(session)
        except Exception as e:
            context = self._create_error_context("get_all")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_nodes(self, session, **kwargs) -> List[Node]:
        """
        Filter nodes by various criteria using database-level filtering.

        Args:
            session: Database session
            **kwargs: Filter criteria (workflow_id, script_id, etc.)

        Returns:
            List[Node]: Filtered list of nodes

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            # Use database-level filtering for better performance
            if not kwargs:
                return self.node_crud.get_all_nodes(session)
            
            # Use BaseCRUD filter method for efficient querying
            return self.node_crud.filter(session, kwargs)
        except Exception as e:
            context = self._create_error_context("filter", filters=kwargs)
            raise OrchestrationError(str(e), context=context) from e
