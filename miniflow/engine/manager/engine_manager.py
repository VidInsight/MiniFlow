from ..engine import ProcessController, QueueController
from miniflow.core.logger import get_logger
from ..queue_module import BaseQueue
import json
import atexit
import signal
import sys
import platform
import multiprocessing

class EngineManager:
    def __init__(self, queue_limit: int = 20, iob_task_limit: int = 20, cb_task_limit: int = 1):
        self.input_queue = BaseQueue(maxsize=queue_limit)
        self.output_queue = BaseQueue()
        self.process_controller = None
        self.queue_controller = None
        self.started = False
        self.logger = get_logger("execution_engine")

        self.iob_task_limit = iob_task_limit
        self.cb_task_limit = cb_task_limit
        self.logger.info(f"[ENGINE MANAGER] Execution Engine initialized with IO_Task_Limit={iob_task_limit}s, CPU_Task_Limit={cb_task_limit}")

        self.logger.info("[ENGINE MANAGER] Starting Execution Engine")

        self.logger.info(f"[ENGINE MANAGER] Setting up signal handlers...")
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            self.logger.info(f"[ENGINE MANAGER] Signal handlers set successfully")
        except Exception as e:
            self.logger.error(f"[ENGINE MANAGER] Signal handler setup failed: {str(e)}")

        atexit.register(self.shutdown)
        self.logger.info(f"[ENGINE MANAGER] Constructor completed successfully")

    def start(self):
        try:
            if not self.started:
                self.logger.info(f"[ENGINE MANAGER STARTER] Getting system information...")
                # Log system information
                system_info = platform.system()
                cpu_count = multiprocessing.cpu_count()
                is_unix = False if system_info == "Windows" else True
                
                self.logger.info(f"[ENGINE MANAGER STARTER] Engine Manager starting on {system_info} with {cpu_count} CPUs, Unix mode: {is_unix}")
                
                self.logger.info(f"[ENGINE MANAGER STARTER] Starting ProcessController...")
                self.process_controller = ProcessController(output_queue=self.output_queue, logger=self.logger, input_queue=self.input_queue,
                                                            os=is_unix,
                                                            iob_task_limit=self.iob_task_limit, cb_task_limit=self.cb_task_limit)
                self.process_controller.start()
                self.logger.info(f"[ENGINE MANAGER STARTER] ProcessController started")

                self.logger.info(f"[ENGINE MANAGER STARTER] Starting QueueController...")
                self.queue_controller = QueueController(input_queue=self.input_queue, logger=self.logger, process_controller=self.process_controller)
                self.queue_controller.start()
                self.logger.info(f"[ENGINE MANAGER STARTER] QueueController started")

                self.started = True
                self.logger.info("[ENGINE MANAGER STARTER] Execution Engine started successfully")
                return True

            else:
                return False

        except Exception as e:
            self.logger.error(f"[ENGINE MANAGER STARTER] Failed to start Execution Engine: {str(e)}")
            self.started = False
            return False

    def put_item(self, item: json):
        if not self.started:
            return False
        return self.input_queue.put(item)

    def put_items_bulk(self, items: list):
        """
        Amaç: Birden fazla item'ı bulk olarak ekler (batch processing için)
        Döner: Başarı durumu (True/False)

        Performance optimized version with retry mechanism
        """
        if not self.started:
            self.logger.error("[ENGINE MANAGER PUT ITEMS] Execution Engine is not running")
            return False

        self.logger.info(f"[ENGINE MANAGER PUT ITEMS] Received {len(items)} tasks from InputHandler")
        
        # Log task details for debugging
        for i, item in enumerate(items):
            self.logger.debug(f"[ENGINE MANAGER PUT ITEMS] Task {i+1}: execution_id={item.get('execution_id')}, "
                            f"node_id={item.get('node_id')}, script_path={item.get('script_path')}")
            self.logger.debug(f"[ENGINE MANAGER PUT ITEMS] Task {i+1} context: {item.get('context', {})}")

        if not items:
            return True

        result = self.input_queue.put_batch(items)
        self.logger.info(f"[ENGINE MANAGER PUT ITEMS] Batch put result: {result}")
        return result

    def shutdown(self):
        self.logger.info(f"[ENGINE MANAGER SHUTDOWN] Engine shutting down")
        """Graceful shutdown"""
        if self.queue_controller and self.process_controller and self.started:
            self.queue_controller.shutdown()
            self.process_controller.shutdown()
            self.started = False
            self.logger.info(f"[ENGINE MANAGER SHUTDOWN] Engine shut down successfully")
            return True

        self.logger.error(f"[ENGINE MANAGER SHUTDOWN] Engine shut down failed")
        return False

    def _signal_handler(self, signum, frame):
        self.shutdown()
        sys.exit(0)

    def get_output_item(self):
        return self.output_queue.get_with_timeout(timeout=1.0)

    def get_execution_results(self, max_items=25, timeout=0.1):
        """
        Amaç: Output queue'dan birden fazla item'ı bulk olarak alır
        Döner: Item listesi
        
        Performance optimized version for batch result processing
        """
        if not self.started:
            self.logger.warning("[ENGINE MANAGER GET ITEMS] Engine not started, returning empty results")
            return []

        items = []
        for i in range(max_items):
            try:
                item = self.output_queue.get_with_timeout(timeout=timeout)
                if item is None:
                    break
                items.append(item)
                self.logger.debug(f"[ENGINE MANAGER GET ITEMS] Retrieved result {i+1}: execution_id={item.get('execution_id')}, "
                                f"status={item.get('status')}")
            except Exception as e:
                self.logger.error(f"[ENGINE MANAGER GET ITEMS] Exception getting item {i+1}: {str(e)}")
                break

        if items:
            self.logger.info(f"[ENGINE MANAGER GET ITEMS] Retrieved {len(items)} execution results from output queue")
        else:
            self.logger.debug("[ENGINE MANAGER GET ITEMS] No execution results available in output queue")
            
        return items
