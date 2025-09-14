"""Script Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_script_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import ScriptOperations
from .schemas import ScriptCreateRequest, ScriptUpdateRequest, ScriptFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=Dict[str, Any])
@with_api_error_handling(operation="count_scripts")
async def count_scripts(operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_script_records()
    return APIResponse(data={"count": result}, message="Scripts count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=Dict[str, Any])
@with_api_error_handling(operation="filter_scripts")
async def filter_scripts(request: ScriptFilterRequest, operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_script_records(request)
    return APIResponse(data=result, message="Scripts filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="create_script")
async def create_script(request: ScriptCreateRequest, operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.create_script_record(request)
    return APIResponse(data=result, message="Script created", correlation_id=correlation_id)

@router.get("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="list_scripts")
async def list_scripts(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_script_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Scripts retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{script_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="get_script")
async def get_script(script_id: str, operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.get_script_record(script_id)
    return APIResponse(data=result, message="Script retrieved", correlation_id=correlation_id)

@router.put("/{script_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="update_script")
async def update_script(script_id: str, request: ScriptUpdateRequest, operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.update_script_record(script_id, request)
    return APIResponse(data=result, message="Script updated", correlation_id=correlation_id)

@router.delete("/{script_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="delete_script")
async def delete_script(script_id: str, operations: ScriptOperations = Depends(get_script_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.delete_script_record(script_id)
    return APIResponse(data=result, message="Script deleted", correlation_id=correlation_id)
