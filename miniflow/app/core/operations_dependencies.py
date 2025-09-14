"""
Operations Dependencies
BFF Operations için tüm dependency'ler
"""

from fastapi import Request
from .dependencies import get_database_orchestrator


# === BFF OPERATIONS DEPENDENCIES ===

def get_envar_operations(request: Request):
    """Get Environment Variable Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_envar_routes.operations import EnvironmentVariableOperations
    return EnvironmentVariableOperations(orchestrator.envar_orchestrator)


def get_workflow_operations(request: Request):
    """Get Workflow Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_workflow_routes.operations import WorkflowOperations
    return WorkflowOperations(orchestrator.workflow_orchestrator)


def get_node_operations(request: Request):
    """Get Node Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_node_routes.operations import NodeOperations
    return NodeOperations(orchestrator.node_orchestrator)


def get_edge_operations(request: Request):
    """Get Edge Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_edge_routes.operations import EdgeOperations
    return EdgeOperations(orchestrator.edge_orchestrator)


def get_script_operations(request: Request):
    """Get Script Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_script_routes.operations import ScriptOperations
    return ScriptOperations(orchestrator.script_orchestrator)


def get_execution_operations(request: Request):
    """Get Execution Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_execution_routes.operations import ExecutionOperations
    return ExecutionOperations(orchestrator.execution_orchestrator)


def get_execution_input_operations(request: Request):
    """Get Execution Input Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_execution_input_routes.operations import ExecutionInputOperations
    return ExecutionInputOperations(orchestrator.execution_input_orchestrator)


def get_execution_output_operations(request: Request):
    """Get Execution Output Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_execution_output_routes.operations import ExecutionOutputOperations
    return ExecutionOutputOperations(orchestrator.execution_output_orchestrator)


def get_file_operations(request: Request):
    """Get File Upload Operations dependency"""
    orchestrator = get_database_orchestrator(request)
    from miniflow.app.routes.bff.bff_file_routes.operations import FileUploadOperations
    return FileUploadOperations(orchestrator.fileupload_orchestrator)
