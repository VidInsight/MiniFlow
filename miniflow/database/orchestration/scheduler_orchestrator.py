from typing import List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select

from miniflow.database.models import Node, Script, ExecutionStatus, ExecutionOutputStatus
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class SchedulerOrchestrator(BaseOrchestrator):
    """
    Scheduler orchestrator for execution result processing and workflow management.
    
    Node State Tracking Flow:
    1. get_ready_execution_inputs() - Get tasks ready to process (dependency_count=0)
    2. [CALLER] mark_nodes_as_running() - Move pending → running (before execution)
    3. [CALLER] Execute tasks in engine
    4. process_execution_result() - Handle result and automatically increment executed count
    5. [AUTOMATIC] Updates next nodes' dependencies or completes execution
    
    Example Usage:
        # Step 1: Get ready tasks
        tasks = scheduler.get_ready_execution_inputs(batch_size=50)
        
        # Step 2: Mark as running (pending → running)
        for task in tasks:
            scheduler.mark_nodes_as_running(task['execution_id'], count=1)
        
        # Step 3: Execute tasks (external)
        results = execute_tasks(tasks)
        
        # Step 4: Process results (running → executed, automatic)
        for result in results:
            scheduler.process_execution_result(result)
    """

    def _get_primary_crud(self):
        return self.execution_output_crud

    @with_orchestration_errors('process_execution_result')
    @with_session
    def process_execution_result(self, session, execution_result: Dict[str, Any]) -> bool:
        execution_id = execution_result.get('execution_id')
        node_id = execution_result.get('node_id')
        status = execution_result.get('status')
        
        if not all([execution_id, node_id, status]):
            missing_fields = [f for f, v in [("execution_id", execution_id), ("node_id", node_id), ("status", status)] if not v]
            raise ValueError(f"Missing required fields: {missing_fields}")

        self._validate_execution_exist(session, execution_id)
        self._validate_node_exist(session, node_id)
        
        self._create_execution_output(session, execution_result)
        
        self.execution_crud._increment_executed_nodes(session, execution_id, increment=1)
        
        if status == 'FAILED':
            self._handle_failed_execution(session, execution_id, node_id)
            return True
        
        is_last_node = self._is_last_node(session, node_id)
        
        if is_last_node:
            self._handle_complete_execution(session, execution_id)
        else:
            self._update_next_node_dependencies(session, execution_id, node_id)
        
        return True

    def _create_execution_output(self, session, execution_result: Dict[str, Any]):
        output_data = {
            'execution_id': execution_result['execution_id'],
            'workflow_id': execution_result['workflow_id'],
            'node_id': execution_result['node_id'],
            'status': ExecutionOutputStatus.SUCCESS if execution_result['status'] == 'SUCCESS' else ExecutionOutputStatus.FAILED,
            'result_data': execution_result.get('result_data', {}) if execution_result.get('result_data') else {}
        }
        
        self.execution_output_crud._create(session, **output_data)

    def _handle_failed_execution(self, session, execution_id: str, failed_node_id: str):
        pending_inputs_nodes = self.execution_input_crud._get_all(session, execution_id=execution_id, limit=1000)
        completed_output_nodes = self.execution_output_crud._get_all(session, execution_id=execution_id, limit=1000)

        results_dict = {}
        for output in completed_output_nodes:
            results_dict[output.node_id] = {
                'status': output.status.value,
                'result_data': output.result_data,
            }
            self.execution_output_crud._delete(session, output.id)
        
        for pending_input in pending_inputs_nodes:
            if pending_input.node_id not in results_dict:
                results_dict[pending_input.node_id] = {
                    'status': 'CANCELLED',
                    'result_data': {"error": "Cancelled by failed node"},
                    'start_time': "N/A",
                    'end_time': "N/A"
                }
                self.execution_input_crud._delete(session, pending_input.id)

        data = {
            'status': ExecutionStatus.FAILED,
            'results': results_dict,
            'ended_at': datetime.now(timezone.utc)
        }
        self.execution_crud._update(session, execution_id, **data)

    def _is_last_node(self, session, node_id: str):
        outgoing_edges = self.edge_crud._get_all(session, from_node_id=node_id, limit=100)
        return len(outgoing_edges) == 0

    def _handle_complete_execution(self, session, execution_id: str):
        completed_output_nodes = self.execution_output_crud._get_all(session, execution_id=execution_id, limit=1000)
        
        results_dict = {}
        for output in completed_output_nodes:
            results_dict[output.node_id] = {
                'status': output.status.value,
                'result_data': output.result_data,
            }
        
        data = {
            'status': ExecutionStatus.COMPLETED,
            'results': results_dict,
            'ended_at': datetime.now(timezone.utc)
        }
        self.execution_crud._update(session, execution_id, **data)

    def _update_next_node_dependencies(self, session, execution_id: str, node_id: str):
        edges = self.edge_crud._get_all(session, from_node_id=node_id, limit=100)
        
        for edge in edges:
            next_node_id = edge.to_node_id
            
            execution_inputs = self.execution_input_crud._get_all(
                session,
                execution_id=execution_id,
                node_id=next_node_id,
                limit=10
            )
            
            if execution_inputs:
                execution_input = execution_inputs[0]
                new_dependency_count = max(0, execution_input.dependency_count - 1)
                
                self.execution_input_crud._update(
                    session, 
                    execution_input.id,
                    dependency_count=new_dependency_count
                )

    @with_orchestration_errors('get_ready_execution_inputs')
    @with_session
    def get_ready_execution_inputs(self, session, batch_size: int = 50) -> List[Dict[str, Any]]:
        batch_size = min(max(1, batch_size), 1000)
        
        ready_inputs = self.execution_input_crud._get_ready_to_process(session, limit=batch_size)
        
        execution_ids = list(set([ei.execution_id for ei in ready_inputs]))
        executions = {}
        if execution_ids:
            for exec_id in execution_ids:
                execution = self.execution_crud._get_by_id(session, exec_id)
                if execution:
                    executions[exec_id] = execution
        
        node_ids = [ei.node_id for ei in ready_inputs]
        nodes = {}
        if node_ids:
            stmt = select(Node).where(Node.id.in_(node_ids))
            node_results = session.execute(stmt).scalars().all()
            nodes = {node.id: node for node in node_results}
        
        script_ids = [node.script_id for node in nodes.values() if node.script_id]
        scripts = {}
        if script_ids:
            stmt = select(Script).where(Script.id.in_(script_ids))
            script_results = session.execute(stmt).scalars().all()
            scripts = {script.id: script for script in script_results}
        
        ready_tasks = []
        for execution_input in ready_inputs:
            execution = executions.get(execution_input.execution_id)
            node = nodes.get(execution_input.node_id)
            script = None
            if node and node.script_id:
                script = scripts.get(node.script_id)
            
            task = {
                'id': execution_input.id,
                'execution_id': execution_input.execution_id,
                'workflow_id': execution_input.workflow_id,
                'node_id': execution_input.node_id,
                'trigger_id': execution.trigger_id if execution else None,
                'priority': execution_input.priority,
                'dependency_count': execution_input.dependency_count,
                'node_params': execution_input.node_params,
                'node_name': node.name if node else f"Node-{execution_input.node_id}",
                'script_name': script.name if script else None,
                'script_path': script.file_path if script else None
            }
            ready_tasks.append(task)
        
        return ready_tasks

    @with_orchestration_errors('process_task_context')
    @with_session
    def process_task_context(self, session, task: Dict[str, Any]) -> Dict[str, Any]:
        raw_node_params = task.get('node_params', {})
        execution_id = task['execution_id']
        workflow_id = task['workflow_id']
        trigger_id = task.get('trigger_id')
        
        if not isinstance(raw_node_params, dict):
            return {}
            
        processed_context = {}
        
        for key, param_data in raw_node_params.items():
            try:
                if isinstance(param_data, dict) and 'value' in param_data:
                    raw_value = param_data['value']
                else:
                    raw_value = param_data
                
                processed_value = self._resolve_parameter_value(session, raw_value, execution_id, workflow_id, trigger_id)
                processed_context[key] = processed_value
                
            except Exception:
                if isinstance(param_data, dict) and 'value' in param_data:
                    processed_context[key] = param_data['value']
                else:
                    processed_context[key] = param_data
        
        return processed_context

    def _resolve_parameter_value(self, session, value: Any, execution_id: str, workflow_id: str, trigger_id: str = None) -> Any:
        if not isinstance(value, str):
            return value
            
        if value.startswith('{n{') and value.endswith('}}'):
            try:
                return self._resolve_node_output_reference(session, value, execution_id)
            except Exception:
                return value
            
        elif value.startswith('{e{') and value.endswith('}}'):
            try:
                return self._resolve_environment_variable_reference(session, value, workflow_id)
            except Exception:
                return value
            
        elif value.startswith('{t{') and value.endswith('}}'):
            try:
                return self._resolve_trigger_data_reference(session, value, execution_id, trigger_id)
            except Exception:
                return value
        else:
            return value

    def _resolve_node_output_reference(self, session, placeholder: str, execution_id: str) -> Any:
        inner_content = placeholder[3:-2]
        if '.' not in inner_content:
            return placeholder
            
        node_id, variable_name = inner_content.split('.', 1)
        
        execution_outputs = self.execution_output_crud._get_all(
            session,
            execution_id=execution_id,
            node_id=node_id,
            limit=10
        )
        
        if not execution_outputs:
            return placeholder
            
        execution_output = execution_outputs[-1]
        
        result_data = execution_output.result_data or {}
        if isinstance(result_data, str):
            import json
            try:
                result_data = json.loads(result_data)
            except json.JSONDecodeError:
                result_data = {}
                
        if variable_name in result_data:
            value_data = result_data[variable_name]
            if isinstance(value_data, dict) and 'value' in value_data:
                return value_data['value']
            else:
                return value_data
        else:
            return placeholder

    def _resolve_environment_variable_reference(self, session, placeholder: str, workflow_id: str) -> Any:
        variable_name = placeholder[3:-2]
        
        env_vars = self.envar_crud._get_all(
            session,
            name=variable_name,
            limit=10
        )
        
        if env_vars:
            return env_vars[0].value
        else:
            return placeholder

    def _resolve_trigger_data_reference(self, session, placeholder: str, execution_id: str, trigger_id: str) -> Any:
        inner_content = placeholder[3:-2]
        if '.' not in inner_content:
            return placeholder
            
        ref_trigger_id, variable_name = inner_content.split('.', 1)
        
        execution = self.execution_crud._get_by_id(session, execution_id)
        if not execution:
            return placeholder
            
        trigger_data = execution.trigger_data or {}
        if isinstance(trigger_data, str):
            import json
            try:
                trigger_data = json.loads(trigger_data)
            except json.JSONDecodeError:
                trigger_data = {}
        
        if variable_name in trigger_data:
            return trigger_data[variable_name]
        else:
            if trigger_id or ref_trigger_id:
                trigger = self.trigger_crud._get_by_id(session, trigger_id or ref_trigger_id)
                if trigger and hasattr(trigger, 'config'):
                    trigger_record_data = trigger.config or {}
                    if isinstance(trigger_record_data, str):
                        import json
                        try:
                            trigger_record_data = json.loads(trigger_record_data)
                        except json.JSONDecodeError:
                            trigger_record_data = {}
                            
                    if variable_name in trigger_record_data:
                        return trigger_record_data[variable_name]
                        
            return placeholder

    @with_orchestration_errors('mark_nodes_as_running')
    @with_session
    def mark_nodes_as_running(self, session, execution_id: str, count: int = 1) -> Dict[str, Any]:
        self._validate_execution_exist(session, execution_id)
        
        result = self.execution_crud._increment_running_nodes(session, execution_id, increment=count)
        return self._serialize_single_result(result)

    @with_orchestration_errors('mark_nodes_as_executed')
    @with_session
    def mark_nodes_as_executed(self, session, execution_id: str, count: int = 1) -> Dict[str, Any]:
        self._validate_execution_exist(session, execution_id)
        
        result = self.execution_crud._increment_executed_nodes(session, execution_id, increment=count)
        return self._serialize_single_result(result)

    @with_orchestration_errors('remove_processed_execution_inputs')
    @with_session
    def remove_processed_execution_inputs(self, session, task_ids: List[str]) -> int:
        if not task_ids:
            return 0
            
        removed_count = 0
        for task_id in task_ids:
            try:
                self.execution_input_crud._delete(session, task_id)
                removed_count += 1
            except Exception:
                continue
                
        return removed_count

