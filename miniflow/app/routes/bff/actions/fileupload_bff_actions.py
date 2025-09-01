import os
import uuid
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

from miniflow.core.exceptions import (
    MiniflowException, ResourceNotFound, ValidationError, 
    DatabaseError, ErrorContext, ErrorSeverity
)


class FileUploadActions:
    """Minimal FileUpload operations for BFF layer"""
    
    def __init__(self, orchestrator):
        """
        Initialize FileUpload operations
        
        Args:
            orchestrator: FileUploadOrchestrator instance
        """
        self.orchestrator = orchestrator

    def _create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """Create error context for better error tracking"""
        return ErrorContext(
            operation=operation,
            component="FileUploadActions",
            additional_info=kwargs
        )

    def _generate_unique_path(self, filename: str) -> str:
        """
        Generate clean file path without UUID prefix
        
        Args:
            filename: Original filename (e.g., "document.pdf")
            
        Returns:
            str: Clean file path (e.g., "./temp/document.pdf")
        """
        return f"./temp/{filename}"

    def _extract_file_metadata(self, uploaded_file: UploadFile, file_path: str, content: bytes) -> Dict[str, Any]:
        """
        Extract all metadata from uploaded file for FileUpload model
        
        Args:
            uploaded_file: FastAPI UploadFile object
            file_path: Saved file path
            content: File content bytes
            
        Returns:
            Dict: Metadata for orchestrator (FileUpload model fields)
        """
        # 1. Get original filename from upload
        original_filename = uploaded_file.filename
        
        # 2. Extract name and extension
        filename_base, file_extension = os.path.splitext(original_filename)
        
        # 3. Calculate file metadata
        file_size = len(content)
        mime_type = uploaded_file.content_type or mimetypes.guess_type(original_filename)[0]
        checksum = hashlib.sha256(content).hexdigest()
        
        # 4. Return FileUpload model field mapping
        return {
            # FileUpload model fields:
            "name": original_filename,           # Full filename with extension (e.g., "document.pdf")
            "filename": filename_base,           # Base filename without extension (e.g., "document")
            "file_extension": file_extension,    # Extension (e.g., ".pdf")
            "file_path": file_path,             # Absolute path to saved file
            "file_size": file_size,             # Size in bytes
            "mime_type": mime_type,             # MIME type (e.g., "application/pdf")
            "checksum": checksum                # SHA256 hash
            # is_temporary: Will be passed separately to orchestrator
        }

    async def create_file_upload(self,  uploaded_file: UploadFile,  is_temporary: bool = True) -> Dict[str, Any]:
        """
        Create file upload from API with auto metadata extraction
        
        Args:
            uploaded_file: FastAPI UploadFile object
            is_temporary: Whether file is temporary (default: True)
            
        Returns:
            Dict: FileUpload.to_dict() - Pure model response
            
        Raises:
            ValidationError: If file validation fails
            DatabaseError: If file creation fails
        """
        try:
            # Validate uploaded file
            if not uploaded_file.filename:
                context = self._create_error_context("create_file_upload")
                raise ValidationError(
                    "Filename is required", 
                    context=context, 
                    severity=ErrorSeverity.MEDIUM
                )
            
            # Generate unique file path
            file_path = self._generate_unique_path(uploaded_file.filename)
            
            # Read file content
            content = await uploaded_file.read()
            if len(content) == 0:
                context = self._create_error_context(
                    "create_file_upload", 
                    filename=uploaded_file.filename
                )
                raise ValidationError(
                    "File content cannot be empty", 
                    context=context, 
                    severity=ErrorSeverity.MEDIUM
                )
            
            # Create temp directory if it doesn't exist
            os.makedirs("./temp", exist_ok=True)
            
            # Save file to filesystem
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Extract metadata
            metadata = self._extract_file_metadata(uploaded_file, file_path, content)
            
            # Call orchestrator to save to database with all FileUpload model fields
            file_record = self.orchestrator.create_file_upload(
                name=metadata["name"],                    # Full filename with extension
                file_path=metadata["file_path"],          # Absolute path to saved file
                file_size=metadata["file_size"],          # Size in bytes
                mime_type=metadata["mime_type"],          # MIME type
                checksum=metadata["checksum"],            # SHA256 hash
                is_temporary=is_temporary                 # Temporary status
            )
            
            # Return pure model response
            return file_record.to_dict()
            
        except (ValidationError, ResourceNotFound):
            raise
        except Exception as e:
            context = self._create_error_context("create_file_upload",  filename=getattr(uploaded_file, 'filename', 'unknown'))
            raise DatabaseError(f"Failed to create file upload: {str(e)}",  context=context,  severity=ErrorSeverity.HIGH,  source_error=e)

    async def get_file_record(self, file_id: str) -> Dict[str, Any]:
        """
        Get single file upload record by ID
        
        Args:
            file_id: File upload ID
            
        Returns:
            Dict: FileUpload.to_dict() - Pure model response
            
        Raises:
            ResourceNotFound: If file not found
            DatabaseError: If database query fails
        """
        try:
            file_record = self.orchestrator.get_file_upload_by_id(file_id)
            if not file_record:
                context = self._create_error_context("get_file_record", file_id=file_id)
                raise ResourceNotFound(f"File '{file_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)
            
            # Return pure model response
            return file_record.to_dict()
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("get_file_record", file_id=file_id)
            raise DatabaseError(f"Failed to retrieve file '{file_id}': {str(e)}",  context=context,  severity=ErrorSeverity.HIGH,  source_error=e)

    async def get_file_records(self, is_temporary: Optional[bool] = None, mime_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of file upload records with optional filtering
        
        Args:
            is_temporary: Filter by temporary status
            mime_type: Filter by MIME type
            
        Returns:
            List[Dict]: List of FileUpload.to_dict() - Pure model responses
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            # Build filters
            filters = {}
            if is_temporary is not None:
                filters['is_temporary'] = is_temporary
            if mime_type is not None:
                filters['mime_type'] = mime_type
            
            # Get filtered files
            if filters:
                file_records = self.orchestrator.filter_file_uploads(**filters)
            else:
                file_records = self.orchestrator.get_all_file_upload()
            
            # Return pure model responses
            return [file_record.to_dict() for file_record in file_records]
            
        except Exception as e:
            context = self._create_error_context("get_file_records", is_temporary=is_temporary, mime_type=mime_type)
            raise DatabaseError( f"Failed to retrieve file records: {str(e)}",  context=context,  severity=ErrorSeverity.HIGH,  source_error=e)

    async def delete_file_upload(self, file_id: str) -> Dict[str, Any]:
        """
        Delete file upload with detailed response
        
        Args:
            file_id: File upload ID
            
        Returns:
            Dict: FileUploadDeleteResponse schema format
            
        Raises:
            ResourceNotFound: If file not found
            DatabaseError: If deletion fails
        """
        try:
            # Get file before deletion
            file_record = self.orchestrator.get_file_upload_by_id(file_id)
            if not file_record:
                context = self._create_error_context("delete_file_upload", file_id=file_id)
                raise ResourceNotFound(f"File '{file_id}' not found", context=context, severity=ErrorSeverity.MEDIUM)
            
            # Check if physical file exists before deletion
            file_existed = os.path.exists(file_record.file_path)
            
            # Delete from database and filesystem (orchestrator handles both)
            deleted_record = self.orchestrator.delete_file_upload_by_id(file_id)
            
            # Check if physical file was actually removed
            physical_file_deleted = file_existed and not os.path.exists(file_record.file_path)
            
            # Collect any warnings
            warnings = []
            if file_existed and not physical_file_deleted:
                warnings.append(f"Physical file could not be removed: {file_record.file_path}")
            elif not file_existed:
                warnings.append("Physical file did not exist on filesystem")
            
            # Return enhanced delete response
            return {
                "deleted_record": deleted_record.to_dict(),
                "database_deleted": True,
                "physical_file_deleted": physical_file_deleted,
                "file_existed": file_existed,
                "message": f"File '{file_record.name}' deleted successfully",
                "warnings": warnings if warnings else None
            }
            
        except ResourceNotFound:
            raise
        except Exception as e:
            context = self._create_error_context("delete_file_upload", file_id=file_id)
            raise DatabaseError(f"Failed to delete file '{file_id}': {str(e)}", context=context, severity=ErrorSeverity.HIGH, source_error=e)