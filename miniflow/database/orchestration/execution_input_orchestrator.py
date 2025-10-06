from typing import Dict, Any, List, Optional
from sqlalchemy import select

from miniflow.database.enums import Roles
from miniflow.database.models import Execution
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class ExecutionInputOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.execution_input_crud

    @with_orchestration_errors('get_execution_input_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get execution input by ID with execution access control.
        User must have access to the parent execution.
        """
        record_id = self._validate_execution_input_exist(session, record_id)
        user_id = self._validate_user_exist(session, user_id)
        
        # Get execution input to find execution_id
        execution_input = self.execution_input_crud._get_by_id(session, record_id)
        if not execution_input:
            return None
        
        # Check if user has access to the execution (at least VIEWER role)
        has_access = self._does_user_have_access(
            session,
            user_id,
            execution_input.execution_id,
            self.user_execution_role_crud,
            min_role=Roles.VIEWER
        )
        
        if not has_access:
            self._raise_permission_denied('access', user_id, execution_input.execution_id, 'execution')
        
        return self._serialize_single_result(
            execution_input,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_execution_inputs')
    @with_session
    def get_all(self, session, *, user_id: str, execution_id: str = None, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all execution inputs accessible to user via execution permissions.
        Optimized with single JOIN query through execution junction table.
        """
        user_id = self._validate_user_exist(session, user_id)
        
        # Build base query with JOIN to execution junction table (SINGLE QUERY OPTIMIZATION)
        query = select(self.execution_input_crud.model)
        query = self._build_parent_junction_query(
            query,
            user_id,
            self.user_execution_role_crud,
            Execution,
            self.execution_input_crud.model,
            parent_id_field='execution_id',
            junction_parent_field='execution_id'
        )
        
        # Optional execution filter
        if execution_id:
            query = query.where(self.execution_input_crud.model.execution_id == execution_id)
        
        # Apply is_deleted filter
        if not include_deleted:
            query = query.where(self.execution_input_crud.model.is_deleted == False)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.execution_input_crud.model, key):
                query = query.where(getattr(self.execution_input_crud.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.execution_input_crud.model, order_by):
            order_column = getattr(self.execution_input_crud.model, order_by)
            query = query.order_by(order_column.desc() if order_desc else order_column)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute single optimized query
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results,
            include_relationships=False,
            exclude_fields=exclude_fields
        )

