"""
Miniflow Database Orchestration Module

Provides high-level business logic and session management for database operations.
"""

from .envar_orchestrator import EnvironmentVariableOrchestrator
from .fileupload_orchestrator import FileUploadOrchestrator
from .script_orchestrator import ScriptOrchestrator
from .workflow_orchestrator import WorkflowOrchestrator
from .node_orchestrator import NodeOrchestrator
from .edge_orchestrator import EdgeOrchestrator
from .execution_orchestrator import ExecutionOrchestrator
from .execution_input_orchestrator import ExecutionInputOrchestrator
from .execution_output_orchestrator import ExecutionOutputOrchestrator
# from .credential_orchestrator import CredentialOrchestrator  # TODO: Implement CredentialOrchestrator


class DatabaseOrchestrator:
    """High-level database orchestration interface - tüm orchestrator'ları yönetir"""
    
    def __init__(self, database_engine):
        """
        DatabaseOrchestrator başlatır
        
        Args:
            database_engine: DatabaseEngine instance
        """
        # Tüm orchestrator'ları başlat
        self.envar_orchestrator = EnvironmentVariableOrchestrator(database_engine)
        self.fileupload_orchestrator = FileUploadOrchestrator(database_engine)
        self.script_orchestrator = ScriptOrchestrator(database_engine)
        self.workflow_orchestrator = WorkflowOrchestrator(database_engine)
        self.node_orchestrator = NodeOrchestrator(database_engine)
        self.edge_orchestrator = EdgeOrchestrator(database_engine)
        self.execution_orchestrator = ExecutionOrchestrator(database_engine)
        self.execution_input_orchestrator = ExecutionInputOrchestrator(database_engine)
        self.execution_output_orchestrator = ExecutionOutputOrchestrator(database_engine)
        # self.credential_orchestrator = CredentialOrchestrator(database_engine)  # TODO: Implement
        
        # Gelecekte eklenecek orchestrator'lar için yer tutucular
        # self.audit_orchestrator = AuditOrchestrator(database_engine)


__all__ = [
    'DatabaseOrchestrator',
]