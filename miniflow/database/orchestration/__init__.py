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
from .scheduler_orchestrator import SchedulerOrchestrator
from .trigger_orchestrator import TriggerOrchestrator

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
        self.scheduler_orchestrator = SchedulerOrchestrator(database_engine)
        self.trigger_orchestrator = TriggerOrchestrator(database_engine)
        # self.credential_orchestrator = CredentialOrchestrator(database_engine)  # TODO: Implement
    
    # ==============================
    # Context Processing Methods
    # ==============================
    
    def process_context_parameters(self, node_params: dict, execution_id: str, workflow_id: str) -> dict:
        """
        Process node_params to resolve dynamic parameters:
        - statik -> direct values ("string", 6, 5.2)
        - trigger -> {t{variable_name}} 
        - environment -> {e{environment_variable}}
        - node -> {n{node_id.variable_name}}
        
        Args:
            node_params: Raw node parameters dict
            execution_id: Current execution ID
            workflow_id: Current workflow ID
            
        Returns:
            Processed context dict with resolved parameters
        """
        if not isinstance(node_params, dict):
            return {}
            
        processed_context = {}
        
        for key, value in node_params.items():
            try:
                processed_value = self._resolve_parameter_value(value, execution_id, workflow_id)
                processed_context[key] = processed_value
            except Exception as e:
                # Keep original value if processing fails
                processed_context[key] = value
                
        return processed_context
    
    def _resolve_parameter_value(self, value, execution_id: str, workflow_id: str):
        """Resolve a single parameter value based on its type."""
        # If not a string, return as-is (statik values like numbers, booleans)
        if not isinstance(value, str):
            return value
            
        # Check for parameter patterns
        if value.startswith('{t{') and value.endswith('}}'):
            # Trigger parameter: {t{variable_name}}
            variable_name = value[3:-2]  # Remove {t{ and }}
            return self.resolve_trigger_parameter(variable_name, execution_id, workflow_id)
            
        elif value.startswith('{e{') and value.endswith('}}'):
            # Environment parameter: {e{environment_variable}}
            env_var_name = value[3:-2]  # Remove {e{ and }}
            return self.resolve_environment_parameter(env_var_name, execution_id, workflow_id)
            
        elif value.startswith('{n{') and value.endswith('}}'):
            # Node parameter: {n{node_id.variable_name}}
            node_reference = value[3:-2]  # Remove {n{ and }}
            return self.resolve_node_parameter(node_reference, execution_id, workflow_id)
            
        else:
            # Statik parameter - return as-is
            return value
    
    def resolve_trigger_parameter(self, variable_name: str, execution_id: str, workflow_id: str):
        """
        Resolve trigger parameter from execution inputs or workflow trigger data.
        
        Args:
            variable_name: Variable name to resolve
            execution_id: Current execution ID
            workflow_id: Current workflow ID
            
        Returns:
            Resolved value or original pattern if not found
        """
        try:
            # Get execution record to find trigger data
            execution = self.execution_orchestrator.get_by_id(execution_id)
            if execution and 'trigger_data' in execution:
                trigger_data = execution.get('trigger_data', {})
                if variable_name in trigger_data:
                    return trigger_data[variable_name]
            
            return f"{{t{{{variable_name}}}}}"  # Return original if not found
            
        except Exception as e:
            return f"{{t{{{variable_name}}}}}"
    
    def resolve_environment_parameter(self, env_var_name: str, execution_id: str, workflow_id: str):
        """
        Resolve environment variable parameter.
        
        Args:
            env_var_name: Environment variable name
            execution_id: Current execution ID
            workflow_id: Current workflow ID
            
        Returns:
            Environment variable value or original pattern if not found
        """
        try:
            # Get environment variables for this workflow
            env_vars = self.envar_orchestrator.filter(
                filters={"workflow_id": workflow_id}
            )
            
            for env_var in env_vars:
                if env_var.get('name') == env_var_name:
                    return env_var.get('value')
            
            return f"{{e{{{env_var_name}}}}}"  # Return original if not found
            
        except Exception as e:
            return f"{{e{{{env_var_name}}}}}"
    
    def resolve_node_parameter(self, node_reference: str, execution_id: str, workflow_id: str):
        """
        Resolve node parameter from previous node execution results.
        
        Args:
            node_reference: Node reference in format "node_id.variable_name"
            execution_id: Current execution ID
            workflow_id: Current workflow ID
            
        Returns:
            Node output variable value or original pattern if not found
        """
        try:
            # Parse node_id.variable_name
            if '.' not in node_reference:
                return f"{{n{{{node_reference}}}}}"
            
            node_id, variable_name = node_reference.split('.', 1)
            
            # Get execution output for the referenced node
            execution_outputs = self.execution_output_orchestrator.filter(
                filters={
                    "execution_id": execution_id,
                    "node_id": node_id
                }
            )
            
            if execution_outputs:
                output = execution_outputs[0]  # Should be only one output per node per execution
                result_data = output.get('result_data', {})
                
                if isinstance(result_data, dict) and variable_name in result_data:
                    return result_data[variable_name]
            
            return f"{{n{{{node_reference}}}}}"  # Return original if not found
            
        except Exception as e:
            return f"{{n{{{node_reference}}}}}"
        


__all__ = [
    'DatabaseOrchestrator',
    'TriggerOrchestrator',
]