from typing import Dict, Any

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class TriggerOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.trigger_crud

    @with_orchestration_errors('create_trigger')
    @with_session
    def create(self, session, user_id: str, workflow_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_workflow_exist(session, workflow_id)
        
        trigger = self.trigger_crud._create(
            session,
            workflow_id=workflow_id,
            created_by=user_id,
            **kwargs
        )
        
        return self._serialize_single_result(trigger)

    @with_orchestration_errors('update_trigger')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'workflow_id' in kwargs:
            self._validate_workflow_exist(session, kwargs['workflow_id'])
        
        result = self.trigger_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('activate_trigger')
    @with_session
    def activate(self, session, trigger_id: str) -> Dict[str, Any]:
        self._validate_trigger_exist(session, trigger_id)
        
        result = self.trigger_crud._activate(session, trigger_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('deactivate_trigger')
    @with_session
    def deactivate(self, session, trigger_id: str) -> Dict[str, Any]:
        self._validate_trigger_exist(session, trigger_id)
        
        result = self.trigger_crud._deactivate(session, trigger_id)
        return self._serialize_single_result(result)

