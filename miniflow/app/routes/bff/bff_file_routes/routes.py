"""File Upload Routes"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File

from miniflow.app.core.operations_dependencies import get_file_operations
from miniflow.app.middleware.correlation import get_current_correlation_id
from miniflow.app.core.response import APIResponse
from miniflow.app.utils.decorators import with_api_error_handling
from .operations import FileUploadOperations
from .schemas import FileUploadCreateRequest, FileUploadFilterRequest

router = APIRouter()

# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get("/count", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="count_files")
async def count_files(operations: FileUploadOperations = Depends(get_file_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.count_file_upload_records()
    return APIResponse(data={"count": result}, message="Files count retrieved", correlation_id=correlation_id)

@router.post("/filter", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="filter_files")
async def filter_files(request: FileUploadFilterRequest, operations: FileUploadOperations = Depends(get_file_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.filter_file_upload_records(request)
    return APIResponse(data=result, message="Files filtered", correlation_id=correlation_id)

# GENERAL ROUTES

@router.post("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="upload_file")
async def upload_file(file: UploadFile = File(...), is_temporary: bool = Query(True, description="Mark as temporary file"), operations: FileUploadOperations = Depends(get_file_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.create_file_upload_record(file, is_temporary)
    return APIResponse(data=result, message="File uploaded", correlation_id=correlation_id)

@router.get("/", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="list_files")
async def list_files(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), order_by: Optional[str] = Query(None), include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: FileUploadOperations = Depends(get_file_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.list_file_upload_records(skip, limit, order_by, include_relationships, exclude_list)
    return APIResponse(data=result, message="Files retrieved", correlation_id=correlation_id)

# PARAMETERIZED ROUTES LAST

@router.get("/{file_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="get_file")
async def get_file(file_id: str, include_relationships: bool = Query(False), exclude_fields: Optional[str] = Query(None), operations: FileUploadOperations = Depends(get_file_operations), correlation_id: str = Depends(get_current_correlation_id)):
    exclude_list = exclude_fields.split(',') if exclude_fields else None
    result = await operations.get_file_upload_record(file_id, include_relationships, exclude_list)
    return APIResponse(data=result, message="File retrieved", correlation_id=correlation_id)

@router.delete("/{file_id}", response_model=APIResponse[Dict[str, Any]])
@with_api_error_handling(operation="delete_file")
async def delete_file(file_id: str, operations: FileUploadOperations = Depends(get_file_operations), correlation_id: str = Depends(get_current_correlation_id)):
    result = await operations.delete_file_upload_record(file_id)
    return APIResponse(data=result, message="File deleted", correlation_id=correlation_id)
