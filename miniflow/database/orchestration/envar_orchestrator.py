from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity
from miniflow.database.models import EnvironmentVariable


class EnvironmentVariableOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        """Return the EnvironmentVariable CRUD instance."""
        return self.envar_crud

    @with_session
    def create(self, session: Session, name: str, value: str, **kwargs) -> Dict[str, Any]:
        try:
            result = self.envar_crud._create_with_validation(session, name, value, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_name(self, session: Session, name: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        try:
            results = self.envar_crud._filter(session, filters={"name": name})
            return self._serialize_single_result(results[0] if results else None, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.envar_crud._exists(session, record_id):
            self._handle_not_found("Environment variable", record_id, "delete")

        try:
            result = self.envar_crud._delete(session, record_id)
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