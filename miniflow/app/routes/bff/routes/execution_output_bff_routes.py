"""
ExecutionOutput BFF Routes

FastAPI endpoints for ExecutionOutput operations in the BFF layer.
READ-ONLY endpoints for execution results monitoring and analysis.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from miniflow.app.routes.bff.schemas.execution_output_bff_schemas import (
    ExecutionOutputResponse,
    ExecutionOutputListResponse,
    ExecutionOutputStatus
)
from miniflow.app.routes.bff.actions.execution_output_bff_actions import ExecutionOutputActions
from miniflow.app.core.dependencies import get_database_orchestrator, get_current_correlation_id
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError
from miniflow.core.logger import get_logger


# Router setup
router = APIRouter()
logger = get_logger("execution_output_bff_routes")


def get_execution_output_actions(
    database_orchestrator: DatabaseOrchestrator = Depends(get_database_orchestrator)
) -> ExecutionOutputActions:
    """Local dependency to get ExecutionOutput actions instance"""
    return ExecutionOutputActions(database_orchestrator)


@router.get("/", response_model=ExecutionOutputListResponse)
async def list_execution_outputs(
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    status: Optional[ExecutionOutputStatus] = Query(None, description="Filter by execution output status"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    execution_output_actions: ExecutionOutputActions = Depends(get_execution_output_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    List execution outputs with optional filtering
    
    Returns a list of execution outputs with optional filters for execution, workflow, node, and status.
    Supports pagination with skip and limit parameters.
    Each execution output includes enhanced data with related entities and computed fields.
    
    Use cases:
    - Execution results monitoring
    - Performance analysis and debugging
    - Success/failure rate tracking
    - Error pattern analysis
    - Workflow analytics
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
        if status:
            filters.append(f"status={status.value}")
        filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
        
        logger.info(f"[{correlation_id}] Listing execution outputs{filter_desc} (skip={skip}, limit={limit})")
        
        # Get execution outputs
        result = await execution_output_actions.get_execution_output_records(
            execution_id=execution_id,
            workflow_id=workflow_id,
            node_id=node_id,
            status=status.value if status else None,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"[{correlation_id}] Retrieved {len(result['execution_outputs'])} execution outputs (total: {result['total_count']})")
        return result
        
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error listing execution outputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error listing execution outputs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to list execution outputs: {str(e)}")


@router.get("/{execution_output_id}", response_model=ExecutionOutputResponse)
async def get_execution_output(
    execution_output_id: str,
    execution_output_actions: ExecutionOutputActions = Depends(get_execution_output_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Get a specific execution output by ID
    
    Returns detailed execution output information including:
    - Basic execution output data (status, results, timing)
    - Related execution information
    - Related workflow information
    - Related node information
    - Computed fields (duration, success flag)
    - Result data for analysis
    """
    try:
        logger.info(f"[{correlation_id}] Getting execution output: {execution_output_id}")
        
        # Get execution output
        result = await execution_output_actions.get_execution_output_record(execution_output_id)
        
        logger.info(f"[{correlation_id}] Execution output retrieved successfully: {execution_output_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Execution output not found: {execution_output_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error getting execution output: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error getting execution output: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to get execution output: {str(e)}")
