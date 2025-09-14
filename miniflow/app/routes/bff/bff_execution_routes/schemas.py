from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutionFilterRequest(BaseModel):
    """Execution filter request (READ-ONLY)"""
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


class ExecutionResponse(BaseModel):
    """Execution response data (READ-ONLY)"""
    id: str = Field(description="Execution unique identifier")
    workflow_id: str = Field(description="Workflow ID")
    
    status: str = Field(description="Execution status")
    pending_nodes: int = Field(description="Pending nodes count")
    executed_nodes: int = Field(description="Executed nodes count")
    results: Dict[str, Any] = Field(description="Execution results")
    error_details: Dict[str, Any] = Field(description="Detailed error information")
    
    started_at: str = Field(description="Start timestamp")
    ended_at: Optional[str] = Field(None, description="End timestamp")
    
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")

class ExecutionListResponse(BaseModel):
    """Execution list response (READ-ONLY)"""
    items: List[ExecutionResponse] = Field(description="List of executions")
    total: int = Field(description="Total number of executions")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")
