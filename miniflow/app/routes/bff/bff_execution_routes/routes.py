"""Execution Routes (Read-Only)"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_execution_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import ExecutionOperations
from .schemas import ExecutionFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=Dict[str, Any])
@with_api_error_handling(operation="count_executions")
async def count_executions(operations: ExecutionOperations = Depends(get_execution_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_execution_records()
    return APIResponse(data={"count": result}, message="Executions count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=Dict[str, Any])
@with_api_error_handling(operation="filter_executions")
async def filter_executions(request: ExecutionFilterRequest, operations: ExecutionOperations = Depends(get_execution_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_execution_records(request)
    return APIResponse(data=result, message="Executions filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.get("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="list_executions")
async def list_executions(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: ExecutionOperations = Depends(get_execution_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_execution_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Executions retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{execution_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="get_execution")
async def get_execution(execution_id: str, operations: ExecutionOperations = Depends(get_execution_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.get_execution_record(execution_id)
    return APIResponse(data=result, message="Execution retrieved", correlation_id=correlation_id)
