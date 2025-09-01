from sqlalchemy.orm import Session
from datetime import datetime, timezone

from miniflow.database.models import EnvironmentVariable, VariableScope, VariableType
from miniflow.core.exceptions import (ValidationError, DatabaseQueryError, ErrorSeverity)
from miniflow.database.crud.base_crud import BaseCRUD


class EnvironmentVariableCRUD(BaseCRUD[EnvironmentVariable]):
    """Environment Variable specific CRUD operations with encryption support"""

    def __init__(self):
        super().__init__(EnvironmentVariable)

    def create_environment_variable(self, session: Session, name: str, value: str, **kwargs) -> EnvironmentVariable:
        """Create new environment variable with validation"""
        # Key Validation
        if not name or not name.strip():
            context = self._create_error_context("create_record", name=name)
            raise ValidationError("Environment variable name cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        # Value Validation
        if not value or not value.strip():
            context = self._create_error_context("create_record", value=value)
            raise ValidationError("Environment variable value cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        name = name.strip().upper()
        record = self.find_by_name(session, name)

        # If Name/Key already exists
        if record:
            context = self._create_error_context("create_record", name=name)
            raise ValidationError(f"Environment variable '{name}' already exists", context=context, severity=ErrorSeverity.MEDIUM)

        # Prepare data
        record_payload = {
            'name': name,
            'value': value,
            'variable_type': kwargs.get('variable_type', VariableType.STRING),
            'scope': kwargs.get('scope', VariableScope.GLOBAL),
            'description': kwargs.get('description'),
        }

        return self.create(session, **record_payload)

    def update_environment_variable(self, session: Session, record_id: str, **kwargs) -> EnvironmentVariable:
        """Update environment variable"""
        if not record_id or not record_id.strip():
            context = self._create_error_context("update_record", record_id=record_id)
            raise ValidationError("Record ID cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        # Validate update data
        if not kwargs:
            context = self._create_error_context("update_record", record_id=record_id)
            raise ValidationError("No update data provided", context=context, severity=ErrorSeverity.MEDIUM)

        record = self.find_by_id(session, record_id)
        if not record:
            context = self._create_error_context("update_record", record_id=record_id)
            raise DatabaseQueryError(f"Environment variable '{record_id}' not found", context=context, severity=ErrorSeverity.HIGH)

        return self.update(session, record_id, **kwargs)

    def delete_environment_variable(self, session: Session, record_id: str) -> EnvironmentVariable:
        """Delete environment variable"""
        if not record_id or not record_id.strip():
            context = self._create_error_context("delete_record", record_id=record_id)
            raise ValidationError("Record ID cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        record = self.find_by_id(session, record_id)
        if not record:
            context = self._create_error_context("delete_record", record_id=record_id)
            raise DatabaseQueryError(f"Environment variable '{record_id}' not found", context=context, severity=ErrorSeverity.HIGH)

        return self.delete(session, record_id)