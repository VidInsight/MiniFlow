from typing import Dict, Any, List, Optional

from miniflow.database.enums import Roles
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class FileUploadOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.fileupload_crud

    @with_orchestration_errors('create_file')
    @with_session
    def create(self, session, user_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        
        file_upload = self.fileupload_crud._create(session, created_by=user_id, **kwargs)
        
        self.user_file_role_crud._create(
            session,
            user_id=user_id,
            file_id=file_upload.id,
            role=Roles.OWNER,
            granted_by=user_id
        )
        
        return self._serialize_single_result(file_upload)

    @with_orchestration_errors('update_file')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        result = self.fileupload_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_file_by_id')
    @with_session
    def get_by_id(
        self, 
        session, 
        record_id: str,
        user_id: str,
        include_relationships: bool = False,
        exclude_fields: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get file by ID with RBAC check."""
        self._validate_user_exist(session, user_id)
        
        has_access = self._check_user_has_access_to_resource(
            session, user_id, record_id, 
            self.user_file_role_crud,
            min_role=Roles.VIEWER
        )
        
        if not has_access:
            self._raise_permission_denied('access', user_id, record_id, 'file')
        
        result = self.fileupload_crud._get_by_id(
            session, record_id, include_relationships=include_relationships
        )
        return self._serialize_single_result(
            result, include_relationships=include_relationships, 
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_files')
    @with_session
    def get_all(
        self,
        session,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False,
        exclude_fields: List[str] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get all files accessible to user with SQL-level filtering."""
        self._validate_user_exist(session, user_id)
        
        accessible_file_ids = self._get_user_accessible_resource_ids(
            session, user_id, self.user_file_role_crud,
            resource_field='file_id'
        )
        
        if not accessible_file_ids:
            return []
        
        from sqlalchemy import select
        query = select(self.fileupload_crud.model).where(
            self.fileupload_crud.model.id.in_(accessible_file_ids)
        )
        
        if not include_deleted:
            query = query.where(self.fileupload_crud.model.is_deleted == False)
        
        for key, value in filters.items():
            if hasattr(self.fileupload_crud.model, key):
                query = query.where(getattr(self.fileupload_crud.model, key) == value)
        
        if order_by and hasattr(self.fileupload_crud.model, order_by):
            order_column = getattr(self.fileupload_crud.model, order_by)
            query = query.order_by(order_column.desc() if order_desc else order_column)
        
        query = query.offset(skip).limit(limit)
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results, include_relationships=False, 
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('add_user_to_file')
    @with_session
    def add_user(self, session, file_id: str, user_id: str, role: Roles, granted_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, granted_by)
        
        user_role = self.user_file_role_crud._add_user(session, file_id, user_id, role, granted_by)
        return self._serialize_single_result(user_role)

    @with_orchestration_errors('remove_user_from_file')
    @with_session
    def remove_user(self, session, file_id: str, user_id: str, removed_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, removed_by)
        
        success = self.user_file_role_crud._remove_user(session, file_id, user_id, removed_by)
        return {'deleted': success, 'file_id': file_id, 'user_id': user_id}

    @with_orchestration_errors('update_file_user_role')
    @with_session
    def update_user_role(self, session, file_id: str, user_id: str, new_role: Roles, updated_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, updated_by)
        
        user_role = self.user_file_role_crud._update_user_role(session, file_id, user_id, new_role, updated_by)
        return self._serialize_single_result(user_role)

    @with_orchestration_errors('transfer_file_ownership')
    @with_session
    def transfer_ownership(self, session, file_id: str, current_owner_id: str, new_owner_id: str) -> Dict[str, Any]:
        self._validate_user_exist(session, current_owner_id)
        self._validate_user_exist(session, new_owner_id)
        
        return self.user_file_role_crud._transfer_ownership(session, file_id, current_owner_id, new_owner_id)

    @with_orchestration_errors('revoke_all_file_non_owners')
    @with_session
    def revoke_all_non_owners(self, session, file_id: str, revoked_by: str) -> Dict[str, Any]:
        self._validate_user_exist(session, revoked_by)
        
        return self.user_file_role_crud._revoke_all_non_owners(session, file_id, revoked_by)

