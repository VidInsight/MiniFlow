from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json

from sqlalchemy.orm import Session
from miniflow.database.models import (
    Edge, ExecutionOutput, ExecutionInput, Execution, 
    ExecutionStatus, ExecutionOutputStatus, EnvironmentVariable, VariableScope
)
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError
from miniflow.core.logger import get_logger


class SchedulerOrchestrator(BaseOrchestrator):
    """Scheduler orchestrator for execution result processing and workflow management."""

    def __init__(self, database_engine):
        super().__init__(database_engine)

    def _get_primary_crud(self):
        """Return the ExecutionOutput CRUD instance as primary."""
        return self.execution_output_crud

    @with_session
    def process_execution_result(self, session: Session, execution_result: Dict[str, Any]) -> bool:
        """
        Process single execution result:
        1. Create execution_output record
        2. Handle FAILED status (cancel pending tasks)
        3. Check if last node and update execution record
        4. Update dependency counts for next nodes (if not last and success)

        Used by scheduler/output_handler.py
        """
        try:
            execution_id = execution_result.get('execution_id')
            node_id = execution_result.get('node_id')
            status = execution_result.get('status')
            
            if not all([execution_id, node_id, status]):
                raise OrchestrationError("Missing required fields: execution_id, node_id, status")

            # 1. Always create execution_output record
            self._create_execution_output(session, execution_result)
            
            # 2. Handle FAILED status
            if status == 'FAILED':
                self._handle_failed_execution(session, execution_id, node_id)
                return True
            
            # 3. Check if this is the last node
            is_last_node = self._is_last_node(session, node_id)
            
            if is_last_node:
                # 4. Handle last node completion
                self._handle_complete_execution(session, execution_id)
            else:
                # 5. Update dependency counts for next nodes
                self._update_next_node_dependencies(session, execution_id, node_id)
            
            # 6. Log successful processing
            self.logger.info(f"Successfully processed node {node_id} for execution {execution_id}")
        
            self.logger.info(f"Successfully processed execution result for {execution_id}/{node_id}")
            return True
            
        except Exception as e:
            context = self._create_error_context("process_execution_result", execution_id=execution_result.get('execution_id'),node_id=execution_result.get('node_id'))
            raise OrchestrationError(f"Failed to process execution result: {str(e)}", context=context) from e

    def _create_execution_output(self, session: Session, execution_result: Dict[str, Any]):
        """Create execution_output record."""
        try:
            output_data = {
                'execution_id': execution_result['execution_id'],
                'workflow_id': execution_result['workflow_id'],
                'node_id': execution_result['node_id'],
                'status': ExecutionOutputStatus.SUCCESS if execution_result['status'] == 'SUCCESS' else ExecutionOutputStatus.FAILED,
                'result_data': execution_result.get('result_data', {})
            }
            
            self.execution_output_crud._create(session, **output_data)

        except Exception as e:
            raise OrchestrationError(f"Failed to create execution_output: {str(e)}") from e

    def _handle_failed_execution(self, session: Session, execution_id: str, failed_node_id: str):
        """Handle FAILED execution: cancel pending tasks and update execution record."""
        try:
            pending_inputs_nodes = self.execution_input_crud._get_by_execution(session, execution_id)
            completed_output_nodes = self.execution_output_crud._filter(session, {'execution_id': execution_id})

            results_dict = {}
            for output in completed_output_nodes:
                results_dict[output.node_id] = {
                    'status': output.status.value,
                    'result_data': output.result_data,
                }
                self.execution_output_crud._delete(session, record_id=output.id)
            
            for pending_input in pending_inputs_nodes:
                if pending_input.node_id not in results_dict:
                    results_dict[pending_input.node_id] = {
                        'status': 'CANCELLED',
                        'result_data': {"error": "Cancelled by failed node"},
                        'start_time': "N/A",
                        'end_time': "N/A"
                    }
                    self.execution_input_crud._delete(session, record_id=pending_input.id)

            data = {
                'status': ExecutionStatus.FAILED,
                'results': results_dict,
                'ended_at': datetime.now(timezone.utc)
            }
            self.execution_crud._update(session, execution_id, **data)
            self.logger.info(f"Handled failed execution {execution_id}, cancelled pending tasks")
            
        except Exception as e:
            raise OrchestrationError(f"Failed to handle failed execution: {str(e)}") from e

    def _is_last_node(self, session: Session, node_id: str):
        """Check if this node is the last node (no outgoing edges)."""
        try:
            # Check if there are any outgoing edges from this node
            outgoing_edges = self.edge_crud._filter(session, {"from_node_id": node_id})
            return len(outgoing_edges) == 0
            
        except Exception as e:
            raise OrchestrationError(f"Failed to check if last node: {str(e)}") from e

    def _handle_complete_execution(self, session: Session, execution_id: str):
        """Handle last node completion: build final results and update execution."""
        try:
            # Get all execution_outputs for this execution ordered by creation time
            completed_output_nodes = self.execution_output_crud._filter(session, {'execution_id': execution_id})
            
            # Build final results dict
            results_dict = {}
            
            for output in completed_output_nodes:
                results_dict[output.node_id] = {
                    'status': output.status.value,
                    'result_data': output.result_data,
                }
                
            
            # Update execution record
            data = {
                'status': ExecutionStatus.COMPLETED,
                'results': results_dict,
                'ended_at': datetime.now(timezone.utc)
            }
            self.execution_crud._update(session, execution_id, **data)
                    
            self.logger.info(f"Completed execution {execution_id} with {len(results_dict)} nodes")
            
        except Exception as e:
            raise OrchestrationError(f"Failed to handle last node completion: {str(e)}") from e

    def _update_next_node_dependencies(self, session: Session, execution_id: str, node_id: str):
        """Update dependency counts for next nodes in the workflow."""
        try:
            # Get outgoing edges from the completed node
            edges = self.edge_crud._filter(session, {"from_node_id": node_id})
            
            # Update dependency count for each next node
            for edge in edges:
                next_node_id = edge.to_node_id
                
                # Find execution_input record for next node in this execution
                execution_inputs = self.execution_input_crud._filter(
                    session, 
                    filters={
                        "execution_id": execution_id,
                        "node_id": next_node_id
                    }
                )
                
                if execution_inputs:
                    execution_input = execution_inputs[0]  # Should be only one
                    new_dependency_count = max(0, execution_input.dependency_count - 1)
                    
                    # Update the dependency count
                    self.execution_input_crud._update(
                        session, 
                        execution_input.id, 
                        **{'dependency_count': new_dependency_count}
                    )
                    
                    self.logger.debug(f"Updated dependency count for node {next_node_id} to {new_dependency_count}")
            
        except Exception as e:
            raise OrchestrationError(f"Failed to update next node dependencies: {str(e)}") from e

    # ==========================================
    # INPUT HANDLER SUPPORT METHODS
    # ==========================================

    @with_session
    def get_ready_execution_inputs(self, session: Session, batch_size: int = 50) -> List[Dict[str, Any]]:
        """
        Get ready ExecutionInput records (dependency_count = 0) sorted by priority.
        
        Used by Input Handler for task processing.
        """
        try:
            self.logger.info(f"Getting ready execution inputs with batch_size={batch_size}")
            print(f"DEBUG: get_ready_execution_inputs called with batch_size={batch_size}")
            
            # Get execution inputs ready for processing (dependency_count = 0)
            ready_inputs = self.execution_input_crud._filter(
                session, 
                filters={"dependency_count": 0},
                limit=batch_size,
                order_by_field="priority"
            )
            
            self.logger.info(f"SQL query returned {len(ready_inputs)} rows")
            print(f"DEBUG: SQL query returned {len(ready_inputs)} rows")
            
            # Build enhanced task objects with all necessary data
            ready_tasks = []
            self.logger.info(f"Processing {len(ready_inputs)} execution inputs")
            
            for i, execution_input in enumerate(ready_inputs):
                self.logger.debug(f"Processing execution input {i+1}/{len(ready_inputs)}: {execution_input.id}")
                
                # Get node data for script information
                node = self.node_crud._get_by_id(session, execution_input.node_id)
                script = None
                if node and node.script_id:
                    script = self.script_crud._get_by_id(session, node.script_id)
                
                task = {
                    'id': execution_input.id,
                    'execution_id': execution_input.execution_id,
                    'workflow_id': execution_input.workflow_id,
                    'node_id': execution_input.node_id,
                    'trigger_id': execution_input.trigger_id,
                    'priority': execution_input.priority,
                    'dependency_count': execution_input.dependency_count,
                    'node_params': execution_input.node_params,
                    'node_name': node.name if node else f"Node-{execution_input.node_id}",
                    'script_name': script.name if script else None,
                    'script_path': script.file_path if script else None
                }
                ready_tasks.append(task)
                self.logger.debug(f"Added task {i+1}: {task['node_name']} (script: {task['script_path']})")
            
            self.logger.info(f"Found {len(ready_tasks)} ready execution inputs")
            return ready_tasks
            
        except Exception as e:
            self.logger.error(f"Exception in get_ready_execution_inputs: {str(e)}", exc_info=True)
            print(f"DEBUG: Exception in get_ready_execution_inputs: {str(e)}")
            context = self._create_error_context("get_ready_execution_inputs", batch_size=batch_size)
            raise OrchestrationError(f"Failed to get ready execution inputs: {str(e)}", context=context) from e

    @with_session
    def process_task_context(self, session: Session, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process node_params for a task to resolve dynamic parameters.
        
        Supports both formats:
        - New format: {variable_name: {value: variable_value, type: ..., format: ...}}
        - Old format: {variable_name: variable_value} (backward compatibility)
        
        Placeholder formats for values:
        - {n{node_id.variable_name}} -> ExecutionOutput lookup  
        - {e{variable_name}} -> EnvironmentVariable lookup
        - {t{trigger_id.variable_name}} -> Trigger data lookup
        - Static values -> returned as-is
        
        Returns flattened context for script execution: {variable_name: variable_value}
        """
        try:
            raw_node_params = task.get('node_params', {})
            execution_id = task['execution_id']
            workflow_id = task['workflow_id']
            trigger_id = task.get('trigger_id')
            
            self.logger.info(f"Processing task context for execution {execution_id}, node {task.get('node_id')}")
            self.logger.debug(f"Raw node_params: {raw_node_params}")
            
            if not isinstance(raw_node_params, dict):
                self.logger.warning(f"node_params is not a dict: {type(raw_node_params)}")
                return {}
                
            processed_context = {}
            
            for key, param_data in raw_node_params.items():
                try:
                    self.logger.debug(f"Processing parameter '{key}' with data: {param_data}")
                    
                    # Extract value based on format
                    if isinstance(param_data, dict) and 'value' in param_data:
                        # New format: {variable_name: {value: variable_value, ...}}
                        raw_value = param_data['value']
                        self.logger.debug(f"New format detected - extracting value: {raw_value}")
                    else:
                        # Old format: {variable_name: variable_value} (backward compatibility)
                        raw_value = param_data
                        self.logger.debug(f"Old format detected - using direct value: {raw_value}")
                    
                    # Resolve parameter value (placeholders, etc.)
                    processed_value = self._resolve_parameter_value(session, raw_value, execution_id, workflow_id, trigger_id)
                    processed_context[key] = processed_value
                    self.logger.debug(f"Resolved '{key}': {raw_value} -> {processed_value}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process parameter '{key}': {str(e)}")
                    # Keep original value if processing fails
                    if isinstance(param_data, dict) and 'value' in param_data:
                        processed_context[key] = param_data['value']
                    else:
                        processed_context[key] = param_data
                    
            self.logger.info(f"Processed context: {processed_context}")
            return processed_context
            
        except Exception as e:
            context = self._create_error_context("process_task_context", task_id=task.get('id'),execution_id=task.get('execution_id'))
            raise OrchestrationError(f"Failed to process task context: {str(e)}", context=context) from e

    def _resolve_parameter_value(self, session: Session, value: Any, execution_id: str, workflow_id: str, trigger_id: str = None) -> Any:
        """
        Resolve a single parameter value with placeholder support.
        
        Placeholder formats:
        - {n{node_id.variable_name}} -> ExecutionOutput lookup  
        - {e{variable_name}} -> EnvironmentVariable lookup
        - {t{trigger_id.variable_name}} -> Trigger data lookup
        - Static values -> returned as-is
        """
        # Non-string values are static
        if not isinstance(value, str):
            self.logger.debug(f"Value is not a string, returning as-is: {value}")
            return value
            
        self.logger.debug(f"Resolving parameter value: {value}")
            
        # Check for placeholders
        if value.startswith('{n{') and value.endswith('}}'):
            # Node output reference: {n{node_id.variable_name}}
            self.logger.debug(f"Detected node reference: {value}")
            resolved = self._resolve_node_output_reference(session, value, execution_id)
            self.logger.debug(f"Node reference resolved: {value} -> {resolved}")
            return resolved
            
        elif value.startswith('{e{') and value.endswith('}}'):
            # Environment variable reference: {e{variable_name}}
            self.logger.debug(f"Detected environment variable reference: {value}")
            resolved = self._resolve_environment_variable_reference(session, value, workflow_id)
            self.logger.debug(f"Environment variable resolved: {value} -> {resolved}")
            return resolved
            
        elif value.startswith('{t{') and value.endswith('}}'):
            # Trigger data reference: {t{trigger_id.variable_name}}
            self.logger.debug(f"Detected trigger data reference: {value}")
            resolved = self._resolve_trigger_data_reference(session, value, execution_id, trigger_id)
            self.logger.debug(f"Trigger data resolved: {value} -> {resolved}")
            return resolved
            
        else:
            # Static value
            self.logger.debug(f"Static value, returning as-is: {value}")
            return value

    def _resolve_node_output_reference(self, session: Session, placeholder: str, execution_id: str) -> Any:
        """
        Resolve node output reference: {n{node_id.variable_name}}
        
        Looks up ExecutionOutput table for:
        - execution_id = current execution
        - node_id = specified node
        - variable_name in result_data JSON
        """
        try:
            self.logger.debug(f"Resolving node output reference: {placeholder} for execution {execution_id}")
            
            # Extract node_id and variable_name from placeholder: {n{node_id.variable_name}}
            inner_content = placeholder[3:-2]  # Remove {n{ and }}
            if '.' not in inner_content:
                self.logger.warning(f"Invalid node reference format: {placeholder}")
                return placeholder
                
            node_id, variable_name = inner_content.split('.', 1)
            self.logger.debug(f"Extracted node_id: {node_id}, variable_name: {variable_name}")
            
            # Find ExecutionOutput for this execution and node
            execution_outputs = self.execution_output_crud._filter(
                session, 
                filters={
                    "execution_id": execution_id,
                    "node_id": node_id
                }
            )
            
            self.logger.debug(f"Found {len(execution_outputs)} execution outputs for node {node_id}")
            
            if not execution_outputs:
                self.logger.warning(f"No execution output found for node {node_id} in execution {execution_id}")
                return placeholder
                
            # Get the most recent output (last one)
            execution_output = execution_outputs[-1]
            self.logger.debug(f"Using execution output: {execution_output.id}")
            
            # Extract variable from result_data JSON
            result_data = execution_output.result_data or {}
            if isinstance(result_data, str):
                import json
                try:
                    result_data = json.loads(result_data)
                except json.JSONDecodeError:
                    result_data = {}
                    
            self.logger.debug(f"Result data: {result_data}")
            self.logger.debug(f"Looking for variable '{variable_name}' in result_data")
                    
            if variable_name in result_data:
                # Handle both direct values and nested structures
                value_data = result_data[variable_name]
                if isinstance(value_data, dict) and 'value' in value_data:
                    # New format: {variable_name: {value: actual_value, ...}}
                    resolved_value = value_data['value']
                    self.logger.debug(f"Resolved {placeholder} from new format to: {resolved_value}")
                else:
                    # Old format or direct value: {variable_name: actual_value}
                    resolved_value = value_data
                    self.logger.debug(f"Resolved {placeholder} from direct value to: {resolved_value}")
                return resolved_value
            else:
                self.logger.warning(f"Variable '{variable_name}' not found in node {node_id} output. Available keys: {list(result_data.keys())}")
                return placeholder
                
        except Exception as e:
            self.logger.error(f"Failed to resolve node output reference {placeholder}: {str(e)}")
            return placeholder  # Return original if resolution fails

    def _resolve_environment_variable_reference(self, session: Session, placeholder: str, workflow_id: str) -> Any:
        """
        Resolve environment variable reference: {e{variable_name}}
        
        Looks up EnvironmentVariable table for:
        - name = variable_name
        - scope = WORKFLOW (for workflow-specific) or GLOBAL
        """
        try:
            # Extract variable_name from placeholder: {e{variable_name}}
            variable_name = placeholder[3:-2]  # Remove {e{ and }}
            
            # First, try to find workflow-specific environment variable (scope = WORKFLOW)
            env_vars = self.envar_crud._filter(
                session,
                filters={
                    "name": variable_name,
                }
            )
            
            # If no workflow-specific variable found, try global
            if not env_vars:
                env_vars = self.envar_crud._filter(
                    session,
                    filters={
                        "name": variable_name,
                        "scope": VariableScope.GLOBAL
                    }
                )
            
            if env_vars:
                env_var = env_vars[0]  # Get first match
                resolved_value = env_var.value
                self.logger.debug(f"Resolved environment variable {placeholder} to: {resolved_value}")
                return resolved_value
            else:
                self.logger.warning(f"Environment variable '{variable_name}' not found")
                return placeholder
                
        except Exception as e:
            self.logger.error(f"Failed to resolve environment variable {placeholder}: {str(e)}")
            return placeholder  # Return original if resolution fails

    def _resolve_trigger_data_reference(self, session: Session, placeholder: str, execution_id: str, trigger_id: str) -> Any:
        """
        Resolve trigger data reference: {t{trigger_id.variable_name}}
        
        Looks up trigger data from execution results:
        - execution_id = current execution
        - results.trigger_data[variable_name]
        """
        try:
            # Extract variable_name from placeholder: {t{trigger_id.variable_name}}
            inner_content = placeholder[3:-2]  # Remove {t{ and }}
            if '.' not in inner_content:
                self.logger.warning(f"Invalid trigger reference format: {placeholder}")
                return placeholder
                
            ref_trigger_id, variable_name = inner_content.split('.', 1)
            
            # Get execution record to access trigger data
            execution = self.execution_crud._get_by_id(session, execution_id)
            if not execution:
                self.logger.warning(f"Execution {execution_id} not found")
                return placeholder
                
            # Extract trigger data from execution results
            results = execution.results or {}
            if isinstance(results, str):
                import json
                try:
                    results = json.loads(results)
                except json.JSONDecodeError:
                    results = {}

            trigger_data = results.get('trigger_data', {})
            
            # Look for the variable in trigger data
            if variable_name in trigger_data:
                resolved_value = trigger_data[variable_name]
                self.logger.debug(f"Resolved trigger reference {placeholder} to: {resolved_value}")
                return resolved_value
            else:
                # If not found in trigger_data, try to get from trigger record directly
                if trigger_id or ref_trigger_id:
                    trigger = self.trigger_crud._get_by_id(session, trigger_id or ref_trigger_id)
                    if trigger and hasattr(trigger, 'config'):
                        trigger_record_data = trigger.config or {}
                        if isinstance(trigger_record_data, str):
                            try:
                                trigger_record_data = json.loads(trigger_record_data)
                            except json.JSONDecodeError:
                                trigger_record_data = {}
                                
                        if variable_name in trigger_record_data:
                            resolved_value = trigger_record_data[variable_name]
                            self.logger.debug(f"Resolved trigger reference {placeholder} from trigger record to: {resolved_value}")
                            return resolved_value
                            
                self.logger.warning(f"Variable '{variable_name}' not found in trigger data")
                return placeholder
                
        except Exception as e:
            self.logger.error(f"Failed to resolve trigger data reference {placeholder}: {str(e)}")
            return placeholder  # Return original if resolution fails

    @with_session
    def remove_processed_execution_inputs(self, session: Session, task_ids: List[str]) -> int:
        """
        Remove processed ExecutionInput records after they're sent to execution engine.
        
        Returns number of records removed.
        """
        try:
            if not task_ids:
                return 0
                
            removed_count = 0
            for task_id in task_ids:
                try:
                    self.execution_input_crud._delete(session, task_id)
                    removed_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to remove task {task_id}: {str(e)}")
                    
            self.logger.info(f"Removed {removed_count} processed execution inputs from {len(task_ids)} total")
            return removed_count
            
        except Exception as e:
            context = self._create_error_context("remove_processed_execution_inputs", task_ids=task_ids)
            raise OrchestrationError(f"Failed to remove processed execution inputs: {str(e)}", context=context) from e