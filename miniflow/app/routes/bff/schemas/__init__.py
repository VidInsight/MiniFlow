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

from .workflow_bff_schemas import (
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowResponse,
    WorkflowDeleteResponse
)
from .node_bff_schemas import (
    NodeCreateRequest,
    NodeUpdateRequest,
    NodeResponse,
    NodeDeleteResponse
)
from .edge_bff_schemas import (
    EdgeCreateRequest,
    EdgeUpdateRequest,
    EdgeResponse,
    EdgeDeleteResponse
)
from .execution_bff_schemas import (
    ExecutionResponse,
    ExecutionListResponse,
    ExecutionStatus
)
from .execution_input_bff_schemas import (
    ExecutionInputResponse,
    ExecutionInputListResponse
)
from .execution_output_bff_schemas import (
    ExecutionOutputResponse,
    ExecutionOutputListResponse,
    ExecutionOutputStatus
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
    # Workflows
    'WorkflowCreateRequest',
    'WorkflowUpdateRequest',
    'WorkflowResponse',
    'WorkflowDeleteResponse',
    # Nodes
    'NodeCreateRequest',
    'NodeUpdateRequest',
    'NodeResponse',
    'NodeDeleteResponse',
    # Edges
    'EdgeCreateRequest',
    'EdgeUpdateRequest',
    'EdgeResponse',
    'EdgeDeleteResponse',
    # Executions
    'ExecutionResponse',
    'ExecutionListResponse', 
    'ExecutionStatus',
    # Execution Inputs
    'ExecutionInputResponse',
    'ExecutionInputListResponse',
    # Execution Outputs
    'ExecutionOutputResponse',
    'ExecutionOutputListResponse',
    'ExecutionOutputStatus',
    # TODO: Add other schemas when files are created
]