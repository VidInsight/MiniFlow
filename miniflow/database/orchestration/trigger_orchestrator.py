from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from miniflow.database.models import Workflow
from .base_orchestrator import (
    BaseOrchestrator,
    with_session,
    with_orchestration_errors
)
from miniflow.core.exceptions import OrchestrationError
from ..enums import ExecutionStatus, Roles


class TriggerOrchestrator(BaseOrchestrator):

    def _get_primary_crud(self):
        return self.trigger_crud

    @with_orchestration_errors('create_trigger')
    @with_session
    def create(self, session, created_by: str, workflow_id: str, **kwargs) -> Dict[str, Any]:
        created_by = self._validate_user_exist(session, created_by)
        workflow_id = self._validate_workflow_exist(session, workflow_id)
        
        trigger = self.trigger_crud._create(
            session,
            workflow_id=workflow_id,
            created_by=created_by,
            **kwargs
        )
        
        return self._serialize_single_result(trigger)

    @with_orchestration_errors('update_trigger')
    @with_session
    def update(self, session, record_id: str, updated_by: str, **kwargs) -> Dict[str, Any]:
        record_id = self._validate_trigger_exist(session, record_id)
        updated_by = self._validate_user_exist(session, updated_by)
        
        result = self.trigger_crud._update(
            session,
            record_id,
            updated_by=updated_by,
            **kwargs
        )
        return self._serialize_single_result(result)

    @with_orchestration_errors('activate_trigger')
    @with_session
    def activate(self, session, trigger_id: str) -> Dict[str, Any]:
        trigger_id = self._validate_trigger_exist(session, trigger_id)
        
        result = self.trigger_crud._activate(session, trigger_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('deactivate_trigger')
    @with_session
    def deactivate(self, session, trigger_id: str) -> Dict[str, Any]:
        trigger_id = self._validate_trigger_exist(session, trigger_id)
        
        result = self.trigger_crud._deactivate(session, trigger_id)
        return self._serialize_single_result(result)

    @with_orchestration_errors('trigger_by_api')
    @with_session
    def trigger_by_api(self, session, trigger_id: str, created_by: str, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        trigger_id = self._validate_trigger_exist(session, trigger_id)
        created_by = self._validate_user_exist(session, created_by)
        trigger = self.trigger_crud._get_by_id(session, trigger_id)

        workflow_id = trigger.workflow_id
        
        # Check if user has EDITOR or OWNER role on the workflow
        has_access = self._does_user_have_access(
            session,
            created_by,
            workflow_id,
            self.user_workflow_role_crud,
            min_role=Roles.EDITOR
        )
        
        if not has_access:
            self._raise_permission_denied('trigger', created_by, workflow_id, 'workflow')
        
        return self._trigger_workflow(session, workflow_id, created_by, trigger_id, trigger_data)

    @with_orchestration_errors('trigger_by_webhook')
    @with_session
    def trigger_by_webhook(self, session, trigger_id: str, created_by: str, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        trigger_id = self._validate_trigger_exist(session, trigger_id)
        created_by = self._validate_user_exist(session, created_by)
        trigger = self.trigger_crud._get_by_id(session, trigger_id)

        workflow_id = trigger.workflow_id
        
        # Check if user has EDITOR or OWNER role on the workflow
        has_access = self._does_user_have_access(
            session,
            created_by,
            workflow_id,
            self.user_workflow_role_crud,
            min_role=Roles.EDITOR
        )
        
        if not has_access:
            self._raise_permission_denied('trigger', created_by, workflow_id, 'workflow')
        
        return self._trigger_workflow(session, workflow_id, created_by, trigger_id, trigger_data)

    @with_orchestration_errors('trigger_by_scheduled')
    @with_session
    def trigger_by_scheduled(self, session, trigger_id: str, created_by: str, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:
        trigger_id = self._validate_trigger_exist(session, trigger_id)
        created_by = self._validate_user_exist(session, created_by)
        trigger = self.trigger_crud._get_by_id(session, trigger_id)

        workflow_id = trigger.workflow_id
        
        # Check if user has EDITOR or OWNER role on the workflow
        has_access = self._does_user_have_access(
            session,
            created_by,
            workflow_id,
            self.user_workflow_role_crud,
            min_role=Roles.EDITOR
        )
        
        if not has_access:
            self._raise_permission_denied('trigger', created_by, workflow_id, 'workflow')
        
        return self._trigger_workflow(session, workflow_id, created_by, trigger_id, trigger_data)


    def _trigger_workflow(self, session: Session, workflow_id: str, created_by: str, trigger_id: str = None, trigger_data: Dict[str, Any] = None) -> Dict[str, Any]:

        try:
            # 1. Validate workflow exists
            workflow = self.workflow_crud._get_by_id(session, workflow_id)
            if not workflow:
                self._handle_not_found("Workflow", workflow_id, "trigger_workflow")
            
            # 2. Get all nodes in the workflow
            nodes = self.node_crud._get_all(session, workflow_id=workflow_id, include_deleted=False)
            if not nodes:
                context = self._create_error_context("trigger_workflow", workflow_id=workflow_id)
                raise OrchestrationError(f"No nodes found for workflow {workflow_id}", context=context)
            
            # 3. Create execution record with user role assignment
            execution_data = {
                'trigger_id': trigger_id,
                'status': ExecutionStatus.PENDING,
                'trigger_data': trigger_data or {},
                'results': {},
                'pending_nodes': len(nodes),
                'running_nodes': 0,
                'executed_nodes': 0
            }
            
            # Use execution orchestrator to properly create execution with user roles
            from .execution_orchestrator import ExecutionOrchestrator
            execution_orch = ExecutionOrchestrator(self.engine)
            execution_result = execution_orch.create(
                created_by=created_by,
                workflow_id=workflow_id,
                **execution_data
            )
            
            # Get the actual execution object for further processing
            execution = self.execution_crud._get_by_id(session, execution_result['id'])
            
            # 4. Get workflow edges to calculate dependencies upfront
            edges = self.edge_crud._get_by_workflow(session, workflow_id=workflow_id, limit=10000, include_deleted=False)
            
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
                    'dependency_count': dependency_count,
                    'priority': workflow.priority,  # Use workflow priority
                    'wait_factor': 0,  # Default wait factor
                    'node_name': node.name,
                    'node_params': node.input_params or {},
                    'script_name': script_name or 'unknown',
                    'script_path': script_path or 'unknown'
                }
                execution_inputs_data.append(execution_input_data)
            
            # 7. Batch create all execution inputs
            execution_inputs = self._batch_create_execution_inputs(session, execution_inputs_data, created_by)
            
            # 8. Return execution details
            execution_result = self._serialize_single_result(execution)
            execution_result['nodes_count'] = len(nodes)
            execution_result['execution_inputs_count'] = len(execution_inputs)
            
            self.logger.info(f"Successfully triggered workflow {workflow_id} with execution {execution.id}")
            return execution_result
            
        except Exception as e:
            context = self._create_error_context("trigger_workflow", workflow_id=workflow_id)
            raise OrchestrationError(f"Failed to trigger workflow: {str(e)}", context=context) from e
    
    def _batch_create_execution_inputs(self, session: Session, execution_inputs_data: List[Dict[str, Any]], created_by: str) -> List:
        """
        Batch create execution inputs for better performance with proper validation.
        
        Args:
            session: Database session
            execution_inputs_data: List of execution input data dictionaries
            created_by: User ID who initiated the execution
            
        Returns:
            List of created execution input objects
        """
        try:
            if not execution_inputs_data:
                return []
            
            # Create all execution input objects using CRUD pattern
            execution_input_objects = []
            for i, data in enumerate(execution_inputs_data):
                try:
                    # Add created_by to each execution input
                    data['created_by'] = created_by
                    # Use CRUD create method for proper validation
                    execution_input = self.execution_input_crud._create(session, **data)
                    execution_input_objects.append(execution_input)
                except Exception as e:
                    context = self._create_error_context("create_execution_input", 
                        data_index=i, 
                        execution_id=data.get('execution_id'), 
                        node_id=data.get('node_id'))
                    raise OrchestrationError(f"Failed to create execution input {i}: {str(e)}", context=context) from e
            
            self.logger.info(f"Batch created {len(execution_input_objects)} execution inputs")
            return execution_input_objects
            
        except Exception as e:
            self.logger.error(f"Failed to batch create execution inputs: {str(e)}")
            raise OrchestrationError(f"Failed to batch create execution inputs: {str(e)}") from e

    @with_orchestration_errors('get_trigger_by_id')
    @with_session
    def get_by_id(self, session, *, record_id: str, user_id: str, include_relationships: bool = False, exclude_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get trigger by ID with workflow access control."""
        record_id = self._validate_trigger_exist(session, record_id)
        user_id = self._validate_user_exist(session, user_id)
        
        # Get trigger to find workflow_id
        trigger = self.trigger_crud._get_by_id(session, record_id)
        if not trigger:
            return None
        
        # Check if user has access to the workflow (at least VIEWER role)
        has_access = self._does_user_have_access(
            session,
            user_id,
            trigger.workflow_id,
            self.user_workflow_role_crud,
            min_role=Roles.VIEWER
        )
        
        if not has_access:
            self._raise_permission_denied('access', user_id, trigger.workflow_id, 'workflow')
        
        return self._serialize_single_result(
            trigger,
            include_relationships=include_relationships,
            exclude_fields=exclude_fields
        )

    @with_orchestration_errors('get_all_triggers')
    @with_session
    def get_all(self, session, *, user_id: str, workflow_id: str = None, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = False, include_deleted: bool = False, exclude_fields: List[str] = None, **filters) -> List[Dict[str, Any]]:
        """
        Get all triggers accessible to user via workflow permissions.
        Optimized with single JOIN query through workflow junction table.
        """
        user_id = self._validate_user_exist(session, user_id)
        
        # Build base query with JOIN to workflow junction table (SINGLE QUERY OPTIMIZATION)
        query = select(self.trigger_crud.model)
        query = self._build_parent_junction_query(
            query,
            user_id,
            self.user_workflow_role_crud,
            Workflow,
            self.trigger_crud.model,
            parent_id_field='workflow_id',
            junction_parent_field='workflow_id'
        )
        
        # Optional workflow filter
        if workflow_id:
            query = query.where(self.trigger_crud.model.workflow_id == workflow_id)
        
        # Apply is_deleted filter
        if not include_deleted:
            query = query.where(self.trigger_crud.model.is_deleted == False)
        
        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.trigger_crud.model, key):
                query = query.where(getattr(self.trigger_crud.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.trigger_crud.model, order_by):
            order_column = getattr(self.trigger_crud.model, order_by)
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
