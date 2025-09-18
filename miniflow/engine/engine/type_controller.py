import json, psutil, time
from multiprocessing import Pipe
from ..process import BaseProcess
from threading import Thread, Lock, Event


class TypeController:
    def __init__(self, output_queue, os: bool, process_count: int, task_limit: int, controller_type: str):
        self.output_queue = output_queue
        self.priority = -19 if os else psutil.HIGH_PRIORITY_CLASS  # self._unix_process_classes() if os else self._nt_process_classes()
        self.process_count = process_count
        self.task_limit = task_limit
        self.controller_type = controller_type
        self._set_options()
        self._start()

    def _set_options(self):
        self.active_processes = []
        self.scaler_thread = None
        self.started = False
        self.shutdown_event = Event()
        self.process_lock = Lock()

    def _start(self):
        if self.started:
            raise RuntimeError("CB Controller already started")

        self.started = True

        self._start_processes(self.process_count)

        self._start_thread_counter()

    def _start_processes(self, count):
        for _ in range(count):
            cmd_parent_conn, cmd_child_conn = Pipe()
            health_parent_conn, health_child_conn = Pipe()
            process = BaseProcess(cmd_child_conn, health_child_conn, self.output_queue)
            process.start()
            self._set_process_priority(process.process.pid, self.priority)
            print(f"[QUEUEWATCHER] Starting process {process.process.pid}")
            self.active_processes.append({
                'name': f'{self.controller_type}-{_}',
                'pid': process.process.pid,
                'process': process,
                'cmd_pipe': cmd_parent_conn,
                'health_pipe': health_parent_conn,
                'thread_count': 0
            })

    def new_process(self):
        self._start_processes(1)

    def get_ps_info(self):
        ps_info_list = []

        for process in self.active_processes:
            ps_info_list.append({'name': process['name'], 'pid': process['pid'], 'thread_count': process['thread_count']})

        return ps_info_list

    def _get_next_process(self):
        if not self.active_processes:
            return None

        selected_process = min(
            (p for p in self.active_processes if p['thread_count'] < self.task_limit),
            key=lambda p: p['thread_count'],
            default=None
        )

        return selected_process

    def create_thread(self, item: json):
        print(f"[TYPE CONTROLLER {self.controller_type}] Looking for available process")
        process = self._get_next_process()

        if process is None:
            print(f"[TYPE CONTROLLER {self.controller_type}] No available process found")
            return False

        print(f"[TYPE CONTROLLER {self.controller_type}] Selected process {process['pid']} with {process['thread_count']} threads")
        command_data = {
            "command": "start_thread",
            "data": "miniflow.engine.process.modules.python_runner.python_runner",
            "args": (item,),
            "kwargs": {}
        }
        process.get("cmd_pipe").send(command_data)
        print(f"[TYPE CONTROLLER {self.controller_type}] Command sent to process {process['pid']}")
        return True

    def shutdown(self):
        self.shutdown_event.set()

        for p in self.active_processes:
            try:
                p['cmd_pipe'].send({"command": "shutdown"})
                p['process'].shutdown()
            except Exception as e:
                print(f"Error shutting down process: {e}")

    def _get_process_thread_counts(self):
        with self.process_lock:
            for proc_dict in self.active_processes:
                try:
                    proc_dict['health_pipe'].send({"command": "get_thread_count"})
                    if proc_dict['health_pipe'].poll(0.05):
                        resp = proc_dict['health_pipe'].recv()
                        proc_dict['thread_count'] = resp.get("thread_count", 0)
                    else:
                        proc_dict['thread_count'] = 0
                except Exception as e:
                    print(f"Error getting thread count: {e}")
                    proc_dict['thread_count'] = 0

    def _thread_count_updater(self):
        while not self.shutdown_event.is_set():
            self._get_process_thread_counts()
            time.sleep(0.2)

    def _start_thread_counter(self):
        self.scaler_thread = Thread(target=self._thread_count_updater, daemon=True)
        self.scaler_thread.start()

    def _set_process_priority(self, pid: int, priority):
        try:
            ps_process = psutil.Process(pid)
            ps_process.nice(priority)
            return True
        except (psutil.AccessDenied, PermissionError) as e:
            print(f"[QueueWatcher] Priority ayarlanamadı (normal): {e}")
            return False
        except Exception as e:
            print(f"[QueueWatcher] Priority ayarlama hatası: {e}")
            return False

    def _nt_process_classes(self):
        """Windows process priority classes"""
        return [psutil.IDLE_PRIORITY_CLASS, psutil.BELOW_NORMAL_PRIORITY_CLASS,
                psutil.NORMAL_PRIORITY_CLASS, psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                psutil.HIGH_PRIORITY_CLASS, psutil.REALTIME_PRIORITY_CLASS]

    def _unix_process_classes(self):
        """Unix based systems process priority range (-20 max priority, 20 min priority)"""
        return [i for i in range(-20, 21)]
