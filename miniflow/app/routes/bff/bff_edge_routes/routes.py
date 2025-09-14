"""Edge Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_edge_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import EdgeOperations
from .schemas import EdgeCreateRequest, EdgeUpdateRequest, EdgeFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="count_edges")
async def count_edges(operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_edge_records()
    return APIResponse(data={"count": result}, message="Edges count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="filter_edges")
async def filter_edges(request: EdgeFilterRequest, operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_edge_records(request)
    return APIResponse(data=result, message="Edges filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="create_edge")
async def create_edge(request: EdgeCreateRequest, operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.create_edge_record(request)
    return APIResponse(data=result, message="Edge created", correlation_id=correlation_id)

@router.get("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="list_edges")
async def list_edges(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_edge_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Edges retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{edge_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_edge")
async def get_edge(edge_id: str, include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.get_edge_record(edge_id, include_relationships, exclude_list)
    return APIResponse(data=result, message="Edge retrieved", correlation_id=correlation_id)

@router.put("/{edge_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="update_edge")
async def update_edge(edge_id: str, request: EdgeUpdateRequest, operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.update_edge_record(edge_id, request)
    return APIResponse(data=result, message="Edge updated", correlation_id=correlation_id)

@router.delete("/{edge_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="delete_edge")
async def delete_edge(edge_id: str, operations: EdgeOperations = Depends(get_edge_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.delete_edge_record(edge_id)
    return APIResponse(data=result, message="Edge deleted", correlation_id=correlation_id)
