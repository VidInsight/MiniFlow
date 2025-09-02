"""
ExecutionOutput Orchestrator

High-level business logic for ExecutionOutput operations.
READ-ONLY operations for execution results monitoring and analysis.
"""

from typing import List, Optional
from miniflow.database.models import ExecutionOutput
from miniflow.database.crud.execution_output_crud import ExecutionOutputCRUD
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class ExecutionOutputOrchestrator(BaseOrchestrator):
    """ExecutionOutput orchestration logic (READ-ONLY)"""

    def __init__(self, database_engine):
        """
        Initialize ExecutionOutput orchestrator
        
        Args:
            database_engine: Database engine instance
        """
        super().__init__(database_engine)
        self.execution_output_crud = ExecutionOutputCRUD()
        self.logger = get_logger("execution_output_orchestrator")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    @with_session
    def get_execution_output_by_id(self, session, execution_output_id: str) -> Optional[ExecutionOutput]:
        """
        Get execution output by ID
        
        Args:
            execution_output_id: ID of the execution output
            session: Database session (injected by decorator)
            
        Returns:
            ExecutionOutput instance or None
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution output by ID: {execution_output_id}")
            
            execution_output = self.execution_output_crud.get_execution_output_by_id(session, execution_output_id)
            
            if execution_output:
                self.logger.info(f"Execution output found: {execution_output_id}")
            else:
                self.logger.warning(f"Execution output not found: {execution_output_id}")
            
            return execution_output
            
        except Exception as e:
            context = self._create_error_context("get_execution_output_by_id", execution_output_id=execution_output_id)
            self.logger.error(f"Failed to get execution output '{execution_output_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution output '{execution_output_id}': {str(e)}", context=context) from e

    @with_session
    def get_all_execution_outputs(self, session, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get all execution outputs with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionOutput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting all execution outputs (skip={skip}, limit={limit})")
            
            execution_outputs = self.execution_output_crud.get_all_execution_outputs(session, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_outputs)} execution outputs")
            return execution_outputs
            
        except Exception as e:
            context = self._create_error_context("get_all_execution_outputs", skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution outputs: {str(e)}")
            raise OrchestrationError(f"Failed to get execution outputs: {str(e)}", context=context) from e

    @with_session
    def get_execution_outputs_by_execution(self, session, execution_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by execution ID
        
        Args:
            execution_id: ID of the execution
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionOutput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution outputs for execution: {execution_id} (skip={skip}, limit={limit})")
            
            execution_outputs = self.execution_output_crud.get_execution_outputs_by_execution(session, execution_id, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_outputs)} execution outputs for execution {execution_id}")
            return execution_outputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_outputs_by_execution", execution_id=execution_id, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution outputs for execution '{execution_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution outputs for execution '{execution_id}': {str(e)}", context=context) from e

    @with_session
    def get_execution_outputs_by_workflow(self, session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by workflow ID
        
        Args:
            workflow_id: ID of the workflow
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionOutput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution outputs for workflow: {workflow_id} (skip={skip}, limit={limit})")
            
            execution_outputs = self.execution_output_crud.get_execution_outputs_by_workflow(session, workflow_id, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_outputs)} execution outputs for workflow {workflow_id}")
            return execution_outputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_outputs_by_workflow", workflow_id=workflow_id, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution outputs for workflow '{workflow_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution outputs for workflow '{workflow_id}': {str(e)}", context=context) from e

    @with_session
    def get_execution_outputs_by_node(self, session, node_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by node ID
        
        Args:
            node_id: ID of the node
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionOutput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution outputs for node: {node_id} (skip={skip}, limit={limit})")
            
            execution_outputs = self.execution_output_crud.get_execution_outputs_by_node(session, node_id, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_outputs)} execution outputs for node {node_id}")
            return execution_outputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_outputs_by_node", node_id=node_id, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution outputs for node '{node_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution outputs for node '{node_id}': {str(e)}", context=context) from e

    @with_session
    def get_execution_outputs_by_status(self, session, status: str, skip: int = 0, limit: int = 100) -> List[ExecutionOutput]:
        """
        Get execution outputs by status
        
        Args:
            status: Status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionOutput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution outputs with status: {status} (skip={skip}, limit={limit})")
            
            execution_outputs = self.execution_output_crud.get_execution_outputs_by_status(session, status, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_outputs)} execution outputs with status {status}")
            return execution_outputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_outputs_by_status", status=status, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution outputs with status '{status}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution outputs with status '{status}': {str(e)}", context=context) from e

    @with_session
    def filter_execution_outputs(
        self, 
        session,
        execution_id: Optional[str] = None, 
        workflow_id: Optional[str] = None, 
        node_id: Optional[str] = None, 
        status: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ExecutionOutput]:
        """
        Get execution outputs with flexible filtering
        
        Args:
            execution_id: Optional execution ID filter
            workflow_id: Optional workflow ID filter
            node_id: Optional node ID filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionOutput instances matching filters
            
        Raises:
            OrchestrationError: If operation fails
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
            
            self.logger.info(f"Filtering execution outputs{filter_desc} (skip={skip}, limit={limit})")
            
            # Apply filters in priority order
            if execution_id:
                execution_outputs = self.execution_output_crud.get_execution_outputs_by_execution(session, execution_id, skip=skip, limit=limit)
            elif workflow_id:
                execution_outputs = self.execution_output_crud.get_execution_outputs_by_workflow(session, workflow_id, skip=skip, limit=limit)
            elif node_id:
                execution_outputs = self.execution_output_crud.get_execution_outputs_by_node(session, node_id, skip=skip, limit=limit)
            elif status:
                execution_outputs = self.execution_output_crud.get_execution_outputs_by_status(session, status, skip=skip, limit=limit)
            else:
                execution_outputs = self.execution_output_crud.get_all_execution_outputs(session, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_outputs)} execution outputs{filter_desc}")
            return execution_outputs
            
        except Exception as e:
            context = self._create_error_context("filter_execution_outputs", execution_id=execution_id, workflow_id=workflow_id, node_id=node_id, status=status, skip=skip, limit=limit)
            self.logger.error(f"Failed to filter execution outputs: {str(e)}")
            raise OrchestrationError(f"Failed to filter execution outputs: {str(e)}", context=context) from e

    @with_session
    def count_execution_outputs(
        self, 
        session,
        execution_id: Optional[str] = None, 
        workflow_id: Optional[str] = None, 
        node_id: Optional[str] = None, 
        status: Optional[str] = None
    ) -> int:
        """
        Count execution outputs with optional filtering
        
        Args:
            execution_id: Optional execution ID filter
            workflow_id: Optional workflow ID filter
            node_id: Optional node ID filter
            status: Optional status filter
            session: Database session (injected by decorator)
            
        Returns:
            Number of execution outputs matching filters
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            # Apply filters for counting
            if execution_id:
                count = self.execution_output_crud.count_execution_outputs_by_execution(session, execution_id)
            elif workflow_id:
                count = self.execution_output_crud.count_execution_outputs_by_workflow(session, workflow_id)
            elif node_id:
                count = self.execution_output_crud.count_execution_outputs_by_node(session, node_id)
            elif status:
                count = self.execution_output_crud.count_execution_outputs_by_status(session, status)
            else:
                count = self.execution_output_crud.count_execution_outputs(session)
            
            self.logger.info(f"Counted {count} execution outputs")
            return count
            
        except Exception as e:
            context = self._create_error_context("count_execution_outputs", execution_id=execution_id, workflow_id=workflow_id, node_id=node_id, status=status)
            self.logger.error(f"Failed to count execution outputs: {str(e)}")
            raise OrchestrationError(f"Failed to count execution outputs: {str(e)}", context=context) from e
