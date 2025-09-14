"""Workflow Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_workflow_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import WorkflowOperations
from .schemas import WorkflowCreateRequest, WorkflowUpdateRequest, WorkflowFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=Dict[str, Any])
@with_api_error_handling(operation="count_workflows")
async def count_workflows(operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_workflow_records()
    return APIResponse(data={"count": result}, message="Workflows count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=Dict[str, Any])
@with_api_error_handling(operation="filter_workflows")
async def filter_workflows(request: WorkflowFilterRequest, operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_workflow_records(request)
    return APIResponse(data=result, message="Workflows filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="create_workflow")
async def create_workflow(request: WorkflowCreateRequest, operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.create_workflow_record(request)
    return APIResponse(data=result, message="Workflow created", correlation_id=correlation_id)

@router.get("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="list_workflows")
async def list_workflows(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_workflow_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Workflows retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{workflow_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="get_workflow")
async def get_workflow(workflow_id: str, operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.get_workflow_record(workflow_id)
    return APIResponse(data=result, message="Workflow retrieved", correlation_id=correlation_id)

@router.put("/{workflow_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="update_workflow")
async def update_workflow(workflow_id: str, request: WorkflowUpdateRequest, operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.update_workflow_record(workflow_id, request)
    return APIResponse(data=result, message="Workflow updated", correlation_id=correlation_id)

@router.delete("/{workflow_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="delete_workflow")
async def delete_workflow(workflow_id: str, operations: WorkflowOperations = Depends(get_workflow_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.delete_workflow_record(workflow_id)
    return APIResponse(data=result, message="Workflow deleted", correlation_id=correlation_id)
