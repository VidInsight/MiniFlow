from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from miniflow.database.models import TriggerType, TriggerStatus
import re


class TriggerCreateRequest(BaseModel):
    """Trigger create request model"""
    # REQUIRED fields
    workflow_id: str = Field(..., min_length=1, max_length=20, description="Workflow ID to trigger")
    name: str = Field(..., min_length=1, max_length=100, description="Trigger name (unique within workflow)")
    trigger_type: TriggerType = Field(..., description="Type of trigger (MANUAL, WEBHOOK, SCHEDULED)")
    
    # OPTIONAL fields
    description: Optional[str] = Field(None, max_length=1000, description="Trigger description")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Trigger configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping configuration")
    status: Optional[TriggerStatus] = Field(TriggerStatus.ACTIVE, description="Trigger status")

    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'trigger_type': self.trigger_type,
            'description': self.description,
            'config': self.config,
            'input_mapping': self.input_mapping,
            'status': self.status
        }


class TriggerUpdateRequest(BaseModel):
    """Trigger update request model (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Trigger name")
    description: Optional[str] = Field(None, max_length=1000, description="Trigger description")
    config: Optional[Dict[str, Any]] = Field(None, description="Trigger configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping configuration")
    status: Optional[TriggerStatus] = Field(None, description="Trigger status")

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'config': self.config,
            'input_mapping': self.input_mapping,
            'status': self.status
        }


class TriggerFilterRequest(BaseModel):
    """Trigger filter request model"""
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


class ManualTriggerRequest(BaseModel):
    """Manual trigger execution request"""
    input_data: Optional[Dict[str, Any]] = Field(None, description="Optional input data for manual trigger")


class WebhookPayloadRequest(BaseModel):
    """Webhook payload model"""
    # Dynamic payload - any structure is allowed
    class Config:
        extra = "allow"  # Allow additional fields


class TriggerResponse(BaseModel):
    """Trigger response model"""
    # BaseModel fields
    id: str = Field(description="Trigger unique identifier (TR-XXXXXXXXXXXXX)")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    updated_at: str = Field(description="Last update timestamp (ISO format)")
    
    # Trigger model fields
    workflow_id: str = Field(description="Associated workflow ID")
    name: str = Field(description="Trigger name")
    description: Optional[str] = Field(None, description="Trigger description")
    trigger_type: TriggerType = Field(description="Trigger type")
    status: TriggerStatus = Field(description="Trigger status")
    config: Dict[str, Any] = Field(description="Trigger configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping configuration")
    
    # Computed properties
    webhook_endpoint: Optional[str] = Field(None, description="Webhook endpoint (if webhook trigger)")
    is_active: bool = Field(description="Whether trigger is active")


class TriggerListResponse(BaseModel):
    """Trigger list response model"""
    items: List[TriggerResponse] = Field(description="List of triggers")
    total: int = Field(description="Total number of triggers")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum number of records requested")


class TriggerOperationResponse(BaseModel):
    """Trigger operation response model"""
    action_status: bool = Field(description="Whether action was successful")
    record_id: str = Field(description="ID of trigger")
    message: str = Field(description="Action result message")


class TriggerExecutionResponse(BaseModel):
    """Trigger execution response model"""
    trigger_id: str = Field(description="Trigger ID that was executed")
    workflow_id: str = Field(description="Workflow ID that was triggered")
    execution_id: str = Field(description="Generated execution ID")
    execution_status: str = Field(description="Execution status")
    trigger_type: str = Field(description="Type of trigger")
    triggered_at: str = Field(description="Timestamp when trigger was executed")
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Processed trigger data")


class WebhookInfoResponse(BaseModel):
    """Webhook information response"""
    webhook_id: str = Field(description="Webhook ID")
    endpoint: str = Field(description="Webhook endpoint URL")
    content_type: str = Field(description="Expected content type")
    signature_validation: bool = Field(description="Whether signature validation is enabled")
    secret_configured: bool = Field(description="Whether secret is configured")
    trigger_name: str = Field(description="Trigger name")
    workflow_id: str = Field(description="Associated workflow ID")


class TriggerStatsResponse(BaseModel):
    """Trigger statistics response"""
    total_triggers: int = Field(description="Total number of triggers")
    by_status: Dict[str, int] = Field(description="Triggers count by status")
    by_type: Dict[str, int] = Field(description="Active triggers count by type")


class TriggerStatusResponse(BaseModel):
    """Trigger handler status response"""
    trigger_id: str = Field(description="Trigger ID")
    trigger_name: str = Field(description="Trigger name")
    trigger_type: str = Field(description="Trigger type")
    workflow_id: str = Field(description="Associated workflow ID")
    is_running: bool = Field(description="Whether handler is running")
    config: Dict[str, Any] = Field(description="Trigger configuration")


class ScheduleInfoResponse(BaseModel):
    """Schedule information response for scheduled triggers"""
    trigger_type: str = Field(description="Should be 'SCHEDULED'")
    cron_expression: Optional[str] = Field(None, description="Cron expression if used")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds if used")
    timezone: str = Field(description="Timezone for scheduling")
    next_execution_time: Optional[str] = Field(None, description="Next scheduled execution time")
    is_running: bool = Field(description="Whether scheduler is running")
