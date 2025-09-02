"""
Node BFF Actions

Business logic for Node operations in the BFF layer.
Handles Node CRUD with related entities (Workflow, Script, Edges).
"""

from typing import List, Dict, Any, Optional
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class NodeActions:
    """Node business logic for BFF layer"""

    def __init__(self, database_orchestrator: DatabaseOrchestrator):
        """
        Initialize Node actions
        
        Args:
            database_orchestrator: Database orchestrator instance
        """
        self.orchestrator = database_orchestrator
        self.logger = get_logger("node_bff_actions")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    async def create_node(self, workflow_id: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create new node record
        
        Args:
            workflow_id: ID of the workflow
            name: Name of the node
            **kwargs: Additional node parameters
            
        Returns:
            Dict: Created node with related data
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Creating node '{name}' in workflow '{workflow_id}'")
            
            # Create node via orchestrator
            node = self.orchestrator.node_orchestrator.create_node(
                workflow_id=workflow_id,
                name=name,
                **kwargs
            )
            
            # Get enhanced response with related data
            return await self._build_node_response(node)
            
        except Exception as e:
            context = self._create_error_context("create_node", workflow_id=workflow_id, name=name)
            self.logger.error(f"Failed to create node '{name}': {str(e)}")
            raise DatabaseError(f"Failed to create node '{name}': {str(e)}", context=context) from e

    async def get_node_record(self, node_id: str) -> Dict[str, Any]:
        """
        Get single node record with related data
        
        Args:
            node_id: ID of the node
            
        Returns:
            Dict: Node data with relationships
            
        Raises:
            ResourceNotFound: If node not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Getting node record: {node_id}")
            
            # Get node via orchestrator
            node = self.orchestrator.node_orchestrator.get_node_by_id(node_id)
            if not node:
                context = self._create_error_context("get_node_record", node_id=node_id)
                raise ResourceNotFound(f"Node '{node_id}' not found", context=context)
            
            # Build enhanced response
            return await self._build_node_response(node)
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_node_record", node_id=node_id)
            self.logger.error(f"Failed to get node '{node_id}': {str(e)}")
            raise DatabaseError(f"Failed to retrieve node '{node_id}': {str(e)}", context=context) from e

    async def get_node_records(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get node records with optional workflow filtering
        
        Args:
            workflow_id: Optional workflow ID for filtering
            
        Returns:
            List[Dict]: List of nodes with related data
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            operation = f"get_node_records{'_by_workflow' if workflow_id else ''}"
            self.logger.info(f"Getting nodes{f' for workflow {workflow_id}' if workflow_id else ''}")
            
            # Get nodes via orchestrator
            if workflow_id:
                nodes = self.orchestrator.node_orchestrator.get_nodes_by_workflow(workflow_id)
            else:
                nodes = self.orchestrator.node_orchestrator.get_all_nodes()
            
            # Build enhanced responses
            results = []
            for node in nodes:
                node_response = await self._build_node_response(node)
                results.append(node_response)
            
            self.logger.info(f"Retrieved {len(results)} nodes")
            return results
            
        except Exception as e:
            context = self._create_error_context(operation, workflow_id=workflow_id)
            self.logger.error(f"Failed to get nodes: {str(e)}")
            raise DatabaseError(f"Failed to retrieve nodes: {str(e)}", context=context) from e

    async def update_node(self, node_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update node record
        
        Args:
            node_id: ID of the node to update
            **kwargs: Fields to update
            
        Returns:
            Dict: Updated node with related data
            
        Raises:
            ResourceNotFound: If node not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Updating node: {node_id}")
            
            # Update node via orchestrator
            updated_node = self.orchestrator.node_orchestrator.update_node(node_id, **kwargs)
            
            # Build enhanced response
            return await self._build_node_response(updated_node)
            
        except Exception as e:
            context = self._create_error_context("update_node", node_id=node_id)
            self.logger.error(f"Failed to update node '{node_id}': {str(e)}")
            raise DatabaseError(f"Failed to update node '{node_id}': {str(e)}", context=context) from e

    async def delete_node(self, node_id: str) -> Dict[str, Any]:
        """
        Delete node record and related edges
        
        Args:
            node_id: ID of the node to delete
            
        Returns:
            Dict: Enhanced deletion response
            
        Raises:
            ResourceNotFound: If node not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Deleting node: {node_id}")
            
            # Get node data before deletion for response
            node = self.orchestrator.node_orchestrator.get_node_by_id(node_id)
            if not node:
                context = self._create_error_context("delete_node", node_id=node_id)
                raise ResourceNotFound(f"Node '{node_id}' not found", context=context)
            
            node_data = node.to_dict()
            node_name = node.name
            
            # Step 1: Get and delete all related edges first
            edges_deleted = 0
            try:
                # Get all edges connected to this node
                connected_edges = self.orchestrator.edge_orchestrator.get_edges_by_node(node_id, 'both')
                edges_deleted = len(connected_edges)
                
                # Delete each edge
                for edge in connected_edges:
                    self.orchestrator.edge_orchestrator.delete_edge(edge.id)
                    self.logger.debug(f"Deleted edge: {edge.id}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to delete some edges for node {node_id}: {str(e)}")
                edges_deleted = 0
            
            # Step 2: Delete the node
            success = self.orchestrator.node_orchestrator.delete_node(node_id)
            
            return {
                "success": success,
                "message": f"Node '{node_name}' deleted successfully",
                "node_id": node_id,
                "deleted_node": node_data,
                "database_deleted": success,
                "related_edges_deleted": edges_deleted,
                "warnings": []
            }
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("delete_node", node_id=node_id)
            self.logger.error(f"Failed to delete node '{node_id}': {str(e)}")
            raise DatabaseError(f"Failed to delete node '{node_id}': {str(e)}", context=context) from e

    async def _build_node_response(self, node) -> Dict[str, Any]:
        """
        Build enhanced node response with related data
        
        Args:
            node: Node model instance
            
        Returns:
            Dict: Enhanced node data for frontend
        """
        try:
            # Base node data
            response = node.to_dict()
            
            # Add related workflow data
            if node.workflow:
                response["workflow"] = node.workflow.to_dict()
            else:
                response["workflow"] = None
            
            # Add related script data
            if node.script:
                response["script"] = node.script.to_dict()
            else:
                response["script"] = None
            
            # Add edge data safely using edge orchestrator
            try:
                outgoing_edges = self.orchestrator.edge_orchestrator.get_edges_by_node(node.id, 'outgoing')
                incoming_edges = self.orchestrator.edge_orchestrator.get_edges_by_node(node.id, 'incoming')
                response["outgoing_edges"] = [edge.to_dict() for edge in outgoing_edges]
                response["incoming_edges"] = [edge.to_dict() for edge in incoming_edges]
            except Exception as edge_error:
                self.logger.warning(f"Failed to load edges for node {node.id}: {str(edge_error)}")
                response["outgoing_edges"] = []
                response["incoming_edges"] = []
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to build node response: {str(e)}")
            # Fallback to basic node data with empty edges
            basic_response = node.to_dict()
            basic_response["workflow"] = None
            basic_response["script"] = None
            basic_response["outgoing_edges"] = []
            basic_response["incoming_edges"] = []
            return basic_response
