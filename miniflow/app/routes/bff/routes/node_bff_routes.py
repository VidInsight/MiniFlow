"""
Node BFF Routes

FastAPI endpoints for Node operations in the BFF layer.
Provides Node CRUD with enhanced data including relationships.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from miniflow.app.routes.bff.schemas.node_bff_schemas import (
    NodeCreateRequest,
    NodeUpdateRequest,
    NodeResponse,
    NodeDeleteResponse
)
from miniflow.app.routes.bff.actions.node_bff_actions import NodeActions
from miniflow.app.core.dependencies import get_database_orchestrator, get_current_correlation_id
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError
from miniflow.core.logger import get_logger


# Router setup
router = APIRouter()
logger = get_logger("node_bff_routes")


def get_node_actions(
    database_orchestrator: DatabaseOrchestrator = Depends(get_database_orchestrator)
) -> NodeActions:
    """Local dependency to get Node actions instance"""
    return NodeActions(database_orchestrator)


@router.post("/", response_model=NodeResponse, status_code=201)
async def create_node(
    request: NodeCreateRequest,
    node_actions: NodeActions = Depends(get_node_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Create a new node
    
    Creates a new node record with the provided details.
    Returns the created node with all related data (workflow, script, edges).
    """
    try:
        logger.info(f"[{correlation_id}] Creating node '{request.name}' in workflow '{request.workflow_id}'")
        
        # Create node
        result = await node_actions.create_node(
            workflow_id=request.workflow_id,
            name=request.name,
            description=request.description,
            script_id=request.script_id,
            params=request.params,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds
        )
        
        logger.info(f"[{correlation_id}] Node created successfully: {result['id']}")
        return result
        
    except ValidationError as e:
        logger.error(f"[{correlation_id}] Validation error creating node: {str(e)}")
        raise HTTPException(status_code=400, detail=f"[VALIDATION_ERROR] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error creating node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error creating node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to create node: {str(e)}")


@router.get("/", response_model=List[NodeResponse])
async def list_nodes(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    node_actions: NodeActions = Depends(get_node_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    List all nodes with optional workflow filtering
    
    Returns a list of all nodes. Can be filtered by workflow_id.
    Each node includes full related data (workflow, script, edges).
    """
    try:
        logger.info(f"[{correlation_id}] Listing nodes{f' for workflow {workflow_id}' if workflow_id else ''}")
        
        # Get nodes
        results = await node_actions.get_node_records(workflow_id=workflow_id)
        
        logger.info(f"[{correlation_id}] Retrieved {len(results)} nodes")
        return results
        
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error listing nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error listing nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to list nodes: {str(e)}")


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    node_actions: NodeActions = Depends(get_node_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Get a specific node by ID
    
    Returns detailed node information including all related data
    (workflow, script, incoming/outgoing edges).
    """
    try:
        logger.info(f"[{correlation_id}] Getting node: {node_id}")
        
        # Get node
        result = await node_actions.get_node_record(node_id)
        
        logger.info(f"[{correlation_id}] Node retrieved successfully: {node_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Node not found: {node_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error getting node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error getting node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to get node: {str(e)}")


@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    request: NodeUpdateRequest,
    node_actions: NodeActions = Depends(get_node_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Update a node by ID
    
    Updates the specified node with the provided data.
    Returns the updated node with all related information.
    """
    try:
        logger.info(f"[{correlation_id}] Updating node: {node_id}")
        
        # Prepare update data
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        
        # Update node
        result = await node_actions.update_node(node_id, **update_data)
        
        logger.info(f"[{correlation_id}] Node updated successfully: {node_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Node not found for update: {node_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except ValidationError as e:
        logger.error(f"[{correlation_id}] Validation error updating node: {str(e)}")
        raise HTTPException(status_code=400, detail=f"[VALIDATION_ERROR] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error updating node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error updating node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to update node: {str(e)}")


@router.delete("/{node_id}", response_model=NodeDeleteResponse)
async def delete_node(
    node_id: str,
    node_actions: NodeActions = Depends(get_node_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Delete a node by ID
    
    Deletes the specified node and all related edges.
    Returns detailed information about the deletion process.
    """
    try:
        logger.info(f"[{correlation_id}] Deleting node: {node_id}")
        
        # Delete node
        result = await node_actions.delete_node(node_id)
        
        logger.info(f"[{correlation_id}] Node deleted successfully: {node_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Node not found for deletion: {node_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error deleting node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error deleting node: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to delete node: {str(e)}")
