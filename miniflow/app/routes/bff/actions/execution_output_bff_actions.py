"""
ExecutionOutput BFF Actions

Business logic for ExecutionOutput operations in the BFF layer.
READ-ONLY operations for execution results monitoring and analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class ExecutionOutputActions:
    """ExecutionOutput business logic for BFF layer (READ-ONLY)"""

    def __init__(self, database_orchestrator: DatabaseOrchestrator):
        """
        Initialize ExecutionOutput actions
        
        Args:
            database_orchestrator: Database orchestrator instance
        """
        self.orchestrator = database_orchestrator
        self.logger = get_logger("execution_output_bff_actions")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    async def get_execution_output_record(self, execution_output_id: str) -> Dict[str, Any]:
        """
        Get single execution output record with related data
        
        Args:
            execution_output_id: ID of the execution output
            
        Returns:
            Dict: ExecutionOutput data with relationships and computed fields
            
        Raises:
            ResourceNotFound: If execution output not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Getting execution output record: {execution_output_id}")
            
            # Get execution output via orchestrator
            execution_output = self.orchestrator.execution_output_orchestrator.get_execution_output_by_id(execution_output_id)
            if not execution_output:
                context = self._create_error_context("get_execution_output_record", execution_output_id=execution_output_id)
                raise ResourceNotFound(f"ExecutionOutput '{execution_output_id}' not found", context=context)
            
            # Build enhanced response
            return await self._build_execution_output_response(execution_output)
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_execution_output_record", execution_output_id=execution_output_id)
            self.logger.error(f"Failed to get execution output '{execution_output_id}': {str(e)}")
            raise DatabaseError(f"Failed to retrieve execution output '{execution_output_id}': {str(e)}", context=context) from e

    async def get_execution_output_records(
        self, 
        execution_id: Optional[str] = None, 
        workflow_id: Optional[str] = None, 
        node_id: Optional[str] = None, 
        status: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get execution output records with optional filtering
        
        Args:
            execution_id: Optional execution ID for filtering
            workflow_id: Optional workflow ID for filtering
            node_id: Optional node ID for filtering
            status: Optional status for filtering
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Dict: List of execution outputs with pagination info
            
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
            if status:
                filters.append(f"status={status}")
            filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
            
            self.logger.info(f"Getting execution outputs{filter_desc} (skip={skip}, limit={limit})")
            
            # Get execution outputs via orchestrator
            execution_outputs = self.orchestrator.execution_output_orchestrator.filter_execution_outputs(
                execution_id, workflow_id, node_id, status, skip, limit
            )
            
            # Get total count for pagination
            total_count = self.orchestrator.execution_output_orchestrator.count_execution_outputs(
                execution_id, workflow_id, node_id, status
            )
            
            # Build enhanced responses
            execution_output_responses = []
            for execution_output in execution_outputs:
                execution_output_response = await self._build_execution_output_response(execution_output)
                execution_output_responses.append(execution_output_response)
            
            # Build pagination info
            page_info = {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": (skip + len(execution_outputs)) < total_count,
                "current_page": (skip // limit) + 1 if limit > 0 else 1,
                "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
            }
            
            self.logger.info(f"Retrieved {len(execution_output_responses)} execution outputs (total: {total_count})")
            
            return {
                "execution_outputs": execution_output_responses,
                "total_count": total_count,
                "page_info": page_info
            }
            
        except Exception as e:
            context = self._create_error_context("get_execution_output_records", execution_id=execution_id, workflow_id=workflow_id, node_id=node_id, status=status, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution outputs: {str(e)}")
            raise DatabaseError(f"Failed to retrieve execution outputs: {str(e)}", context=context) from e

    async def _build_execution_output_response(self, execution_output) -> Dict[str, Any]:
        """
        Build enhanced execution output response with related data and computed fields
        
        Args:
            execution_output: ExecutionOutput model instance
            
        Returns:
            Dict: Enhanced execution output data for frontend
        """
        try:
            # Base execution output data
            response = execution_output.to_dict()
            
            # Add related execution data using orchestrator
            try:
                execution = self.orchestrator.execution_orchestrator.get_execution_by_id(execution_output.execution_id)
                response["execution"] = execution.to_dict() if execution else None
            except Exception as execution_error:
                self.logger.warning(f"Failed to load execution for execution output {execution_output.id}: {str(execution_error)}")
                response["execution"] = None
            
            # Add related workflow data using orchestrator
            try:
                workflow = self.orchestrator.workflow_orchestrator.get_workflow_by_id(execution_output.workflow_id)
                response["workflow"] = workflow.to_dict() if workflow else None
            except Exception as workflow_error:
                self.logger.warning(f"Failed to load workflow for execution output {execution_output.id}: {str(workflow_error)}")
                response["workflow"] = None
            
            # Add related node data using orchestrator
            try:
                node = self.orchestrator.node_orchestrator.get_node_by_id(execution_output.node_id)
                response["node"] = node.to_dict() if node else None
            except Exception as node_error:
                self.logger.warning(f"Failed to load node for execution output {execution_output.id}: {str(node_error)}")
                response["node"] = None
            
            # Calculate computed fields
            response.update(self._calculate_computed_fields(execution_output))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to build execution output response: {str(e)}")
            # Fallback to basic execution output data
            basic_response = execution_output.to_dict()
            basic_response["execution"] = None
            basic_response["workflow"] = None
            basic_response["node"] = None
            basic_response["duration_seconds"] = None
            basic_response["success"] = False
            return basic_response

    def _calculate_computed_fields(self, execution_output) -> Dict[str, Any]:
        """
        Calculate computed fields for execution output response
        
        Args:
            execution_output: ExecutionOutput model instance
            
        Returns:
            Dict: Computed fields
        """
        computed = {}
        
        # Calculate duration
        if execution_output.started_at and execution_output.ended_at:
            try:
                start = datetime.fromisoformat(execution_output.started_at.isoformat())
                end = datetime.fromisoformat(execution_output.ended_at.isoformat())
                computed["duration_seconds"] = (end - start).total_seconds()
            except:
                computed["duration_seconds"] = None
        else:
            computed["duration_seconds"] = None
        
        # Determine success
        computed["success"] = execution_output.status == "SUCCESS"
        
        return computed
