import os
from sqlalchemy.orm import Session

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext
import miniflow.database.validators as validators

from ..models import FileUpload
from .base_crud import BaseCRUD


class FileUploadCRUD(BaseCRUD[FileUpload]):
    def __init__(self):
        super().__init__(FileUpload)
        self.model_fields = {column.name for column in FileUpload.__table__.columns}
        self.required_fields = {'name', 'filename', 'file_extension', 'file_path'}
        self.protected_fields = {'filename', 'file_extension', 'file_path', 'file_size', 'mime_type', 'checksum'}

    def _create(self, session: Session, **kwargs):
        """Create a new file upload record with validation."""
        self._validate_required_fields_in_kwargs(self.required_fields, kwargs)

        name = kwargs.get('name')
        kwargs['name'] = validators._validate_name(name)

        file_name = kwargs.get('filename')
        kwargs['filename'] = validators._validate_file_name(file_name)

        file_extension = kwargs.get('file_extension')
        kwargs['file_extension'] = validators._validate_file_extension(file_extension)

        file_path = kwargs.get('file_path')
        validators._validate_file_path(file_path)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        file_upload =  super()._create(session, **kwargs)
        return file_upload

    def _update(self, session: Session, record_id: str, **kwargs):
        """Update file upload record with protected field restrictions."""
        self._validate_no_protected_fields(self.protected_fields, kwargs)

        if kwargs.get('name'):
            name = kwargs.get('name')
            kwargs['name'] = validators._validate_name(name)

        self._validate_no_extra_fields(self.model_fields, kwargs)
        file_upload = super()._update(session, record_id, **kwargs)
        return file_upload

    def _validate_file_existence(self, session: Session, record_id: str) -> bool:
        """Validate that file record and physical file both exist."""
        file_record = super()._get_by_id(session, record_id)
        if not file_record:
            context = ErrorContext(operation="file_existence_check",component=self.model_name,additional_info={'id': record_id})
            raise ValidationError(f"File with ID {record_id} does not exist", severity=ErrorSeverity.HIGH, context=context)

        # Check if physical file exists
        if not os.path.isfile(file_record.file_path):
            return False
        return True