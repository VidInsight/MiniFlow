from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from miniflow.core.exceptions import MiniflowException

from miniflow.app.core.response import APIResponse
from miniflow.app.routes.bff.actions.workflow_bff_actions import WorkflowActions
from miniflow.app.core.dependencies import get_current_correlation_id, get_database_orchestrator
from miniflow.app.routes.bff.schemas.workflow_bff_schemas import (
    WorkflowCreateRequest, WorkflowUpdateRequest, 
    WorkflowResponse, WorkflowDeleteResponse
)


router = APIRouter()


def get_workflow_actions(orchestrator=Depends(get_database_orchestrator)):
    """Get WorkflowActions with injected orchestrator"""
    return WorkflowActions(orchestrator=orchestrator.workflow_orchestrator)


# CREATE
@router.post("/", response_model=APIResponse[WorkflowResponse])
async def create_workflow(
    workflow_request: WorkflowCreateRequest,
    correlation_id: str = Depends(get_current_correlation_id),
    workflow_actions: WorkflowActions = Depends(get_workflow_actions)
):
    """Create a new workflow"""
    try:
        result = await workflow_actions.create_workflow(
            name=workflow_request.name,
            description=workflow_request.description,
            priority=workflow_request.priority
        )
        return APIResponse(
            data=result,
            message=f"Workflow '{workflow_request.name}' created successfully",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# LIST
@router.get("/", response_model=APIResponse[List[WorkflowResponse]])
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, ACTIVE, DEACTIVATED)"),
    priority: Optional[int] = Query(None, description="Filter by priority"),
    correlation_id: str = Depends(get_current_correlation_id),
    workflow_actions: WorkflowActions = Depends(get_workflow_actions)
):
    """List all workflows with optional filtering"""
    try:
        result = await workflow_actions.get_workflow_records(
            status=status,
            priority=priority
        )
        return APIResponse(
            data=result,
            message=f"Retrieved {len(result)} workflows",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GET
@router.get("/{workflow_id}", response_model=APIResponse[WorkflowResponse])
async def get_workflow(
    workflow_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    workflow_actions: WorkflowActions = Depends(get_workflow_actions)
):
    """Get workflow by ID"""
    try:
        result = await workflow_actions.get_workflow_record(workflow_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# UPDATE
@router.put("/{workflow_id}", response_model=APIResponse[WorkflowResponse])
async def update_workflow(
    workflow_id: str,
    workflow_request: WorkflowUpdateRequest,
    correlation_id: str = Depends(get_current_correlation_id),
    workflow_actions: WorkflowActions = Depends(get_workflow_actions)
):
    """Update workflow by ID"""
    try:
        result = await workflow_actions.update_workflow(
            workflow_id=workflow_id,
            name=workflow_request.name,
            description=workflow_request.description,
            priority=workflow_request.priority,
            status=workflow_request.status,
            status_message=workflow_request.status_message
        )
        return APIResponse(
            data=result,
            message=f"Workflow '{workflow_id}' updated successfully",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE
@router.delete("/{workflow_id}", response_model=APIResponse[WorkflowDeleteResponse])
async def delete_workflow(
    workflow_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    workflow_actions: WorkflowActions = Depends(get_workflow_actions)
):
    """Delete workflow by ID"""
    try:
        result = await workflow_actions.delete_workflow(workflow_id)
        return APIResponse(
            data=result,
            message=f"Workflow '{workflow_id}' deleted successfully",
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
