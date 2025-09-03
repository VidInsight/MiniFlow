from miniflow.database.models import Script, ScriptTestStatus
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class ScriptCRUD(BaseCRUD[Script]):
    def __init__(self):
        super().__init__(Script)

    def _create_with_validation(self, session, name: str, content: str, **kwargs):
        if not name or not name.strip():
            raise ValidationError("Script name cannot be empty", severity=ErrorSeverity.MEDIUM)

        if not content or not content.strip():
            raise ValidationError("Script content cannot be empty", severity=ErrorSeverity.MEDIUM)

        name = name.strip().upper()
        existing_record = self._filter(session, filters={"name": name})
        if existing_record:
            raise ValidationError(f"Script by '{name}' already exists", severity=ErrorSeverity.MEDIUM)

        return self._create(session, name=name, content=content, **kwargs)

    def update_test_stats(self, session, record_id, test_status, test_coverage, last_test_run_at, test_results):
        payload = {
            'test_status': test_status,
            'test_coverage': test_coverage,
            'last_test_run_at': last_test_run_at,
            'test_results': test_results
        }
        return self._update(session, record_id, **payload)

    def update_performance_metrics(self, session, record_id, avg_execution_time, min_execution_time, max_execution_time, test_results, success_rate, total_executions):
        payload = {
            'avg_execution_time': avg_execution_time,
            'min_execution_time': min_execution_time,
            'max_execution_time': max_execution_time,
            'test_results': test_results,
            'success_rate': success_rate,
            'total_executions': total_executions
        }
        return self._update(session, record_id, **payload)

    def get_test_stats(self, session, record_id):
        record = self._get_by_id(session, record_id)
        return {
            'test_status': record.test_status,
            'test_coverage': record.test_coverage,
            'last_test_run_at': record.last_test_run_at,
            'test_results': record.test_results
        }

    def get_performance_metrics(self, session, record_id):
        record = self._get_by_id(session, record_id)
        return {
            'avg_execution_time': record.avg_execution_time,
            'min_execution_time': record.min_execution_time,
            'max_execution_time': record.max_execution_time,
            'test_results': record.test_results,
            'success_rate': record.success_rate,
            'total_executions': record.total_executions
        }