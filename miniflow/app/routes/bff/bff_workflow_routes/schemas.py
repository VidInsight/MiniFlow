from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from miniflow.database.models import WorkflowStatus


class WorkflowCreateRequest(BaseModel):
    """Workflow create modeli (Frontend için)"""
    # REQUIRED: Core workflow fields
    name: str = Field(..., min_length=1, max_length=100, description="Workflow name (unique)")
    
    # OPTIONAL: Basic metadata
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    priority: Optional[int] = Field(0, ge=0, le=100, description="Workflow priority (0-100)")

    def to_dict(self):
        return {
            'name': self.name,  
            'description': self.description,
            'priority': self.priority
        }


class WorkflowUpdateRequest(BaseModel):
    """Workflow update modeli (All fields optional)"""
    # OPTIONAL: Core workflow fields
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Workflow name")
    description: Optional[str] = Field(None, max_length=1000, description="Workflow description")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Workflow priority (0-100)")
    status: Optional[WorkflowStatus] = Field(None, description="Workflow status")

    def to_dict(self):
        return {
            'name': self.name,  
            'description': self.description,
            'priority': self.priority,
            'status': self.status
        }


class WorkflowFilterRequest(BaseModel):
    """Workflow filter request modeli"""
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


class WorkflowResponse(BaseModel):
    """Workflow response modeli (Workflow.to_dict() yapısına uygun)"""
    # BaseModel alanları
    id: str = Field(description="Workflow unique identifier (WF-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # Workflow model alanları
    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    priority: int = Field(description="Workflow priority (0-100)")
    status: WorkflowStatus = Field(description="Workflow status")
    status_message: Optional[str] = Field(None, description="Status message")


class WorkflowListResponse(BaseModel):
    """Workflow list response modeli"""
    items: List[WorkflowResponse] = Field(description="List of workflows")
    total: int = Field(description="Total number of workflows")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class WorkflowOperationResponse(BaseModel):
    """Workflow action response modeli"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of workflow")
    message: str = Field(description="Action result message")


class CountResponse(BaseModel):
    """Count response modeli"""
    count: int = Field(description="Total count")

class WorkflowStatsResponse(BaseModel):
    total_executions: int = Field(description="Total executions")
    successful_executions: int = Field(description="Successful executions")
    failed_executions: int = Field(description="Failed executions")
    cancelled_executions: int = Field(description="Cancelled executions")
    avg_execution_duration: float = Field(description="Average execution duration")
    min_execution_duration: float = Field(description="Minimum execution duration")
    max_execution_duration: float = Field(description="Maximum execution duration")
    last_executed_at: str = Field(description="Last executed at")
    last_successful_execution_at: str = Field(description="Last successful execution at")
    last_failed_execution_at: str = Field(description="Last failed execution at")