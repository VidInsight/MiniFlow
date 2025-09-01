"""
BFF Routes Module

API route handlers for BFF endpoints.
"""

from .envar_bff_routes import router as environment_variables_router
from .fileupload_bff_routes import router as fileupload_router
from .script_bff_routes import router as script_router
# from .credential_routes import router as credential_router  # TODO: File doesn't exist yet

__all__ = [
    'environment_variables_router',
    'fileupload_router',
    'script_router',
    # 'credential_router'  # TODO: Add when file is created
]
