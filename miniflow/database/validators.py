import os
import re
import json
from urllib.parse import urlparse

from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext

ALLOWED_FILE_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'csv', 'xml', 'yaml', 'yml', 'toml'}
ALLOWED_SCRIPT_EXTENSIONS = {'py'}

def validate_record_id(record_id: str, component:str) -> str:
    """Validate ID format (e.g., 'WF-ABC123DEF456')."""
    if not record_id or not isinstance(record_id, str):
        context = ErrorContext(operation="validate_record_id", component=component, additional_info={"id": record_id})
        raise ValidationError("Invalid ID provided", context=context, severity=ErrorSeverity.MEDIUM)
    
    record_id = record_id.strip()
    
    # Check ID format: PREFIX-ALPHANUMERIC (e.g., WF-ABC123, SC-XYZ789)
    if not re.match(r'^[A-Z]{2}-[A-Z0-9]{17}$', record_id):
        context = ErrorContext(operation="get_by_id", component=component, additional_info={"id": record_id})
        raise ValidationError("ID must follow the format: XX-XXXXXXXXXXXXXXXXX (2 letter prefix, dash, 17 alphanumeric characters)", context=context, severity=ErrorSeverity.MEDIUM)

    return record_id

def validate_name(name: str, component: str) -> str:
    if not name or not isinstance(name, str):
        context = ErrorContext(operation="validate_name", component=component, additional_info={"name": name})
        raise ValidationError("Invalid name provided", context=context, severity=ErrorSeverity.MEDIUM)

    name = name.strip()

    if not name:
        raise ValueError("Name cannot be empty")
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters long")
    if len(name) > 100:
        raise ValueError("Name cannot exceed 100 characters")
    if not re.match(r'^[A-Za-z0-9_-]+$', name):
        raise ValueError("Name can only contain letters, numbers, underscores, and hyphens")

    return name

def validate_variable_type(value, variable_type: str, component: str):
    try:
        if variable_type == "STRING":
            if not isinstance(value, str):
                raise TypeError("Value must be a string")
            elif len(value) == 0:
                raise ValueError("Value must not be empty")

        elif variable_type == "INTEGER":
            if not isinstance(value, int):
                raise TypeError("Value must be an integer")

        elif variable_type == "FLOAT":
            if not isinstance(value, float):
                raise TypeError("Value must be a float")

        elif variable_type == "BOOLEAN":
            if not isinstance(value, bool):
                raise TypeError("Value must be a boolean")

        elif variable_type == "JSON":
            if isinstance(value, str):
                json.loads(value)
            elif not isinstance(value, (dict, list)):
                raise TypeError("Value must be valid JSON (dict, list or JSON string)")

        elif variable_type == "SECRET":
            if not isinstance(value, str) or len(value.strip()) == 0:
                raise ValueError("Secret cannot be empty")

        elif variable_type == "FILE_PATH":
            if not isinstance(value, str):
                raise TypeError("File path must be a string")
            if not os.path.exists(value):
                raise FileNotFoundError(f"File path does not exist: {value}")

        elif variable_type == "URL":
            if not isinstance(value, str):
                raise TypeError("URL must be a string")
            parsed = urlparse(value)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError(f"Invalid URL format: {value}")

        else:
            raise ValueError(f"Unsupported variable type: {variable_type}")

    except (TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        context = ErrorContext(operation="validate_variable_type", component=component, additional_info={"value": value})
        raise ValidationError(str(e), severity=ErrorSeverity.MEDIUM, context=context) from e

def validate_file_name(filename: str, component) -> str:
    if not filename or not isinstance(filename, str):
        context = ErrorContext(operation="validate_file_name", component=component, additional_info={"filename": filename})
        raise ValidationError("Invalid name provided", context=context, severity=ErrorSeverity.MEDIUM)

    filename = filename.strip()

    try:
        if not filename:
            raise ValueError("Filename cannot be empty")
        if len(filename) < 3:
            raise ValueError("Filename must be at least 3 characters long")
        if len(filename) > 245:
            raise ValueError("Filename cannot exceed 245 characters (without extension)")
        if not re.match(r'^[A-Za-z0-9._-]+$', filename):
            raise ValueError("Filename can only contain letters, numbers, dots, underscores, and hyphens")
    except (TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        context = ErrorContext(operation="validate_file_name", component=component, additional_info={"filename": filename})
        raise ValidationError(str(e), severity=ErrorSeverity.MEDIUM, context=context) from e

    return filename

def validate_file_extension(file_extension: str, type: str, component: str) -> str:
    if not isinstance(file_extension, str):
        raise ValueError("File extension must be a string")

    file_extension = file_extension.strip().lstrip('.').lower()

    try:
        if not file_extension:
            raise ValueError("File extension cannot be empty")
        if len(file_extension) < 1:
            raise ValueError("File extension must be at least 1 character long")
        if len(file_extension) > 10:
            raise ValueError("File extension cannot exceed 10 characters")
        if not re.match(r'^[A-Za-z0-9]+$', file_extension):
            raise ValueError("File extension can only contain letters and numbers")

        if type == 'script':
            if file_extension not in ALLOWED_SCRIPT_EXTENSIONS:
                raise ValueError("File extension must be one of {}".format(ALLOWED_SCRIPT_EXTENSIONS))
        elif type == 'file':
            if file_extension not in ALLOWED_FILE_EXTENSIONS:
                raise ValueError("File extension must be one of {}".format(ALLOWED_FILE_EXTENSIONS))
        else:
            raise ValueError("Unsupported file extension: {}".format(file_extension))

    except (TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        context = ErrorContext(operation="_validate_file_extension", component=component, additional_info={"file_extension": file_extension})
        raise ValidationError(str(e), severity=ErrorSeverity.MEDIUM, context=context) from e

    return file_extension

def validate_file_path(file_path: str, component: str) -> str:
    try:
        if not isinstance(file_path, str):
            raise ValueError("File path must be a string")

        file_path = file_path.strip()
        if not file_path:
            raise ValueError("File path cannot be empty")

        # Path'i ayır
        parts = file_path.split(os.sep)

        if len(parts) < 2:
            raise ValueError("File path must include at least one folder and the file name")

        # Dosya adı ve uzantıyı ayır
        *folders, file_name_ext = parts

        # Klasörleri kontrol et (boş string'leri atla - absolute path'ler için)
        for folder in folders:
            if folder and not re.match(r'^[A-Za-z0-9._-]+$', folder):
                raise ValueError(f"Invalid folder name: {folder}")

        # Dosya adı ve uzantıyı ayır
        if '.' not in file_name_ext:
            raise ValueError("File name must include an extension")
    except (TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        context = ErrorContext(operation="validate_file_path", component=component, additional_info={"file_path": file_path})
        raise ValidationError(str(e), severity=ErrorSeverity.MEDIUM, context=context) from e

def validate_input_schema(schema, component: str):
    try:
        if schema is None:
            return {}

        if not isinstance(schema, dict):
            raise TypeError("Input schema must be a dictionary")
    except (TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        context = ErrorContext(operation="validate_input_schema", component=component, additional_info={"schema": schema})
        raise ValidationError(str(e), severity=ErrorSeverity.MEDIUM, context=context) from e

    return schema

def validate_output_schema(schema, component: str):
    try:
        if schema is None:
            return {}

        if not isinstance(schema, dict):
            raise TypeError("Output schema must be a dictionary")
    except (TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        context = ErrorContext(operation="validate_output_schema", component=component, additional_info={"schema": schema})
        raise ValidationError(str(e), severity=ErrorSeverity.MEDIUM, context=context) from e

    return schema