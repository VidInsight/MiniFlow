from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from miniflow.core.logger import get_logger


class BaseTriggerHandler(ABC):
    def __init__(self, trigger_data: Dict[str, Any], database_orchestrator):
        self.trigger_data = trigger_data
        self.orchestrator = database_orchestrator
        self.logger = get_logger("miniflow_trigger")
        self.is_running = False
        
        # Extract common trigger info
        self.trigger_id = trigger_data.get('id')
        self.workflow_id = trigger_data.get('workflow_id')
        self.trigger_name = trigger_data.get('name', 'Unknown')
        self.config = trigger_data.get('config', {})
        self.input_mapping = trigger_data.get('input_mapping', {})
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the trigger handler
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the trigger handler
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_trigger_type(self) -> str:
        """
        Return trigger type identifier
        
        Returns:
            str: Trigger type (MANUAL, WEBHOOK, SCHEDULED)
        """
        pass
    
    async def execute_workflow(self, source_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute workflow with trigger data

        This is the main method that processes trigger source data,
        applies input mapping, creates execution record, and starts workflow.

        Args:
            source_data: Raw data from trigger source

        Returns:
            Dict containing execution information if successful, None if failed
        """
        try:
            # Generate correlation ID for tracking
            import uuid
            correlation_id = str(uuid.uuid4())
            
            # Process input mapping to create trigger_data
            processed_trigger_data = self._process_input_mapping(source_data)
            
            # Get workflow info for execution creation
            workflow = self.orchestrator.workflow_orchestrator.get_by_id(self.workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {self.workflow_id} not found")
            
            # Get all nodes for this workflow to calculate node count
            nodes = self.orchestrator.node_orchestrator.get_by_workflow(self.workflow_id)
            total_nodes = len(nodes)
            
            # Create execution record manually (since ExecutionOrchestrator is read-only)
            from miniflow.database.models import Execution, ExecutionStatus
            from uuid import uuid4
            import time
            
            execution_id = f"EX-{str(uuid4()).replace('-', '').upper()[:13]}"
            
            # Create execution using direct CRUD
            execution_data = {
                'id': execution_id,
                'workflow_id': self.workflow_id,
                'status': ExecutionStatus.PENDING,
                'pending_nodes': total_nodes,
                'executed_nodes': 0,
                'results': {
                    'trigger_data': processed_trigger_data, 
                    'triggered_by': f"{self.get_trigger_type()}_{self.trigger_name}",
                    'correlation_id': correlation_id,
                    'trigger_id': self.trigger_id
                },
                'error_details': {}
            }
            
            # ExecutionOrchestrator is read-only, use direct CRUD
            execution_crud = self.orchestrator.execution_orchestrator._get_primary_crud()
            with self.orchestrator.execution_orchestrator.engine.get_session() as session:
                execution_record = execution_crud._create(session, **execution_data)
                session.commit()  # Explicitly commit the transaction
                # Convert to dict for compatibility
                execution_dict = {
                    'id': execution_record.id,
                    'workflow_id': execution_record.workflow_id,
                    'status': execution_record.status,
                    'trigger_data': execution_data.get('results', {}).get('trigger_data'),
                    'triggered_by': execution_data.get('results', {}).get('triggered_by'),
                    'correlation_id': execution_data.get('results', {}).get('correlation_id'),
                    'trigger_id': execution_data.get('results', {}).get('trigger_id')
                }
            
            # Create execution inputs for all workflow nodes
            await self._create_execution_inputs(execution_id, nodes, correlation_id)
            
            self.logger.info(f"Workflow {self.workflow_id} triggered successfully", 
                           extra={
                               "execution_id": execution_id, 
                               "trigger_data": processed_trigger_data,
                               "trigger_id": self.trigger_id,
                               "total_nodes": total_nodes
                           })
            
            return execution_dict
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow {self.workflow_id}: {str(e)}", 
                           extra={"trigger_id": self.trigger_id, "error": str(e)})
            raise

    def _process_input_mapping(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input mapping to extract trigger data
        
        Converts raw source data into workflow trigger parameters
        using the input_mapping configuration.
        
        Args:
            source_data: Raw data from trigger source
            
        Returns:
            Dict with processed trigger data for workflow
        """
        if not self.input_mapping:
            # No mapping defined - return source data as-is
            return source_data
        
        trigger_data = {}
        
        for target_key, source_key in self.input_mapping.items():
            if isinstance(source_key, str):
                # Try to get value from source_data
                value = self._get_nested_value(source_data, source_key)
                if value is not None:
                    trigger_data[target_key] = value
                # If not found in source_data, use source_key as static value
                else:
                    trigger_data[target_key] = source_key
            else:
                # Non-string values are static values
                trigger_data[target_key] = source_key
        
        return trigger_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from dictionary using dot notation
        
        Args:
            data: Source dictionary
            path: Dot-separated path (e.g., 'payload.customer.email')
            
        Returns:
            Value at the path, or None if not found
        """
        try:
            keys = path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
                    
            return value
        except Exception:
            return None

    async def _create_execution_inputs(self, execution_id: str, nodes: List[Dict[str, Any]], correlation_id: str):
        """
        Create execution inputs for all workflow nodes
        
        This prepares the workflow for execution by creating
        ExecutionInput records for each node in the workflow with proper
        dependency counting and priority handling.
        
        Args:
            execution_id: ID of the execution record
            nodes: List of node data from workflow
        """
        try:
            if not nodes:
                self.logger.warning(f"No nodes found for workflow {self.workflow_id}")
                return
            
            # Get workflow priority for inheritance
            workflow = self.orchestrator.workflow_orchestrator.get_by_id(self.workflow_id)
            workflow_priority = workflow.get('priority', 0) if workflow else 0
            
            # Pre-calculate dependency counts for all nodes in this workflow
            all_edges = self.orchestrator.edge_orchestrator.filter(
                filters={"workflow_id": self.workflow_id}
            )
            dependency_counts = {}
            for node in nodes:
                node_id = node['id']
                dependency_counts[node_id] = len([edge for edge in all_edges if edge.get('to_node_id') == node_id])
            
            # Pre-fetch all script information to avoid nested sessions
            script_cache = {}
            for node in nodes:
                if node.get('script_id') and node['script_id'] not in script_cache:
                    try:
                        script = self.orchestrator.script_orchestrator.get_by_id(node['script_id'])
                        script_cache[node['script_id']] = script
                    except Exception:
                        script_cache[node['script_id']] = None
            
            # Create execution input for each node
            execution_inputs_created = 0
            
            # Use execution input CRUD directly since orchestrator might be read-only
            execution_input_crud = self.orchestrator.execution_input_orchestrator._get_primary_crud()
            
            with self.orchestrator.execution_input_orchestrator.engine.get_session() as session:
                for node in nodes:
                    # Get pre-calculated dependency count
                    dependency_count = dependency_counts.get(node['id'], 0)
                    self.logger.info(f"Processing node {node['name']} (id: {node['id']}) with dependency_count: {dependency_count}")
                    
                    # Get script information from cache
                    script_name = None
                    script_path = None
                    if node.get('script_id'):
                        script = script_cache.get(node['script_id'])
                        if script:
                            script_name = script.get('name')
                            script_path = script.get('file_path')
                    
                    # Calculate node priority (inherit from workflow + node specific)
                    node_priority = workflow_priority + node.get('priority', 0)
                    
                    # Create execution input data
                    execution_input_data = {
                        'execution_id': execution_id,
                        'workflow_id': self.workflow_id,
                        'node_id': node['id'],
                        'trigger_id': self.trigger_id,  # Trigger ID eklendi
                        'correlation_id': correlation_id,  # Correlation ID eklendi
                        'priority': node_priority,
                        'dependency_count': dependency_count,
                        'wait_factor': 0,  # Initially no waiting
                        # Denormalized fields for performance (Input Handler optimization)
                        'node_name': node['name'],
                        'script_name': script_name,
                        'script_path': script_path,
                        'node_params': node.get('params', {})
                    }
                    
                    # Create execution input record
                    execution_input_record = execution_input_crud._create(session, **execution_input_data)
                    execution_inputs_created += 1

                    self.logger.info(f"Created ExecutionInput {execution_input_record.id} for node {node['name']} with {dependency_count} dependencies")
                
                # Commit all execution inputs
                session.commit()
            
            self.logger.info(f"Created {execution_inputs_created} execution inputs for execution {execution_id}")
            self.logger.info(f"Workflow {self.workflow_id} execution prepared - Input Handler can now process")
                
        except Exception as e:
            self.logger.error(f"Failed to create execution inputs: {str(e)}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the trigger handler
        
        Returns:
            Dict with handler status information
        """
        return {
            "trigger_id": self.trigger_id,
            "trigger_name": self.trigger_name,
            "trigger_type": self.get_trigger_type(),
            "workflow_id": self.workflow_id,
            "is_running": self.is_running,
            "config": self.config
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(trigger_id={self.trigger_id}, name={self.trigger_name}, running={self.is_running})>"
