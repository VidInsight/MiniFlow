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
from miniflow.app.routes.bff.routes.node_bff_routes import router as node_router
from miniflow.app.routes.bff.routes.edge_bff_routes import router as edge_router
from miniflow.app.routes.bff.routes.execution_bff_routes import router as execution_router
from miniflow.app.routes.bff.routes.execution_input_bff_routes import router as execution_input_router
from miniflow.app.routes.bff.routes.execution_output_bff_routes import router as execution_output_router
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

# Node routes - nodes endpoints
bff_router.include_router(
    node_router,
    prefix="/nodes",  # Nodes prefix
    tags=["BFF - Nodes"]
)

# Edge routes - edges endpoints
bff_router.include_router(
    edge_router,
    prefix="/edges",  # Edges prefix
    tags=["BFF - Edges"]
)

# Execution routes - executions endpoints (READ-ONLY)
bff_router.include_router(
    execution_router,
    prefix="/executions",  # Executions prefix
    tags=["BFF - Executions"]
)

# Execution Input routes - execution-inputs endpoints (READ-ONLY)
bff_router.include_router(
    execution_input_router,
    prefix="/execution-inputs",  # Execution Inputs prefix
    tags=["BFF - Execution Inputs"]
)

# Execution Output routes - execution-outputs endpoints (READ-ONLY)
bff_router.include_router(
    execution_output_router,
    prefix="/execution-outputs",  # Execution Outputs prefix
    tags=["BFF - Execution Outputs"]
)
