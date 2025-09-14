from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity
from miniflow.database.models import FileUpload


class FileUploadOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        """Return the FileUpload CRUD instance."""
        return self.fileupload_crud

    @with_session
    def create(self, session: Session, **kwargs) -> Dict[str, Any]:
        try:
            result = self.fileupload_crud._create(session, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", name=kwargs.get("name"))
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.fileupload_crud._exists(session, record_id):
            self._handle_not_found("File upload", record_id, "delete")

        try:
            result = self.fileupload_crud._delete(session, record_id)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("delete", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_by_name(self, session: Session, name: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        try:
            results = self.fileupload_crud._filter(session, filters={"name": name})
            if not results:
                return None
            return self._serialize_single_result(results[0], include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_path(self, session: Session, file_path: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        try:
            results = self.fileupload_crud._filter(session, filters={"file_path": file_path})
            if not results:
                return None
            return self._serialize_single_result(results[0], include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_path", file_path=file_path)
            raise OrchestrationError(str(e), context=context) from e