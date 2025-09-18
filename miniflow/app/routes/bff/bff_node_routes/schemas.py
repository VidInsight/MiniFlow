from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NodeCreateRequest(BaseModel):
    """Create new node request"""
    workflow_id: str = Field(..., description="ID of the workflow this node belongs to")
    name: str = Field(..., description="Name of the node")
    description: Optional[str] = Field(None, description="Description of the node")
    script_id: str = Field(None, description="ID of the script to execute")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata parameters")
    max_retries: Optional[int] = Field(3, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(300, description="Timeout in seconds")

    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'script_id': self.script_id,
            'meta_data': self.meta_data,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds
        }


class NodeUpdateRequest(BaseModel):
    """Update node request"""
    name: Optional[str] = Field(None, description="Name of the node")
    description: Optional[str] = Field(None, description="Description of the node")
    script_id: Optional[str] = Field(None, description="ID of the script to execute")
    input_params: Optional[Dict[str, Any]] = Field(None, description="Node parameters")
    output_params: Optional[Dict[str, Any]] = Field(None, description="Node parameters")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata parameters")
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in seconds")

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'script_id': self.script_id,
            'meta_data': self.meta_data,
            'input_params': self.input_params,
            'output_params': self.output_params,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds
        }


class NodeFilterRequest(BaseModel):
    """Node filter request"""
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


class NodeResponse(BaseModel):
    """Node response data"""
    id: str = Field(description="Node unique identifier")
    workflow_id: str = Field(description="Workflow ID")
    script_id: Optional[str] = Field(description="Script ID")
    name: str = Field(description="Node name")
    description: Optional[str] = Field(description="Node description")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata parameters")
    params: Dict[str, Any] = Field(description="Node parameters")
    max_retries: int = Field(description="Maximum retry attempts")
    timeout_seconds: int = Field(description="Timeout in seconds")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class NodeListResponse(BaseModel):
    """Node list response"""
    items: List[NodeResponse] = Field(description="List of nodes")
    total: int = Field(description="Total number of nodes")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class NodeOperationResponse(BaseModel):
    """Node action response"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of node")
    message: str = Field(description="Action result message")


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")
