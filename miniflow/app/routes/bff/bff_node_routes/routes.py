"""Node Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query

from miniflow.app.core.operations_dependencies import get_node_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import NodeOperations
from .schemas import NodeCreateRequest, NodeUpdateRequest, NodeFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=Dict[str, Any])
@with_api_error_handling(operation="count_nodes")
async def count_nodes(operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_node_records()
    return APIResponse(data={"count": result}, message="Nodes count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=Dict[str, Any])
@with_api_error_handling(operation="filter_nodes")
async def filter_nodes(request: NodeFilterRequest, operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_node_records(request)
    return APIResponse(data=result, message="Nodes filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="create_node")
async def create_node(request: NodeCreateRequest, operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.create_node_record(request)
    return APIResponse(data=result, message="Node created", correlation_id=correlation_id)

@router.get("/", response_model=Dict[str, Any])
@with_api_error_handling(operation="list_nodes")
async def list_nodes(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_node_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Nodes retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{node_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="get_node")
async def get_node(node_id: str, operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.get_node_record(node_id)
    return APIResponse(data=result, message="Node retrieved", correlation_id=correlation_id)

@router.put("/{node_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="update_node")
async def update_node(node_id: str, request: NodeUpdateRequest, operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.update_node_record(node_id, request)
    return APIResponse(data=result, message="Node updated", correlation_id=correlation_id)

@router.delete("/{node_id}", response_model=Dict[str, Any])
@with_api_error_handling(operation="delete_node")
async def delete_node(node_id: str, operations: NodeOperations = Depends(get_node_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.delete_node_record(node_id)
    return APIResponse(data=result, message="Node deleted", correlation_id=correlation_id)
