from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from miniflow.database.models import Edge
from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError


class EdgeOrchestrator(BaseOrchestrator):
    """Edge orchestrator for basic CRUD operations and edge management."""

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        """Return the Edge CRUD instance."""
        return self.edge_crud

    @with_session
    def create(self, session: Session, **kwargs) -> Dict[str, Any]:
        # Safe key extraction
        workflow_id = kwargs.get("workflow_id")
        from_node_id = kwargs.get("from_node_id")
        to_node_id = kwargs.get("to_node_id")
        
        try:
            # Check if edge already exists for this combination
            existing = self.edge_crud._filter(session, filters={
                "workflow_id": workflow_id,
                "from_node_id": from_node_id,
                "to_node_id": to_node_id
            })

            if existing:
                # Return existing record instead of creating duplicate
                return self._serialize_single_result(existing[0])

            # Use standard CRUD create (no positional args)
            result = self.edge_crud._create(session, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            # Safe context creation
            context = self._create_error_context("create", 
                workflow_id=workflow_id or "unknown",
                from_node_id=from_node_id or "unknown", 
                to_node_id=to_node_id or "unknown")
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]:
        if not self.edge_crud._exists(session, record_id):
            self._handle_not_found("Edge", record_id, "update")

        try:
            result = self.edge_crud._update(session, record_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.edge_crud._exists(session, record_id):
            self._handle_not_found("Edge", record_id, "delete")

        try:
            result = self.edge_crud._delete(session, record_id)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("delete", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def get_edges_by_workflow(self, session: Session, workflow_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get all edges for a specific workflow."""
        if not workflow_id:
            return []
        try:
            results = self.edge_crud._filter(session, filters={"workflow_id": workflow_id})
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_edges_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_edges_by_node(self, session: Session, node_id: str, direction: str = 'both', include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get edges connected to a specific node."""
        if not node_id:
            return []
        try:
            if direction == 'outgoing':
                results = self.edge_crud._filter(session, filters={"from_node_id": node_id})
                return self._serialize_multiple_results(results, include_relationships, exclude_fields)
            elif direction == 'incoming':
                results = self.edge_crud._filter(session, filters={"to_node_id": node_id})
                return self._serialize_multiple_results(results, include_relationships, exclude_fields)
            else:  # both
                outgoing = self.edge_crud._filter(session, filters={"from_node_id": node_id})
                incoming = self.edge_crud._filter(session, filters={"to_node_id": node_id})
                return self._serialize_multiple_results(outgoing + incoming, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_edges_by_node", node_id=node_id, direction=direction)
            raise OrchestrationError(str(e), context=context) from e
    @with_session
    def get_total_count(self, session: Session) -> int:
        """Get total count of all edges."""
        try:
            return self.edge_crud._count(session) or 0
        except Exception as e:
            context = self._create_error_context("get_total_count")
            raise OrchestrationError(f"Failed to get total edge count: {str(e)}", context=context) from e
