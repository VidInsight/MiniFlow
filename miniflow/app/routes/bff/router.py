"""
BFF Router
Back for Frontend - Frontend için API router
"""

from fastapi import APIRouter, Depends

from miniflow.app.core.dependencies import verify_bff_access
from miniflow.app.routes.bff.routes.envar_bff_routes import router as envvar_router
from miniflow.app.routes.bff.routes.fileupload_bff_routes import router as fileupload_router
from miniflow.app.routes.bff.routes.script_bff_routes import router as script_router
from miniflow.app.routes.bff.routes.workflow_bff_routes import router as workflow_router
# from miniflow.app.routes.bff.routes.credential_routes import router as credential_router  # Not implemented yet

# BFF Ana router - Frontend yetkilendirmesi ile
bff_router = APIRouter(dependencies=[Depends(verify_bff_access)])

# Environment Variables routes - envar endpoints
bff_router.include_router(
    envvar_router,
    prefix="/envar",  # Environment variables prefix
    tags=["BFF - Environment Variables"]
)

# File Upload routes - files endpoints
bff_router.include_router(
    fileupload_router,
    prefix="/files",  # File uploads prefix
    tags=["BFF - File Uploads"]
)

# Script routes - scripts endpoints
bff_router.include_router(
    script_router,
    prefix="/scripts",  # Scripts prefix
    tags=["BFF - Scripts"]
)

# Workflow routes - workflows endpoints
bff_router.include_router(
    workflow_router,
    prefix="/workflows",  # Workflows prefix
    tags=["BFF - Workflows"]
)
