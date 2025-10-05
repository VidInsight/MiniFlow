import os
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext
import miniflow.database.validators as validators

from ..models import Script
from .base_crud import BaseCRUD


class ScriptCRUD(BaseCRUD[Script]):
    def __init__(self):
        super().__init__(Script)
        self.model_fields = {column.name for column in Script.__table__.columns}
        self.required_fields = {'name', 'category', 'file_extension', 'file_path', 'content', 'input_schema', 'output_schema'}
        self.protected_fields = {'category', 'subcategory', 'file_extension', 'file_path', 'file_size'}

    def _create(self, session: Session, **kwargs):
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)

        name = kwargs.get('name')
        kwargs['name'] = validators._validate_name(name)

        category = kwargs.get('category')
        kwargs['category'] = validators._validate_name(category)

        if kwargs.get('subcategory'):
            subcategory = kwargs.get('subcategory')
            kwargs['subcategory'] = validators._validate_name(subcategory)

        file_extension = kwargs.get('file_extension')
        kwargs['file_extension'] = validators._validate_file_extension(file_extension, type='script')

        file_path = kwargs.get('file_path')
        validators._validate_file_path(file_path)

        input_schema = kwargs.get('input_schema')
        validators._validate_input_schema(input_schema)

        output_schema = kwargs.get('output_schema')
        validators._validate_output_schema(output_schema)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        script =  super()._create(session, **kwargs)
        return script

    def _update(self, session: Session, record_id: str, **kwargs):
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        if kwargs.get('name'):
            name = kwargs.get('name')
            kwargs['name'] = validators._validate_name(name)

        if kwargs.get('input_schema'):
            input_schema = kwargs.get('input_schema')
            validators._validate_input_schema(input_schema)

        if kwargs.get('output_schema'):
            output_schema = kwargs.get('output_schema')
            validators._validate_output_schema(output_schema)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        script = super()._update(session, record_id, **kwargs)
        return script

    def _update_test_stats(self, session: Session, record_id: str, **kwargs):
        """Update test statistics for a script."""
        test_stats = ['test_status', 'test_coverage', 'last_test_run_at', 'test_results', 'is_dangerous']

        script = super()._get_by_id(session, record_id)
        if not script:
            context = ErrorContext(operation='update_test_stats', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        # Update only the fields that are provided
        for field in test_stats:
            if field in kwargs:
                setattr(script, field, kwargs[field])
        
        if 'last_test_run_at' not in kwargs:
            script.last_test_run_at = datetime.now(timezone.utc)

        session.add(script)
        session.flush()

        return script

    def _get_test_stats(self, session: Session, record_id: str):
        """Get test statistics for a script."""
        script = super()._get_by_id(session, record_id)
        if not script:
            context = ErrorContext(operation='get_test_stats', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        return {
            'test_status': script.test_status,
            'test_coverage': script.test_coverage,
            'last_test_run_at': script.last_test_run_at,
            'test_results': script.test_results
        }

    def _update_performance_stats(self, session: Session, record_id: str, **kwargs):
        """Update performance statistics for a script."""
        performance_stats = ['avg_execution_time', 'min_execution_time', 'max_execution_time', 'success_rate', 'total_executions']

        script = super()._get_by_id(session, record_id)
        if not script:
            context = ErrorContext(operation='update_performance_stats', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

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
            context = ErrorContext(operation='get_performance_stats', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        return {
            'avg_execution_time': script.avg_execution_time,
            'min_execution_time': script.min_execution_time,
            'max_execution_time': script.max_execution_time,
            'success_rate': script.success_rate,
            'total_executions': script.total_executions
        }

    def _update_security_stats(self, session: Session, record_id: str, **kwargs):
        """Update security statistics for a script."""
        security_stats = ['is_approved', 'approved_by', 'approved_at', 'is_dangerous']

        script = super()._get_by_id(session, record_id)
        if not script:
            context = ErrorContext(operation='update_security_stats', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        # Update only the fields that are provided
        for field in security_stats:
            if field in kwargs:
                setattr(script, field, kwargs[field])
        
        # Automatically set approved_at if is_approved is True and approved_at not provided
        if kwargs.get('is_approved') is True and 'approved_at' not in kwargs:
            script.approved_at = datetime.now(timezone.utc)

        session.add(script)
        session.flush()

        return script

    def _get_security_stats(self, session: Session, record_id: str):
        """Get security statistics for a script."""
        script = super()._get_by_id(session, record_id)
        if not script:
            context = ErrorContext(operation='get_security_stats', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        return {
            'is_approved': script.is_approved,
            'approved_by': script.approved_by,
            'approved_at': script.approved_at,
            'is_dangerous': script.is_dangerous
        }

    def _approve(self, session: Session, record_id: str, approved_by: str):
        """Approve script for production use."""
        from miniflow.database.enums import ScriptTestStatus

        # Validate approved_by user ID
        validators._validate_id(approved_by)

        script = super()._get_by_id(session, record_id)
        if not script:
            context = ErrorContext(operation='approve', component=self.model_name, additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)
        
        # Validate script has been tested
        if script.test_status == ScriptTestStatus.UNTESTED:
            context = ErrorContext(operation='approve', component=self.model_name, additional_info={'id': record_id, 'test_status': script.test_status.value})
            raise ValidationError("Cannot approve untested script. Run tests first.", severity=ErrorSeverity.HIGH, context=context)
        
        # Validate script tests passed
        if script.test_status == ScriptTestStatus.FAILED:
            context = ErrorContext(operation='approve', component=self.model_name,additional_info={'id': record_id, 'test_status': script.test_status.value})
            raise ValidationError("Cannot approve script with failed tests", severity=ErrorSeverity.HIGH, context=context)
        
        # Validate script is not flagged as dangerous
        if script.is_dangerous:
            context = ErrorContext(operation='approve', component=self.model_name,additional_info={'id': record_id, 'is_dangerous': True})
            raise ValidationError("Cannot approve script flagged as dangerous. Run security scan first.", severity=ErrorSeverity.CRITICAL, context=context)
        
        # Approve the script
        script.is_approved = True
        script.approved_by = approved_by
        script.approved_at = datetime.now(timezone.utc)
        
        session.add(script)
        session.flush()
        
        return script

    def _validate_script_existence(self, session: Session, record_id: str) -> bool:
        """Validate that script record and physical file both exist."""
        script_record = super()._get_by_id(session, record_id)
        if not script_record:
            context = ErrorContext(operation="script_existence_check",component=self.model_name,additional_info={'id': record_id})
            raise ValidationError(f"Script with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        # Check if physical file exists
        if not os.path.isfile(script_record.file_path):
            return False
        return True