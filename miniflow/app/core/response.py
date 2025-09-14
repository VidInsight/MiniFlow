from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Standart API response formatı"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __init__(self, **data):
        # Auto-add timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)
    
    def dict(self, **kwargs):
        """Pydantic V1 compatibility"""
        return self.model_dump(**kwargs)


class ErrorResponse(BaseModel):
    """Error response formatı"""
    error: bool = True
    message: str
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response formatı"""
    success: bool = True
    data: List[T]
    pagination: Dict[str, Any] = Field(description="Pagination metadata")
    correlation_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "miniflow-api"
    version: str = "1.0.0"
    timestamp: str
    correlation_id: Optional[str] = None


def create_success_response(data: Any, message: str = None, correlation_id: str = None) -> APIResponse:
    """Create standardized success response with timestamp"""
    return APIResponse(
        success=True,
        data=data,
        message=message,
        correlation_id=correlation_id,
        timestamp=datetime.utcnow().isoformat()
    )


def create_error_response(error: str, correlation_id: str = None, error_code: str = None) -> Dict[str, Any]:
    """Create standardized error response with timestamp"""
    return {
        "success": False,
        "error": error,
        "error_code": error_code,
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat()
    }