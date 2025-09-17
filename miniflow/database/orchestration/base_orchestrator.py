from typing import Dict, Optional, List, Any
from functools import wraps
from miniflow.database.engine import DatabaseEngine
from miniflow.core.logger import get_logger
from miniflow.core.exceptions import DatabaseQueryError, ErrorContext, ErrorSeverity, OrchestrationError

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
from ..crud import TriggerCRUD


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
        self.trigger_crud = TriggerCRUD()
        
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
    
    # ============================
    # Enhanced to_dict Operations
    # ============================
    
    def _serialize_single_result(self, result, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Serialize single result with configurable options."""
        if result is None:
            return None
        return result.to_dict(include_relationships=include_relationships, exclude_fields=exclude_fields)
    
    def _serialize_multiple_results(self, results, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Serialize multiple results with configurable options."""
        return [item.to_dict(include_relationships=include_relationships, exclude_fields=exclude_fields) for item in results]
        
    # ========================
    # Generic CRUD Operations
    # ========================
    
    def _get_primary_crud(self):
        """Get the primary CRUD instance for this orchestrator. Should be overridden in child classes."""
        raise NotImplementedError("Child orchestrators must implement _get_primary_crud method")

    @with_session
    def get_by_id(self, session, record_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Generic get by ID method using the orchestrator's primary CRUD."""
        crud = self._get_primary_crud()
        try:
            result = crud._get_by_id(session, record_id)
            return self._serialize_single_result(result, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_all(self, session, skip: int = 0, limit: int = 100, order_by: str = None, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Generic get all method using the orchestrator's primary CRUD."""
        crud = self._get_primary_crud()
        try:
            results = crud._get_all(session, skip=skip, limit=limit, order_by=order_by)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_all", skip=skip, limit=limit)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def count(self, session) -> int:
        """Generic count method using the orchestrator's primary CRUD."""
        crud = self._get_primary_crud()
        try:
            return crud._count(session)
        except Exception as e:
            context = self._create_error_context("count")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session, record_id: str) -> Dict[str, Any]:
        """Generic delete method using the orchestrator's primary CRUD. 
        Override this method in child orchestrators for custom cascade logic."""
        crud = self._get_primary_crud()
        try:
            result = crud._delete(session, record_id)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("delete", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter(self, session, filters: Dict[str, Any], skip: int = 0, limit: int = 100, order_by_field: str = None, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Generic filter method using the orchestrator's primary CRUD."""
        crud = self._get_primary_crud()
        try:
            results = crud._filter(session, filters=filters, skip=skip, limit=limit, order_by_field=order_by_field)
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("filter", filters=filters, skip=skip, limit=limit)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def count_with_filter(self, session, filters: Dict[str, Any]) -> int:
        """Generic count with filter method using the orchestrator's primary CRUD."""
        crud = self._get_primary_crud()
        try:
            return crud._count_with_filter(session, filters=filters)
        except Exception as e:
            context = self._create_error_context("count_with_filter", filters=filters)
            raise OrchestrationError(str(e), context=context) from e