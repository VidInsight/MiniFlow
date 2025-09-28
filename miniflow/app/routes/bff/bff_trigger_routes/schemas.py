from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from miniflow.database.models import TriggerType


class TriggerCreateRequest(BaseModel):
    """Trigger create modeli (Frontend için)"""
    # REQUIRED: Core trigger fields
    workflow_id: str = Field(..., min_length=1, max_length=20, description="Workflow ID to trigger")
    name: str = Field(..., min_length=1, max_length=100, description="Trigger name (unique within workflow)")
    trigger_type: TriggerType = Field(..., description="Type of trigger")
    
    # OPTIONAL: Basic metadata
    description: Optional[str] = Field(None, max_length=1000, description="Trigger description")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Trigger configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input mapping configuration")

    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'trigger_type': self.trigger_type,
            'description': self.description,
            'config': self.config,
            'input_mapping': self.input_mapping
        }


class TriggerUpdateRequest(BaseModel):
    """Trigger update modeli (All fields optional)"""
    # OPTIONAL: Core trigger fields
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Trigger name")
    description: Optional[str] = Field(None, max_length=1000, description="Trigger description")
    trigger_type: Optional[TriggerType] = Field(None, description="Type of trigger")
    config: Optional[Dict[str, Any]] = Field(None, description="Trigger configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping configuration")

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'trigger_type': self.trigger_type,
            'config': self.config,
            'input_mapping': self.input_mapping
        }


class TriggerFilterRequest(BaseModel):
    """Trigger filter request modeli"""
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


class TriggerResponse(BaseModel):
    """Trigger response modeli (Trigger.to_dict() yapısına uygun)"""
    # BaseModel alanları
    id: str = Field(description="Trigger unique identifier (TR-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # Trigger model alanları
    workflow_id: str = Field(description="Workflow ID")
    name: str = Field(description="Trigger name")
    description: Optional[str] = Field(None, description="Trigger description")
    trigger_type: TriggerType = Field(description="Trigger type")
    config: Dict[str, Any] = Field(description="Trigger configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping configuration")


class TriggerListResponse(BaseModel):
    """Trigger list response modeli"""
    items: List[TriggerResponse] = Field(description="List of triggers")
    total: int = Field(description="Total number of triggers")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class TriggerOperationResponse(BaseModel):
    """Trigger action response modeli"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of trigger")
    message: str = Field(description="Action result message")


class CountResponse(BaseModel):
    """Count response modeli"""
    count: int = Field(description="Total count")


class TriggerExecutionRequest(BaseModel):
    """Trigger execution request modeli"""
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    trigger_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Trigger payload data")

    def to_dict(self):
        return {
            'correlation_id': self.correlation_id,
            'trigger_data': self.trigger_data
        }


class TriggerExecutionResponse(BaseModel):
    """Trigger execution response modeli"""
    execution_id: str = Field(description="Created execution ID")
    workflow_id: str = Field(description="Workflow ID")
    trigger_id: str = Field(description="Trigger ID")
    correlation_id: str = Field(description="Correlation ID")
    nodes_count: int = Field(description="Number of nodes in workflow")
    execution_inputs_count: int = Field(description="Number of execution inputs created")
    status: str = Field(description="Execution status")
    message: str = Field(description="Execution result message")
