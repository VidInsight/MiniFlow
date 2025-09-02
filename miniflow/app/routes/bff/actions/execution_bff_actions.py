"""
Execution BFF Actions

Business logic for Execution operations in the BFF layer.
READ-ONLY operations for execution monitoring and analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class ExecutionActions:
    """Execution business logic for BFF layer (READ-ONLY)"""

    def __init__(self, database_orchestrator: DatabaseOrchestrator):
        """
        Initialize Execution actions
        
        Args:
            database_orchestrator: Database orchestrator instance
        """
        self.orchestrator = database_orchestrator
        self.logger = get_logger("execution_bff_actions")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    async def get_execution_record(self, execution_id: str) -> Dict[str, Any]:
        """
        Get single execution record with related data
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Dict: Execution data with relationships and computed fields
            
        Raises:
            ResourceNotFound: If execution not found
            DatabaseError: If database operation fails
        """
        try:
            self.logger.info(f"Getting execution record: {execution_id}")
            
            # Get execution via orchestrator
            execution = self.orchestrator.execution_orchestrator.get_execution_by_id(execution_id)
            if not execution:
                context = self._create_error_context("get_execution_record", execution_id=execution_id)
                raise ResourceNotFound(f"Execution '{execution_id}' not found", context=context)
            
            # Build enhanced response
            return await self._build_execution_response(execution)
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_execution_record", execution_id=execution_id)
            self.logger.error(f"Failed to get execution '{execution_id}': {str(e)}")
            raise DatabaseError(f"Failed to retrieve execution '{execution_id}': {str(e)}", context=context) from e

    async def get_execution_records(
        self, 
        workflow_id: Optional[str] = None, 
        status: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get execution records with optional filtering
        
        Args:
            workflow_id: Optional workflow ID for filtering
            status: Optional status for filtering
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            Dict: List of executions with pagination info
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build filter description for logging
            filters = []
            if workflow_id:
                filters.append(f"workflow_id={workflow_id}")
            if status:
                filters.append(f"status={status}")
            filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
            
            self.logger.info(f"Getting executions{filter_desc} (skip={skip}, limit={limit})")
            
            # Get executions via orchestrator
            executions = self.orchestrator.execution_orchestrator.filter_executions(
                workflow_id=workflow_id,
                status=status,
                skip=skip,
                limit=limit
            )
            
            # Get total count for pagination
            total_count = self.orchestrator.execution_orchestrator.count_executions(
                workflow_id=workflow_id,
                status=status
            )
            
            # Build enhanced responses
            execution_responses = []
            for execution in executions:
                execution_response = await self._build_execution_response(execution)
                execution_responses.append(execution_response)
            
            # Build pagination info
            page_info = {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": (skip + len(executions)) < total_count,
                "current_page": (skip // limit) + 1 if limit > 0 else 1,
                "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
            }
            
            self.logger.info(f"Retrieved {len(execution_responses)} executions (total: {total_count})")
            
            return {
                "executions": execution_responses,
                "total_count": total_count,
                "page_info": page_info
            }
            
        except Exception as e:
            context = self._create_error_context("get_execution_records", workflow_id=workflow_id, status=status, skip=skip, limit=limit)
            self.logger.error(f"Failed to get executions: {str(e)}")
            raise DatabaseError(f"Failed to retrieve executions: {str(e)}", context=context) from e

    async def _build_execution_response(self, execution) -> Dict[str, Any]:
        """
        Build enhanced execution response with related data and computed fields
        
        Args:
            execution: Execution model instance
            
        Returns:
            Dict: Enhanced execution data for frontend
        """
        try:
            # Base execution data
            response = execution.to_dict()
            
            # Add related workflow data using orchestrator
            try:
                workflow = self.orchestrator.workflow_orchestrator.get_workflow_by_id(execution.workflow_id)
                response["workflow"] = workflow.to_dict() if workflow else None
            except Exception as workflow_error:
                self.logger.warning(f"Failed to load workflow for execution {execution.id}: {str(workflow_error)}")
                response["workflow"] = None
            
            # Calculate computed fields
            response.update(self._calculate_computed_fields(execution, response.get("workflow")))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to build execution response: {str(e)}")
            # Fallback to basic execution data
            basic_response = execution.to_dict()
            basic_response["workflow"] = None
            basic_response["duration_seconds"] = None
            basic_response["progress_percentage"] = None
            basic_response["total_nodes"] = None
            basic_response["is_active"] = False
            return basic_response

    def _calculate_computed_fields(self, execution, workflow_data: Optional[Dict]) -> Dict[str, Any]:
        """
        Calculate computed fields for execution response
        
        Args:
            execution: Execution model instance
            workflow_data: Related workflow data
            
        Returns:
            Dict: Computed fields
        """
        computed = {}
        
        # Calculate duration
        if execution.started_at:
            if execution.ended_at:
                # Completed execution - calculate actual duration
                try:
                    start = datetime.fromisoformat(execution.started_at.isoformat())
                    end = datetime.fromisoformat(execution.ended_at.isoformat())
                    computed["duration_seconds"] = (end - start).total_seconds()
                except:
                    computed["duration_seconds"] = None
            else:
                # Running execution - calculate current duration
                try:
                    start = datetime.fromisoformat(execution.started_at.isoformat())
                    now = datetime.now(start.tzinfo)
                    computed["duration_seconds"] = (now - start).total_seconds()
                except:
                    computed["duration_seconds"] = None
        else:
            computed["duration_seconds"] = None
        
        # Calculate progress percentage
        total_nodes = execution.pending_nodes + execution.executed_nodes
        if total_nodes > 0:
            computed["progress_percentage"] = round((execution.executed_nodes / total_nodes) * 100, 2)
            computed["total_nodes"] = total_nodes
        else:
            computed["progress_percentage"] = 0.0
            computed["total_nodes"] = 0
        
        # Determine if execution is active
        computed["is_active"] = execution.status in ["PENDING", "RUNNING"]
        
        return computed
