from miniflow.database.models import FileUpload
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class FileUploadCRUD(BaseCRUD[FileUpload]):
    def __init__(self):
        super().__init__(FileUpload)

    def _create_with_validation(self, session, name: str, file_path: str, file_size: int, **kwargs):
        if not name or not name.strip():
            raise ValidationError("File name cannot be empty", severity=ErrorSeverity.MEDIUM)

        if not file_path or not file_path.strip():
            raise ValidationError("File path cannot be empty", severity=ErrorSeverity.MEDIUM)

        if file_size < 0:
            raise ValidationError("File size cannot be negative", severity=ErrorSeverity.MEDIUM)

        name = name.strip().upper()
        existing_record = self._filter(session, filters={"name": name})
        if existing_record:
            raise ValidationError(f"File by '{name}' already exists", severity=ErrorSeverity.MEDIUM)

        return self._create(session, name=name, file_path=file_path, file_size=file_size, **kwargs)