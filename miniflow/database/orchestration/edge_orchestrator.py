from typing import Dict, Any, List, Optional
from sqlalchemy import select

from miniflow.database.enums import ConditionType, Roles
from miniflow.database.models import Workflow
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class EdgeOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.edge_crud

    @with_orchestration_errors('create_edge')
    @with_session
    def create(self, session, *, created_by: str, workflow_id: str, from_node_id: str, to_node_id: str, **kwargs) -> Dict[str, Any]:
        created_by = self._validate_user_exist(session, created_by)
        workflow_id = self._validate_workflow_exist(session, workflow_id)
        from_node_id = self._validate_node_exist(session, from_node_id)
        to_node_id = self._validate_node_exist(session, to_node_id)
        
        edge = self.edge_crud._create(
            session,
            workflow_id=workflow_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            created_by=created_by,
            **kwargs
        )
        
        return self._serialize_single_result(edge)

    @with_orchestration_errors('update_edge')
    @with_session
    def update(self, session, *, updated_by: str, record_id: str, **kwargs) -> Dict[str, Any]:
        updated_by = self._validate_user_exist(session, updated_by)

        if 'from_node_id' in kwargs:
            self._validate_node_exist(session, kwargs['from_node_id'])
        
        if 'to_node_id' in kwargs:
            self._validate_node_exist(session, kwargs['to_node_id'])
        
        result = self.edge_crud._update(
            session,
            record_id,
            updated_by=updated_by,
            **kwargs
        )

        return self._serialize_single_result(result)

    @with_orchestration_errors('get_next_nodes')
    @with_session
    def get_next_nodes(self, session, from_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Dict[str, Any]]:
        from_node_id = self._validate_node_exist(session, from_node_id)
        
        edges = self.edge_crud._get_next_nodes(
            session,
            from_node_id,
            condition_type
        )

        return self._serialize_multiple_results(edges)

    @with_orchestration_errors('get_previous_nodes')
    @with_session
    def get_previous_nodes(self, session, to_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Dict[str, Any]]:
        to_node_id = self._validate_node_exist(session, to_node_id)
        
        edges = self.edge_crud._get_previous_nodes(
            session,
            to_node_id,
            condition_type
        )

        return self._serialize_multiple_results(edges)

    @with_orchestration_errors('get_edge_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get edge by ID with workflow access control."""
        record_id = self._validate_edge_exist(session, record_id)
        user_id = self._validate_user_exist(session, user_id)
        
        # Get edge to find workflow_id
        edge = self.edge_crud._get_by_id(session, record_id)
        if not edge:
            return None
        
        # Check if user has access to the workflow (at least VIEWER role)
        has_access = self._does_user_have_access(
            session,
            user_id,
            edge.workflow_id,
            self.user_workflow_role_crud,
            min_role=Roles.VIEWER
        )
        
        if not has_access:
            self._raise_permission_denied('access', user_id, edge.workflow_id, 'workflow')
        
        return self._serialize_single_result(
            edge,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_edges')
    @with_session
    def get_all(self, session, *, user_id: str, workflow_id: str = None, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all edges accessible to user via workflow permissions.
        Optimized with single JOIN query through workflow junction table.
        """
        user_id = self._validate_user_exist(session, user_id)
        
        # Build base query with JOIN to workflow junction table (SINGLE QUERY OPTIMIZATION)
        query = select(self.edge_crud.model)
        query = self._build_parent_junction_query(
            query,
            user_id,
            self.user_workflow_role_crud,
            Workflow,
            self.edge_crud.model,
            parent_id_field='workflow_id',
            junction_parent_field='workflow_id'
        )
        
        # Optional workflow filter
        if workflow_id:
            query = query.where(self.edge_crud.model.workflow_id == workflow_id)
        
        # Apply is_deleted filter
        if not include_deleted:
            query = query.where(self.edge_crud.model.is_deleted == False)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.edge_crud.model, key):
                query = query.where(getattr(self.edge_crud.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.edge_crud.model, order_by):
            order_column = getattr(self.edge_crud.model, order_by)
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

