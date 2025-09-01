"""
BFF Schemas Module

Pydantic schemas for BFF (Back for Frontend) endpoints.
"""

from .envar_bff_schemes import (
    EnvironmentVariableCreateRequest,
    EnvironmentVariableUpdateRequest,
    EnvironmentVariableResponse,
    EnvironmentVariableDeleteResponse
)

from .fileupload_bff_schemas import (
    FileUploadCreateRequest,
    FileUploadResponse,
    FileUploadDeleteResponse
)

from .scripts_bff_schemas import (
    ScriptCreateRequest,
    ScriptResponse,
    ScriptDeleteResponse
)

# TODO: Add other schema imports when files are created
# from .credentials import (...)

__all__ = [
    # Environment Variables  
    'EnvironmentVariableCreateRequest',
    'EnvironmentVariableUpdateRequest',
    'EnvironmentVariableResponse',
    'EnvironmentVariableDeleteResponse',
    # File Uploads
    'FileUploadCreateRequest',
    'FileUploadResponse',
    'FileUploadDeleteResponse',
    # Scripts
    'ScriptCreateRequest',
    'ScriptResponse',
    'ScriptDeleteResponse',
    # TODO: Add other schemas when files are created
]