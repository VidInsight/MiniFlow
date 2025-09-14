from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from miniflow.database.models import ConditionType


class EdgeCreateRequest(BaseModel):
    """Create new edge request"""
    workflow_id: str = Field(..., description="ID of the workflow this edge belongs to")
    from_node_id: str = Field(..., description="ID of the source node")
    to_node_id: str = Field(..., description="ID of the target node")
    condition_type: Optional[ConditionType] = Field(ConditionType.SUCCESS, description="Edge condition type")

    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'from_node_id': self.from_node_id,
            'to_node_id': self.to_node_id,
            'condition_type': self.condition_type
        }


class EdgeUpdateRequest(BaseModel):
    """Update edge request"""
    from_node_id: Optional[str] = Field(None, description="ID of the source node")
    to_node_id: Optional[str] = Field(None, description="ID of the target node")
    condition_type: Optional[ConditionType] = Field(None, description="Edge condition type")

    def to_dict(self):
        return {
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            'condition_type': self.condition_type
        }


class EdgeFilterRequest(BaseModel):
    """Edge filter request"""
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


class EdgeResponse(BaseModel):
    """Edge response data"""
    id: str = Field(description="Edge unique identifier")
    workflow_id: str = Field(description="Workflow ID")
    from_node_id: str = Field(description="Source node ID")
    to_node_id: str = Field(description="Target node ID")
    condition_type: str = Field(description="Edge condition type")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class EdgeListResponse(BaseModel):
    """Edge list response"""
    items: List[EdgeResponse] = Field(description="List of edges")
    total: int = Field(description="Total number of edges")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class EdgeOperationResponse(BaseModel):
    """Edge action response"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of edge")
    message: str = Field(description="Action result message")


class CountResponse(BaseModel):
    """Count response"""
    count: int = Field(description="Total count")
