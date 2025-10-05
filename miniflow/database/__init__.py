"""
MiniFlow Database Module

Provides database models, CRUD operations, orchestration layer, and utilities.
"""

# Models and Enums
from .models import (
    BaseModel,
    User,
    Permission,
    ApiKey,
    AuthSession,
    Workflow,
    Node,
    Edge,
    Trigger,
    Script,
    FileUpload,
    EnvironmentVariable,
    Execution,
    ExecutionInput,
    ExecutionOutput,
    UserWorkflowRole,
    UserEnvarRole,
    UserFileRole,
    UserExecutionRole,
)

from .enums import (
    WorkflowStatus,
    ScriptStatus,
    ScriptTestStatus,
    ConditionType,
    ExecutionStatus,
    ExecutionOutputStatus,
    VariableScope,
    VariableType,
    TriggerType,
    Roles,
    Plans,
)

# Database Engine and Config
from .engine import DatabaseEngine
from .config import DatabaseConfig

# Validators
from . import validators

# CRUD Layer
from .crud import (
    # Base
    BaseCRUD,
    BaseJunctionCRUD,
    
    # User & Auth
    UserCRUD,
    PermissionCRUD,
    ApiKeyCRUD,
    AuthSessionCRUD,
    
    # Workflow
    WorkflowCRUD,
    NodeCRUD,
    EdgeCRUD,
    TriggerCRUD,
    
    # Resources
    ScriptCRUD,
    FileUploadCRUD,
    EnvironmentVariableCRUD,
    
    # Execution
    ExecutionCRUD,
    ExecutionInputCRUD,
    ExecutionOutputCRUD,
    
    # Junction Tables
    UserWorkflowRoleCRUD,
    UserEnvarRoleCRUD,
    UserFileRoleCRUD,
    UserExecutionRoleCRUD,
)

# Orchestration Layer
from .orchestration import (
    DatabaseOrchestrator,
    BaseOrchestrator,
    WorkflowOrchestrator,
    NodeOrchestrator,
    EdgeOrchestrator,
    TriggerOrchestrator,
    ScriptOrchestrator,
    FileUploadOrchestrator,
    EnvironmentVariableOrchestrator,
    ExecutionOrchestrator,
)


__all__ = [
    # Models
    'BaseModel',
    'User',
    'Permission',
    'ApiKey',
    'AuthSession',
    'Workflow',
    'Node',
    'Edge',
    'Trigger',
    'Script',
    'FileUpload',
    'EnvironmentVariable',
    'Execution',
    'ExecutionInput',
    'ExecutionOutput',
    'UserWorkflowRole',
    'UserEnvarRole',
    'UserFileRole',
    'UserExecutionRole',
    
    # Enums
    'WorkflowStatus',
    'ScriptStatus',
    'ScriptTestStatus',
    'ConditionType',
    'ExecutionStatus',
    'ExecutionOutputStatus',
    'VariableScope',
    'VariableType',
    'TriggerType',
    'Roles',
    'Plans',
    
    # Engine & Config
    'DatabaseEngine',
    'DatabaseConfig',
    
    # Validators
    'validators',
    
    # CRUD
    'BaseCRUD',
    'BaseJunctionCRUD',
    'UserCRUD',
    'PermissionCRUD',
    'ApiKeyCRUD',
    'AuthSessionCRUD',
    'WorkflowCRUD',
    'NodeCRUD',
    'EdgeCRUD',
    'TriggerCRUD',
    'ScriptCRUD',
    'FileUploadCRUD',
    'EnvironmentVariableCRUD',
    'ExecutionCRUD',
    'ExecutionInputCRUD',
    'ExecutionOutputCRUD',
    'UserWorkflowRoleCRUD',
    'UserEnvarRoleCRUD',
    'UserFileRoleCRUD',
    'UserExecutionRoleCRUD',
    
    # Orchestration
    'DatabaseOrchestrator',
    'BaseOrchestrator',
    'WorkflowOrchestrator',
    'NodeOrchestrator',
    'EdgeOrchestrator',
    'TriggerOrchestrator',
    'ScriptOrchestrator',
    'FileUploadOrchestrator',
    'EnvironmentVariableOrchestrator',
    'ExecutionOrchestrator',
]

