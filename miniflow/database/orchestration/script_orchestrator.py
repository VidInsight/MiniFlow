from typing import Dict, Any

from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class ScriptOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.script_crud

    @with_orchestration_errors('create_script')
    @with_session
    def create(self, session, user_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        
        script = self.script_crud._create(session, created_by=user_id, **kwargs)
        return self._serialize_single_result(script)

    @with_orchestration_errors('update_script')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'approved_by' in kwargs and kwargs['approved_by']:
            self._validate_user_exist(session, kwargs['approved_by'])
        
        result = self.script_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('update_test_stats')
    @with_session
    def update_test_stats(self, session, script_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_script_exist(session, script_id)
        
        result = self.script_crud._update_test_stats(session, script_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_test_stats')
    @with_session
    def get_test_stats(self, session, script_id: str) -> Dict[str, Any]:
        self._validate_script_exist(session, script_id)
        
        result = self.script_crud._get_test_stats(session, script_id)
        return result

    @with_orchestration_errors('update_performance_stats')
    @with_session
    def update_performance_stats(self, session, script_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_script_exist(session, script_id)
        
        result = self.script_crud._update_performance_stats(session, script_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_performance_stats')
    @with_session
    def get_performance_stats(self, session, script_id: str) -> Dict[str, Any]:
        self._validate_script_exist(session, script_id)
        
        result = self.script_crud._get_performance_stats(session, script_id)
        return result

    @with_orchestration_errors('approve_script')
    @with_session
    def approve(self, session, script_id: str, approved_by: str) -> Dict[str, Any]:
        self._validate_script_exist(session, script_id)
        self._validate_user_exist(session, approved_by)
        
        result = self.script_crud._approve(session, script_id, approved_by)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_security_stats')
    @with_session
    def get_security_stats(self, session, script_id: str) -> Dict[str, Any]:
        self._validate_script_exist(session, script_id)
        
        result = self.script_crud._get_security_stats(session, script_id)
        return result

