from miniflow.database.models import FileUpload
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, ErrorSeverity


class FileUploadCRUD(BaseCRUD[FileUpload]):
    def __init__(self):
        super().__init__(FileUpload)

    def _create(self, session, **kwargs):
        # Extract required parameters
        name = kwargs.get('name')
        file_path = kwargs.get('file_path')
        file_size = kwargs.get('file_size')

        # Validate required fields
        if not name or not name.strip():
            raise ValidationError("File name cannot be empty", severity=ErrorSeverity.MEDIUM)

        if not file_path or not file_path.strip():
            raise ValidationError("File path cannot be empty", severity=ErrorSeverity.MEDIUM)

        if file_size is None or file_size < 0:
            raise ValidationError("File size cannot be negative or None", severity=ErrorSeverity.MEDIUM)

        # Normalize name and check for duplicates
        normalized_name = name.strip().upper()
        existing_record = self._filter(session, filters={"name": normalized_name})
        if existing_record:
            raise ValidationError(f"File '{normalized_name}' already exists", severity=ErrorSeverity.MEDIUM)

        # Update kwargs with normalized name
        kwargs['name'] = normalized_name

        return super()._create(session, **kwargs)