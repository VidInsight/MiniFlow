from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity
from miniflow.database.models import Script


class ScriptOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        """Return the Script CRUD instance."""
        return self.script_crud

    @with_session
    def create(self, session: Session,  **kwargs) -> Dict[str, Any]:
        try:
            result = self.script_crud._create(session, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", name=kwargs.get("name"))
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]:
        if not self.script_crud._exists(session, record_id):
            self._handle_not_found("Script", record_id, "update")

        try:
            result = self.script_crud._update(session, record_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", record_id=record_id, update_fields=list(kwargs.keys()))
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.script_crud._exists(session, record_id):
            self._handle_not_found("Script", record_id, "delete")

        try:
            result = self.script_crud._delete(session, record_id)
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
            results = self.script_crud._filter(session, filters={"name": name})
            if not results:
                return None
            return self._serialize_single_result(results[0], include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name", name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_content(self, session: Session, record_id: str) -> Dict[str, Any]:
        try:
            record = self.script_crud._get_by_id(session, record_id)
            if not record:
                self._handle_not_found("Script", record_id, "get_content")
            return {'content': record.content}
        except Exception as e:
            context = self._create_error_context("get_content", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def set_content(self, session: Session, record_id: str, content: str) -> Dict[str, Any]:
        try:
            result = self.script_crud._update(session, record_id, **{'content': content})
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("set_content")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_test_stats(self, session: Session, record_id: str, test_status: str, test_coverage: int, last_test_run_at, test_results: Dict[str, Any]) -> Dict[str, Any]:
        if not self.script_crud._exists(session, record_id):
            self._handle_not_found("Script", record_id, "update_test_stats")
        try:
            self.script_crud._update_test_stats(session, record_id, test_status, test_coverage, last_test_run_at, test_results)
            return {"updated": True, "script_id": record_id, "operation": "test_stats_update"}
        except Exception as e:
            context = self._create_error_context("update_test_stats", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update_performance_stats(self, session: Session, record_id: str, avg_execution_time: float, min_execution_time: float, max_execution_time: float, test_results: Dict[str, Any], success_rate: float, total_executions: int) -> Dict[str, Any]:
        if not self.script_crud._exists(session, record_id):
            self._handle_not_found("Script", record_id, "update_performance_stats")
        try:
            self.script_crud._update_performance_metrics(session, record_id, avg_execution_time, min_execution_time, max_execution_time, test_results, success_rate, total_executions)
            return {"updated": True, "script_id": record_id, "operation": "performance_stats_update"}
        except Exception as e:
            context = self._create_error_context("update_performance_stats", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_test_stats(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.script_crud._exists(session, record_id):
            self._handle_not_found("Script", record_id, "get_test_stats")

        try:
            return self.script_crud._get_test_stats(session, record_id)
        except Exception as e:
            context = self._create_error_context("get_test_stats", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_performance_stats(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.script_crud._exists(session, record_id):
            self._handle_not_found("Script", record_id, "get_performance_stats")
            
        try:
            return self.script_crud._get_performance_metrics(session, record_id)
        except Exception as e:
            context = self._create_error_context("get_performance_stats", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e
