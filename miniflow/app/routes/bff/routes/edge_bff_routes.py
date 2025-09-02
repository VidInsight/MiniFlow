"""
Edge BFF Routes

FastAPI endpoints for Edge operations in the BFF layer.
Provides Edge CRUD with enhanced data including relationships.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from miniflow.app.routes.bff.schemas.edge_bff_schemas import (
    EdgeCreateRequest,
    EdgeUpdateRequest,
    EdgeResponse,
    EdgeDeleteResponse
)
from miniflow.app.routes.bff.actions.edge_bff_actions import EdgeActions
from miniflow.app.core.dependencies import get_database_orchestrator, get_current_correlation_id
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError
from miniflow.core.logger import get_logger


# Router setup
router = APIRouter()
logger = get_logger("edge_bff_routes")


def get_edge_actions(
    database_orchestrator: DatabaseOrchestrator = Depends(get_database_orchestrator)
) -> EdgeActions:
    """Local dependency to get Edge actions instance"""
    return EdgeActions(database_orchestrator)


@router.post("/", response_model=EdgeResponse, status_code=201)
async def create_edge(
    request: EdgeCreateRequest,
    edge_actions: EdgeActions = Depends(get_edge_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Create a new edge
    
    Creates a new edge record connecting two nodes.
    Returns the created edge with all related data (workflow, nodes).
    """
    try:
        logger.info(f"[{correlation_id}] Creating edge from '{request.from_node_id}' to '{request.to_node_id}' in workflow '{request.workflow_id}'")
        
        # Create edge
        result = await edge_actions.create_edge(
            workflow_id=request.workflow_id,
            from_node_id=request.from_node_id,
            to_node_id=request.to_node_id,
            condition_type=request.condition_type
        )
        
        logger.info(f"[{correlation_id}] Edge created successfully: {result['id']}")
        return result
        
    except ValidationError as e:
        logger.error(f"[{correlation_id}] Validation error creating edge: {str(e)}")
        raise HTTPException(status_code=400, detail=f"[VALIDATION_ERROR] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error creating edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error creating edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to create edge: {str(e)}")


@router.get("/", response_model=List[EdgeResponse])
async def list_edges(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    direction: str = Query("both", description="Edge direction for node filter: incoming, outgoing, both"),
    edge_actions: EdgeActions = Depends(get_edge_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    List all edges with optional filtering
    
    Returns a list of all edges. Can be filtered by workflow_id and/or node_id.
    Each edge includes full related data (workflow, nodes).
    """
    try:
        filter_info = []
        if workflow_id:
            filter_info.append(f"workflow {workflow_id}")
        if node_id:
            filter_info.append(f"node {node_id} ({direction})")
        
        filter_str = f" for {', '.join(filter_info)}" if filter_info else ""
        logger.info(f"[{correlation_id}] Listing edges{filter_str}")
        
        # Get edges
        results = await edge_actions.get_edge_records(
            workflow_id=workflow_id,
            node_id=node_id,
            direction=direction
        )
        
        logger.info(f"[{correlation_id}] Retrieved {len(results)} edges")
        return results
        
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error listing edges: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error listing edges: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to list edges: {str(e)}")


@router.get("/{edge_id}", response_model=EdgeResponse)
async def get_edge(
    edge_id: str,
    edge_actions: EdgeActions = Depends(get_edge_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Get a specific edge by ID
    
    Returns detailed edge information including all related data
    (workflow, from_node, to_node).
    """
    try:
        logger.info(f"[{correlation_id}] Getting edge: {edge_id}")
        
        # Get edge
        result = await edge_actions.get_edge_record(edge_id)
        
        logger.info(f"[{correlation_id}] Edge retrieved successfully: {edge_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Edge not found: {edge_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error getting edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error getting edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to get edge: {str(e)}")


@router.put("/{edge_id}", response_model=EdgeResponse)
async def update_edge(
    edge_id: str,
    request: EdgeUpdateRequest,
    edge_actions: EdgeActions = Depends(get_edge_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Update an edge by ID
    
    Updates the specified edge with the provided data.
    Returns the updated edge with all related information.
    """
    try:
        logger.info(f"[{correlation_id}] Updating edge: {edge_id}")
        
        # Prepare update data
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        
        # Update edge
        result = await edge_actions.update_edge(edge_id, **update_data)
        
        logger.info(f"[{correlation_id}] Edge updated successfully: {edge_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Edge not found for update: {edge_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except ValidationError as e:
        logger.error(f"[{correlation_id}] Validation error updating edge: {str(e)}")
        raise HTTPException(status_code=400, detail=f"[VALIDATION_ERROR] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error updating edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error updating edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to update edge: {str(e)}")


@router.delete("/{edge_id}", response_model=EdgeDeleteResponse)
async def delete_edge(
    edge_id: str,
    edge_actions: EdgeActions = Depends(get_edge_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Delete an edge by ID
    
    Deletes the specified edge.
    Returns detailed information about the deletion process.
    """
    try:
        logger.info(f"[{correlation_id}] Deleting edge: {edge_id}")
        
        # Delete edge
        result = await edge_actions.delete_edge(edge_id)
        
        logger.info(f"[{correlation_id}] Edge deleted successfully: {edge_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Edge not found for deletion: {edge_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error deleting edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error deleting edge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to delete edge: {str(e)}")
