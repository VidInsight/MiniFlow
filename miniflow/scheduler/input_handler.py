import time
import threading
import multiprocessing
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

from miniflow.core.logger import get_logger
from miniflow.core.monitoring import MonitorableComponent
from miniflow.core.exceptions import OrchestrationError
from miniflow.database import DatabaseEngine, DatabaseOrchestrator


@dataclass
class InputHandlerConfig:
    """Configuration for InputHandler component."""
    batch_size: int = 50
    worker_threads: int = 4
    worker_count: int = min(worker_threads, multiprocessing.cpu_count())
    min_polling_interval: float = 0.1
    max_polling_interval: float = 5.0
    current_polling_interval: float = 1.0
    
    def to_dict(self):
        return {
            "batch_size": self.batch_size,
            "worker_threads": self.worker_threads,
            "worker_count": self.worker_count,
            "min_polling_interval": self.min_polling_interval,
            "max_polling_interval": self.max_polling_interval,
            "current_polling_interval": self.current_polling_interval
        }


class InputHandler(MonitorableComponent):
    """
    InputHandler processes ready execution inputs and sends them to execution engine.
    
    Responsibilities:
    - Poll for ready execution inputs (dependency_count = 0)
    - Process task context and parameters
    - Send tasks to execution engine
    - Remove processed tasks from execution_input table
    - Provide monitoring and metrics
    """
    
    def __init__(self, config: InputHandlerConfig, orchestrator: DatabaseOrchestrator, exec_engine):
        self.orchestrator = orchestrator.scheduler_orchestrator
        self.exec_engine = exec_engine
        self.config = config
        self.logger = get_logger("input_handler")

        # Threading and lifecycle management
        self.running = False
        self.empty_cycles = 0
        self.main_thread: Optional[threading.Thread] = None
        self.worker_pool: Optional[ThreadPoolExecutor] = None
        self.shutdown_event = threading.Event()

        # Metrics and monitoring
        self.metrics = {
            'successful_tasks': 0,
            'failed_tasks': 0
        }

    def get_component_name(self) -> str:
        return "InputHandler"

    def get_component_metrics(self) -> Dict[str, Any]:
        return self.metrics

    def is_running(self) -> bool:
        return self.running

    def get_component_config(self) -> Dict[str, Any]:
        return self.config.to_dict()

    def set_component_config(self, config: InputHandlerConfig) -> None:
        """Update configuration with validation."""
        if not isinstance(config, InputHandlerConfig):
            raise ValueError("Config must be an instance of InputHandlerConfig")
        self.config = config
        self.logger.info("InputHandler configuration updated")

    def start(self) -> bool:
        """Start the InputHandler with proper initialization."""
        if self.running:
            self.logger.warning("InputHandler already running")
            return True

        try:
            self.logger.info("Starting InputHandler")
            self.shutdown_event.clear()

            # Initialize worker pool
            self.worker_pool = ThreadPoolExecutor(
                max_workers=self.config.worker_count,
                thread_name_prefix="InputHandlerWorker"
            )

            # Reset metrics
            self.metrics.update({
                'successful_tasks': 0,
                'failed_tasks': 0
            })
            self.empty_cycles = 0

            self.running = True
            
            # Start main processing thread
            self.main_thread = threading.Thread(
                target=self._main_loop,
                name="InputHandlerThread", 
                daemon=True
            )
            self.main_thread.start()
            
            self.logger.info(f"InputHandler started with {self.config.worker_count} workers")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start InputHandler: {str(e)}")
            self.running = False
            return False

    def stop(self) -> bool:
        """Stop the InputHandler gracefully."""
        if not self.running:
            self.logger.warning("InputHandler already stopped")
            return True

        try:
            self.logger.info("Stopping InputHandler")
            self.shutdown_event.set()

            # Shutdown worker pool gracefully
            if self.worker_pool:
                self.worker_pool.shutdown(wait=True)
                self.logger.debug("Worker pool shutdown completed")

            # Wait for main thread to finish
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=5)
                if self.main_thread.is_alive():
                    self.logger.warning("Main thread did not stop within timeout")
                else:
                    self.logger.debug("Main thread stopped")

            self.running = False
            self.logger.info("InputHandler stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping InputHandler: {str(e)}")
            self.running = False
            return False

    def _adjust_polling_interval(self, idle: bool = False) -> None:
        """Dynamically adjust polling interval based on activity."""
        old_interval = self.config.current_polling_interval
        
        if idle:
            # Increase interval when idle (exponential backoff)
            self.config.current_polling_interval = min(
                self.config.current_polling_interval * 1.2,
                self.config.max_polling_interval
            )
        else:
            # Decrease interval when active (faster processing)
            self.config.current_polling_interval = max(
                self.config.current_polling_interval * 0.8,
                self.config.min_polling_interval
            )
        
        if old_interval != self.config.current_polling_interval:
            self.logger.debug(f"Polling interval adjusted: {old_interval:.2f}s -> {self.config.current_polling_interval:.2f}s")

    def _main_loop(self):
        """Main loop to process ready execution inputs."""
        self.logger.info("Input handler main loop started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                self.logger.debug("Checking for ready tasks...")
                ready_tasks = self._get_ready_tasks()

                if not ready_tasks:
                    self.empty_cycles += 1
                    self.logger.debug(f"No ready tasks found. Empty cycles: {self.empty_cycles}")
                    self._adjust_polling_interval(idle=True)
                    time.sleep(self.config.current_polling_interval)
                    continue

                self.logger.info(f"Found {len(ready_tasks)} ready tasks to process")
                self.empty_cycles = 0
                self._adjust_polling_interval(idle=False)

                self._process_ready_tasks(ready_tasks)
                time.sleep(self.config.current_polling_interval)

            except Exception as e:
                self.logger.error(f"Error in input handler main loop: {str(e)}", exc_info=True)
                self.metrics['failed_tasks'] += 1
                time.sleep(self.config.current_polling_interval)

    def _get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Get ready tasks using SchedulerOrchestrator."""
        try:
            self.logger.debug(f"Calling scheduler_orchestrator.get_ready_execution_inputs with batch_size={self.config.batch_size}")
            self.logger.info(f"InputHandler calling scheduler_orchestrator.get_ready_execution_inputs")
            
            # get_ready_execution_inputs has @with_session decorator, so no session needed
            try:
                ready_tasks = self.orchestrator.get_ready_execution_inputs(
                    batch_size=self.config.batch_size
                )
                self.logger.info(f"InputHandler received {len(ready_tasks) if ready_tasks else 0} tasks from scheduler_orchestrator")
            except Exception as e:
                self.logger.error(f"Exception in scheduler_orchestrator.get_ready_execution_inputs: {str(e)}", exc_info=True)
                ready_tasks = []
            
            if ready_tasks:
                self.logger.info(f"Found {len(ready_tasks)} ready tasks")
                self.logger.debug(f"Ready tasks: {[task.get('id', 'NO_ID') for task in ready_tasks]}")
            else:
                self.logger.debug("No ready tasks returned from scheduler orchestrator")
                
            return ready_tasks or []
            
        except OrchestrationError as e:
            self.logger.error(f"Orchestration error getting ready tasks: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting ready tasks: {str(e)}", exc_info=True)
            return []

    def _process_ready_tasks(self, ready_tasks: List[Dict[str, Any]]):
        """Process ready tasks and send to execution engine."""
        if not ready_tasks:
            return

        self.logger.info(f"Processing {len(ready_tasks)} ready tasks")

        # Create task payloads using worker pool with task mapping
        future_to_task = {}
        for task in ready_tasks:
            future = self.worker_pool.submit(self._create_task_payload, task)
            future_to_task[future] = task

        # Collect prepared payloads
        prepared_payloads = []
        task_ids = []

        for future in as_completed(future_to_task.keys(), timeout=10):
            try:
                payload = future.result()
                if payload:
                    prepared_payloads.append(payload)
                    # Get the original task ID for cleanup
                    original_task = future_to_task[future]
                    task_ids.append(original_task['id'])
                    self.logger.debug(f"Payload prepared for task: {payload.get('node_name', 'unknown')}")
            except Exception as e:
                self.logger.error(f"Error creating task payload: {str(e)}")
                self.metrics['failed_tasks'] += 1

        self.logger.info(f"{len(prepared_payloads)} payloads prepared from {len(ready_tasks)} tasks")

        # Send tasks to execution engine
        if prepared_payloads:
            self._send_tasks_to_engine(prepared_payloads, task_ids)
        else:
            self.logger.warning(f"No payloads prepared from {len(ready_tasks)} tasks")

    def _create_task_payload(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create execution payload from task data."""
        try:
            # Validate task structure
            if not self._validate_task_structure(task):
                self.logger.error(f"Invalid task structure: {task}")
                return None
            
            # Validate script path is present (critical for engine execution)
            script_path = task.get('script_path')
            if not script_path:
                self.logger.error(f"Task {task.get('id')} missing script_path - cannot execute")
                return None
            
            self.logger.debug(f"Creating payload for task: {task.get('id')}, node: {task.get('node_name')}")
            self.logger.debug(f"Script path: {script_path}")
            self.logger.debug(f"Task node_params: {task.get('node_params')}")
            
            # Process node_params to build execution context using SchedulerOrchestrator
            # Use original process_task_context method with @with_session decorator
            try:
                self.logger.debug(f"Calling orchestrator.process_task_context for task {task.get('id')}")
                
                # Call the method - @with_session decorator will inject session automatically
                processed_context = self.orchestrator.process_task_context(task)
                
                self.logger.debug(f"Successfully called process_task_context, result: {processed_context}")
            except Exception as e:
                self.logger.error(f"Exception in process_task_context for task {task.get('id')}: {str(e)}", exc_info=True)
                # Fallback to original node_params with format handling
                raw_node_params = task.get('node_params', {})
                processed_context = self._extract_fallback_context(raw_node_params)
            
            self.logger.debug(f"Processed context: {processed_context}")
            
            # Build execution payload
            payload = {
                'execution_id': task['execution_id'],
                'workflow_id': task['workflow_id'],
                'node_id': task['node_id'],
                'correlation_id': task.get('correlation_id'),
                'node_name': task['node_name'],
                'script_name': task.get('script_name'),
                'script_path': script_path,  # Ensure script_path is not None
                'context': processed_context,
                'priority': task.get('priority', 0),
                'max_retries': 3,  # Default from node configuration
                'timeout_seconds': 300,  # Default from node configuration
                'process_type': 'cb'  # Default to IO-bound for script execution
            }
            
            self.logger.debug(f"Created payload: {payload}")
            return payload
            
        except OrchestrationError as e:
            self.logger.error(f"Orchestration error creating payload for task {task.get('id')}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error creating payload for task {task.get('id')}: {str(e)}", exc_info=True)
            return None
    
    def _validate_task_structure(self, task: Dict[str, Any]) -> bool:
        """Validate that task has required fields."""
        required_fields = ['execution_id', 'workflow_id', 'node_id', 'node_name']
        return all(field in task for field in required_fields)

    def _extract_fallback_context(self, raw_node_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fallback context from node_params with format handling.
        
        Supports both formats:
        - New format: {variable_name: {value: variable_value, ...}}
        - Old format: {variable_name: variable_value}
        
        Returns flattened context: {variable_name: variable_value}
        """
        try:
            if not isinstance(raw_node_params, dict):
                self.logger.warning(f"raw_node_params is not a dict: {type(raw_node_params)}")
                return {}
                
            fallback_context = {}
            
            for key, param_data in raw_node_params.items():
                try:
                    if isinstance(param_data, dict) and 'value' in param_data:
                        # New format: {variable_name: {value: variable_value, ...}}
                        fallback_context[key] = param_data['value']
                        self.logger.debug(f"Fallback extracted new format - {key}: {param_data['value']}")
                    else:
                        # Old format: {variable_name: variable_value}
                        fallback_context[key] = param_data
                        self.logger.debug(f"Fallback extracted old format - {key}: {param_data}")
                except Exception as e:
                    self.logger.warning(f"Failed to extract fallback for parameter '{key}': {str(e)}")
                    fallback_context[key] = param_data
                    
            self.logger.debug(f"Fallback context extracted: {fallback_context}")
            return fallback_context
            
        except Exception as e:
            self.logger.error(f"Error in fallback context extraction: {str(e)}")
            return {}

    

    def _send_tasks_to_engine(self, prepared_payloads: List[Dict[str, Any]], task_ids: List[str]):
        """Send prepared tasks to execution engine."""
        try:
            if not self.exec_engine:
                raise ValueError("Execution Engine not available for task submission")

            self.logger.info(f"Sending {len(prepared_payloads)} tasks to execution engine")
            
            # Log payload details for debugging
            for i, payload in enumerate(prepared_payloads):
                self.logger.debug(f"Payload {i+1}: execution_id={payload.get('execution_id')}, "
                                f"node_id={payload.get('node_id')}, script_path={payload.get('script_path')}")
            
            success = self.exec_engine.put_items_bulk(prepared_payloads)
            
            if success:
                self.metrics['successful_tasks'] += len(prepared_payloads)
                self.logger.info(f"Successfully sent {len(prepared_payloads)} tasks to engine")
                
                # Remove completed tasks from execution_input table
                self._remove_sent_tasks(task_ids)
            else:
                self.logger.error("Failed to send tasks to execution engine - engine rejected payloads")
                self.metrics['failed_tasks'] += len(prepared_payloads)
                
        except Exception as e:
            self.logger.error(f"Error sending tasks to engine: {str(e)}", exc_info=True)
            self.metrics['failed_tasks'] += len(prepared_payloads)

    def _remove_sent_tasks(self, task_ids: List[str]) -> None:
        """Remove sent tasks using SchedulerOrchestrator."""
        try:
            if not task_ids:
                self.logger.debug("No task IDs to remove")
                return
                
            # remove_processed_execution_inputs has @with_session decorator, so no session needed
            removed_count = self.orchestrator.remove_processed_execution_inputs(task_ids)
            self.logger.debug(f"Removed {removed_count} sent tasks from execution_input table")
            
        except OrchestrationError as e:
            self.logger.error(f"Orchestration error removing sent tasks: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error removing sent tasks: {str(e)}", exc_info=True)
