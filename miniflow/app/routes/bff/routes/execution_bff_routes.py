"""
Execution BFF Routes

FastAPI endpoints for Execution operations in the BFF layer.
READ-ONLY endpoints for execution monitoring and analysis.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from miniflow.app.routes.bff.schemas.execution_bff_schemas import (
    ExecutionResponse,
    ExecutionListResponse,
    ExecutionStatus
)
from miniflow.app.routes.bff.actions.execution_bff_actions import ExecutionActions
from miniflow.app.core.dependencies import get_database_orchestrator, get_current_correlation_id
from miniflow.database.orchestration import DatabaseOrchestrator
from miniflow.core.exceptions import ValidationError, ResourceNotFound, DatabaseError
from miniflow.core.logger import get_logger


# Router setup
router = APIRouter()
logger = get_logger("execution_bff_routes")


def get_execution_actions(
    database_orchestrator: DatabaseOrchestrator = Depends(get_database_orchestrator)
) -> ExecutionActions:
    """Local dependency to get Execution actions instance"""
    return ExecutionActions(database_orchestrator)


@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status: Optional[ExecutionStatus] = Query(None, description="Filter by execution status"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    execution_actions: ExecutionActions = Depends(get_execution_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    List executions with optional filtering
    
    Returns a list of executions with optional filters for workflow and status.
    Supports pagination with skip and limit parameters.
    Each execution includes enhanced data with computed fields.
    """
    try:
        # Build filter description for logging
        filters = []
        if workflow_id:
            filters.append(f"workflow_id={workflow_id}")
        if status:
            filters.append(f"status={status.value}")
        filter_desc = f" with filters: {', '.join(filters)}" if filters else ""
        
        logger.info(f"[{correlation_id}] Listing executions{filter_desc} (skip={skip}, limit={limit})")
        
        # Get executions
        result = await execution_actions.get_execution_records(
            workflow_id=workflow_id,
            status=status.value if status else None,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"[{correlation_id}] Retrieved {len(result['executions'])} executions (total: {result['total_count']})")
        return result
        
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error listing executions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error listing executions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to list executions: {str(e)}")


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    execution_actions: ExecutionActions = Depends(get_execution_actions),
    correlation_id: str = Depends(get_current_correlation_id)
):
    """
    Get a specific execution by ID
    
    Returns detailed execution information including:
    - Basic execution data (status, timing, results)
    - Related workflow information
    - Computed fields (duration, progress, etc.)
    - Execution statistics
    """
    try:
        logger.info(f"[{correlation_id}] Getting execution: {execution_id}")
        
        # Get execution
        result = await execution_actions.get_execution_record(execution_id)
        
        logger.info(f"[{correlation_id}] Execution retrieved successfully: {execution_id}")
        return result
        
    except ResourceNotFound as e:
        logger.warning(f"[{correlation_id}] Execution not found: {execution_id}")
        raise HTTPException(status_code=404, detail=f"[RESOURCE_NOT_FOUND] {str(e)}")
    except DatabaseError as e:
        logger.error(f"[{correlation_id}] Database error getting execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[DATABASE_ERROR] {str(e)}")
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error getting execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"[INTERNAL_ERROR] Failed to get execution: {str(e)}")