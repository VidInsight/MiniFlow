from typing import Dict, Any, List, Optional

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
    def create(self, session, created_by: str, **kwargs) -> Dict[str, Any]:
        created_by = self._validate_user_exist(session, created_by)
        
        script = self.script_crud._create(
            session,
            created_by=created_by,
            **kwargs
        )

        return self._serialize_single_result(script)

    @with_orchestration_errors('update_script')
    @with_session
    def update(self, session, record_id: str, updated_by: str, **kwargs) -> Dict[str, Any]:
        updated_by = self._validate_user_exist(session, updated_by)
        record_id = self._validate_script_exist(session, record_id)
        
        result = self.script_crud._update(
            session,
            record_id,
            updated_by=updated_by,
            **kwargs
        )

        return self._serialize_single_result(result)

    @with_orchestration_errors('update_test_stats')
    @with_session
    def update_test_stats(self, session, script_id: str, **kwargs) -> Dict[str, Any]:
        script_id = self._validate_script_exist(session, script_id)
        
        result = self.script_crud._update_test_stats(session, script_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_test_stats')
    @with_session
    def get_test_stats(self, session, script_id: str) -> Dict[str, Any]:
        script_id = self._validate_script_exist(session, script_id)
        
        result = self.script_crud._get_test_stats(session, script_id)
        return result

    @with_orchestration_errors('update_performance_stats')
    @with_session
    def update_performance_stats(self, session, script_id: str, **kwargs) -> Dict[str, Any]:
        script_id = self._validate_script_exist(session, script_id)
        
        result = self.script_crud._update_performance_stats(session, script_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_performance_stats')
    @with_session
    def get_performance_stats(self, session, script_id: str) -> Dict[str, Any]:
        script_id = self._validate_script_exist(session, script_id)
        
        result = self.script_crud._get_performance_stats(session, script_id)
        return result

    @with_orchestration_errors('approve_script')
    @with_session
    def approve(self, session, script_id: str, approved_by: str) -> Dict[str, Any]:
        script_id = self._validate_script_exist(session, script_id)
        approved_by = self._validate_user_exist(session, approved_by)
        
        result = self.script_crud._approve(session, script_id, approved_by)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_security_stats')
    @with_session
    def get_security_stats(self, session, script_id: str) -> Dict[str, Any]:
        script_id = self._validate_script_exist(session, script_id)
        
        result = self.script_crud._get_security_stats(session, script_id)
        return result

    @with_orchestration_errors('get_script_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get script by ID - Public access (no authorization required).
        Scripts are shared resources accessible to all users.
        """
        record_id = self._validate_script_exist(session, record_id)
        
        result = self.script_crud._get_by_id(
            session,
            record_id,
            include_relationships=include_relationships
        )
        
        return self._serialize_single_result(
            result,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_scripts')
    @with_session
    def get_all(self, session, *, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all scripts - Public access (no authorization required).
        Scripts are a shared library accessible to all users.
        """
        from sqlalchemy import select
        
        query = select(self.script_crud.model)
        
        if not include_deleted:
            query = query.where(self.script_crud.model.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(self.script_crud.model, key):
                query = query.where(getattr(self.script_crud.model, key) == value)
        
        if order_by and hasattr(self.script_crud.model, order_by):
            order_column = getattr(self.script_crud.model, order_by)
            query = query.order_by(order_column.desc() if order_desc else order_column)
        
        query = query.offset(skip).limit(limit)
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results,
            include_relationships=False,
            exclude_fields=exclude_fields
        )

