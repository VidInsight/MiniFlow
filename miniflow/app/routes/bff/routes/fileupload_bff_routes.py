from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse

from miniflow.core.exceptions import MiniflowException

from miniflow.app.core.response import APIResponse
from miniflow.app.routes.bff.actions.fileupload_bff_actions import FileUploadActions
from miniflow.app.core.dependencies import verify_bff_access, get_current_correlation_id, get_database_orchestrator
from miniflow.app.routes.bff.schemas.fileupload_bff_schemas import FileUploadResponse, FileUploadDeleteResponse


# Router instance
router = APIRouter()


def get_file_actions(orchestrator=Depends(get_database_orchestrator)):
    """Get FileUploadActions with injected orchestrator"""
    return FileUploadActions(orchestrator=orchestrator.fileupload_orchestrator)


# CREATE - File Upload
@router.post("/", response_model=APIResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    is_temporary: bool = Form(True),
    correlation_id: str = Depends(get_current_correlation_id),
    file_actions: FileUploadActions = Depends(get_file_actions)
):
    """
    Upload a file with automatic metadata extraction
    
    Args:
        file: The file to upload
        is_temporary: Whether file is temporary (default: True)
        correlation_id: Request correlation ID
        file_actions: FileUpload actions dependency
        
    Returns:
        APIResponse[FileUploadResponse]: Created file record
    """
    try:
        result = await file_actions.create_file_upload(
            uploaded_file=file,
            is_temporary=is_temporary
        )
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# READ - List Files
@router.get("/", response_model=APIResponse[List[FileUploadResponse]])
async def list_file_uploads(
    is_temporary: Optional[bool] = Query(None, description="Filter by temporary status"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    correlation_id: str = Depends(get_current_correlation_id),
    file_actions: FileUploadActions = Depends(get_file_actions)
):
    """
    List file uploads with optional filtering
    
    Args:
        is_temporary: Optional filter by temporary status
        mime_type: Optional filter by MIME type
        correlation_id: Request correlation ID
        file_actions: FileUpload actions dependency
        
    Returns:
        APIResponse[List[FileUploadResponse]]: List of file records
    """
    try:
        result = await file_actions.get_file_records(
            is_temporary=is_temporary,
            mime_type=mime_type
        )
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# READ - Single File
@router.get("/{file_id}", response_model=APIResponse[FileUploadResponse])
async def get_file_upload(
    file_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    file_actions: FileUploadActions = Depends(get_file_actions)
):
    """
    Get single file upload by ID
    
    Args:
        file_id: File upload ID
        correlation_id: Request correlation ID
        file_actions: FileUpload actions dependency
        
    Returns:
        APIResponse[FileUploadResponse]: File record
    """
    try:
        result = await file_actions.get_file_record(file_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE - Delete File
@router.delete("/{file_id}", response_model=APIResponse[FileUploadDeleteResponse])
async def delete_file_upload(
    file_id: str,
    correlation_id: str = Depends(get_current_correlation_id),
    file_actions: FileUploadActions = Depends(get_file_actions)
):
    """
    Delete file upload by ID
    
    Args:
        file_id: File upload ID
        correlation_id: Request correlation ID
        file_actions: FileUpload actions dependency
        
    Returns:
        APIResponse[FileUploadDeleteResponse]: Enhanced delete response
    """
    try:
        result = await file_actions.delete_file_upload(file_id)
        return APIResponse(
            data=result,
            correlation_id=correlation_id
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DOWNLOAD - Download File
@router.get("/{file_id}/download", response_class=FileResponse)
async def download_file(
    file_id: str,
    file_actions: FileUploadActions = Depends(get_file_actions)
):
    """
    Download file by ID
    
    Args:
        file_id: File upload ID
        file_actions: FileUpload actions dependency
        
    Returns:
        FileResponse: The requested file for download
    """
    try:
        # Get file record to find path
        file_record = await file_actions.get_file_record(file_id)
        file_path = file_record["file_path"]
        filename = file_record["name"]
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=file_record.get("mime_type", "application/octet-stream")
        )
    except MiniflowException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))