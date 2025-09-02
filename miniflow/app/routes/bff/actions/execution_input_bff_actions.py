"""
ExecutionInput BFF Actions

Business logic for ExecutionInput operations in the BFF layer.
READ-ONLY operations for scheduler monitoring and execution planning.
"""

from typing import List, Dict, Any, Optional
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class ExecutionInputActions:
    """ExecutionInput business logic for BFF layer (READ-ONLY)"""

    def __init__(self, database_orchestrator: DatabaseOrchestrator):
        """
        Initialize ExecutionInput actions
        
        Args:
            database_orchestrator: Database orchestrator instance
        """
        self.orchestrator = database_orchestrator
        self.logger = get_logger("execution_input_bff_actions")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    async def get_execution_input_record(self, execution_input_id: str) -> Dict[str, Any]:
        """
        Get single execution input record with related data
        
        Args:
            execution_input_id: ID of the execution input
            
        Returns:
            Dict: ExecutionInput data with relationships
            
        Raises:
            ResourceNotFound: If execution input not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Getting execution input record: {execution_input_id}")
            
            # Get execution input via orchestrator
            execution_input = self.orchestrator.execution_input_orchestrator.get_execution_input_by_id(execution_input_id)
            if not execution_input:
                context = self._create_error_context("get_execution_input_record", execution_input_id=execution_input_id)
                raise ResourceNotFound(f"ExecutionInput '{execution_input_id}' not found", context=context)
            
            # Build enhanced response
            return await self._build_execution_input_response(execution_input)
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_execution_input_record", execution_input_id=execution_input_id)
            self.logger.error(f"Failed to get execution input '{execution_input_id}': {str(e)}")
            raise DatabaseError(f"Failed to retrieve execution input '{execution_input_id}': {str(e)}", context=context) from e

    async def get_execution_input_records(
        self, 
        execution_id: Optional[str] = None, 
        workflow_id: Optional[str] = None, 
        node_id: Optional[str] = None, 
        priority: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get execution input records with optional filtering
        
        Args:
            execution_id: Optional execution ID for filtering
            workflow_id: Optional workflow ID for filtering
            node_id: Optional node ID for filtering
            priority: Optional priority for filtering
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Dict: List of execution inputs with pagination info
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build filter description for logging
            filters = []
            if execution_id:
                filters.append(f"execution_id={execution_id}")
            if workflow_id:
                filters.append(f"workflow_id={workflow_id}")
            if node_id:
                filters.append(f"node_id={node_id}")
            if priority is not None:
                filters.append(f"priority={priority}")
            filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
            
            self.logger.info(f"Getting execution inputs{filter_desc} (skip={skip}, limit={limit})")
            
            # Get execution inputs via orchestrator
            execution_inputs = self.orchestrator.execution_input_orchestrator.filter_execution_inputs(
                execution_id, workflow_id, node_id, priority, skip, limit
            )
            
            # Get total count for pagination
            total_count = self.orchestrator.execution_input_orchestrator.count_execution_inputs(
                execution_id, workflow_id, node_id
            )
            
            # Build enhanced responses
            execution_input_responses = []
            for execution_input in execution_inputs:
                execution_input_response = await self._build_execution_input_response(execution_input)
                execution_input_responses.append(execution_input_response)
            
            # Build pagination info
            page_info = {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": (skip + len(execution_inputs)) < total_count,
                "current_page": (skip // limit) + 1 if limit > 0 else 1,
                "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
            }
            
            self.logger.info(f"Retrieved {len(execution_input_responses)} execution inputs (total: {total_count})")
            
            return {
                "execution_inputs": execution_input_responses,
                "total_count": total_count,
                "page_info": page_info
            }
            
        except Exception as e:
            context = self._create_error_context("get_execution_input_records", execution_id=execution_id, workflow_id=workflow_id, node_id=node_id, priority=priority, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution inputs: {str(e)}")
            raise DatabaseError(f"Failed to retrieve execution inputs: {str(e)}", context=context) from e

    async def _build_execution_input_response(self, execution_input) -> Dict[str, Any]:
        """
        Build enhanced execution input response with related data
        
        Args:
            execution_input: ExecutionInput model instance
            
        Returns:
            Dict: Enhanced execution input data for frontend
        """
        try:
            # Base execution input data
            response = execution_input.to_dict()
            
            # Add related execution data using orchestrator
            try:
                execution = self.orchestrator.execution_orchestrator.get_execution_by_id(execution_input.execution_id)
                response["execution"] = execution.to_dict() if execution else None
            except Exception as execution_error:
                self.logger.warning(f"Failed to load execution for execution input {execution_input.id}: {str(execution_error)}")
                response["execution"] = None
            
            # Add related workflow data using orchestrator
            try:
                workflow = self.orchestrator.workflow_orchestrator.get_workflow_by_id(execution_input.workflow_id)
                response["workflow"] = workflow.to_dict() if workflow else None
            except Exception as workflow_error:
                self.logger.warning(f"Failed to load workflow for execution input {execution_input.id}: {str(workflow_error)}")
                response["workflow"] = None
            
            # Add related node data using orchestrator
            try:
                node = self.orchestrator.node_orchestrator.get_node_by_id(execution_input.node_id)
                response["node"] = node.to_dict() if node else None
            except Exception as node_error:
                self.logger.warning(f"Failed to load node for execution input {execution_input.id}: {str(node_error)}")
                response["node"] = None
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to build execution input response: {str(e)}")
            # Fallback to basic execution input data
            basic_response = execution_input.to_dict()
            basic_response["execution"] = None
            basic_response["workflow"] = None
            basic_response["node"] = None
            return basic_response
