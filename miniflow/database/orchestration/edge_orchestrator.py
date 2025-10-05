from typing import Dict, Any, List, Optional

from miniflow.database.enums import ConditionType
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
    def create(self, session, user_id: str, workflow_id: str, from_node_id: str, to_node_id: str, **kwargs) -> Dict[str, Any]:
        self._validate_user_exist(session, user_id)
        self._validate_workflow_exist(session, workflow_id)
        self._validate_node_exist(session, from_node_id)
        self._validate_node_exist(session, to_node_id)
        
        edge = self.edge_crud._create(
            session,
            workflow_id=workflow_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            created_by=user_id,
            **kwargs
        )
        
        return self._serialize_single_result(edge)

    @with_orchestration_errors('update_edge')
    @with_session
    def update(self, session, record_id: str, **kwargs) -> Dict[str, Any]:
        if 'workflow_id' in kwargs:
            self._validate_workflow_exist(session, kwargs['workflow_id'])
        
        if 'from_node_id' in kwargs:
            self._validate_node_exist(session, kwargs['from_node_id'])
        
        if 'to_node_id' in kwargs:
            self._validate_node_exist(session, kwargs['to_node_id'])
        
        result = self.edge_crud._update(session, record_id, **kwargs)
        return self._serialize_single_result(result)

    @with_orchestration_errors('get_next_nodes')
    @with_session
    def get_next_nodes(self, session, from_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Dict[str, Any]]:
        self._validate_node_exist(session, from_node_id)
        
        edges = self.edge_crud._get_next_nodes(session, from_node_id, condition_type)
        return self._serialize_multiple_results(edges)

    @with_orchestration_errors('get_previous_nodes')
    @with_session
    def get_previous_nodes(self, session, to_node_id: str, condition_type: Optional[ConditionType] = None) -> List[Dict[str, Any]]:
        self._validate_node_exist(session, to_node_id)
        
        edges = self.edge_crud._get_previous_nodes(session, to_node_id, condition_type)
        return self._serialize_multiple_results(edges)

