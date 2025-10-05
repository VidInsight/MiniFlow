from typing import Dict, Any

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class ExecutionInputOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.execution_input_crud

    @with_orchestration_errors('create_execution_input')
    @with_session
    def create(self, session, user_id: str, execution_id: str, workflow_id: str, node_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_workflow_exist(session, workflow_id)
        self._validate_node_exist(session, node_id)
        
        execution_input = self.execution_input_crud._create(
            session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            node_id=node_id,
            created_by=user_id,
            **kwargs
        )
        
        return self._serialize_single_result(execution_input)

    @with_orchestration_errors('update_execution_input')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'workflow_id' in kwargs:
            self._validate_workflow_exist(session, kwargs['workflow_id'])
        
        if 'node_id' in kwargs:
            self._validate_node_exist(session, kwargs['node_id'])
        
        result = self.execution_input_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('increase_wait_factor')
    @with_session
    def increase_wait_factor(self, session, execution_input_id: str) -> Dict[str, Any]:
        self._validate_execution_input_exist(session, execution_input_id)
        
        result = self.execution_input_crud._increase_wait_factor(session, execution_input_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_ready_to_process')
    @with_session
    def get_ready_to_process(self, session, limit: int = 10) -> Dict[str, Any]:
        results = self.execution_input_crud._get_ready_to_process(session, limit)
        return self._serialize_list_result(results, len(results))

