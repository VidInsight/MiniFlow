from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutionInputFilterRequest(BaseModel):
    """Execution input filter request (READ-ONLY)"""
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


class ExecutionInputResponse(BaseModel):
    """Execution input response data (READ-ONLY)"""
    id: str = Field(description="Execution input unique identifier")
    execution_id: str = Field(description="Execution ID")
    workflow_id: str = Field(description="Workflow ID")
    node_id: str = Field(description="Node ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")

    priority: int = Field(description="Execution priority")
    dependency_count: int = Field(description="Number of dependencies")
    wait_factor: int = Field(description="Wait factor for scheduling")
    
    node_name: str = Field(description="Node name")
    script_name: str = Field(description="Script name")
    script_path: Optional[str] = Field(None, description="Script path")
    node_params: Dict[str, Any] = Field(description="Node parameters")

    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class ExecutionInputListResponse(BaseModel):
    """Execution input list response (READ-ONLY)"""
    items: List[ExecutionInputResponse] = Field(description="List of execution inputs")
    total: int = Field(description="Total number of execution inputs")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")
