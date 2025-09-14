from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FileUploadCreateRequest(BaseModel):
    """File upload create request"""
    is_temporary: Optional[bool] = Field(True, description="Whether file is temporary (default: True)")

    def to_dict(self):
        return {
            'is_temporary': self.is_temporary
        }


class FileUploadFilterRequest(BaseModel):
    """File upload filter request"""
    filters: Dict[str, Any] = Field(..., description="Filter criteria")
    skip: int = Field(0, ge=0, description="Number of records to skip for pagination")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    order_by_field: Optional[str] = Field(None, description="Field to order by")
    include_relationships: bool = Field(False, description="Include related objects")
    exclude_fields: Optional[List[str]] = Field(None, description="Fields to exclude from response")

    def to_dict(self):
        return {
            'filters': self.filters,
            'skip': self.skip,
            'limit': self.limit,
            'order_by_field': self.order_by_field,
            'include_relationships': self.include_relationships,
            'exclude_fields': self.exclude_fields
        }


class FileUploadResponse(BaseModel):
    """File upload response data"""
    id: str = Field(description="File upload unique identifier")
    name: str = Field(description="Full file name with extension")
    filename: str = Field(description="Base filename without extension")
    file_extension: Optional[str] = Field(description="File extension")
    file_path: str = Field(description="Absolute path to file")
    file_size: int = Field(description="File size in bytes")
    mime_type: Optional[str] = Field(description="MIME type")
    checksum: Optional[str] = Field(description="File checksum")
    is_temporary: bool = Field(description="Whether file is temporary")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class FileUploadListResponse(BaseModel):
    """File upload list response"""
    items: List[FileUploadResponse] = Field(description="List of file uploads")
    total: int = Field(description="Total number of file uploads")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class FileUploadOperationResponse(BaseModel):
    """File upload action response"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of file upload")
    message: str = Field(description="Action result message")
    file_operations: Dict[str, Any] = Field(description="File operation details", default_factory=dict)


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")
