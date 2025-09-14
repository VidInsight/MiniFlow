from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DashboardFilterRequest(BaseModel):
    """Dashboard filter request (READ-ONLY)"""
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


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response (READ-ONLY)"""
    total_workflows: int = Field(description="Total number of workflows")
    active_workflows: int = Field(description="Number of active workflows")
    total_executions: int = Field(description="Total number of executions")
    running_executions: int = Field(description="Number of running executions")
    success_rate: float = Field(description="Overall success rate")


class DashboardListResponse(BaseModel):
    """Dashboard list response (READ-ONLY)"""
    items: List[Dict[str, Any]] = Field(description="List of dashboard items")
    total: int = Field(description="Total number of dashboard items")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")
