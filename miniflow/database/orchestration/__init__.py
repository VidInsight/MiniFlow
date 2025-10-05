"""
Miniflow Database Orchestration Module

Provides high-level business logic and session management for database operations.
"""

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors,
    require_role,
    require_plan,
    ROLE_HIERARCHY,
    PLAN_HIERARCHY,
    PLAN_LIMITS
)
from .workflow_orchestrator import WorkflowOrchestrator
from .node_orchestrator import NodeOrchestrator
from .edge_orchestrator import EdgeOrchestrator
from .trigger_orchestrator import TriggerOrchestrator
from .script_orchestrator import ScriptOrchestrator
from .file_orchestrator import FileUploadOrchestrator
from .envar_orchestrator import EnvironmentVariableOrchestrator
from .execution_orchestrator import ExecutionOrchestrator
from .execution_input_orchestrator import ExecutionInputOrchestrator
from .execution_output_orchestrator import ExecutionOutputOrchestrator
from .scheduler_orchestrator import SchedulerOrchestrator
from .permission_orchestrator import PermissionOrchestrator
from .user_orchestrator import UserOrchestrator
from .api_key_orchestrator import ApiKeyOrchestrator
from .auth_session_orchestrator import AuthSessionOrchestrator

class DatabaseOrchestrator:
    """High-level database orchestration interface - tüm orchestrator'ları yönetir"""
    
    def __init__(self, database_engine):
        """
        DatabaseOrchestrator başlatır
        
        Args:
            database_engine: DatabaseEngine instance
        """
        # Initialize orchestrators
        self.workflow_orchestrator = WorkflowOrchestrator(database_engine)
        self.node_orchestrator = NodeOrchestrator(database_engine)
        self.edge_orchestrator = EdgeOrchestrator(database_engine)
        self.trigger_orchestrator = TriggerOrchestrator(database_engine)
        self.script_orchestrator = ScriptOrchestrator(database_engine)
        self.file_orchestrator = FileUploadOrchestrator(database_engine)
        self.envar_orchestrator = EnvironmentVariableOrchestrator(database_engine)
        self.execution_orchestrator = ExecutionOrchestrator(database_engine)
        self.execution_input_orchestrator = ExecutionInputOrchestrator(database_engine)
        self.execution_output_orchestrator = ExecutionOutputOrchestrator(database_engine)
        self.scheduler_orchestrator = SchedulerOrchestrator(database_engine)
        self.permission_orchestrator = PermissionOrchestrator(database_engine)
        self.user_orchestrator = UserOrchestrator(database_engine)
        self.api_key_orchestrator = ApiKeyOrchestrator(database_engine)
        self.auth_session_orchestrator = AuthSessionOrchestrator(database_engine)
    
__all__ = [
    # Base classes and decorators
    'BaseOrchestrator',
    'DatabaseOrchestrator',
    'with_session',
    'with_orchestration_errors',
    'require_role',
    'require_plan',
    'ROLE_HIERARCHY',
    'PLAN_HIERARCHY',
    'PLAN_LIMITS',
    
    # Orchestrators
    'WorkflowOrchestrator',
    'NodeOrchestrator',
    'EdgeOrchestrator',
    'TriggerOrchestrator',
    'ScriptOrchestrator',
    'FileUploadOrchestrator',
    'EnvironmentVariableOrchestrator',
    'ExecutionOrchestrator',
    'ExecutionInputOrchestrator',
    'ExecutionOutputOrchestrator',
    'SchedulerOrchestrator',
    'PermissionOrchestrator',
    'UserOrchestrator',
    'ApiKeyOrchestrator',
    'AuthSessionOrchestrator',
]