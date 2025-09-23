from threading import Event
from multiprocessing import cpu_count
from .type_controller import TypeController


class ProcessController:
    def __init__(self, output_queue, logger, input_queue, iob_task_limit: int, cb_task_limit: int, os: bool):
        self.output_queue = output_queue
        self.input_queue = input_queue
        self.max_process_count = cpu_count() - 1
        self.started = False
        self.shutdown_event = Event()
        self.os = os
        self.cb_task_limit = cb_task_limit
        self.iob_task_limit = iob_task_limit
        self.logger = logger
        
        self.logger.info(f"[PROCESS CONTROLLER] Initializing with max_process_count={self.max_process_count}")
        self.logger.info(f"[PROCESS CONTROLLER] CPU-Bound: 1 process, task_limit={cb_task_limit}")
        self.logger.info(f"[PROCESS CONTROLLER] IO-Bound: {self.max_process_count - 1} processes, task_limit={iob_task_limit}")
        
        self.cb_controller = TypeController(output_queue=self.output_queue, logger=self.logger, process_count=1, task_limit=cb_task_limit,
                                            os=self.os, controller_type="CPU-Bound")
        self.iob_controller = TypeController(output_queue=self.output_queue, logger=self.logger, process_count=self.max_process_count - 1,
                                             task_limit=iob_task_limit, os=self.os, controller_type="IO-Bound")
        
        self.logger.info("[PROCESS CONTROLLER] Type controllers initialized")

    def start(self):
        if self.started:
            raise RuntimeError("QueueWatcher already started")

        self.started = True

    def get_cb_ps_info(self):
        return self.cb_controller.get_ps_info()

    def get_iob_ps_info(self):
        return self.iob_controller.get_ps_info()

    def create_thread(self, item):
        if not self._check_retry(item):
            process_type = item.get("process_type")
            self.logger.debug(f"[PROCESS CONTROLLER] Item process_type: {process_type}")
            
            if process_type == "cb":
                self.logger.debug("[PROCESS CONTROLLER] Using CPU-Bound controller")
                if self.cb_controller.create_thread(item):
                    self.logger.info("[PROCESS CONTROLLER] CPU-Bound task created successfully")
                    return True
                else:
                    self.logger.warning("[PROCESS CONTROLLER] CPU-Bound controller busy, requeueing")
                    self.input_queue.put(item)
                    return False

            elif process_type == "iob":
                self.logger.debug("[PROCESS CONTROLLER] Using IO-Bound controller")
                if self.iob_controller.create_thread(item):
                    self.logger.info("[PROCESS CONTROLLER] IO-Bound task created successfully")
                    return True
                else:
                    self.logger.warning("[PROCESS CONTROLLER] IO-Bound controller busy, requeueing")
                    self.input_queue.put(item)
                    return False

            else:
                self.logger.error(f"[PROCESS CONTROLLER] Unknown process_type: {process_type}, failing task")
                item["error_message"] = f"Unknown process_type: {process_type}"
                item["status"] = "FAILED"
                self.output_queue.put(item)
                return False

        else:
            self.logger.error("[PROCESS CONTROLLER] Retry limit exceeded")
            item["error_message"] = "Retry Limit Exceeded"
            item["status"] = "FAILED"
            self.output_queue.put(item)
            return False

    def _check_retry(self, item):
        if item.get("retry") is not None:
            item["retry"] += 1
            return item.get("retry") > item.get("max_retries")

        else:
            item["retry"] = 0
            return False

    def shutdown(self):
        """Graceful shutdown"""
        self.shutdown_event.set()

        self.cb_controller.shutdown()
        self.iob_controller.shutdown()
        return True
