from miniflow.database.models import Script, ScriptTestStatus
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class ScriptCRUD(BaseCRUD[Script]):
    def __init__(self):
        super().__init__(Script)

    def _update(self, session, record_id: str, **kwargs):
        
        # Define restricted fields that cannot be updated
        RESTRICTED_FIELDS = {
            'name', 'category', 'subcategory', 'file_path', 'file_size'
        }
        
        # Filter out restricted fields
        filtered_kwargs = {}
        restricted_attempts = []
        
        for field, value in kwargs.items():
            if field in RESTRICTED_FIELDS:
                restricted_attempts.append(field)
                self.logger.warning(f"Ignoring restricted field '{field}' in script update")
            else:
                filtered_kwargs[field] = value
        
        # Log restricted field attempts
        if restricted_attempts:
            context = self._create_error_context("update_with_validation", record_id=record_id, restricted_fields=restricted_attempts)
            self.logger.warning(f"Script update attempted on restricted fields: {restricted_attempts}")
        
        # Validate content if provided
        if 'content' in filtered_kwargs:
            content = filtered_kwargs['content']
            if not content or not content.strip():
                raise ValidationError("Script content cannot be empty", severity=ErrorSeverity.MEDIUM)
        
        # Validate version format if provided
        if 'version' in filtered_kwargs:
            version = filtered_kwargs['version']
            if not version or not version.strip():
                raise ValidationError("Script version cannot be empty", severity=ErrorSeverity.MEDIUM)
        
        # Validate required_packages format if provided
        if 'required_packages' in filtered_kwargs:
            packages = filtered_kwargs['required_packages']
            if packages is not None and not isinstance(packages, list):
                raise ValidationError("Required packages must be a list", severity=ErrorSeverity.MEDIUM)
        
        # Validate schemas if provided
        for schema_field in ['input_schema', 'output_schema']:
            if schema_field in filtered_kwargs:
                schema = filtered_kwargs[schema_field]
                if schema is not None and not isinstance(schema, dict):
                    raise ValidationError(f"{schema_field} must be a dictionary", severity=ErrorSeverity.MEDIUM)
        
        # Validate test params if provided
        for param_field in ['test_input_params', 'test_output_params']:
            if param_field in filtered_kwargs:
                params = filtered_kwargs[param_field]
                if params is not None and not isinstance(params, dict):
                    raise ValidationError(f"{param_field} must be a dictionary", severity=ErrorSeverity.MEDIUM)
        
        # Validate tags if provided
        if 'tags' in filtered_kwargs:
            tags = filtered_kwargs['tags']
            if tags is not None and not isinstance(tags, list):
                raise ValidationError("Tags must be a list", severity=ErrorSeverity.MEDIUM)
        
        # If no valid fields to update
        if not filtered_kwargs:
            raise ValidationError("No valid fields provided for update", severity=ErrorSeverity.MEDIUM)
        
        return super()._update(session, record_id, **filtered_kwargs)

    def _update_test_stats(self, session, record_id, test_status, test_coverage, last_test_run_at, test_results):
        payload = {
            'test_status': test_status,
            'test_coverage': test_coverage,
            'last_test_run_at': last_test_run_at,
            'test_results': test_results
        }
        return super()._update(session, record_id, **payload)

    def _update_performance_metrics(self, session, record_id, avg_execution_time, min_execution_time, max_execution_time, test_results, success_rate, total_executions):
        payload = {
            'avg_execution_time': avg_execution_time,
            'min_execution_time': min_execution_time,
            'max_execution_time': max_execution_time,
            'test_results': test_results,
            'success_rate': success_rate,
            'total_executions': total_executions
        }
        return super()._update(session, record_id, **payload)

    def _get_test_stats(self, session, record_id):
        record = self._get_by_id(session, record_id)
        return {
            'test_status': record.test_status,
            'test_coverage': record.test_coverage,
            'last_test_run_at': record.last_test_run_at,
            'test_results': record.test_results
        }

    def _get_performance_metrics(self, session, record_id):
        record = self._get_by_id(session, record_id)
        return {
            'avg_execution_time': record.avg_execution_time,
            'min_execution_time': record.min_execution_time,
            'max_execution_time': record.max_execution_time,
            'success_rate': record.success_rate,
            'total_executions': record.total_executions
        }