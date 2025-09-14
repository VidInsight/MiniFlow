"""Execution Input Routes (Read-Only)"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_execution_input_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import ExecutionInputOperations
from .schemas import ExecutionInputFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="count_execution_inputs")
async def count_execution_inputs(operations: ExecutionInputOperations = Depends(get_execution_input_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_execution_input_records()
    return APIResponse(data={"count": result}, correlation_id=correlation_id)

@router.get("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="list_execution_inputs")
async def list_execution_inputs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: ExecutionInputOperations = Depends(get_execution_input_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_execution_input_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Retrieved successfully", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{execution_input_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_execution_input")
async def get_execution_input(execution_input_id: str, include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: ExecutionInputOperations = Depends(get_execution_input_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.get_execution_input_record(execution_input_id, include_relationships, exclude_list)
    return APIResponse(data=result, message="Retrieved successfully", correlation_id=correlation_id)

@router.post("/filter", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="filter_execution_inputs")
async def filter_execution_inputs(request: ExecutionInputFilterRequest, operations: ExecutionInputOperations = Depends(get_execution_input_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_execution_input_records(request)
    return APIResponse(data=result, message="Retrieved successfully", correlation_id=correlation_id)