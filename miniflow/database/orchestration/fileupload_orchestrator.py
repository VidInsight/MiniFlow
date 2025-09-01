from typing import List, Optional, Dict, Any
from miniflow.database.models import FileUpload
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
import os 


from miniflow.core.exceptions import OrchestrationError


class FileUploadOrchestrator(BaseOrchestrator):
    """
    FileUpload orchestrator for file management operations.
    
    Provides high-level methods for managing file uploads
    with automatic session management through DatabaseEngine.
    """

    def __init__(self, database_engine):
        """
        Initialize FileUpload orchestrator.
        
        Args:
            database_engine: DatabaseEngine instance
        """
        super().__init__(database_engine)
        # FileUpload CRUD instance is already initialized in BaseOrchestrator

    @with_session
    def create_file_upload(self, session, name: str, file_path: str, file_size: int, mime_type: Optional[str] = None, checksum: Optional[str] = None, is_temporary: bool = True) -> FileUpload:
        """
        Create a new file upload record.

        Args:
            session: Database session
            name (str): Name of the uploaded file
            file_path (str): Path where file is stored
            file_size (int): Size of file in bytes
            mime_type (Optional[str]): MIME type of file
            checksum (Optional[str]): File checksum/hash
            is_temporary (bool): Whether file is temporary

        Returns:
            FileUpload: Created file upload record

        Raises:
            OrchestrationError: If file creation fails
        """
        try:
            # Check if file already exists
            existing = self.fileupload_crud.find_by_name(session, name)
            if existing:
                context = self._create_error_context("create", name=name)
                raise OrchestrationError(f"File upload '{name}' already exists", context=context)

            return self.fileupload_crud.create_file_upload(
                session,
                name=name,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                checksum=checksum,
                is_temporary=is_temporary
            )
        except Exception as e:
            context = self._create_error_context("create", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_file_upload_by_id(self, session, record_id: str) -> Optional[FileUpload]:
        """
        Get file upload record by ID.

        Args:
            session: Database session
            record_id (str): ID of the file upload record

        Returns:
            Optional[FileUpload]: File upload record if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.fileupload_crud.find_by_id(session, record_id)
        except Exception as e:
            context = self._create_error_context("get_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_file_upload_by_path(self, session, file_path: str) -> Optional[FileUpload]:
        """
        Get file upload record by path.

        Args:
            session: Database session
            file_path (str): Path of the file upload record

        Returns:
            Optional[FileUpload]: File upload record if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.fileupload_crud.find_by_path(session, file_path)
        except Exception as e:
            context = self._create_error_context("get_by_path", file_path=file_path)
            raise OrchestrationError(str(e), context=context) from e


    @with_session
    def get_file_upload_by_name(self, session, name: str) -> Optional[FileUpload]:
        """
        Get file upload record by name.

        Args:
            session: Database session
            name (str): Name of the file upload record

        Returns:
            Optional[FileUpload]: File upload record if found, None otherwise

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.fileupload_crud.find_by_name(session, name)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e
            
    @with_session
    def delete_file_upload_by_id(self, session, record_id: str) -> FileUpload:
        """
        Delete file upload record by ID.

        Args:
            session: Database session
            record_id (str): ID of the file upload record

        Returns:
            FileUpload: Deleted file upload record

        Raises:
            OrchestrationError: If file upload not found or deletion fails
        """
        try:
            # First get the file info before deletion
            file_upload = self.fileupload_crud.find_by_id(session, record_id)
            if not file_upload:
                context = self._create_error_context("delete_by_id", record_id=record_id)
                raise OrchestrationError(f"File upload '{record_id}' not found", context=context)
            
            # Store file path before deleting record
            file_path = file_upload.file_path
            
            # Delete database record
            deleted_record = self.fileupload_crud.delete_file_upload(session, record_id)
            
            # Delete file from filesystem if it exists
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"Successfully deleted file: {file_path}")
                except OSError as e:
                    self.logger.warning(f"Failed to delete file {file_path}: {str(e)}")
                    # Don't raise exception for file deletion failure
            
            return deleted_record
        except Exception as e:
            context = self._create_error_context("delete_by_id", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e
    @with_session
    def get_all_file_upload(self, session) -> List[FileUpload]:
        """
        Get all file upload records.

        Args:
            session: Database session

        Returns:
            List[FileUpload]: List of all file upload records

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.fileupload_crud.get_all(session)
        except Exception as e:
            context = self._create_error_context("get_all")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def filter_file_uploads(self, session, **kwargs) -> List[FileUpload]:
        """
        Filter file upload records by criteria.

        Args:
            session: Database session
            **kwargs: Filter criteria (e.g. mime_type, is_temporary, etc.)

        Returns:
            List[FileUpload]: List of filtered file upload records

        Raises:
            OrchestrationError: If database query fails
        """
        try:
            return self.fileupload_crud.filter(session, filters=kwargs)
        except Exception as e:
            context = self._create_error_context("filter", filters=kwargs)
            raise OrchestrationError(str(e), context=context) from e


    @with_session
    def delete_file_upload_by_name(self, session, name: str) -> Optional[FileUpload]:
        """
        Delete file upload by name.

        Args:
            session: Database session
            name (str): Name of the file upload to delete

        Returns:
            Optional[FileUpload]: Deleted file upload if found, None otherwise

        Raises:
            OrchestrationError: If database operation fails
        """
        try:
            file_upload = self.fileupload_crud.find_by_name(session, name)
            if not file_upload:
                return None
            
            return self.fileupload_crud.delete(session, file_upload.id)
        except Exception as e:
            context = self._create_error_context("delete_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e