from typing import Dict, Any

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class NodeOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.node_crud

    @with_orchestration_errors('create_node')
    @with_session
    def create(self, session, user_id: str, workflow_id: str, script_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_workflow_exist(session, workflow_id)
        self._validate_script_exist(session, script_id)
        
        node = self.node_crud._create(
            session,
            workflow_id=workflow_id,
            script_id=script_id,
            created_by=user_id,
            **kwargs
        )
        
        return self._serialize_single_result(node)

    @with_orchestration_errors('update_node')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'workflow_id' in kwargs:
            self._validate_workflow_exist(session, kwargs['workflow_id'])
        
        if 'script_id' in kwargs:
            self._validate_script_exist(session, kwargs['script_id'])
        
        result = self.node_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

