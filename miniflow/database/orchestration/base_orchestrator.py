from typing import Dict, Optional
from functools import wraps
from miniflow.database.engine import DatabaseEngine
from miniflow.core.logger import get_logger
from miniflow.core.exceptions import DatabaseQueryError, ErrorContext, ErrorSeverity

# CRUD imports
from ..crud import EnvironmentVariableCRUD
from ..crud import FileUploadCRUD
from ..crud import ScriptCRUD
from ..crud import WorkflowCRUD
from ..crud import NodeCRUD
from ..crud import EdgeCRUD
from ..crud import ExecutionCRUD
from ..crud import ExecutionInputCRUD
from ..crud import ExecutionOutputCRUD


def with_session(func):
    """
    Decorator to automatically handle session management.
    
    This decorator:
    1. Creates a new session using engine.session_context()
    2. Passes the session as the first argument to the CRUD operation
    3. Handles auto-commit (if auto_commit=True)
    4. Handles auto-rollback on exceptions
    5. Ensures session cleanup in finally block
    
    Note: CRUD operations use session.flush() for immediate database operations,
    but actual commit is handled by this decorator's session_context.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.engine.session_context(auto_commit=True) as session:
            # Pass session as first argument to the wrapped function
            return func(self, session, *args, **kwargs)
    return wrapper


class BaseOrchestrator:
    """
    Base orchestrator class providing centralized CRUD management.
    
    Simple library class that holds all CRUD instances.
    Session management is handled automatically through with_session decorator.
    """

    def __init__(self, database_engine: DatabaseEngine):
        """
        Initialize with database engine and CRUD instances.
        
        Args:
            database_engine: DatabaseEngine instance
        """
        self.engine = database_engine
        self.logger = get_logger("orchestrator")
        
        # Initialize CRUD instances
        self.envar_crud = EnvironmentVariableCRUD()
        self.fileupload_crud = FileUploadCRUD()
        self.script_crud = ScriptCRUD()
        self.workflow_crud = WorkflowCRUD()
        self.node_crud = NodeCRUD()
        self.edge_crud = EdgeCRUD()
        self.execution_crud = ExecutionCRUD()
        self.execution_input_crud = ExecutionInputCRUD()
        self.execution_output_crud = ExecutionOutputCRUD()
        
        self.logger.info("BaseOrchestrator initialized")

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking."""
        return ErrorContext(
            operation=operation,
            component=self.__class__.__name__,
            additional_info=kwargs
        )

    def _handle_not_found(self, resource_name: str, identifier: str, operation: str):
        """Standardized not found error handler."""
        context = self._create_error_context(operation, resource_name=resource_name, identifier=identifier)
        raise DatabaseQueryError(f"{resource_name} '{identifier}' not found", context=context, severity=ErrorSeverity.HIGH)