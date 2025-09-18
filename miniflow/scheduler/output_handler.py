import time
import threading
import multiprocessing
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from datetime import datetime

from miniflow.core.logger import get_logger
from miniflow.core.monitoring import MonitorableComponent
from miniflow.core.exceptions import OrchestrationError
from miniflow.database import DatabaseEngine, DatabaseOrchestrator



@dataclass
class OutputHandlerConfig:
    """Configuration for OutputHandler component."""
    batch_size: int = 50
    worker_threads: int = 4
    worker_count: int = min(worker_threads, multiprocessing.cpu_count())
    min_polling_interval: float = 0.1
    max_polling_interval: float = 5.0
    current_polling_interval: float = 0.5

    def to_dict(self):
        return {
            "batch_size": self.batch_size,
            "worker_threads": self.worker_threads,
            "worker_count": self.worker_count,
            "min_polling_interval": self.min_polling_interval,
            "max_polling_interval": self.max_polling_interval,
            "current_polling_interval": self.current_polling_interval
        }


class OutputHandler(MonitorableComponent):
    """
    OutputHandler processes execution results from the execution engine.
    
    Responsibilities:
    - Poll execution engine for completed results
    - Process results using SchedulerOrchestrator
    - Handle failed results with retry mechanisms
    - Provide monitoring and metrics
    """
    
    def __init__(self, config: OutputHandlerConfig, orchestrator: DatabaseOrchestrator, exec_engine):
        self.orchestrator = orchestrator.scheduler_orchestrator
        self.exec_engine = exec_engine
        self.config = config
        self.logger = get_logger("output_handler")

        # Threading and lifecycle management
        self.running = False
        self.empty_cycles = 0
        self.main_thread: Optional[threading.Thread] = None
        self.worker_pool: Optional[ThreadPoolExecutor] = None
        self.shutdown_event = threading.Event()

        # Metrics and monitoring
        self.metrics = {
            'failed_results': 0,
            'successful_results': 0
        }

    def get_component_name(self) -> str:
        return "OutputHandler"

    def get_component_metrics(self) -> Dict[str, Any]:
        return self.metrics

    def is_running(self) -> bool:
        return self.running

    def get_component_config(self) -> Dict[str, Any]:
        return self.config.to_dict()

    def set_component_config(self, config: OutputHandlerConfig) -> None:
        """Update configuration with validation."""
        if not isinstance(config, OutputHandlerConfig):
            raise ValueError("Config must be an instance of OutputHandlerConfig")
        self.config = config
        self.logger.info("OutputHandler configuration updated")

    def start(self) -> bool:
        """Start the OutputHandler with proper initialization."""
        if self.running:
            self.logger.warning("OutputHandler already running")
            return True

        try:
            self.logger.info("Starting OutputHandler")
            self.shutdown_event.clear()

            # Initialize worker pool
            self.worker_pool = ThreadPoolExecutor(
                max_workers=self.config.worker_count,
                thread_name_prefix="OutputHandlerWorker"
            )

            # Reset metrics
            self.metrics.update({
                'failed_results': 0,
                'successful_results': 0
            })
            self.empty_cycles = 0

            self.running = True

            # Start main processing thread
            self.main_thread = threading.Thread(
                target=self._main_loop,
                name="OutputHandlerThread", 
                daemon=True
            )
            self.main_thread.start()
            
            self.logger.info(f"OutputHandler started with {self.config.worker_count} workers")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start OutputHandler: {str(e)}")
            self.running = False
            return False

    def stop(self) -> bool:
        """Stop the OutputHandler gracefully."""
        if not self.running:
            self.logger.warning("OutputHandler already stopped")
            return True

        try:
            self.logger.info("Stopping OutputHandler")
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
            self.logger.info("OutputHandler stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping OutputHandler: {str(e)}")
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
        """Main loop to process execution results from engine."""
        self.logger.info("Output handler main loop started")
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Get results from execution engine
                results = self._get_engine_results()
                
                if not results:
                    self.empty_cycles += 1
                    self.logger.debug(f"No results from engine. Empty cycles: {self.empty_cycles}")
                    self._adjust_polling_interval(idle=True)
                    time.sleep(self.config.current_polling_interval)
                    continue
                
                self.logger.info(f"Processing {len(results)} execution results")
                self.empty_cycles = 0
                self._adjust_polling_interval(idle=False)
                
                # Process results
                self._process(results)
                
                time.sleep(self.config.current_polling_interval)
                
            except Exception as e:
                self.logger.error(f"Error in output handler main loop: {str(e)}", exc_info=True)
                self.metrics['failed_results'] += 1
                time.sleep(self.config.current_polling_interval)
    
    def _get_engine_results(self) -> List[Dict[str, Any]]:
        """Get execution results from engine."""
        try:
            if not self.exec_engine:
                self.logger.error("No exec_engine reference for output handler!")
                raise Exception("No exec_engine reference for output handler!")

            # Get results from engine output queue
            results = self.exec_engine.get_execution_results(max_items=self.config.batch_size)
            
            self.logger.debug(f"Engine returned {len(results) if results else 0} results")
            return results or []
            
        except Exception as e:
            self.logger.error(f"Error getting results from engine: {str(e)}", exc_info=True)
            raise Exception(f"Error getting results from engine: {str(e)}")
    
    def _process(self, results: List[Dict[str, Any]]) -> None:
        """Process execution results and save to database."""
        if not results:
            self.logger.warning("No results to process")
            return
        
        self.logger.info(f"Processing {len(results)} execution results")
        
        for result in results:
            try:
                self.logger.info(f"Processing result for execution {result.get('execution_id', 'UNKNOWN')}")
                self.logger.debug(f"Result data: {result}")
                
                # Log result details
                self.logger.info(f"Result: execution_id={result.get('execution_id')}, "
                               f"node_id={result.get('node_id')}, status={result.get('status')}")
                self.logger.debug(f"Result data content: {result.get('result_data', {})}")
                
                # Validate result structure
                if not self._validate_result_structure(result):
                    self.logger.error(f"Invalid result structure: {result}")
                    self.metrics['failed_results'] += 1
                    continue
                
                # Process result with retry mechanism
                success = self._process_single_result_with_retry(result)
                
                if success:
                    self.metrics['successful_results'] += 1
                    self.logger.debug(f"Successfully processed result for execution {result.get('execution_id')}")
                else:
                    self.metrics['failed_results'] += 1
                    self.logger.error(f"Failed to process result after retries: {result.get('execution_id')}")
                
            except Exception as e:
                self.logger.error(f"Unexpected error processing result: {str(e)}", exc_info=True)
                self.logger.error(f"Failed result data: {result}")
                self.metrics['failed_results'] += 1
    
    def _validate_result_structure(self, result: Dict[str, Any]) -> bool:
        """Validate that result has required fields."""
        required_fields = ['execution_id', 'node_id', 'status']
        return all(field in result for field in required_fields)
    
    def _process_single_result_with_retry(self, result: Dict[str, Any]) -> bool:
        """Process a single result with retry mechanism."""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Try primary processing with SchedulerOrchestrator
                self.orchestrator.process_execution_result(result)
                return True
                
            except OrchestrationError as e:
                self.logger.warning(f"Scheduler orchestrator error (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    # Final attempt failed, try manual fallback
                    self.logger.warning("All retry attempts failed, trying manual fallback")
                    return self._create_execution_output_manual(result)
                    
            except Exception as e:
                self.logger.error(f"Unexpected error in result processing (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return False
        
        return False
    
    def _create_execution_output_manual(self, result: Dict[str, Any]) -> bool:
        """Manual execution output creation as fallback when scheduler orchestrator fails."""
        try:
            from miniflow.database.models import ExecutionOutputStatus
            from uuid import uuid4
            import json
            
            # Generate execution output ID
            execution_output_id = f"EO-{str(uuid4()).replace('-', '').upper()[:13]}"
            
            # Create execution output data
            execution_output_data = {
                'id': execution_output_id,
                'execution_id': result.get('execution_id', 'UNKNOWN'),
                'workflow_id': result.get('workflow_id', 'UNKNOWN'),
                'node_id': result.get('node_id', 'UNKNOWN'),
                'trigger_id': result.get('trigger_id'),
                'status': ExecutionOutputStatus.SUCCESS if result.get('status') == 'SUCCESS' else ExecutionOutputStatus.FAILED,
                'result_data': result.get('result_data', {}),
                'error_message': result.get('error_message'),
                'correlation_id': result.get('correlation_id'),
                'started_at': datetime.now(),
                'ended_at': datetime.now()
            }
            
            # Use execution output CRUD directly
            execution_output_crud = self.orchestrator.execution_output_crud
            
            with self.orchestrator.engine.session_context(auto_commit=True) as session:
                execution_output_crud._create(session, **execution_output_data)
                
            self.logger.info(f"Created execution output {execution_output_id} via manual fallback")
            return True
            
        except Exception as manual_error:
            self.logger.error(f"Manual creation failed: {str(manual_error)}", exc_info=True)
            return False