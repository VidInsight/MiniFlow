"""
ExecutionInput BFF Routes

FastAPI endpoints for ExecutionInput operations in the BFF layer.
READ-ONLY endpoints for scheduler monitoring and execution planning.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from miniflow.app.routes.bff.schemas.execution_input_bff_schemas import (
    ExecutionInputResponse,
    ExecutionInputListResponse
)
from miniflow.app.routes.bff.actions.execution_input_bff_actions import ExecutionInputActions
from miniflow.app.core.dependencies import get_database_orchestrator, get_current_correlation_id
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError
from miniflow.core.logger import get_logger


# Router setup
router = APIRouter()
logger = get_logger("execution_input_bff_routes")


def get_execution_input_actions(
    database_orchestrator: DatabaseOrchestrator = Depends(get_database_orchestrator)
) -> ExecutionInputActions:
    """Local dependency to get ExecutionInput actions instance"""
    return ExecutionInputActions(database_orchestrator)


@router.get("/", response_model=ExecutionInputListResponse)
async def list_execution_inputs(
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    priority: Optional[int] = Query(None, ge=0, le=10, description="Filter by priority level (0-10)"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    execution_input_actions: ExecutionInputActions = Depends(get_execution_input_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    List execution inputs with optional filtering
    
    Returns a list of execution inputs with optional filters for execution, workflow, node, and priority.
    Supports pagination with skip and limit parameters.
    Each execution input includes enhanced data with related entities.
    
    Use cases:
    - Scheduler monitoring and debugging
    - Execution plan visualization  
    - Performance analysis
    - Dependency tracking
    """
    try:
        # Build filter description for logging
        filters = []
        if execution_id:
            filters.append(f"execution_id={execution_id}")
        if workflow_id:
            filters.append(f"workflow_id={workflow_id}")
        if node_id:
            filters.append(f"node_id={node_id}")
        if priority is not None:
            filters.append(f"priority={priority}")
        filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
        
        logger.info(f"[{correlation_id}] Listing execution inputs{filter_desc} (skip={skip}, limit={limit})")
        
        # Get execution inputs
        result = await execution_input_actions.get_execution_input_records(
            execution_id=execution_id,
            workflow_id=workflow_id,
            node_id=node_id,
            priority=priority,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"[{correlation_id}] Retrieved {len(result['execution_inputs'])} execution inputs (total: {result['total_count']})")
        return result
        
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error listing execution inputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error listing execution inputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to list execution inputs: {str(e)}")


@router.get("/{execution_input_id}", response_model=ExecutionInputResponse)
async def get_execution_input(
    execution_input_id: str,
    execution_input_actions: ExecutionInputActions = Depends(get_execution_input_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Get a specific execution input by ID
    
    Returns detailed execution input information including:
    - Basic execution input data (priority, dependencies, etc.)
    - Related execution information
    - Related workflow information
    - Related node information
    - Scheduler optimization fields
    """
    try:
        logger.info(f"[{correlation_id}] Getting execution input: {execution_input_id}")
        
        # Get execution input
        result = await execution_input_actions.get_execution_input_record(execution_input_id)
        
        logger.info(f"[{correlation_id}] Execution input retrieved successfully: {execution_input_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Execution input not found: {execution_input_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error getting execution input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error getting execution input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to get execution input: {str(e)}")
