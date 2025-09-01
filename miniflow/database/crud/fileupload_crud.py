import re
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
import os

from miniflow.database.models import FileUpload
from miniflow.core.exceptions import (ValidationError, DatabaseQueryError, ErrorSeverity)
from miniflow.database.crud.base_crud import BaseCRUD


class FileUploadCRUD(BaseCRUD[FileUpload]):
    """FileUpload specific CRUD operations with file management support"""

    def __init__(self):
        super().__init__(FileUpload)

    def create_file_upload(self, session: Session, name: str, file_path: str, file_size: int, mime_type: Optional[str] = None, checksum: Optional[str] = None, is_temporary: bool = True) -> FileUpload:
        """
        Create new file upload record
        
        Args:
            session: Database session
            name: Full name in format filename.extension
            file_path: Full file path where file is stored
            file_size: File size in bytes
            mime_type: MIME type of the file
            checksum: File checksum (MD5/SHA256)
            is_temporary: Whether file is temporary (default: True)
            
        Returns:
            Created FileUpload instance
            
        Raises:
            ValidationError: If name is empty or file_path is invalid
            DatabaseQueryError: If database operation fails
        """
        # Validation
        if not name or not name.strip():
            raise ValidationError("File name cannot be empty", severity=ErrorSeverity.MEDIUM)
        
        if not file_path or not file_path.strip():
            raise ValidationError("File path cannot be empty", severity=ErrorSeverity.MEDIUM)
        
        if file_size < 0:
            raise ValidationError("File size cannot be negative", severity=ErrorSeverity.MEDIUM)
            
        # Parse filename and extension
        import os
        clean_name = name.strip()
        filename_base = os.path.splitext(clean_name)[0]
        file_extension = os.path.splitext(clean_name)[1]
        
        record_payload = {
            'name': clean_name,  # Full name with extension
            'filename': filename_base,  # Base filename without extension
            'file_extension': file_extension,  # Extension (.pdf, .txt, etc.)
            'file_path': file_path.strip(),
            'file_size': file_size,
            'mime_type': mime_type,
            'checksum': checksum,
            'is_temporary': is_temporary,
        }
            
        return self.create(session, **record_payload)

    def find_by_path(self, session: Session, file_path: str) -> FileUpload:
        """
        Find file upload by file path
        
        Args:
            session: Database session
            file_path: File path to search for
            
        Returns:
            FileUpload instance or None if not found
        """
        records = self.filter(session, filters={'file_path': file_path.strip()})
        
        if len(records) > 2:
            self.logger.warning(f"Multiple file uploads found for path: {file_path.strip()}")
            return records[0]
        elif len(records) == 1:
            return records[0]
        else:
            self.logger.warning(f"No file uploads found for path: {file_path.strip()}")
            return None


    def delete_file_upload(self, session: Session, record_id: str) -> FileUpload:
        """
        Delete file upload record and optionally remove physical file
        
        Args:
            session: Database session
            record_id: File upload record ID

        Returns:
            True if deletion was successful
        """
        if not record_id or not record_id.strip():
            context = self._create_error_context("delete_record", record_id=record_id)
            raise ValidationError("Record ID cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        record = self.find_by_id(session, record_id)
        if not record:
            context = self._create_error_context("delete_record", record_id=record_id)
            raise DatabaseQueryError(f"File upload '{record_id}' not found", context=context, severity=ErrorSeverity.HIGH)

        return self.delete(session, record_id)