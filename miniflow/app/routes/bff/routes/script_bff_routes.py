from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from miniflow.core.exceptions import MiniflowException

from miniflow.app.core.response import APIResponse
from miniflow.app.routes.bff.actions.script_bff_actions import ScriptActions
from miniflow.app.core.dependencies import verify_bff_access, get_current_correlation_id, get_database_orchestrator
from miniflow.app.routes.bff.schemas.scripts_bff_schemas import ScriptCreateRequest, ScriptResponse, ScriptDeleteResponse


# Router instance
router = APIRouter()


def get_script_actions(orchestrator=Depends(get_database_orchestrator)):
    """Get ScriptActions with injected orchestrator"""
    return ScriptActions(orchestrator=orchestrator.script_orchestrator)


# CREATE - Script Creation
@router.post("/", response_model=APIResponse[ScriptResponse])
async def create_script(
    script_request: ScriptCreateRequest,
    correlation_id: str = Depends(get_current_correlation_id),
    script_actions: ScriptActions = Depends(get_script_actions)
):
    """
    Create a new script with automatic file creation
    
    Args:
        script_request: Script creation request data
        correlation_id: Request correlation ID
        script_actions: Script actions dependency
        
    Returns:
        APIResponse[ScriptResponse]: Created script record
    """
    try:
        result = await script_actions.create_script(
            name=script_request.name,
            language=script_request.language,
            category=script_request.category,
            content=script_request.content,
            subcategory=script_request.subcategory,
            description=script_request.description,
            version=script_request.version,
            required_packages=script_request.required_packages,
            input_schema=script_request.input_schema,
            output_schema=script_request.output_schema,
            test_input_params=script_request.test_input_params,
            test_output_params=script_request.test_output_params,
            tags=script_request.tags,
            author=script_request.author
        )
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# READ - List Scripts
@router.get("/", response_model=APIResponse[List[ScriptResponse]])
async def list_scripts(
    language: Optional[str] = Query(None, description="Filter by language (PYTHON, BASH)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    correlation_id: str = Depends(get_current_correlation_id),
    script_actions: ScriptActions = Depends(get_script_actions)
):
    """
    List scripts with optional filtering
    
    Args:
        language: Optional filter by language
        category: Optional filter by category
        correlation_id: Request correlation ID
        script_actions: Script actions dependency
        
    Returns:
        APIResponse[List[ScriptResponse]]: List of script records
    """
    try:
        result = await script_actions.get_script_records(
            language=language,
            category=category
        )
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# READ - Single Script
@router.get("/{script_id}", response_model=APIResponse[ScriptResponse])
async def get_script(
    script_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    script_actions: ScriptActions = Depends(get_script_actions)
):
    """
    Get single script by ID
    
    Args:
        script_id: Script ID
        correlation_id: Request correlation ID
        script_actions: Script actions dependency
        
    Returns:
        APIResponse[ScriptResponse]: Script record
    """
    try:
        result = await script_actions.get_script_record(script_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE - Delete Script
@router.delete("/{script_id}", response_model=APIResponse[ScriptDeleteResponse])
async def delete_script(
    script_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    script_actions: ScriptActions = Depends(get_script_actions)
):
    """
    Delete script by ID
    
    Args:
        script_id: Script ID
        correlation_id: Request correlation ID
        script_actions: Script actions dependency
        
    Returns:
        APIResponse[ScriptDeleteResponse]: Enhanced delete response
    """
    try:
        result = await script_actions.delete_script(script_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))