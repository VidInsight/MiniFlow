from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import os
from pathlib import Path

from miniflow.database.models import Script, ScriptType
from miniflow.database.crud.base_crud import BaseCRUD
from miniflow.core.exceptions import ValidationError, DatabaseQueryError, ErrorContext, ErrorSeverity


class ScriptCRUD(BaseCRUD[Script]):
    """Script specific CRUD operations"""

    def __init__(self):
        super().__init__(Script)

    def create_script_record(self, session: Session, name: str, language: ScriptType, content: str, file_path: str, **kwargs) -> Script:
        """Create new script record with validation"""
        # Validate inputs
        if not name or not name.strip():
            context = self._create_error_context("create_script", name=name)
            raise ValidationError("Script name cannot be empty", context=context, severity=ErrorSeverity.MEDIUM)

        if not language:
            context = self._create_error_context("create_script", language=language)
            raise ValidationError("Script language cannot be empty",context=context, severity=ErrorSeverity.MEDIUM)

        if not content or not content.strip():
            context = self._create_error_context("create_script", content=content)
            raise ValidationError("Script content cannot be empty",context=context, severity=ErrorSeverity.MEDIUM)

        if not file_path or not file_path.strip():
            context = self._create_error_context("create_script", file_path=file_path)
            raise ValidationError("File path cannot be empty",context=context, severity=ErrorSeverity.MEDIUM)

        # Check if name already exists
        existing = self.find_by_name(session, name.strip())
        if existing:
            context = self._create_error_context("create_script", name=name)
            raise ValidationError(f"Script name '{name}' already exists",context=context, severity=ErrorSeverity.MEDIUM)

        # Get file extension from file path
        file_extension = os.path.splitext(file_path)[1]

        # Prepare data
        record_payload = {
            'name': name.strip(),
            'language': language,
            'content': content.strip(),
            'description': kwargs.get('description'),
            'version': kwargs.get('version', '1.0.0'),
            'category': kwargs.get('category', 'default'),
            'subcategory': kwargs.get('subcategory'),
            'file_extension': file_extension,
            'file_path': file_path.strip(),
            'file_size': len(content.encode('utf-8')),
            'required_packages': kwargs.get('required_packages', []),
            'input_schema': kwargs.get('input_schema', {}),
            'output_schema': kwargs.get('output_schema', {}),
            'test_input_params': kwargs.get('test_input_params', {}),
            'test_output_params': kwargs.get('test_output_params', {})
        }

        return self.create(session, **record_payload)


    def delete_script_record(self, session: Session, record_id: str) -> Script:
        """Delete script record"""
        if not record_id or not record_id.strip():
            context = self._create_error_context("delete_script", record_id=record_id)
            raise ValidationError("Record ID cannot be empty", context=context, severity=ErrorSeverity.HIGH)

        record = self.find_by_id(session, record_id)
        if not record:
            context = self._create_error_context("delete_script", record_id=record_id)
            raise DatabaseQueryError(f"Script '{record_id}' not found",context=context, severity=ErrorSeverity.HIGH)

        return self.delete(session, record_id)

