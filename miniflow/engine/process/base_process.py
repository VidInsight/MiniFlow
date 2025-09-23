from multiprocessing import Process
from .base_thread import BaseThread
from ..queue_module import BaseQueue
import threading
import time
import importlib
import os


class BaseProcess:
    def __init__(self, cmd_pipe, health_pipe, logger, output_queue: BaseQueue):
        """
        pipe: Bu process'e özel child_conn
        output_queue: Sonuçları QueueWatcher'a göndermek için paylaşılan kuyruk
        """
        self.cmd_pipe = cmd_pipe
        self.health_pipe = health_pipe
        self.logger = logger
        self.output_queue = output_queue
        # Lock'ları process içinde oluşturacağız - pickle issue
        self.process = Process(target=self.run_process, args=(self.cmd_pipe, self.health_pipe, self.output_queue))

    def _cleanup_dead_threads(self):
        """Bitmiş thread'leri listeden çıkar"""
        if hasattr(self, 'threads'):
            initial_count = len(self.threads)
            self.threads = [t for t in self.threads if t.thread.is_alive()]
            cleaned_count = initial_count - len(self.threads)
            if cleaned_count > 0:
                self.logger.debug(f"[BASE PROCESS] Cleaned up {cleaned_count} dead threads, {len(self.threads)} active threads remaining")

    def start(self):
        try:
            self.logger.info(f"[BASE PROCESS] Starting process...")
            self.process.start()
            self.logger.info(f"[BASE PROCESS] Process started successfully: PID={self.process.pid}")
        except Exception as e:
            self.logger.error(f"[BASE PROCESS] FAILED to start process: {str(e)}")
            raise

    def run_process(self, cmd_pipe, health_pipe, output_queue):
        """
        Bu method, process içinde çalışacak.
        pipe: Bu process'e özel child_conn
        output_queue: Sonuçları QueueWatcher'a göndermek için paylaşılan kuyruk
        """
        try:
            self.logger.info(f"[BASE PROCESS] Process {os.getpid()} started successfully")
            # Process içinde lock ve thread listesi oluştur
            self.threads = []
            self.lock = threading.Lock()
            self.shutdown_event = threading.Event()
        except Exception as e:
            self.logger.error(f"[BASE PROCESS] Error in run_process initialization: {str(e)}")
            return

        def health_check():
            while not self.shutdown_event.is_set():
                try:
                    self._cleanup_dead_threads()
                    if health_pipe.poll():
                        health_data = health_pipe.recv()

                        if health_data["command"] == "shutdown":
                            self.logger.info(f"[BASE PROCESS] Received shutdown command, initiating graceful shutdown")
                            self.shutdown_event.set()
                            break

                        elif health_data["command"] == "get_thread_count":
                            thread_count = len(self.threads)
                            health_pipe.send({"thread_count": thread_count})
                            self.logger.debug(f"[BASE PROCESS] Health check: current thread count = {thread_count}")

                except Exception as e:
                    self.logger.error(f"[BASE PROCESS] Health check error: {e}")
                    output_queue.put({"error": f"Thread controller error: {e}"})

                time.sleep(0.1)
        
        def thread_controller():
            while not self.shutdown_event.is_set():
                try:
                    if cmd_pipe.poll():
                        command_data = cmd_pipe.recv()

                        if command_data["command"] == "start_thread":
                            dotted_path = command_data["data"]
                            self.logger.debug(f"[BASE PROCESS] Received start_thread command for: {dotted_path}")
                            target_func = self.import_from_path(dotted_path)
                            args = command_data.get("args", ())
                            kwargs = command_data.get("kwargs", {})

                            self.start_thread(target_func, args, kwargs)
                            
                        elif command_data["command"] == "shutdown":
                            self.logger.info(f"[BASE PROCESS] Received shutdown command in thread controller")
                            self.shutdown_event.set()
                            break
                            
                except Exception as e:
                    self.logger.error(f"[BASE PROCESS] Thread controller error: {e}")
                    output_queue.put({"error": f"Thread controller error: {e}"})

                time.sleep(0.1)

        controller = threading.Thread(target=thread_controller, daemon=True)
        controller.start()
        self.logger.debug(f"[BASE PROCESS] Thread controller started")

        comm = threading.Thread(target=health_check, daemon=True)
        comm.start()
        self.logger.debug(f"[BASE PROCESS] Health check thread started")

        # Graceful shutdown için controller thread'ini bekle
        while not self.shutdown_event.is_set():
            time.sleep(1)

    def start_thread(self, target, args, kwargs):
        """
        Yeni thread başlat ve yönet.
        """
        thread = BaseThread(target=target, args=args, output_queue=self.output_queue)
        thread.start()
        self.logger.debug(f"[BASE PROCESS] Started new thread: {target.__name__ if hasattr(target, '__name__') else str(target)}")
        
        if hasattr(self, 'lock'):
            with self.lock:
                self.threads.append(thread)
                self.logger.debug(f"[BASE PROCESS] Thread added to management list, total threads: {len(self.threads)}")
                # Periyodik temizlik
                if len(self.threads) > 3:  # Threshold
                    self._cleanup_dead_threads()

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info(f"[BASE PROCESS] Initiating shutdown for process PID={self.process.pid if hasattr(self, 'process') else 'unknown'}")
        if hasattr(self, 'shutdown_event'):
            self.shutdown_event.set()
        if self.process.is_alive():
            self.logger.debug(f"[BASE PROCESS] Terminating process PID={self.process.pid}")
            self.process.terminate()
            self.process.join(timeout=5)
            self.logger.info(f"[BASE PROCESS] Process shutdown completed")

    def import_from_path(self, dotted_path):
        """
        Örnek: "process.modules.bash_runner.bash_runner"
        """
        try:
            module_path, func_name = dotted_path.rsplit(".", 1)
            self.logger.debug(f"[BASE PROCESS] Importing module: {module_path}, function: {func_name}")
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            self.logger.debug(f"[BASE PROCESS] Successfully imported function: {func_name}")
            return func
        except Exception as e:
            self.logger.error(f"[BASE PROCESS] Failed to import from path '{dotted_path}': {e}")
            raise
