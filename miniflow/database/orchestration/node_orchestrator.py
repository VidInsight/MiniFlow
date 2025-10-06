from typing import Dict, Any, List, Optional
from sqlalchemy import select

from miniflow.database.enums import Roles
from miniflow.database.models import Workflow
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
    def create(self, session, *, created_by: str, workflow_id: str, script_id: str, **kwargs) -> Dict[str, Any]:
        created_by = self._validate_user_exist(session, created_by)
        workflow_id = self._validate_workflow_exist(session, workflow_id)
        script_id = self._validate_script_exist(session, script_id)

        script = self.script_crud._get_script(session, script_id)
        if script.input_schema:
            kwargs['input_params'] = script.input_schema.copy()
            kwargs['input_params'].update({'value': None})
        else:
            kwargs['input_params'] = {}

        if script.output_schema:
            kwargs['output_params'] = script.output_schema.copy()
            kwargs['output_params'].update({'value': None})
        else:
            kwargs['output_params'] = {}

        node = self.node_crud._create(
            session,
            workflow_id=workflow_id,
            script_id=script_id,
            created_by=created_by,
            **kwargs
        )
        
        return self._serialize_single_result(node)

    @with_orchestration_errors('update_node')
    @with_session
    def update(self, session, *, updated_by: str, record_id: str, **kwargs) -> Dict[str, Any]:
        updated_by = self._validate_user_exist(session, updated_by)
        record_id = self._validate_node_exist(session, record_id)

        if "input_params" in kwargs:
            node = self.node_crud._get(session, record_id=record_id)
            input_params = node.input_params or {}

            for key, new_value in kwargs["input_params"].items():
                if isinstance(new_value, dict) and isinstance(input_params.get(key), dict):
                    input_params[key].update(new_value)
                else:
                    input_params[key] = new_value

            kwargs['input_params'] = input_params

        result = self.node_crud._update(
            session,
            record_id,
            updated_by=updated_by,
            **kwargs
        )

        return self._serialize_single_result(result)

    @with_orchestration_errors('get_node_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get node by ID with workflow access control."""
        record_id = self._validate_node_exist(session, record_id)
        user_id = self._validate_user_exist(session, user_id)
        
        # Get node to find workflow_id
        node = self.node_crud._get_by_id(session, record_id)
        if not node:
            return None
        
        # Check if user has access to the workflow (at least VIEWER role)
        has_access = self._does_user_have_access(
            session,
            user_id,
            node.workflow_id,
            self.user_workflow_role_crud,
            min_role=Roles.VIEWER
        )
        
        if not has_access:
            self._raise_permission_denied('access', user_id, node.workflow_id, 'workflow')
        
        return self._serialize_single_result(
            node,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_nodes')
    @with_session
    def get_all(self, session, *, user_id: str, workflow_id: str = None, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all nodes accessible to user via workflow permissions.
        Optimized with single JOIN query through workflow junction table.
        """
        user_id = self._validate_user_exist(session, user_id)
        
        # Build base query with JOIN to workflow junction table (SINGLE QUERY OPTIMIZATION)
        query = select(self.node_crud.model)
        query = self._build_parent_junction_query(
            query,
            user_id,
            self.user_workflow_role_crud,
            Workflow,
            self.node_crud.model,
            parent_id_field='workflow_id',
            junction_parent_field='workflow_id'
        )
        
        # Optional workflow filter
        if workflow_id:
            query = query.where(self.node_crud.model.workflow_id == workflow_id)
        
        # Apply is_deleted filter
        if not include_deleted:
            query = query.where(self.node_crud.model.is_deleted == False)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.node_crud.model, key):
                query = query.where(getattr(self.node_crud.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.node_crud.model, order_by):
            order_column = getattr(self.node_crud.model, order_by)
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

