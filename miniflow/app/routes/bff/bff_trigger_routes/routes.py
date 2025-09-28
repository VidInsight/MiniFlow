"""Trigger Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_trigger_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import TriggerOperations
from .schemas import TriggerCreateRequest, TriggerUpdateRequest, TriggerFilterRequest, TriggerExecutionRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="count_triggers")
async def count_triggers(operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_trigger_records()
    return APIResponse(data={"count": result}, message="Triggers count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="filter_triggers")
async def filter_triggers(request: TriggerFilterRequest, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_trigger_records(request)
    return APIResponse(data=result, message="Triggers filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="create_trigger")
async def create_trigger(request: TriggerCreateRequest, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.create_trigger_record(request)
    return APIResponse(data=result, message="Trigger created", correlation_id=correlation_id)

@router.get("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="list_triggers")
async def list_triggers(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_trigger_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Triggers retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{trigger_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_trigger")
async def get_trigger(trigger_id: str, include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.get_trigger_record(trigger_id, include_relationships, exclude_list)
    return APIResponse(data=result, message="Trigger retrieved", correlation_id=correlation_id)

@router.put("/{trigger_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="update_trigger")
async def update_trigger(trigger_id: str, request: TriggerUpdateRequest, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.update_trigger_record(trigger_id, request)
    return APIResponse(data=result, message="Trigger updated", correlation_id=correlation_id)

@router.delete("/{trigger_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="delete_trigger")
async def delete_trigger(trigger_id: str, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.delete_trigger_record(trigger_id)
    return APIResponse(data=result, message="Trigger deleted", correlation_id=correlation_id)

# TRIGGER EXECUTION ROUTES

@router.post("/{trigger_id}/execute/api", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="execute_api_trigger")
async def execute_api_trigger(trigger_id: str, request: TriggerExecutionRequest, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.trigger_by_api(trigger_id, request)
    return APIResponse(data=result, message="API trigger executed", correlation_id=correlation_id)

@router.post("/{trigger_id}/execute/webhook", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="execute_webhook_trigger")
async def execute_webhook_trigger(trigger_id: str, request: TriggerExecutionRequest, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.trigger_by_webhook(trigger_id, request)
    return APIResponse(data=result, message="Webhook trigger executed", correlation_id=correlation_id)

@router.post("/{trigger_id}/execute/scheduled", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="execute_scheduled_trigger")
async def execute_scheduled_trigger(trigger_id: str, request: TriggerExecutionRequest, operations: TriggerOperations = Depends(get_trigger_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.trigger_by_scheduled(trigger_id, request)
    return APIResponse(data=result, message="Scheduled trigger executed", correlation_id=correlation_id)
