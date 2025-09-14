"""
File Upload Operations - Enhanced with File Operations
"""

import os
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

from miniflow.core.logger import get_logger
from miniflow.core.exceptions import ValidationError, DatabaseError
from ..base_operations import BaseBFFOperations
from .schemas import FileUploadCreateRequest, FileUploadFilterRequest
from miniflow.database.orchestration.fileupload_orchestrator import FileUploadOrchestrator


class FileUploadOperations(BaseBFFOperations[FileUploadOrchestrator]):
    def __init__(self, orchestrator: FileUploadOrchestrator):
        self.logger = get_logger("miniflow_api")
        self.orchestrator = orchestrator
        super().__init__(orchestrator, "file_upload")

    # CAPABILITY OVERRIDES - File uploads support CREATE and DELETE only
    @property
    def supports_create(self) -> bool:
        """File uploads can be created"""
        return True
    
    @property 
    def supports_update(self) -> bool:
        """File uploads cannot be updated - they are immutable"""
        return False
    
    @property
    def supports_delete(self) -> bool:
        """File uploads can be deleted"""
        return True
    
    @property
    def supports_filter(self) -> bool:
        """File uploads support filtering"""
        return True

    def _generate_unique_path(self, filename: str) -> str:
        """Generate file path for uploaded files"""
        # Return absolute path
        temp_dir = os.path.abspath("./temp")
        return os.path.join(temp_dir, filename)

    def _extract_file_metadata(self, uploaded_file: UploadFile, file_path: str, content: bytes) -> Dict[str, Any]:
        """Extract all metadata from uploaded file for FileUpload model"""
        # Get original filename from upload
        original_filename = uploaded_file.filename
        
        # Extract name and extension
        filename_base, file_extension = os.path.splitext(original_filename)
        
        # Calculate file metadata
        file_size = len(content)
        mime_type = uploaded_file.content_type or mimetypes.guess_type(original_filename)[0]
        checksum = hashlib.sha256(content).hexdigest()
        
        # Return FileUpload model field mapping
        return {
            "name": original_filename,           # Full filename with extension
            "filename": filename_base,           # Base filename without extension
            "file_extension": file_extension,    # Extension
            "file_path": file_path,             # Absolute path to saved file
            "file_size": file_size,             # Size in bytes
            "mime_type": mime_type,             # MIME type
            "checksum": checksum                # SHA256 hash
        }

    # CREATE WITH FILE OPERATIONS (Based on existing create_file_upload method)
    async def create_file_upload_record(self, uploaded_file: UploadFile, is_temporary: bool = True) -> Dict[str, Any]:
        """Create file upload record with physical file handling - matches existing pattern"""
        try:
            # Validate uploaded file
            if not uploaded_file.filename:
                raise ValidationError("Filename is required")
            
            # Generate unique file path
            file_path = self._generate_unique_path(uploaded_file.filename)
            
            # Read file content
            content = await uploaded_file.read()
            if len(content) == 0:
                raise ValidationError("File content cannot be empty")
            
            # Create temp directory if it doesn't exist
            temp_dir = os.path.abspath("./temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save file to filesystem
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Extract metadata
            metadata = self._extract_file_metadata(uploaded_file, file_path, content)
            
            # Call orchestrator to save to database with all FileUpload model fields
            file_record = self.orchestrator.create(
                name=metadata["name"],
                filename=metadata["filename"],
                file_extension=metadata["file_extension"],
                file_path=metadata["file_path"],
                file_size=metadata["file_size"],
                mime_type=metadata["mime_type"],
                checksum=metadata["checksum"],
                is_temporary=is_temporary
            )
            
            # Return with enhanced response format
            return {
                'action_status': True,
                'record_id': file_record['id'],
                'message': "File upload creation successful",
                'file_operations': {
                    'physical_file_created': True,
                    'file_path': file_record['file_path'],
                    'file_size': file_record['file_size'],
                    'checksum': file_record['checksum']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create file upload: {str(e)}")
            # Cleanup any created files on error
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Cleaned up file on error: {file_path}")
                except OSError as cleanup_error:
                    self.logger.warning(f"Failed to cleanup file {file_path}: {cleanup_error}")
            raise

    # GET BY ID
    async def get_file_upload_record(self, record_id: str, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        response_from_db = await self._get_record(record_id, include_relationships, exclude_fields)
        return response_from_db

    # DELETE WITH FILE CLEANUP (Based on existing delete_file_upload method)
    async def delete_file_upload_record(self, record_id: str) -> Dict[str, Any]:
        """Delete file upload record with physical file cleanup - matches existing pattern"""
        try:
            # Get file before deletion
            file_record = await self._get_record(record_id)
            
            # Check if physical file exists before deletion
            file_existed = os.path.exists(file_record['file_path'])
            
            # Delete from database
            response_from_db = await self._delete_record(record_id)
            
            # Manually delete physical file
            physical_file_deleted = False
            if file_existed:
                try:
                    os.remove(file_record['file_path'])
                    physical_file_deleted = True
                except OSError:
                    # File deletion failed, but database was cleaned
                    pass
            
            # Collect any warnings
            warnings = []
            if file_existed and not physical_file_deleted:
                warnings.append(f"Physical file could not be removed: {file_record['file_path']}")
            elif not file_existed:
                warnings.append("Physical file did not exist on filesystem")
            
            return {
                'action_status': True,
                'record_id': response_from_db['id'],
                'message': "File upload deletion successful",
                'file_operations': {
                    'physical_file_deleted': physical_file_deleted,
                    'file_path': file_record['file_path'],
                    'file_size': file_record['file_size'],
                    'checksum': file_record['checksum'],
                    'warnings': warnings if warnings else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete file upload {record_id}: {str(e)}")
            raise

    # LIST ALL
    async def list_file_upload_records(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        response_from_db = await self._get_all_records(skip, limit, order_by, include_relationships, exclude_fields)
        return response_from_db

    # COUNT
    async def count_file_upload_records(self) -> int:
        response_from_db = await self._count_records()
        return response_from_db

    # FILTER 
    async def filter_file_upload_records(self, request: FileUploadFilterRequest) -> Dict[str, Any]:
        response_from_db = await self._filter_records(request.filters, request.skip, request.limit, request.order_by_field, request.include_relationships, request.exclude_fields)
        return response_from_db
