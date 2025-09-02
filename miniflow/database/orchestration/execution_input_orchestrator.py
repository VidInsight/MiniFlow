"""
ExecutionInput Orchestrator

High-level business logic for ExecutionInput operations.
READ-ONLY operations for scheduler monitoring and execution planning.
"""

from typing import List, Optional
from miniflow.database.models import ExecutionInput
from miniflow.database.crud.execution_input_crud import ExecutionInputCRUD
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ErrorContext, ErrorSeverity
from miniflow.core.logger import get_logger


class ExecutionInputOrchestrator(BaseOrchestrator):
    """ExecutionInput orchestration logic (READ-ONLY)"""

    def __init__(self, database_engine):
        """
        Initialize ExecutionInput orchestrator
        
        Args:
            database_engine: Database engine instance
        """
        super().__init__(database_engine)
        self.execution_input_crud = ExecutionInputCRUD()
        self.logger = get_logger("execution_input_orchestrator")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    @with_session
    def get_execution_input_by_id(self, session, execution_input_id: str) -> Optional[ExecutionInput]:
        """
        Get execution input by ID
        
        Args:
            execution_input_id: ID of the execution input
            session: Database session (injected by decorator)
            
        Returns:
            ExecutionInput instance or None
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution input by ID: {execution_input_id}")
            
            execution_input = self.execution_input_crud.get_execution_input_by_id(session, execution_input_id)
            
            if execution_input:
                self.logger.info(f"Execution input found: {execution_input_id}")
            else:
                self.logger.warning(f"Execution input not found: {execution_input_id}")
            
            return execution_input
            
        except Exception as e:
            context = self._create_error_context("get_execution_input_by_id", execution_input_id=execution_input_id)
            self.logger.error(f"Failed to get execution input '{execution_input_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution input '{execution_input_id}': {str(e)}", context=context) from e

    @with_session
    def get_all_execution_inputs(self, session, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get all execution inputs with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionInput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting all execution inputs (skip={skip}, limit={limit})")
            
            execution_inputs = self.execution_input_crud.get_all_execution_inputs(session, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_inputs)} execution inputs")
            return execution_inputs
            
        except Exception as e:
            context = self._create_error_context("get_all_execution_inputs", skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution inputs: {str(e)}")
            raise OrchestrationError(f"Failed to get execution inputs: {str(e)}", context=context) from e

    @with_session
    def get_execution_inputs_by_execution(self, session, execution_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by execution ID
        
        Args:
            execution_id: ID of the execution
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionInput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution inputs for execution: {execution_id} (skip={skip}, limit={limit})")
            
            execution_inputs = self.execution_input_crud.get_execution_inputs_by_execution(session, execution_id, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_inputs)} execution inputs for execution {execution_id}")
            return execution_inputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_inputs_by_execution", execution_id=execution_id, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution inputs for execution '{execution_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution inputs for execution '{execution_id}': {str(e)}", context=context) from e

    @with_session
    def get_execution_inputs_by_node(self, session, node_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by node ID
        
        Args:
            node_id: ID of the node
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionInput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution inputs for node: {node_id} (skip={skip}, limit={limit})")
            
            execution_inputs = self.execution_input_crud.get_execution_inputs_by_node(session, node_id, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_inputs)} execution inputs for node {node_id}")
            return execution_inputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_inputs_by_node", node_id=node_id, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution inputs for node '{node_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution inputs for node '{node_id}': {str(e)}", context=context) from e

    @with_session
    def get_execution_inputs_by_workflow(self, session, workflow_id: str, skip: int = 0, limit: int = 100) -> List[ExecutionInput]:
        """
        Get execution inputs by workflow ID
        
        Args:
            workflow_id: ID of the workflow
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionInput instances
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            self.logger.info(f"Getting execution inputs for workflow: {workflow_id} (skip={skip}, limit={limit})")
            
            execution_inputs = self.execution_input_crud.get_execution_inputs_by_workflow(session, workflow_id, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_inputs)} execution inputs for workflow {workflow_id}")
            return execution_inputs
            
        except Exception as e:
            context = self._create_error_context("get_execution_inputs_by_workflow", workflow_id=workflow_id, skip=skip, limit=limit)
            self.logger.error(f"Failed to get execution inputs for workflow '{workflow_id}': {str(e)}")
            raise OrchestrationError(f"Failed to get execution inputs for workflow '{workflow_id}': {str(e)}", context=context) from e

    @with_session
    def filter_execution_inputs(
        self, 
        session,
        execution_id: Optional[str] = None, 
        workflow_id: Optional[str] = None, 
        node_id: Optional[str] = None, 
        priority: Optional[int] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ExecutionInput]:
        """
        Get execution inputs with flexible filtering
        
        Args:
            execution_id: Optional execution ID filter
            workflow_id: Optional workflow ID filter
            node_id: Optional node ID filter
            priority: Optional priority filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            session: Database session (injected by decorator)
            
        Returns:
            List of ExecutionInput instances matching filters
            
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
            if priority is not None:
                filters.append(f"priority={priority}")
            filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
            
            self.logger.info(f"Filtering execution inputs{filter_desc} (skip={skip}, limit={limit})")
            
            # Apply filters in priority order
            if execution_id:
                execution_inputs = self.execution_input_crud.get_execution_inputs_by_execution(session, execution_id, skip=skip, limit=limit)
            elif workflow_id:
                execution_inputs = self.execution_input_crud.get_execution_inputs_by_workflow(session, workflow_id, skip=skip, limit=limit)
            elif node_id:
                execution_inputs = self.execution_input_crud.get_execution_inputs_by_node(session, node_id, skip=skip, limit=limit)
            elif priority is not None:
                execution_inputs = self.execution_input_crud.get_execution_inputs_by_priority(session, priority, skip=skip, limit=limit)
            else:
                execution_inputs = self.execution_input_crud.get_all_execution_inputs(session, skip=skip, limit=limit)
            
            self.logger.info(f"Retrieved {len(execution_inputs)} execution inputs{filter_desc}")
            return execution_inputs
            
        except Exception as e:
            context = self._create_error_context("filter_execution_inputs", execution_id=execution_id, workflow_id=workflow_id, node_id=node_id, priority=priority, skip=skip, limit=limit)
            self.logger.error(f"Failed to filter execution inputs: {str(e)}")
            raise OrchestrationError(f"Failed to filter execution inputs: {str(e)}", context=context) from e

    @with_session
    def count_execution_inputs(
        self, 
        session,
        execution_id: Optional[str] = None, 
        workflow_id: Optional[str] = None, 
        node_id: Optional[str] = None
    ) -> int:
        """
        Count execution inputs with optional filtering
        
        Args:
            execution_id: Optional execution ID filter
            workflow_id: Optional workflow ID filter
            node_id: Optional node ID filter
            session: Database session (injected by decorator)
            
        Returns:
            Number of execution inputs matching filters
            
        Raises:
            OrchestrationError: If operation fails
        """
        try:
            # Apply filters for counting
            if execution_id:
                count = self.execution_input_crud.count_execution_inputs_by_execution(session, execution_id)
            elif workflow_id:
                count = self.execution_input_crud.count_execution_inputs_by_workflow(session, workflow_id)
            elif node_id:
                count = self.execution_input_crud.count_execution_inputs_by_node(session, node_id)
            else:
                count = self.execution_input_crud.count_execution_inputs(session)
            
            self.logger.info(f"Counted {count} execution inputs")
            return count
            
        except Exception as e:
            context = self._create_error_context("count_execution_inputs", execution_id=execution_id, workflow_id=workflow_id, node_id=node_id)
            self.logger.error(f"Failed to count execution inputs: {str(e)}")
            raise OrchestrationError(f"Failed to count execution inputs: {str(e)}", context=context) from e
