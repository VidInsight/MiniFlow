"""Trigger Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Request

from miniflow.app.core.operations_dependencies import get_trigger_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import TriggerOperations
from .schemas import (
    TriggerCreateRequest, TriggerUpdateRequest, TriggerFilterRequest,
    ManualTriggerRequest, WebhookPayloadRequest
)

router = APIRouter()

# ==========================================
# SPECIFIC ROUTES FIRST (before parameterized routes)
# ==========================================

@router.get("/count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="count_triggers")
async def count_triggers(
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get total count of triggers"""
    result = await operations.count_trigger_records()
    return APIResponse(data={"count": result}, message="Triggers count retrieved", correlation_id=correlation_id)


@router.post("/filter", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="filter_triggers")
async def filter_triggers(
    request: TriggerFilterRequest, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Filter triggers based on criteria"""
    result = await operations.filter_trigger_records(request)
    return APIResponse(data=result, message="Triggers filtered", correlation_id=correlation_id)


@router.get("/statistics", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_trigger_statistics")
async def get_trigger_statistics(
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get trigger statistics"""
    result = operations.get_trigger_statistics()
    return APIResponse(data=result, message="Trigger statistics retrieved", correlation_id=correlation_id)


@router.get("/status", response_model=APIResponse[List[Dict[str, Any]]])
@with_api_error_handling(operation="get_all_handlers_status")
async def get_all_handlers_status(
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get status of all trigger handlers"""
    result = operations.get_all_handlers_status()
    return APIResponse(data=result, message="All handlers status retrieved", correlation_id=correlation_id)


@router.get("/metrics", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_trigger_manager_metrics")
async def get_trigger_manager_metrics(
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get trigger manager metrics"""
    result = operations.get_trigger_manager_metrics()
    return APIResponse(data=result, message="Trigger manager metrics retrieved", correlation_id=correlation_id)


# ==========================================
# WEBHOOK-SPECIFIC ROUTES
# ==========================================

@router.get("/webhooks", response_model=APIResponse[List[Dict[str, Any]]])
@with_api_error_handling(operation="get_all_webhooks")
async def get_all_webhooks(
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get all active webhook information"""
    result = operations.get_all_webhooks()
    return APIResponse(data=result, message="All webhooks retrieved", correlation_id=correlation_id)


@router.get("/webhooks/{webhook_id}/info", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_webhook_info")
async def get_webhook_info(
    webhook_id: str,
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get webhook information"""
    result = operations.get_webhook_info(webhook_id)
    if result is None:
        return APIResponse(data=None, message="Webhook not found", correlation_id=correlation_id, success=False)
    return APIResponse(data=result, message="Webhook info retrieved", correlation_id=correlation_id)


@router.post("/webhook/{webhook_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="handle_webhook")
async def handle_webhook(
    webhook_id: str,
    request: Request,
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Handle incoming webhook request"""
    # Get request body as JSON
    payload = await request.json()
    
    # Get headers (excluding some internal ones)
    headers = dict(request.headers)
    
    result = await operations.handle_webhook_request(webhook_id, payload, headers)
    return APIResponse(data=result, message="Webhook processed successfully", correlation_id=correlation_id)


@router.get("/webhooks/{webhook_id}/validate", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="validate_webhook_id")
async def validate_webhook_id(
    webhook_id: str,
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Check if webhook ID is available"""
    result = operations.validate_webhook_id_availability(webhook_id)
    return APIResponse(
        data={"webhook_id": webhook_id, "available": result}, 
        message=f"Webhook ID {'available' if result else 'not available'}", 
        correlation_id=correlation_id
    )


# ==========================================
# TYPE-SPECIFIC ROUTES
# ==========================================

@router.get("/type/{trigger_type}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_triggers_by_type")
async def get_triggers_by_type(
    trigger_type: str,
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get triggers by type"""
    result = await operations.get_triggers_by_type(trigger_type, skip, limit)
    return APIResponse(data=result, message=f"Triggers of type {trigger_type} retrieved", correlation_id=correlation_id)


# ==========================================
# WORKFLOW-SPECIFIC ROUTES
# ==========================================

@router.get("/workflow/{workflow_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_workflow_triggers")
async def get_workflow_triggers(
    workflow_id: str,
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get all triggers for a workflow"""
    result = await operations.get_workflow_triggers(workflow_id, skip, limit)
    return APIResponse(data=result, message=f"Triggers for workflow {workflow_id} retrieved", correlation_id=correlation_id)


@router.get("/workflow/{workflow_id}/count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_workflow_triggers_count")
async def get_workflow_triggers_count(
    workflow_id: str,
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get trigger count for workflow"""
    result = await operations.get_workflow_triggers_count(workflow_id)
    return APIResponse(data={"count": result}, message=f"Trigger count for workflow {workflow_id} retrieved", correlation_id=correlation_id)


@router.get("/workflow/{workflow_id}/active-count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_workflow_active_triggers_count")
async def get_workflow_active_triggers_count(
    workflow_id: str,
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get active trigger count for workflow"""
    result = await operations.get_workflow_active_triggers_count(workflow_id)
    return APIResponse(data={"count": result}, message=f"Active trigger count for workflow {workflow_id} retrieved", correlation_id=correlation_id)


# ==========================================
# GENERAL CRUD ROUTES
# ==========================================

@router.post("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="create_trigger")
async def create_trigger(
    request: TriggerCreateRequest, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Create new trigger"""
    result = await operations.create_trigger_record(request)
    return APIResponse(data=result, message="Trigger created", correlation_id=correlation_id)


@router.get("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="list_triggers")
async def list_triggers(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000), 
    order_by: Optional[str] = Query(None), 
    include_relationships: bool = Query(False), 
    exclude_fields: Optional[str] = Query(None), 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """List all triggers"""
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_trigger_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Triggers retrieved", correlation_id=correlation_id)


# ==========================================
# PARAMETERIZED ROUTES LAST
# ==========================================

@router.get("/{trigger_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_trigger")
async def get_trigger(
    trigger_id: str, 
    include_relationships: bool = Query(False), 
    exclude_fields: Optional[str] = Query(None), 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get trigger by ID"""
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.get_trigger_record(trigger_id, include_relationships, exclude_list)
    if result is None:
        return APIResponse(data=None, message="Trigger not found", correlation_id=correlation_id, success=False)
    return APIResponse(data=result, message="Trigger retrieved", correlation_id=correlation_id)


@router.put("/{trigger_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="update_trigger")
async def update_trigger(
    trigger_id: str, 
    request: TriggerUpdateRequest, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Update trigger"""
    result = await operations.update_trigger_record(trigger_id, request)
    return APIResponse(data=result, message="Trigger updated", correlation_id=correlation_id)


@router.delete("/{trigger_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="delete_trigger")
async def delete_trigger(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Delete trigger"""
    result = await operations.delete_trigger_record(trigger_id)
    return APIResponse(data=result, message="Trigger deleted", correlation_id=correlation_id)


# ==========================================
# TRIGGER MANAGEMENT ROUTES
# ==========================================

@router.post("/{trigger_id}/toggle", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="toggle_trigger_status")
async def toggle_trigger_status(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Toggle trigger status (ACTIVE ↔ INACTIVE)"""
    result = await operations.toggle_trigger_status(trigger_id)
    return APIResponse(data=result, message="Trigger status toggled", correlation_id=correlation_id)


@router.post("/{trigger_id}/activate", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="activate_trigger")
async def activate_trigger(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Activate trigger"""
    result = await operations.activate_trigger(trigger_id)
    return APIResponse(data=result, message="Trigger activated", correlation_id=correlation_id)


@router.post("/{trigger_id}/deactivate", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="deactivate_trigger")
async def deactivate_trigger(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Deactivate trigger"""
    result = await operations.deactivate_trigger(trigger_id)
    return APIResponse(data=result, message="Trigger deactivated", correlation_id=correlation_id)


@router.post("/{trigger_id}/reload", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="reload_trigger")
async def reload_trigger(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Reload trigger in manager"""
    result = await operations.reload_trigger(trigger_id)
    return APIResponse(data=result, message="Trigger reloaded", correlation_id=correlation_id)


@router.get("/{trigger_id}/status", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_trigger_handler_status")
async def get_trigger_handler_status(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get trigger handler status"""
    result = operations.get_trigger_handler_status(trigger_id)
    if result is None:
        return APIResponse(data=None, message="Trigger handler not found", correlation_id=correlation_id, success=False)
    return APIResponse(data=result, message="Trigger handler status retrieved", correlation_id=correlation_id)


@router.get("/{trigger_id}/schedule-info", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_schedule_info")
async def get_schedule_info(
    trigger_id: str, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Get schedule information for scheduled trigger"""
    result = operations.get_schedule_info(trigger_id)
    if result is None:
        return APIResponse(data=None, message="Schedule info not available", correlation_id=correlation_id, success=False)
    return APIResponse(data=result, message="Schedule info retrieved", correlation_id=correlation_id)


# ==========================================
# TRIGGER EXECUTION ROUTES
# ==========================================

@router.post("/{trigger_id}/execute", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="execute_manual_trigger")
async def execute_manual_trigger(
    trigger_id: str, 
    request: ManualTriggerRequest, 
    operations: TriggerOperations = Depends(get_trigger_operations), 
    correlation_id: str = Depends(get_current_correlation_id)
):
    """Execute manual trigger"""
    result = await operations.execute_manual_trigger(trigger_id, request)
    return APIResponse(data=result, message="Manual trigger executed", correlation_id=correlation_id)
