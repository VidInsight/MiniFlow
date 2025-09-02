"""
Edge Orchestrator

This module provides high-level orchestration for edge operations,
managing database sessions and coordinating edge workflows.
"""

from typing import List, Optional, Dict, Any
from miniflow.database.models import Edge
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class EdgeOrchestrator(BaseOrchestrator):
    """Edge orchestrator for basic CRUD operations and edge management."""

    def __init__(self, database_engine):
        """
        Initialize edge orchestrator
        
        Args:
            database_engine: DatabaseEngine instance
        """
        super().__init__(database_engine)
        # Edge CRUD instance is already initialized in BaseOrchestrator

    @with_session
    def create_edge(self, session, workflow_id: str, from_node_id: str, to_node_id: str, **kwargs) -> Edge:
        """
        Create a new edge record.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow this edge belongs to
            from_node_id (str): ID of the source node
            to_node_id (str): ID of the target node
            **kwargs: Additional edge attributes (condition_type, etc.)

        Returns:
            Edge: Created edge record

        Raises:
            OrchestrationError: If edge creation fails
        """
        try:
            return self.edge_crud.create_edge(session, workflow_id=workflow_id, from_node_id=from_node_id, to_node_id=to_node_id, **kwargs)
        except Exception as e:
            context = self._create_error_context("create", workflow_id=workflow_id, from_node_id=from_node_id, to_node_id=to_node_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_edge_by_id(self, session, edge_id: str) -> Optional[Edge]:
        """
        Get edge by ID.

        Args:
            session: Database session
            edge_id (str): ID of the edge

        Returns:
            Optional[Edge]: Edge if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.edge_crud.get_edge_by_id(session, edge_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", edge_id=edge_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_edges_by_workflow(self, session, workflow_id: str) -> List[Edge]:
        """
        Get all edges for a specific workflow.

        Args:
            session: Database session
            workflow_id (str): ID of the workflow

        Returns:
            List[Edge]: List of edges in the workflow

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.edge_crud.get_edges_by_workflow(session, workflow_id)
        except Exception as e:
            context = self._create_error_context("get_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_edges_by_node(self, session, node_id: str, direction: str = 'both') -> List[Edge]:
        """
        Get edges connected to a specific node.

        Args:
            session: Database session
            node_id (str): ID of the node
            direction (str): 'incoming', 'outgoing', or 'both'

        Returns:
            List[Edge]: List of edges connected to the node

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.edge_crud.get_edges_by_node(session, node_id, direction)
        except Exception as e:
            context = self._create_error_context("get_by_node", node_id=node_id, direction=direction)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_edge(self, session, edge_id: str, **kwargs) -> Edge:
        """
        Update edge by ID.

        Args:
            session: Database session
            edge_id (str): ID of the edge
            **kwargs: Fields to update (condition_type, etc.)

        Returns:
            Edge: Updated edge record

        Raises:
            OrchestrationError: If edge not found or update fails
        """
        try:
            return self.edge_crud.update_edge(session, edge_id, **kwargs)
        except Exception as e:
            context = self._create_error_context("update", edge_id=edge_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete_edge(self, session, edge_id: str) -> bool:
        """
        Delete edge by ID.

        Args:
            session: Database session
            edge_id (str): ID of the edge

        Returns:
            bool: True if deletion successful

        Raises:
            OrchestrationError: If edge not found or deletion fails
        """
        try:
            return self.edge_crud.delete_edge(session, edge_id)
        except Exception as e:
            context = self._create_error_context("delete", edge_id=edge_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all_edges(self, session) -> List[Edge]:
        """
        Get all edges.

        Args:
            session: Database session

        Returns:
            List[Edge]: List of all edges

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.edge_crud.get_all_edges(session)
        except Exception as e:
            context = self._create_error_context("get_all")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_edges(self, session, **kwargs) -> List[Edge]:
        """
        Filter edges by various criteria.

        Args:
            session: Database session
            **kwargs: Filter criteria (workflow_id, from_node_id, to_node_id, etc.)

        Returns:
            List[Edge]: Filtered list of edges

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            # Use database-level filtering for better performance
            if not kwargs:
                return self.edge_crud.get_all_edges(session)
            
            # Use BaseCRUD filter method for efficient querying
            return self.edge_crud.filter(session, kwargs)
        except Exception as e:
            context = self._create_error_context("filter", filters=kwargs)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def find_edge_between_nodes(self, session, from_node_id: str, to_node_id: str) -> Optional[Edge]:
        """
        Find edge between two specific nodes.

        Args:
            session: Database session
            from_node_id (str): ID of the source node
            to_node_id (str): ID of the target node

        Returns:
            Optional[Edge]: Edge if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.edge_crud.find_edge_between_nodes(session, from_node_id, to_node_id)
        except Exception as e:
            context = self._create_error_context("find_between_nodes", from_node_id=from_node_id, to_node_id=to_node_id)
            raise OrchestrationError(str(e), context=context) from e
