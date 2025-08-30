from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Standart API response formatı"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None


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