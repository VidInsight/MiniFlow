from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from miniflow.database.orchestration.base_orchestrator import BaseOrchestrator, with_session
from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity, ErrorContext
from miniflow.database.models import Node


class NodeOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        return self.node_crud

    @with_session
    def create(self, session: Session, **kwargs) -> Dict[str, Any]:
        try:
            script_id = kwargs.get('script_id')
            script = self.script_crud._get_by_id(session, script_id)
            
            if script and script.input_schema:
                kwargs['output_params'] = script.output_schema
                kwargs['input_params'] = script.input_schema
                for key in kwargs['input_params']:
                    kwargs['input_params'][key].update({'value': None})

            result = self.node_crud._create(session, **kwargs)
            return self._serialize_single_result(result)

        except Exception as e:
            name = kwargs.get("name", "unknown")
            workflow_id = kwargs.get("workflow_id", "unknown")
            context = self._create_error_context("create", workflow_id=workflow_id, name=name)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, record_id: str, **kwargs) -> Dict[str, Any]:
        if not self.node_crud._exists(session, record_id):
            self._handle_not_found("Node", record_id, "update")

        try:
            if "input_params" in kwargs:
                for key, value in kwargs['input_params'].items():
                    kwargs['input_params'][key].update({'value': value.get('value', None)})

            result = self.node_crud._update(session, record_id, **kwargs)
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
        if not name or not workflow_id:
            return None
        try:
            results = self.node_crud._filter(session, filters={"name": name.strip(), "workflow_id": workflow_id}, limit=1)
            if not results:
                return None
            return self._serialize_single_result(results[0], include_relationships, exclude_fields)
        except Exception as e:
            context = self._create_error_context("get_by_name_and_workflow", name=name, workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def get_by_workflow(self, session: Session, workflow_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        if not workflow_id:
            self.logger.warning("get_by_workflow called with empty workflow_id")
            return []
        try:
            self.logger.info(f"Getting nodes for workflow_id: {workflow_id}")
            results = self.node_crud._filter(session, filters={"workflow_id": workflow_id})
            self.logger.info(f"Found {len(results)} nodes for workflow {workflow_id}")
            serialized = self._serialize_multiple_results(results, include_relationships, exclude_fields)
            self.logger.info(f"Serialized {len(serialized)} nodes")
            return serialized

        except Exception as e:
            self.logger.error(f"Error in get_by_workflow: {str(e)}", exc_info=True)
            context = self._create_error_context("get_nodes_by_workflow", workflow_id=workflow_id)
            raise OrchestrationError(str(e), context=context) from e