from miniflow.database.models import EnvironmentVariable
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class EnvironmentVariableCRUD(BaseCRUD[EnvironmentVariable]):
    def __init__(self):
        super().__init__(EnvironmentVariable)

    def _create_with_validation(self, session, name: str, value: str, **kwargs):
        if not name or not name.strip():
            raise ValidationError("Environment variable name cannot be empty", severity=ErrorSeverity.HIGH)

        if not value or not value.strip():
            raise ValidationError("Environment variable value cannot be empty", severity=ErrorSeverity.HIGH)

        name = name.strip().upper()
        existing_record = self._filter(session, filters={"name": name})
        if existing_record:
            raise ValidationError(f"Environment variable '{name}' already exists", severity=ErrorSeverity.HIGH)

        return self._create(session, name=name, value=value, **kwargs)

    def _update_with_validation(self, session, record_id: str, name: str, value: str, **kwargs):
        if not name or not name.strip():
            raise ValidationError("Environment variable name cannot be empty", severity=ErrorSeverity.HIGH)

        if not value or not value.strip():
            raise ValidationError("Environment variable value cannot be empty", severity=ErrorSeverity.HIGH)

        name = name.strip().upper()
        existing_record = self._filter(session, filters={"name": name})
        if existing_record and existing_record[0].id != record_id:
            raise ValidationError(f"Environment variable '{name}' already exists", severity=ErrorSeverity.HIGH)

        return self._update(session, record_id, name=name, value=value, **kwargs)