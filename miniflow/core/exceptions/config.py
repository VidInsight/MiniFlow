from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCode(Enum):
    """Standard error codes"""
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Business logic errors
    BUSINESS_LOGIC_ERROR = "BUSINESS_LOGIC_ERROR"
    INVALID_STATE = "INVALID_STATE"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ACCESS_DENIED = "RESOURCE_ACCESS_DENIED"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"

    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_TRANSACTION_ERROR = "DATABASE_TRANSACTION_ERROR"

    # Network errors
    NETWORK_ERROR = "NETWORK_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"

    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SERVICE_TIMEOUT = "SERVICE_TIMEOUT"

    # Application errors
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    ENGINE_ERROR = "ENGINE_ERROR"
    SCHEDULER_ERROR = "SCHEDULER_ERROR"
    ORCHESTRATION_ERROR = "ORCHESTRATION_ERROR"


# Error Code to HTTP Status Code mapping
ERROR_CODE_TO_STATUS = {
    # General errors
    ErrorCode.UNKNOWN_ERROR: 500,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.CONFIGURATION_ERROR: 500,

    # Validation errors
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.MISSING_REQUIRED_FIELD: 400,
    ErrorCode.INVALID_FORMAT: 400,

    # Business logic errors
    ErrorCode.BUSINESS_LOGIC_ERROR: 400,
    ErrorCode.INVALID_STATE: 409,
    ErrorCode.OPERATION_NOT_ALLOWED: 403,
    ErrorCode.RESOURCE_CONFLICT: 409,

    # Resource errors
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.RESOURCE_ACCESS_DENIED: 403,
    ErrorCode.RESOURCE_UNAVAILABLE: 503,

    # Database errors
    ErrorCode.DATABASE_ERROR: 500,
    ErrorCode.DATABASE_CONNECTION_ERROR: 503,
    ErrorCode.DATABASE_QUERY_ERROR: 500,
    ErrorCode.DATABASE_TRANSACTION_ERROR: 500,

    # Network errors
    ErrorCode.NETWORK_ERROR: 503,
    ErrorCode.CONNECTION_ERROR: 503,
    ErrorCode.TIMEOUT_ERROR: 408,

    # External service errors
    ErrorCode.EXTERNAL_SERVICE_ERROR: 502,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.SERVICE_TIMEOUT: 504,

    # Application errors
    ErrorCode.WORKFLOW_ERROR: 500,
    ErrorCode.ENGINE_ERROR: 500,
    ErrorCode.SCHEDULER_ERROR: 500,
    ErrorCode.ORCHESTRATION_ERROR: 500,
}


class ErrorContext:
    """Error context information with memory optimization"""
    __slots__ = ['operation', 'component', 'user_id', 'correlation_id', 'additional_info', 'timestamp', '_dict_cache']

    def __init__(self,
                 operation: Optional[str] = None,
                 component: Optional[str] = None,
                 user_id: Optional[str] = None,
                 correlation_id: Optional[str] = None,
                 additional_info: Optional[Dict[str, Any]] = None
                 ):

        self.operation = operation
        self.component = component
        self.user_id = user_id
        self.correlation_id = correlation_id
        self.additional_info = additional_info or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self._dict_cache: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary with error handling"""
        if self._dict_cache is None:
            try:
                self._dict_cache = {
                    "operation": self.operation,
                    "component": self.component,
                    "user_id": self.user_id,
                    "correlation_id": self.correlation_id,
                    "additional_info": self.additional_info,
                    "timestamp": self.timestamp
                }
            except Exception as e:
                # Fallback in case of serialization issues
                self._dict_cache = {
                    "error": f"Context serialization failed: {str(e)}",
                    "timestamp": self.timestamp
                }
        return self._dict_cache