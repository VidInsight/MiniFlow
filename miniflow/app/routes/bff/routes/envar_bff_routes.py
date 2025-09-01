from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query

from miniflow.core.exceptions import MiniflowException

from miniflow.app.core.response import APIResponse
from miniflow.app.routes.bff.actions.envar_bff_actions import EnvironmentVariableActions
from miniflow.app.core.dependencies import verify_bff_access, get_current_correlation_id, get_database_orchestrator
from miniflow.app.routes.bff.schemas.envar_bff_schemes import EnvironmentVariableCreateRequest, EnvironmentVariableUpdateRequest
from miniflow.app.routes.bff.schemas.envar_bff_schemes import EnvironmentVariableResponse, EnvironmentVariableDeleteResponse


router = APIRouter()

def get_envar_actions(orchestrator=Depends(get_database_orchestrator)):
    """Get EnvironmentVariableOperations with injected orchestrator"""
    return EnvironmentVariableActions(orchestrator=orchestrator.envar_orchestrator)

# CREATE
@router.post("/", response_model=APIResponse[EnvironmentVariableResponse])
async def create_environment_variable(
    envar_request: EnvironmentVariableCreateRequest,
    correlation_id: str = Depends(get_current_correlation_id),
    envar_actions: EnvironmentVariableActions = Depends(get_envar_actions)
):
    """Create new environment variable"""
    try:
        result = await envar_actions.create_envar_record(
            name=envar_request.name,
            value=envar_request.value,
            description=envar_request.description,
            variable_type=envar_request.variable_type
        )
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET
@router.get("/{variable_id}", response_model=APIResponse[EnvironmentVariableResponse])
async def get_environment_variable(
    variable_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    envar_actions: EnvironmentVariableActions = Depends(get_envar_actions)
):
    """Get environment variable by ID"""
    try:
        result = await envar_actions.get_envar_record(variable_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# UPDATE
@router.put("/{variable_id}", response_model=APIResponse[EnvironmentVariableResponse])
async def update_environment_variable(
    variable_id: str,
    envar_request: EnvironmentVariableUpdateRequest,
    correlation_id: str = Depends(get_current_correlation_id),
    envar_actions: EnvironmentVariableActions = Depends(get_envar_actions)
):
    """Update environment variable by ID"""
    try:
        result = await envar_actions.update_envar_record(
            record_id=variable_id,
            value=envar_request.value,
            description=envar_request.description
        )
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# DELETE
@router.delete("/{variable_id}", response_model=APIResponse[EnvironmentVariableDeleteResponse])
async def delete_environment_variable(
    variable_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    envar_actions: EnvironmentVariableActions = Depends(get_envar_actions)
):
    """Delete environment variable by ID"""
    try:
        result = await envar_actions.delete_envar_record(variable_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# LIST
@router.get("/", response_model=APIResponse[List[EnvironmentVariableResponse]])
async def list_environment_variables(
    correlation_id: str = Depends(get_current_correlation_id),
    envar_actions: EnvironmentVariableActions = Depends(get_envar_actions)
):
    """List all environment variables"""
    try:
        result = await envar_actions.get_envar_records()
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))