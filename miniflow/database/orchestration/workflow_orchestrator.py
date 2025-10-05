from typing import Dict, Any, Set, List, Optional

from miniflow.database.enums import Roles
from miniflow.core.exceptions import ValidationError, ErrorSeverity, ErrorContext
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)


class WorkflowOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.workflow_crud

    @with_orchestration_errors('create_workflow')
    @with_session
    def create(self, session, user_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        
        workflow = self.workflow_crud._create(session, created_by=user_id, **kwargs)
        
        self.user_workflow_role_crud._create(
            session,
            user_id=user_id,
            workflow_id=workflow.id,
            role=Roles.OWNER,
            granted_by=user_id
        )
        
        return self._serialize_single_result(workflow)

    @with_orchestration_errors('update_workflow')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        result = self.workflow_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_workflow_by_id')
    @with_session
    def get_by_id(
        self, 
        session, 
        record_id: str,
        user_id: str,
        include_relationships: bool = False,
        exclude_fields: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get workflow by ID with RBAC check.
        User must have at least VIEWER role on the workflow.
        
        Args:
            session: Database session
            record_id: Workflow ID
            user_id: User ID making the request
            include_relationships: Include related data
            exclude_fields: Fields to exclude from response
            
        Returns:
            Workflow dict or None
            
        Raises:
            OrchestrationError: If user doesn't have access
        """
        # Validate IDs
        self._validate_workflow_exist(session, record_id)
        self._validate_user_exist(session, user_id)
        
        # Check user has access (at least VIEWER role)
        has_access = self._check_user_has_access_to_resource(
            session, 
            user_id, 
            record_id, 
            self.user_workflow_role_crud,
            min_role=Roles.VIEWER
        )
        
        if not has_access:
            self._raise_permission_denied('access', user_id, record_id, 'workflow')
        
        # Get and return
        result = self.workflow_crud._get_by_id(
            session, record_id, include_relationships=include_relationships
        )
        return self._serialize_single_result(
            result, 
            include_relationships=include_relationships, 
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_workflows')
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
        """
        Get all workflows accessible to user.
        Only returns workflows where user has at least VIEWER role.
        Uses SQL-level filtering for performance.
        
        Args:
            session: Database session
            user_id: User ID making the request
            skip: Pagination offset
            limit: Max results
            order_by: Field to sort by
            order_desc: Sort descending
            include_deleted: Include soft-deleted records
            exclude_fields: Fields to exclude from response
            **filters: Additional filters
            
        Returns:
            List of workflow dicts user has access to
        """
        # Validate user
        self._validate_user_exist(session, user_id)
        
        # Get user's accessible workflow IDs from junction table
        accessible_workflow_ids = self._get_user_accessible_resource_ids(
            session,
            user_id,
            self.user_workflow_role_crud,
            resource_field='workflow_id'
        )
        
        # If user has no workflows, return empty list
        if not accessible_workflow_ids:
            return []
        
        # Query workflows using SQL WHERE IN - much more efficient!
        # Build query with accessible IDs filter
        from sqlalchemy import select, and_
        
        query = select(self.workflow_crud.model).where(
            self.workflow_crud.model.id.in_(accessible_workflow_ids)
        )
        
        # Apply is_deleted filter
        if not include_deleted:
            query = query.where(self.workflow_crud.model.is_deleted == False)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.workflow_crud.model, key):
                query = query.where(getattr(self.workflow_crud.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.workflow_crud.model, order_by):
            order_column = getattr(self.workflow_crud.model, order_by)
            if order_desc:
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
        
        # Apply pagination at SQL level
        query = query.offset(skip).limit(limit)
        
        # Execute query
        results = session.execute(query).scalars().all()
        
        return self._serialize_multiple_results(
            results,
            include_relationships=False,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('add_user_to_workflow')
    @with_session
    def add_user(self, session, workflow_id: str, user_id: str, role: Roles, granted_by: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, granted_by)
        
        user_role = self.user_workflow_role_crud._add_user(session, workflow_id, user_id, role, granted_by)
        return self._serialize_single_result(user_role)

    @with_orchestration_errors('remove_user_from_workflow')
    @with_session
    def remove_user(self, session, workflow_id: str, user_id: str, removed_by: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, removed_by)
        
        success = self.user_workflow_role_crud._remove_user(session, workflow_id, user_id, removed_by)
        return {'deleted': success, 'workflow_id': workflow_id, 'user_id': user_id}

    @with_orchestration_errors('update_workflow_user_role')
    @with_session
    def update_user_role(self, session, workflow_id: str, user_id: str, new_role: Roles, updated_by: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        self._validate_user_exist(session, user_id)
        self._validate_user_exist(session, updated_by)
        
        user_role = self.user_workflow_role_crud._update_user_role(session, workflow_id, user_id, new_role, updated_by)
        return self._serialize_single_result(user_role)

    @with_orchestration_errors('transfer_workflow_ownership')
    @with_session
    def transfer_ownership(self, session, workflow_id: str, current_owner_id: str, new_owner_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        self._validate_user_exist(session, current_owner_id)
        self._validate_user_exist(session, new_owner_id)
        
        return self.user_workflow_role_crud._transfer_ownership(session, workflow_id, current_owner_id, new_owner_id)

    @with_orchestration_errors('revoke_all_workflow_non_owners')
    @with_session
    def revoke_all_non_owners(self, session, workflow_id: str, revoked_by: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        self._validate_user_exist(session, revoked_by)
        
        return self.user_workflow_role_crud._revoke_all_non_owners(session, workflow_id, revoked_by)

    @with_orchestration_errors('activate_workflow')
    @with_session
    def activate(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._set_to_active(session, workflow_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('deactivate_workflow')
    @with_session
    def deactivate(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._set_to_deactive(session, workflow_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('set_workflow_to_draft')
    @with_session
    def set_to_draft(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._set_to_draft(session, workflow_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('increment_successful_executions')
    @with_session
    def increment_successful_executions(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._increment_successful_executions(session, workflow_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('increment_failed_executions')
    @with_session
    def increment_failed_executions(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._increment_failed_executions(session, workflow_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('increment_cancelled_executions')
    @with_session
    def increment_cancelled_executions(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._increment_cancelled_executions(session, workflow_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('update_execution_durations')
    @with_session
    def update_execution_durations(self, session, workflow_id: str, duration: float) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        result = self.workflow_crud._update_execution_durations(session, workflow_id, duration)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_execution_stats')
    @with_session
    def get_execution_stats(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        return self.workflow_crud._get_execution_stats(session, workflow_id)

    @with_orchestration_errors('validate_workflow_integrity')
    @with_session
    def validate_workflow_integrity(self, session, workflow_id: str) -> Dict[str, Any]:
        self._validate_workflow_exist(session, workflow_id)
        
        nodes = self.node_crud._get_all(session, workflow_id=workflow_id, include_deleted=False)
        edges = self.edge_crud._get_all(session, workflow_id=workflow_id, include_deleted=False)
        triggers = self.trigger_crud._get_all(session, workflow_id=workflow_id, include_deleted=False)
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'total_triggers': len(triggers)
            }
        }
        
        if len(nodes) == 0:
            validation_result['errors'].append("Workflow has no nodes")
            validation_result['valid'] = False
            return validation_result
        
        node_ids = {node.id for node in nodes}
        
        adjacency_list = {node.id: [] for node in nodes}
        incoming_edges_count = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.from_node_id not in node_ids:
                validation_result['errors'].append(f"Edge references non-existent source node: {edge.from_node_id}")
                validation_result['valid'] = False
                continue
            
            if edge.to_node_id not in node_ids:
                validation_result['errors'].append(f"Edge references non-existent target node: {edge.to_node_id}")
                validation_result['valid'] = False
                continue
            
            adjacency_list[edge.from_node_id].append(edge.to_node_id)
            incoming_edges_count[edge.to_node_id] += 1
        
        start_nodes = [node_id for node_id, count in incoming_edges_count.items() if count == 0]
        
        if len(start_nodes) == 0:
            validation_result['errors'].append("No start node found (all nodes have incoming edges - circular dependency detected)")
            validation_result['valid'] = False
            return validation_result
        
        if len(start_nodes) > 1:
            validation_result['warnings'].append(f"Multiple start nodes detected: {len(start_nodes)} nodes")
        
        visited = set()
        rec_stack = set()
        
        def dfs_check_cycle(node_id: str, path: List[str]) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in adjacency_list.get(node_id, []):
                if neighbor not in visited:
                    if dfs_check_cycle(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    cycle_path = ' → '.join(path + [neighbor])
                    validation_result['errors'].append(f"Circular dependency detected: {cycle_path}")
                    validation_result['valid'] = False
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for start_node in start_nodes:
            if start_node not in visited:
                dfs_check_cycle(start_node, [start_node])
        
        unreachable_nodes = node_ids - visited
        if unreachable_nodes:
            validation_result['warnings'].append(f"Unreachable nodes detected: {len(unreachable_nodes)} nodes")
            validation_result['info']['unreachable_nodes'] = list(unreachable_nodes)
        
        end_nodes = [node_id for node_id in node_ids if len(adjacency_list[node_id]) == 0]
        if len(end_nodes) == 0:
            validation_result['warnings'].append("No end node found (all nodes have outgoing edges)")
        
        orphan_nodes = [node_id for node_id in node_ids 
                       if incoming_edges_count[node_id] == 0 and len(adjacency_list[node_id]) == 0]
        if orphan_nodes:
            validation_result['warnings'].append(f"Orphan nodes detected (no incoming/outgoing edges): {len(orphan_nodes)} nodes")
            validation_result['info']['orphan_nodes'] = orphan_nodes
        
        if len(triggers) == 0:
            validation_result['warnings'].append("No triggers configured for workflow")
        
        for trigger in triggers:
            if not trigger.is_enabled:
                validation_result['info']['disabled_triggers'] = validation_result['info'].get('disabled_triggers', 0) + 1
        
        validation_result['info']['start_nodes'] = start_nodes
        validation_result['info']['end_nodes'] = end_nodes
        validation_result['info']['reachable_nodes'] = len(visited)
        
        return validation_result

