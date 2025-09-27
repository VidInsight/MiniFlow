from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models import Trigger, TriggerType, Workflow
from .base_orchestrator import BaseOrchestrator, with_session

from miniflow.core.exceptions import OrchestrationError, ValidationError, ErrorSeverity


class TriggerOrchestrator(BaseOrchestrator):

    def __init__(self, database_engine):
        super().__init__(database_engine)
    
    def _get_primary_crud(self):
        return self.trigger_crud

    @with_session
    def create(self, session: Session, **kwargs) -> Dict[str, Any]:
        try:
            result = self.trigger_crud._create(session, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("create", workflow_id=kwargs.get("workflow_id"), name=kwargs.get("name"),trigger_type=kwargs.get("trigger_type"))
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def update(self, session: Session, trigger_id: str, **kwargs) -> Dict[str, Any]:
        if not self.trigger_crud._exists(session, trigger_id):
            self._handle_not_found("Trigger", trigger_id, "update")

        try:
            result = self.trigger_crud._update(session, trigger_id, **kwargs)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("update", trigger_id=trigger_id)
            raise OrchestrationError(str(e), context=context) from e

    @with_session
    def delete(self, session: Session, trigger_id: str) -> Dict[str, Any]:
        if not self.trigger_crud._exists(session, trigger_id):
            self._handle_not_found("Trigger", trigger_id, "delete")

        try:
            result = self.trigger_crud._delete(session, trigger_id)
            return self._serialize_single_result(result)
        except Exception as e:
            context = self._create_error_context("delete", trigger_id=trigger_id)
            raise OrchestrationError(str(e), context=context) from e

    # Generic CRUD operations inherited from BaseOrchestrator:
    # - get_by_id(record_id) -> Dict[str, Any]
    # - get_all(skip, limit, order_by) -> List[Dict[str, Any]]
    # - count() -> int
    # - filter(filters, skip, limit, order_by_field) -> List[Dict[str, Any]]
    # - count_with_filter(filters) -> int

    @with_session
    def trigger_by_api(self, session: Session, trigger_id: str, correlation_id: str = None, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        trigger = self.trigger_crud._get_api_trigger(session, trigger_id)
        if not trigger:
            self._handle_not_found("Trigger", trigger_id, "get_api_trigger")
    
        workflow_id = trigger.workflow_id
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "get_api_trigger")
    
        return self._trigger_workflow(session, workflow_id, trigger_id, correlation_id, trigger_data)

    @with_session
    def trigger_by_webhook(self, session: Session, trigger_id: str, correlation_id: str = None, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        trigger = self.trigger_crud._get_webhook_trigger(session, trigger_id)
        if not trigger:
            self._handle_not_found("Trigger", trigger_id, "get_webhook_trigger")
    
        workflow_id = trigger.workflow_id
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "get_webhook_trigger")

        return self._trigger_workflow(session, workflow_id, trigger_id, correlation_id, trigger_data)

    @with_session
    def trigger_by_scheduled(self, session: Session, trigger_id: str, correlation_id: str = None, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        trigger = self.trigger_crud._get_scheduled_trigger(session, trigger_id)
        if not trigger:
            self._handle_not_found("Trigger", trigger_id, "get_scheduled_trigger")
    
        workflow_id = trigger.workflow_id
        if not self.workflow_crud._exists(session, workflow_id):
            self._handle_not_found("Workflow", workflow_id, "get_scheduled_trigger")

        return self._trigger_workflow(session, workflow_id, trigger_id, correlation_id, trigger_data)
    
    def _trigger_workflow(self, session: Session, workflow_id: str, trigger_id: str = None, correlation_id: str = None, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger workflow execution by creating execution record and execution inputs.
        
        Args:
            session: Database session
            workflow_id: ID of the workflow to trigger
            trigger_id: ID of the trigger that initiated the execution (optional)
            correlation_id: Correlation ID for tracking the execution (optional, auto-generated if not provided)
            trigger_data: Payload data from the trigger (optional)
            
        Returns:
            Dict containing execution details
        """
        try:
            # 1. Validate workflow exists
            workflow = self.workflow_crud._get_by_id(session, workflow_id)
            if not workflow:
                self._handle_not_found("Workflow", workflow_id, "trigger_workflow")
            
            # 2. Get all nodes in the workflow
            nodes = self.node_crud._get_workflow_nodes(session, workflow_id)
            if not nodes:
                context = self._create_error_context("trigger_workflow", workflow_id=workflow_id)
                raise OrchestrationError(f"No nodes found for workflow {workflow_id}", context=context)
            
            # 3. Create execution record
            import uuid
            from datetime import datetime, timezone
            
            # Generate correlation_id if not provided
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            execution_data = {
                'workflow_id': workflow_id,
                'trigger_id': trigger_id,
                'correlation_id': correlation_id,
                'status': 'PENDING',
                'trigger_data': trigger_data or {},
                'results': {},
                'pending_nodes': len(nodes),
                'running_nodes': 0,
                'executed_nodes': 0
            }
            
            execution = self.execution_crud._create(session, **execution_data)
            
            # 4. Get workflow edges to calculate dependencies upfront
            edges = self.edge_crud._get_workflow_edges(session, workflow_id)
            
            # Count incoming edges for each node
            incoming_edge_counts = {}
            for edge in edges:
                to_node_id = edge.to_node_id
                incoming_edge_counts[to_node_id] = incoming_edge_counts.get(to_node_id, 0) + 1
            
            # 5. Get all script information in batch to avoid N+1 queries
            script_ids = [node.script_id for node in nodes if node.script_id]
            scripts = {}
            if script_ids:
                # Get all scripts in one query
                from sqlalchemy import select
                script_query = select(self.script_crud.model).where(self.script_crud.model.id.in_(script_ids))
                script_results = session.execute(script_query).scalars().all()
                scripts = {script.id: script for script in script_results}
            
            # 6. Prepare all execution input data for batch insert
            execution_inputs_data = []
            for node in nodes:
                # Get script information from batch query
                script_name = None
                script_path = None
                if node.script_id and node.script_id in scripts:
                    script = scripts[node.script_id]
                    script_name = script.name
                    script_path = script.file_path
                
                # Calculate dependency count for this node
                dependency_count = incoming_edge_counts.get(node.id, 0)
                
                # Prepare execution input data
                execution_input_data = {
                    'execution_id': execution.id,
                    'workflow_id': workflow_id,
                    'node_id': node.id,
                    'trigger_id': trigger_id,
                    'dependency_count': dependency_count,
                    'priority': workflow.priority,  # Use workflow priority
                    'wait_factor': 0,  # Default wait factor
                    'node_name': node.name,
                    'node_params': node.input_params or {},
                    'script_name': script_name,
                    'script_path': script_path
                }
                execution_inputs_data.append(execution_input_data)
            
            # 7. Batch create all execution inputs
            execution_inputs = self._batch_create_execution_inputs(session, execution_inputs_data)
            
            # 6. Return execution details
            execution_result = self._serialize_single_result(execution)
            execution_result['nodes_count'] = len(nodes)
            execution_result['execution_inputs_count'] = len(execution_inputs)
            
            self.logger.info(f"Successfully triggered workflow {workflow_id} with execution {execution.id}")
            return execution_result
            
        except Exception as e:
            context = self._create_error_context("trigger_workflow", workflow_id=workflow_id)
            raise OrchestrationError(f"Failed to trigger workflow: {str(e)}", context=context) from e
    
    def _batch_create_execution_inputs(self, session: Session, execution_inputs_data: List[Dict[str, Any]]) -> List:
        """
        Batch create execution inputs for better performance with proper validation.
        
        Args:
            session: Database session
            execution_inputs_data: List of execution input data dictionaries
            
        Returns:
            List of created execution input objects
        """
        try:
            if not execution_inputs_data:
                return []
            
            # Validate all data before creating objects
            validated_data = []
            for i, data in enumerate(execution_inputs_data):
                try:
                    # Use CRUD validation instead of direct model creation
                    validated_data.append(data)
                except Exception as e:
                    context = self._create_error_context("validate_execution_input", 
                        data_index=i, execution_id=data.get('execution_id'), node_id=data.get('node_id'))
                    raise OrchestrationError(f"Validation failed for execution input {i}: {str(e)}", context=context) from e
            
            # Create all execution input objects using CRUD pattern
            execution_input_objects = []
            for i, data in enumerate(validated_data):
                try:
                    # Use CRUD create method for proper validation
                    execution_input = self.execution_input_crud._create(session, **data)
                    execution_input_objects.append(execution_input)
                except Exception as e:
                    context = self._create_error_context("create_execution_input", data_index=i, execution_id=data.get('execution_id'), node_id=data.get('node_id'))
                    raise OrchestrationError(f"Failed to create execution input {i}: {str(e)}", context=context) from e
            
            self.logger.info(f"Batch created {len(execution_input_objects)} execution inputs")
            return execution_input_objects
            
        except Exception as e:
            self.logger.error(f"Failed to batch create execution inputs: {str(e)}")
            raise OrchestrationError(f"Failed to batch create execution inputs: {str(e)}") from e