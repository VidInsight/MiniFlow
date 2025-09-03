from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError
from miniflow.database.models import Node


class NodeOrchestrator(BaseOrchestrator):
    """Node orchestrator for basic CRUD operations and node management."""

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        """Return the Node CRUD instance."""
        return self.node_crud

    @with_session
    def create(self, session: Session, workflow_id: str, name: str, **kwargs) -> Dict[str, Any]:
        try:
            result = self.node_crud._create_with_validation(session, workflow_id, name, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", workflow_id=workflow_id, name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]:
        if not self.node_crud._exists(session, record_id):
            self._handle_not_found("Node", record_id, "update")

        try:
            result = self.node_crud._update_with_validation(session, record_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", record_id=record_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, record_id: str) -> Dict[str, Any]:
        if not self.node_crud._exists(session, record_id):
            self._handle_not_found("Node", record_id, "delete")

        try:
            result = self.node_crud._delete(session, record_id)
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
    def get_by_name_and_workflow(self, session: Session, name: str, workflow_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get node by name within a specific workflow."""
        try:
            results = self.node_crud._filter(session, filters={"name": name, "workflow_id": workflow_id}, limit=1)
            return self._serialize_single_result(results[0] if results else None, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name_and_workflow", name=name, workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Get all nodes for a specific workflow."""
        try:
            results = self.node_crud._filter(session, filters={"workflow_id": workflow_id})
            return self._serialize_multiple_results(results, include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_nodes_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e