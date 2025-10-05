from typing import Dict, Any

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class ExecutionOutputOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.execution_output_crud

    @with_orchestration_errors('create_execution_output')
    @with_session
    def create(self, session, user_id: str, execution_id: str, workflow_id: str, node_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_workflow_exist(session, workflow_id)
        self._validate_node_exist(session, node_id)
        
        execution_output = self.execution_output_crud._create(
            session,
            execution_id=execution_id,
            workflow_id=workflow_id,
            node_id=node_id,
            created_by=user_id,
            **kwargs
        )
        
        return self._serialize_single_result(execution_output)

    @with_orchestration_errors('update_execution_output')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'workflow_id' in kwargs:
            self._validate_workflow_exist(session, kwargs['workflow_id'])
        
        if 'node_id' in kwargs:
            self._validate_node_exist(session, kwargs['node_id'])
        
        result = self.execution_output_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('collect_all_results_by_execution_id')
    @with_session
    def collect_all_results_by_execution_id(self, session, execution_id: str) -> Dict[str, Any]:
        self._validate_execution_exist(session, execution_id)
        
        results = self.execution_output_crud._collect_all_results_by_execution_id(session, execution_id)
        return {'results': results, 'execution_id': execution_id}

