import time
import threading
import queue
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from miniflow.core.logger import get_logger


@dataclass
class MockExecutionResult:
    """Mock execution result data structure."""
    execution_id: str
    workflow_id: str
    node_id: str
    trigger_id: Optional[str]
    correlation_id: Optional[str]
    status: str  # 'SUCCESS' or 'FAILED'
    result_data: Dict[str, Any]
    error_message: Optional[str]
    started_at: datetime
    ended_at: datetime


class MockExecutionEngine:
    """
    Mock Execution Engine for testing and development.
    
    Features:
    - Input queue for receiving tasks from InputHandler
    - Output queue for sending results to OutputHandler
    - Simulates script execution with configurable delay
    - Logs all task details including script paths and parameters
    - Generates mock results based on task data
    """
    
    def __init__(self, 
                 processing_delay: float = 2.0,
                 success_rate: float = 0.95,
                 max_queue_size: int = 1000):
        """
        Initialize Mock Execution Engine.
        
        Args:
            processing_delay: Simulated processing time in seconds
            success_rate: Probability of successful execution (0.0-1.0)
            max_queue_size: Maximum queue size for input/output queues
        """
        self.processing_delay = processing_delay
        self.success_rate = success_rate
        self.max_queue_size = max_queue_size
        self.logger = get_logger("execution_engine")
        
        # Queues for communication with handlers
        self.input_queue = queue.Queue(maxsize=max_queue_size)
        self.output_queue = queue.Queue(maxsize=max_queue_size)
        
        # Processing control
        self.running = False
        self.processing_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.stats = {
            'tasks_received': 0,
            'tasks_processed': 0,
            'tasks_successful': 0,
            'tasks_failed': 0,
            'queue_errors': 0
        }
        
        self.logger.info(f"MockExecutionEngine initialized with delay={processing_delay}s, success_rate={success_rate}")
    
    def start(self) -> bool:
        """Start the mock execution engine."""
        if self.running:
            self.logger.warning("MockExecutionEngine already running")
            return True
        
        try:
            self.logger.info("Starting MockExecutionEngine")
            self.shutdown_event.clear()
            self.running = True
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                name="MockExecutionEngineThread",
                daemon=True
            )
            self.processing_thread.start()
            
            self.logger.info("MockExecutionEngine started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start MockExecutionEngine: {str(e)}")
            self.running = False
            return False
    
    def stop(self) -> bool:
        """Stop the mock execution engine."""
        if not self.running:
            self.logger.warning("MockExecutionEngine already stopped")
            return True
        
        try:
            self.logger.info("Stopping MockExecutionEngine")
            self.shutdown_event.set()
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
                if self.processing_thread.is_alive():
                    self.logger.warning("Processing thread did not stop within timeout")
                else:
                    self.logger.debug("Processing thread stopped")
            
            self.running = False
            self.logger.info("MockExecutionEngine stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping MockExecutionEngine: {str(e)}")
            self.running = False
            return False
    
    def put_items_bulk(self, tasks: List[Dict[str, Any]]) -> bool:
        """
        Put multiple tasks into input queue (called by InputHandler).
        
        Args:
            tasks: List of task dictionaries from InputHandler
            
        Returns:
            bool: True if all tasks were queued successfully
        """
        try:
            if not self.running:
                self.logger.error("MockExecutionEngine is not running")
                return False
            
            self.logger.info(f"Received {len(tasks)} tasks from InputHandler")
            
            for task in tasks:
                try:
                    # Add task to input queue
                    self.input_queue.put_nowait(task)
                    self.stats['tasks_received'] += 1
                    
                    # Log task details
                    self._log_task_details(task)
                    
                except queue.Full:
                    self.logger.error(f"Input queue is full, dropping task: {task.get('node_name', 'unknown')}")
                    self.stats['queue_errors'] += 1
                    return False
            
            self.logger.debug(f"Successfully queued {len(tasks)} tasks")
            return True
            
        except Exception as e:
            self.logger.error(f"Error putting tasks to input queue: {str(e)}")
            return False
    
    def get_execution_results(self, max_items: int = 50) -> List[Dict[str, Any]]:
        """
        Get execution results from output queue (called by OutputHandler).
        
        Args:
            max_items: Maximum number of results to return
            
        Returns:
            List of result dictionaries for OutputHandler
        """
        try:
            if not self.running:
                self.logger.error("MockExecutionEngine is not running")
                return []
            
            results = []
            items_collected = 0
            
            # Try to get results from output queue
            while items_collected < max_items:
                try:
                    result = self.output_queue.get_nowait()
                    results.append(result)
                    items_collected += 1
                except queue.Empty:
                    break
            
            if results:
                self.logger.debug(f"Returning {len(results)} results to OutputHandler")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting results from output queue: {str(e)}")
            return []
    
    def _processing_loop(self):
        """Main processing loop that simulates task execution."""
        self.logger.info("MockExecutionEngine processing loop started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get task from input queue with timeout
                try:
                    task = self.input_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the task
                self._process_task(task)
                
                # Mark task as done
                self.input_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {str(e)}")
                time.sleep(0.1)
        
        self.logger.info("MockExecutionEngine processing loop stopped")
    
    def _process_task(self, task: Dict[str, Any]):
        """Process a single task and generate result."""
        try:
            self.logger.info(f"Processing task: {task.get('node_name', 'unknown')}")
            
            # Simulate processing delay
            time.sleep(self.processing_delay)
            
            # Generate mock result
            result = self._generate_mock_result(task)
            
            # Add result to output queue
            try:
                self.output_queue.put_nowait(result)
                self.stats['tasks_processed'] += 1
                
                if result['status'] == 'SUCCESS':
                    self.stats['tasks_successful'] += 1
                else:
                    self.stats['tasks_failed'] += 1
                
                self.logger.debug(f"Task processed successfully: {task.get('node_name', 'unknown')}")
                
            except queue.Full:
                self.logger.error(f"Output queue is full, dropping result for: {task.get('node_name', 'unknown')}")
                self.stats['queue_errors'] += 1
            
        except Exception as e:
            self.logger.error(f"Error processing task: {str(e)}")
            # Generate error result
            error_result = self._generate_error_result(task, str(e))
            try:
                self.output_queue.put_nowait(error_result)
                self.stats['tasks_processed'] += 1
                self.stats['tasks_failed'] += 1
            except queue.Full:
                self.logger.error("Output queue is full, cannot queue error result")
                self.stats['queue_errors'] += 1
    
    def _log_task_details(self, task: Dict[str, Any]):
        """Log detailed task information."""
        try:
            self.logger.info("=" * 60)
            self.logger.info("TASK RECEIVED FROM INPUT HANDLER")
            self.logger.info("=" * 60)
            self.logger.info(f"Execution ID: {task.get('execution_id', 'N/A')}")
            self.logger.info(f"Workflow ID: {task.get('workflow_id', 'N/A')}")
            self.logger.info(f"Node ID: {task.get('node_id', 'N/A')}")
            self.logger.info(f"Node Name: {task.get('node_name', 'N/A')}")
            self.logger.info(f"Script Name: {task.get('script_name', 'N/A')}")
            self.logger.info(f"Script Path: {task.get('script_path', 'N/A')}")
            self.logger.info(f"Correlation ID: {task.get('correlation_id', 'N/A')}")
            self.logger.info(f"Priority: {task.get('priority', 'N/A')}")
            self.logger.info(f"Max Retries: {task.get('max_retries', 'N/A')}")
            self.logger.info(f"Timeout Seconds: {task.get('timeout_seconds', 'N/A')}")
            
            # Log context/parameters
            context = task.get('context', {})
            if context:
                self.logger.info("CONTEXT/PARAMETERS:")
                for key, value in context.items():
                    self.logger.info(f"  {key}: {value}")
            else:
                self.logger.info("CONTEXT/PARAMETERS: None")
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error logging task details: {str(e)}")
    
    def _generate_mock_result(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock execution result."""
        try:
            import random
            
            # Determine success/failure based on success_rate
            is_success = random.random() < self.success_rate
            
            # Generate result data based on task
            if is_success:
                # Create result_data with only actual script output variables
                result_data = {
                    'mock_output': f"Mock result for {task.get('node_name', 'unknown')}",
                    'random_value': random.randint(1, 1000)
                }
                # Note: Input context parameters are NOT added to result_data
                # result_data should only contain actual script output variables
                status = 'SUCCESS'
                error_message = None
            else:
                result_data = {
                    'error_type': 'MockFailure'
                }
                status = 'FAILED'
                error_message = f"Mock failure for {task.get('node_name', 'unknown')}"
            
            # Create result
            result = {
                'execution_id': task.get('execution_id', 'UNKNOWN'),
                'workflow_id': task.get('workflow_id', 'UNKNOWN'),
                'node_id': task.get('node_id', 'UNKNOWN'),
                'trigger_id': task.get('trigger_id'),
                'correlation_id': task.get('correlation_id'),
                'status': status,
                'result_data': result_data,
                'error_message': error_message
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating mock result: {str(e)}")
            return self._generate_error_result(task, str(e))
    
    def _generate_error_result(self, task: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Generate an error result."""
        return {
            'execution_id': task.get('execution_id', 'UNKNOWN'),
            'workflow_id': task.get('workflow_id', 'UNKNOWN'),
            'node_id': task.get('node_id', 'UNKNOWN'),
            'trigger_id': task.get('trigger_id'),
            'correlation_id': task.get('correlation_id'),
            'status': 'FAILED',
            'result_data': {
                'processed_at': datetime.now().isoformat(),
                'error_type': 'ProcessingError',
                'node_name': task.get('node_name', 'unknown')
            },
            'error_message': error_msg
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'running': self.running,
            'input_queue_size': self.input_queue.qsize(),
            'output_queue_size': self.output_queue.qsize(),
            'stats': self.stats.copy()
        }
    
    def reset_stats(self):
        """Reset engine statistics."""
        self.stats = {
            'tasks_received': 0,
            'tasks_processed': 0,
            'tasks_successful': 0,
            'tasks_failed': 0,
            'queue_errors': 0
        }
        self.logger.info("Engine statistics reset")
