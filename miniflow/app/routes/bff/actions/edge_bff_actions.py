"""
Edge BFF Actions

Business logic for Edge operations in the BFF layer.
Handles Edge CRUD with related entities (Workflow, Nodes).
"""

from typing import List, Dict, Any, Optional
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class EdgeActions:
    """Edge business logic for BFF layer"""

    def __init__(self, database_orchestrator: DatabaseOrchestrator):
        """
        Initialize Edge actions
        
        Args:
            database_orchestrator: Database orchestrator instance
        """
        self.orchestrator = database_orchestrator
        self.logger = get_logger("edge_bff_actions")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    async def create_edge(self, workflow_id: str, from_node_id: str, to_node_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create new edge record
        
        Args:
            workflow_id: ID of the workflow
            from_node_id: ID of the source node
            to_node_id: ID of the target node
            **kwargs: Additional edge parameters
            
        Returns:
            Dict: Created edge with related data
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Creating edge from '{from_node_id}' to '{to_node_id}' in workflow '{workflow_id}'")
            
            # Create edge via orchestrator
            edge = self.orchestrator.edge_orchestrator.create_edge(
                workflow_id=workflow_id,
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                **kwargs
            )
            
            # Get enhanced response with related data
            return await self._build_edge_response(edge)
            
        except Exception as e:
            context = self._create_error_context("create_edge", workflow_id=workflow_id, from_node_id=from_node_id, to_node_id=to_node_id)
            self.logger.error(f"Failed to create edge: {str(e)}")
            raise DatabaseError(f"Failed to create edge: {str(e)}", context=context) from e

    async def get_edge_record(self, edge_id: str) -> Dict[str, Any]:
        """
        Get single edge record with related data
        
        Args:
            edge_id: ID of the edge
            
        Returns:
            Dict: Edge data with relationships
            
        Raises:
            ResourceNotFound: If edge not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Getting edge record: {edge_id}")
            
            # Get edge via orchestrator
            edge = self.orchestrator.edge_orchestrator.get_edge_by_id(edge_id)
            if not edge:
                context = self._create_error_context("get_edge_record", edge_id=edge_id)
                raise ResourceNotFound(f"Edge '{edge_id}' not found", context=context)
            
            # Build enhanced response
            return await self._build_edge_response(edge)
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_edge_record", edge_id=edge_id)
            self.logger.error(f"Failed to get edge '{edge_id}': {str(e)}")
            raise DatabaseError(f"Failed to retrieve edge '{edge_id}': {str(e)}", context=context) from e

    async def get_edge_records(self, workflow_id: Optional[str] = None, node_id: Optional[str] = None, direction: str = 'both') -> List[Dict[str, Any]]:
        """
        Get edge records with optional filtering
        
        Args:
            workflow_id: Optional workflow ID for filtering
            node_id: Optional node ID for filtering
            direction: For node filtering: 'incoming', 'outgoing', or 'both'
            
        Returns:
            List[Dict]: List of edges with related data
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            operation = f"get_edge_records"
            if workflow_id:
                operation += f"_by_workflow"
            if node_id:
                operation += f"_by_node_{direction}"
                
            self.logger.info(f"Getting edges{f' for workflow {workflow_id}' if workflow_id else ''}{f' for node {node_id} ({direction})' if node_id else ''}")
            
            # Get edges via orchestrator
            if workflow_id:
                edges = self.orchestrator.edge_orchestrator.get_edges_by_workflow(workflow_id)
            elif node_id:
                edges = self.orchestrator.edge_orchestrator.get_edges_by_node(node_id, direction)
            else:
                edges = self.orchestrator.edge_orchestrator.get_all_edges()
            
            # Build enhanced responses
            results = []
            for edge in edges:
                edge_response = await self._build_edge_response(edge)
                results.append(edge_response)
            
            self.logger.info(f"Retrieved {len(results)} edges")
            return results
            
        except Exception as e:
            context = self._create_error_context(operation, workflow_id=workflow_id, node_id=node_id, direction=direction)
            self.logger.error(f"Failed to get edges: {str(e)}")
            raise DatabaseError(f"Failed to retrieve edges: {str(e)}", context=context) from e

    async def update_edge(self, edge_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update edge record
        
        Args:
            edge_id: ID of the edge to update
            **kwargs: Fields to update
            
        Returns:
            Dict: Updated edge with related data
            
        Raises:
            ResourceNotFound: If edge not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Updating edge: {edge_id}")
            
            # Update edge via orchestrator
            updated_edge = self.orchestrator.edge_orchestrator.update_edge(edge_id, **kwargs)
            
            # Build enhanced response
            return await self._build_edge_response(updated_edge)
            
        except Exception as e:
            context = self._create_error_context("update_edge", edge_id=edge_id)
            self.logger.error(f"Failed to update edge '{edge_id}': {str(e)}")
            raise DatabaseError(f"Failed to update edge '{edge_id}': {str(e)}", context=context) from e

    async def delete_edge(self, edge_id: str) -> Dict[str, Any]:
        """
        Delete edge record
        
        Args:
            edge_id: ID of the edge to delete
            
        Returns:
            Dict: Enhanced deletion response
            
        Raises:
            ResourceNotFound: If edge not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Deleting edge: {edge_id}")
            
            # Get edge data before deletion for response
            edge = self.orchestrator.edge_orchestrator.get_edge_by_id(edge_id)
            if not edge:
                context = self._create_error_context("delete_edge", edge_id=edge_id)
                raise ResourceNotFound(f"Edge '{edge_id}' not found", context=context)
            
            edge_data = edge.to_dict()
            
            # Delete edge
            success = self.orchestrator.edge_orchestrator.delete_edge(edge_id)
            
            return {
                "success": success,
                "message": f"Edge from '{edge.from_node_id}' to '{edge.to_node_id}' deleted successfully",
                "edge_id": edge_id,
                "deleted_edge": edge_data,
                "database_deleted": success,
                "warnings": []
            }
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("delete_edge", edge_id=edge_id)
            self.logger.error(f"Failed to delete edge '{edge_id}': {str(e)}")
            raise DatabaseError(f"Failed to delete edge '{edge_id}': {str(e)}", context=context) from e

    async def _build_edge_response(self, edge) -> Dict[str, Any]:
        """
        Build enhanced edge response with related data
        
        Args:
            edge: Edge model instance
            
        Returns:
            Dict: Enhanced edge data for frontend
        """
        try:
            # Base edge data
            response = edge.to_dict()
            
            # Add related workflow data using orchestrator
            try:
                workflow = self.orchestrator.workflow_orchestrator.get_workflow_by_id(edge.workflow_id)
                response["workflow"] = workflow.to_dict() if workflow else None
            except Exception as workflow_error:
                self.logger.warning(f"Failed to load workflow for edge {edge.id}: {str(workflow_error)}")
                response["workflow"] = None
            
            # Add related from_node data using orchestrator
            try:
                from_node = self.orchestrator.node_orchestrator.get_node_by_id(edge.from_node_id)
                response["from_node"] = from_node.to_dict() if from_node else None
            except Exception as from_node_error:
                self.logger.warning(f"Failed to load from_node for edge {edge.id}: {str(from_node_error)}")
                response["from_node"] = None
                
            # Add related to_node data using orchestrator
            try:
                to_node = self.orchestrator.node_orchestrator.get_node_by_id(edge.to_node_id)
                response["to_node"] = to_node.to_dict() if to_node else None
            except Exception as to_node_error:
                self.logger.warning(f"Failed to load to_node for edge {edge.id}: {str(to_node_error)}")
                response["to_node"] = None
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to build edge response: {str(e)}")
            # Fallback to basic edge data with null relationships
            basic_response = edge.to_dict()
            basic_response["workflow"] = None
            basic_response["from_node"] = None
            basic_response["to_node"] = None
            return basic_response
