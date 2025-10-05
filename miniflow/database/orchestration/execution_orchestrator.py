from typing import Dict, Any, Optional, List

from miniflow.database.enums import Roles
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class ExecutionOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.execution_crud

    @with_orchestration_errors('create_execution')
    @with_session
    def create(self, session, user_id: str, workflow_id: str, trigger_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_workflow_exist(session, workflow_id)
        
        if trigger_id:
            self._validate_trigger_exist(session, trigger_id)
        
        execution = self.execution_crud._create(
            session,
            workflow_id=workflow_id,
            trigger_id=trigger_id,
            created_by=user_id,
            **kwargs
        )
        
        self.user_execution_role_crud._create(
            session,
            user_id=user_id,
            execution_id=execution.id,
            role=Roles.OWNER,
            granted_by=user_id
        )
        
        return self._serialize_single_result(execution)

    @with_orchestration_errors('update_execution')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'workflow_id' in kwargs:
            self._validate_workflow_exist(session, kwargs['workflow_id'])
        
        if 'trigger_id' in kwargs and kwargs['trigger_id']:
            self._validate_trigger_exist(session, kwargs['trigger_id'])
        
        result = self.execution_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_execution_by_id')
    @with_session
    def get_by_id(self, session, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get execution by ID with RBAC check."""
        self._validate_user_exist(session, user_id)
        has_access = self._check_user_has_access_to_resource(session, user_id, record_id, self.user_execution_role_crud, min_role=Roles.VIEWER)
        if not has_access:
            self._raise_permission_denied('access', user_id, record_id, 'execution')
        result = self.execution_crud._get_by_id(session, record_id, include_relationships=include_relationships)
        return self._serialize_single_result(result, include_relationships=include_relationships, exclude_fields=exclude_fields)

    @with_orchestration_errors('get_all_executions')
    @with_session
    def get_all(self, session, user_id: str, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """Get all executions accessible to user with SQL-level filtering."""
        self._validate_user_exist(session, user_id)
        accessible_execution_ids = self._get_user_accessible_resource_ids(session, user_id, self.user_execution_role_crud, resource_field='execution_id')
        if not accessible_execution_ids:
            return []
        from sqlalchemy import select
        query = select(self.execution_crud.model).where(self.execution_crud.model.id.in_(accessible_execution_ids))
        if not include_deleted:
            query = query.where(self.execution_crud.model.is_deleted == False)
        for key, value in filters.items():
            if hasattr(self.execution_crud.model, key):
                query = query.where(getattr(self.execution_crud.model, key) == value)
        if order_by and hasattr(self.execution_crud.model, order_by):
            order_column = getattr(self.execution_crud.model, order_by)
            query = query.order_by(order_column.desc() if order_desc else order_column)
        query = query.offset(skip).limit(limit)
        results = session.execute(query).scalars().all()
        return self._serialize_multiple_results(results, include_relationships=False, exclude_fields=exclude_fields)

    @with_orchestration_errors('add_user_to_execution')
    @with_session
    def add_user(self, session, execution_id: str, user_id: str, role: Roles, granted_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, granted_by)
        
        user_role = self.user_execution_role_crud._add_user(session, execution_id, user_id, role, granted_by)
        return self._serialize_single_result(user_role)

    @with_orchestration_errors('remove_user_from_execution')
    @with_session
    def remove_user(self, session, execution_id: str, user_id: str, removed_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, removed_by)
        
        success = self.user_execution_role_crud._remove_user(session, execution_id, user_id, removed_by)
        return {'deleted': success, 'execution_id': execution_id, 'user_id': user_id}

    @with_orchestration_errors('update_execution_user_role')
    @with_session
    def update_user_role(self, session, execution_id: str, user_id: str, new_role: Roles, updated_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, updated_by)
        
        user_role = self.user_execution_role_crud._update_user_role(session, execution_id, user_id, new_role, updated_by)
        return self._serialize_single_result(user_role)

    @with_orchestration_errors('transfer_execution_ownership')
    @with_session
    def transfer_ownership(self, session, execution_id: str, current_owner_id: str, new_owner_id: str) -> Dict[str, Any]:
        self._validate_user_exist(session, current_owner_id)
        self._validate_user_exist(session, new_owner_id)
        
        return self.user_execution_role_crud._transfer_ownership(session, execution_id, current_owner_id, new_owner_id)

    @with_orchestration_errors('revoke_all_execution_non_owners')
    @with_session
    def revoke_all_non_owners(self, session, execution_id: str, revoked_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, revoked_by)
        
        return self.user_execution_role_crud._revoke_all_non_owners(session, execution_id, revoked_by)

