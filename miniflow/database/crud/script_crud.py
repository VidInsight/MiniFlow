import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext
import miniflow.database.validators as validators

from ..models import Script
from ..enums import ScriptTestStatus
from .base_crud import BaseCRUD


class ScriptCRUD(BaseCRUD[Script]):
    def __init__(self):
        super().__init__(Script)
        self.model_fields = {column.name for column in Script.__table__.columns}
        self.required_fields = {'name', 'category', 'file_extension', 'file_path', 'content', 'input_schema', 'output_schema'}
        self.protected_fields = {'category', 'subcategory', 'file_extension', 'file_path', 'file_size'}

    # ============================================================================================ CRUD OPERATIONS =====
    def _create(self, session: Session, **kwargs):
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)

        name = kwargs.get('name')
        kwargs['name'] = validators.validate_name(name, component=self.model_name)

        category = kwargs.get('category')
        kwargs['category'] = validators.validate_name(category, component=self.model_name)

        if kwargs.get('subcategory'):
            subcategory = kwargs.get('subcategory')
            kwargs['subcategory'] = validators.validate_name(subcategory, component=self.model_name)

        file_extension = kwargs.get('file_extension')
        kwargs['file_extension'] = validators.validate_file_extension(file_extension, type='script')

        file_path = kwargs.get('file_path')
        validators.validate_file_path(file_path)

        input_schema = kwargs.get('input_schema')
        validators.validate_input_schema(input_schema)

        output_schema = kwargs.get('output_schema')
        validators.validate_output_schema(output_schema)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        script =  super()._create(session, **kwargs)
        return script

    def _update(self, session: Session, record_id: str, **kwargs):
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        if kwargs.get('name'):
            name = kwargs.get('name')
            kwargs['name'] = validators.validate_name(name)

        if kwargs.get('input_schema'):
            input_schema = kwargs.get('input_schema')
            validators.validate_input_schema(input_schema)

        if kwargs.get('output_schema'):
            output_schema = kwargs.get('output_schema')
            validators.validate_output_schema(output_schema)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        script = super()._update(session, record_id, **kwargs)
        return script

    # =========================================================================================== STATS OPERATIONS =====
    def _update_test_stats(self, session: Session, record_id: str, **kwargs):
        """Update test statistics for a script."""
        test_stats = ['test_status', 'test_coverage', 'last_test_run_at', 'test_results', 'is_dangerous']

        script = super()._get_by_id(session, record_id)
        if not script:
            self._raise_not_found_error(operation="_update_execution_durations" , record_id=record_id)

        for field in test_stats:
            if field in kwargs:
                setattr(script, field, kwargs[field])

        session.add(script)
        session.flush()

        return script

    def _get_test_stats(self, session: Session, record_id: str):
        """Get test statistics for a script."""
        script = super()._get_by_id(session, record_id)
        if not script:
            self._raise_not_found_error(operation="_update_execution_durations" , record_id=record_id)

        return {
            'test_status': script.test_status,
            'test_coverage': script.test_coverage,
            'last_test_run_at': script.last_test_run_at,
            'test_results': script.test_results
        }

    def _update_performance_stats(self, session: Session, record_id: str, **kwargs):
        """Update performance statistics for a script."""
        performance_stats = ['avg_execution_time', 'min_execution_time', 'max_execution_time', 'total_executions']

        script = super()._get_by_id(session, record_id)
        if not script:
            self._raise_not_found_error(operation="_update_execution_durations" , record_id=record_id)

        # Update only the fields that are provided
        for field in performance_stats:
            if field in kwargs:
                setattr(script, field, kwargs[field])

        session.add(script)
        session.flush()

        return script

    def _get_performance_stats(self, session: Session, record_id: str):
        """Get performance statistics for a script."""
        script = super()._get_by_id(session, record_id)
        if not script:
            self._raise_not_found_error(operation="_update_execution_durations" , record_id=record_id)

        return {
            'avg_execution_time': script.avg_execution_time,
            'min_execution_time': script.min_execution_time,
            'max_execution_time': script.max_execution_time,
            'success_rate': script.success_rate,
            'total_executions': script.total_executions
        }

    def _approve(self, session: Session, record_id: str, approved_by: str):
        """Approve script for production use."""

        # Validate approved_by user ID
        record_id = validators.validate_record_id(record_id, component=self.model_name)
        approved_by = validators.validate_record_id(approved_by, component=self.model_name)

        script = super()._get_by_id(session, record_id)
        if not script:
            self._raise_not_found_error(operation="_update_execution_durations" , record_id=record_id)

        # Validate script has been tested
        if script.test_status == ScriptTestStatus.UNTESTED:
            context = ErrorContext(operation='approve', component=self.model_name,additional_info={'id': record_id, 'test_status': script.test_status.value})
            raise ValidationError("Cannot approve untested script. Run tests first.", severity=ErrorSeverity.HIGH,context=context)

        # Validate script tests passed
        if script.test_status == ScriptTestStatus.FAILED:
            context = ErrorContext(operation='approve', component=self.model_name, additional_info={'id': record_id, 'test_status': script.test_status.value})
            raise ValidationError("Cannot approve script with failed tests", severity=ErrorSeverity.HIGH, context=context)

        # Validate script is not flagged as dangerous
        if script.is_dangerous:
            context = ErrorContext(operation='approve', component=self.model_name, additional_info={'id': record_id, 'is_dangerous': True})
            raise ValidationError("Cannot approve script flagged as dangerous. Run security scan first.", severity=ErrorSeverity.CRITICAL, context=context)

        # Approve the script
        script.is_approved = True
        script.approved_by = approved_by
        script.approved_at = datetime.now(timezone.utc)

        session.add(script)
        session.flush()

        return script

    def _get_security_stats(self, session: Session, record_id: str):
        """Get security statistics for a script."""
        script = super()._get_by_id(session, record_id)
        if not script:
            self._raise_not_found_error(operation="_update_execution_durations" , record_id=record_id)

        return {
            'is_approved': script.is_approved,
            'approved_by': script.approved_by,
            'approved_at': script.approved_at,
            'is_dangerous': script.is_dangerous
        }