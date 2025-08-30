from .config import ErrorContext, ErrorSeverity, ErrorCode, ERROR_CODE_TO_STATUS
from .base_exception import MiniflowException, create_miniflow_exception

# Additional exception classes for backward compatibility and testing
# General errors
class UnknownError(MiniflowException):
    """Exception raised for unknown errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.UNKNOWN_ERROR, **kwargs)

class InternalError(MiniflowException):
    """Exception raised for internal errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.INTERNAL_ERROR, **kwargs)

class ConfigurationError(MiniflowException):
    """Exception raised for configuration errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONFIGURATION_ERROR, **kwargs)


# Validation errors
class ValidationError(MiniflowException):
    """Exception raised for validation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.VALIDATION_ERROR, **kwargs)

class InvalidInput(MiniflowException):
    """Exception raised for invalid input errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.INVALID_INPUT, **kwargs)

class MissingRequiredField(MiniflowException):
    """Exception raised for missing required field errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.MISSING_REQUIRED_FIELD, **kwargs)

class InvalidFormat(MiniflowException):
    """Exception raised for invalid format errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.INVALID_FORMAT, **kwargs)


# Business logic errors
class BusinessLogicError(MiniflowException):
    """Exception raised for business logic errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.BUSINESS_LOGIC_ERROR, **kwargs)

class InvalidState(MiniflowException):
    """Exception raised for invalid state errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.INVALID_STATE, **kwargs)

class OperationNotAllowed(MiniflowException):
    """Exception raised for operation not allowed errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.OPERATION_NOT_ALLOWED, **kwargs)

class ResourceConflict(MiniflowException):
    """Exception raised for resource conflict errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.RESOURCE_CONFLICT, **kwargs)


# Resource errors
class ResourceNotFound(MiniflowException):
    """Exception raised for resource not found errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.RESOURCE_NOT_FOUND, **kwargs)

class ResourceAccessDenied(MiniflowException):
    """Exception raised for resource access denied errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.RESOURCE_ACCESS_DENIED, **kwargs)

class ResourceUnavailable(MiniflowException):
    """Exception raised for resource unavailable errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.RESOURCE_UNAVAILABLE, **kwargs)


# Database errors
class DatabaseError(MiniflowException):
    """Exception raised for database errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_ERROR, **kwargs)

class DatabaseConnectionError(MiniflowException):
    """Exception raised for database connection errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_CONNECTION_ERROR, **kwargs)

class DatabaseQueryError(MiniflowException):
    """Exception raised for database query errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_QUERY_ERROR, **kwargs)

class DatabaseTransactionError(MiniflowException):
    """Exception raised for database transaction errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_TRANSACTION_ERROR, **kwargs)


# Network errors
class NetworkError(MiniflowException):
    """Exception raised for network errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.NETWORK_ERROR, **kwargs)

class ConnectionError(MiniflowException):
    """Exception raised for connection errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONNECTION_ERROR, **kwargs)

class TimeoutError(MiniflowException):
    """Exception raised for timeout errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.TIMEOUT_ERROR, **kwargs)


# External service errors
class ExternalServiceError(MiniflowException):
    """Exception raised for external service errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.EXTERNAL_SERVICE_ERROR, **kwargs)

class ServiceUnavailable(MiniflowException):
    """Exception raised for service unavailable errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SERVICE_UNAVAILABLE, **kwargs)

class ServiceTimeout(MiniflowException):
    """Exception raised for service timeout errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SERVICE_TIMEOUT, **kwargs)


# Application errors
class WorkflowError(MiniflowException):
    """Exception raised for workflow errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.WORKFLOW_ERROR, **kwargs)

class SchedulerError(MiniflowException):
    """Exception raised for scheduler errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SCHEDULER_ERROR, **kwargs)

class EngineError(MiniflowException):
    """Exception raised for engine errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.ENGINE_ERROR, **kwargs)

class OrchestrationError(MiniflowException):
    """Exception raised for orchestration errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.ORCHESTRATION_ERROR, **kwargs)


# Error management functions
def create_error_response(error: Exception) -> dict:
    """Create a standardized error response"""
    if hasattr(error, 'get_error_info'):
        return error.get_error_info()
    else:
        return {
            "error_code": ErrorCode.UNKNOWN_ERROR.value,
            "message": str(error),
            "exception_type": type(error).__name__
        }

def handle_unexpected_error(error: Exception) -> dict:
    """Handle unexpected errors and create a response"""
    return create_error_response(error)


# Define __all__ to specify what should be exported from this module
__all__ = [
    # Base classes and utilities from imported modules
    'ErrorContext',
    'ErrorSeverity', 
    'ErrorCode',
    'ERROR_CODE_TO_STATUS',
    'MiniflowException',
    'create_miniflow_exception',
    
    # General errors
    'UnknownError',
    'InternalError',
    'ConfigurationError',
    
    # Validation errors
    'ValidationError',
    'InvalidInput',
    'MissingRequiredField',
    'InvalidFormat',
    
    # Business logic errors
    'BusinessLogicError',
    'InvalidState',
    'OperationNotAllowed',
    'ResourceConflict',
    
    # Resource errors
    'ResourceNotFound',
    'ResourceAccessDenied',
    'ResourceUnavailable',
    
    # Database errors
    'DatabaseError',
    'DatabaseConnectionError',
    'DatabaseQueryError',
    'DatabaseTransactionError',
    
    # Network errors
    'NetworkError',
    'ConnectionError',
    'TimeoutError',
    
    # External service errors
    'ExternalServiceError',
    'ServiceUnavailable',
    'ServiceTimeout',
    
    # Application errors
    'WorkflowError',
    'SchedulerError',
    'EngineError',
    'OrchestrationError',
    
    # Error management functions
    'create_error_response',
    'handle_unexpected_error',
]


