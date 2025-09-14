"""Environment Variable Routes - Clean Syntax"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_envar_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import EnvironmentVariableOperations
from .schemas import EnvironmentVariableCreateRequest, EnvironmentVariableUpdateRequest, EnvironmentVariableFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=Dict[str, Any])
@with_api_error_handling(operation="count_envars")
async def count_envars(operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """Count environment variables"""
    result = await operations.count_envar_records()
    return APIResponse(data={"count": result}, message="Count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=Dict[str, Any])
@with_api_error_handling(operation="filter_envars")
async def filter_envars(request: EnvironmentVariableFilterRequest, operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """Filter environment variables"""
    result = await operations.filter_envar_records(request)
    return APIResponse(data=result, message="Environment variables filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="create_envar")
async def create_envar(request: EnvironmentVariableCreateRequest, operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """Create environment variable"""
    result = await operations.create_envar_record(request)
    return APIResponse(data=result, message="Environment variable created", correlation_id=correlation_id)

@router.get("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="list_envars")
async def list_envars(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """List environment variables"""
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_envar_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Environment variables retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{envar_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="get_envar")
async def get_envar(envar_id: str, operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """Get environment variable by ID"""
    result = await operations.get_envar_record(envar_id)
    return APIResponse(data=result, message="Environment variable retrieved", correlation_id=correlation_id)

@router.put("/{envar_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="update_envar")
async def update_envar(envar_id: str, request: EnvironmentVariableUpdateRequest, operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """Update environment variable"""
    result = await operations.update_envar_record(envar_id, request)
    return APIResponse(data=result, message="Environment variable updated", correlation_id=correlation_id)

@router.delete("/{envar_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="delete_envar")
async def delete_envar(envar_id: str, operations: EnvironmentVariableOperations = Depends(get_envar_operations), correlation_id: str = Depends(get_current_correlation_id)):
    """Delete environment variable"""
    result = await operations.delete_envar_record(envar_id)
    return APIResponse(data=result, message="Environment variable deleted", correlation_id=correlation_id)