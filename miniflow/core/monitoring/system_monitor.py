import gc
import time
import json
import psutil
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

from .config import MonitoringConfig, SystemMetrics
from .alert_manager import AlertManager, AlertLevel, AlertType
from .components import MonitorableComponent

from miniflow.core.exceptions import InternalError

class SystemMonitor:
    def __init__(self, config: MonitoringConfig = None):
        self.running: bool = False
        self.system_start_time = None
        self.config: MonitoringConfig = config or MonitoringConfig()
        self.components: Dict[str, MonitorableComponent] = {}
        self.system_metrics: Optional[SystemMetrics] = None
        self.alert_manager: Optional[AlertManager] = None
        self.monitoring_thread: Optional[threading.Thread] = None
        self.lock_timeout = 5.0  # 5 saniye timeout
        self._lock = threading.RLock()  

    def _start_alert_manager(self):
        if self.config.enable_alerts:
            self.alert_manager = AlertManager(max_history=self.config.max_alerts_history)

    def register_component(self, name: str, component: MonitorableComponent):
        component_name = component.get_component_name()
        with self._lock:
            self.components[component_name] = component

    def unregister_component(self, component_name: str):
        with self._lock:
            if component_name in self.components:
                self.components.pop(component_name, None)

    def start(self):
        if self.running:
            return True

        try:
            # Initialize alert manager first
            self._start_alert_manager()
            
            # Set start time
            self.system_start_time = time.time()
            
            # Create and start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="SystemMonitoringThread",
                daemon=True
            )
            
            # Set running flag before starting thread
            self.running = True
            
            # Collect initial metrics immediately
            self._collect_system_metrics()
            
            self.monitoring_thread.start()
            
            return True
            
        except Exception as e:
            # Cleanup on failure
            self.running = False
            self.monitoring_thread = None
            self.system_start_time = None
            raise InternalError(message="Failed to start SystemMonitor", details=str(e))

    def stop(self, timeout: float = 10.0) -> bool:
        if not self.running:
            return True

        try:
            # Signal thread to stop
            self.running = False
            
            # Wait for thread to finish with timeout
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=timeout)
                
                # Check if thread actually stopped
                if self.monitoring_thread.is_alive():
                    return False
                else:
                    pass
            
            # Cleanup resources
            self._cleanup_resources()
            
            return True
            
        except Exception as e:
            return False

    def _cleanup_resources(self):
        try:
            # Clear components
            with self._lock:
                self.components.clear()
            
            # Clear system metrics
            with self._lock:
                self.system_metrics = None
            
            # Clear alert manager
            if self.alert_manager:
                self.alert_manager.clear_alerts()
                self.alert_manager = None
            

        except Exception as e:
            pass

    def _monitoring_loop(self):
        while self.running:
            try:
                self._collect_system_metrics()
                self._check_thresholds()
                time.sleep(self.config.monitoring_interval)
            except Exception as e:
                time.sleep(self.config.monitoring_interval)

    def _collect_system_metrics(self):
        # Sistem genelindeki metrikler
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent()
        disk_usage = psutil.disk_usage('/')

        # Process sayısı
        current_process = psutil.Process()
        child_processes = current_process.children(recursive=True)
        total_processes = len(child_processes) + 1

        # Thread-safe component count
        with self._lock:
            registered_components = len(self.components)

        new_system_metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                monitoring_uptime=round(time.time() - self.system_start_time, 2),
                system_memory_percent=system_memory.percent,
                system_cpu_percent=system_cpu,
                disk_usage_percent=disk_usage.percent,
                active_threads=threading.active_count(),
                registered_components=registered_components,
                total_processes=total_processes
            )

        # Thread-safe system_metrics update
        with self._lock:
            self.system_metrics = new_system_metrics

    def _check_thresholds(self):
        # 2.1: Lock içinde SADECE veri kopyalama
        system_metrics_snapshot = None
        alert_manager_ref = None
        
        with self._lock:
            if not self.system_metrics:
                return
            # Veriyi kopyala (immutable)
            system_metrics_snapshot = self.system_metrics
            
        # 2.2: Alert manager referansını al (lock dışında)
        alert_manager_ref = self.alert_manager
        if not alert_manager_ref:
            return

        # 2.3: Tüm işlemleri lock dışında yap
        alerts_to_create = []
        actions_to_execute = []
        
        # Memory usage alerts
        if system_metrics_snapshot.system_memory_percent > self.config.memory_critical_threshold:
            alerts_to_create.append({
                "level": AlertLevel.CRITICAL,
                "type": AlertType.SYSTEM,
                "message": f"Critical memory usage: {system_metrics_snapshot.system_memory_percent:.1f}%",
                "component": "MEMORY_MONITOR",
                "metadata": {
                    "metric_type": "memory",
                    "current_value": system_metrics_snapshot.system_memory_percent,
                    "threshold": self.config.memory_critical_threshold,
                    "timestamp": system_metrics_snapshot.timestamp
                }
            })
            actions_to_execute.append(("memory_critical", system_metrics_snapshot))

        elif system_metrics_snapshot.system_memory_percent > self.config.memory_warning_threshold:
            alerts_to_create.append({
                "level": AlertLevel.WARNING,
                "type": AlertType.SYSTEM,
                "message": f"High memory usage: {system_metrics_snapshot.system_memory_percent:.1f}%",
                "component": "MEMORY_MONITOR",
                "metadata": {
                    "metric_type": "memory",
                    "current_value": system_metrics_snapshot.system_memory_percent,
                    "threshold": self.config.memory_warning_threshold,
                    "timestamp": system_metrics_snapshot.timestamp
                }
            })
            actions_to_execute.append(("memory_warning", system_metrics_snapshot))

        # CPU usage alerts
        if system_metrics_snapshot.system_cpu_percent > self.config.cpu_critical_threshold:
            alerts_to_create.append({
                "level": AlertLevel.CRITICAL,
                "type": AlertType.SYSTEM,
                "message": f"Critical CPU usage: {system_metrics_snapshot.system_cpu_percent:.1f}%",
                "component": "CPU_MONITOR",
                "metadata": {
                    "metric_type": "cpu",
                    "current_value": system_metrics_snapshot.system_cpu_percent,
                    "threshold": self.config.cpu_critical_threshold,
                    "timestamp": system_metrics_snapshot.timestamp
                }
            })
            actions_to_execute.append(("cpu_critical", system_metrics_snapshot))

        elif system_metrics_snapshot.system_cpu_percent > self.config.cpu_warning_threshold:
            alerts_to_create.append({
                "level": AlertLevel.WARNING,
                "type": AlertType.SYSTEM,
                "message": f"High CPU usage: {system_metrics_snapshot.system_cpu_percent:.1f}%",
                "component": "CPU_MONITOR",
                "metadata": {
                    "metric_type": "cpu",
                    "current_value": system_metrics_snapshot.system_cpu_percent,
                    "threshold": self.config.cpu_warning_threshold,
                    "timestamp": system_metrics_snapshot.timestamp
                }
            })
            actions_to_execute.append(("cpu_warning", system_metrics_snapshot))

        # Disk usage alerts
        if system_metrics_snapshot.disk_usage_percent > self.config.disk_critical_threshold:
            alerts_to_create.append({
                "level": AlertLevel.CRITICAL,
                "type": AlertType.SYSTEM,
                "message": f"Critical disk usage: {system_metrics_snapshot.disk_usage_percent:.1f}%",
                "component": "DISK_MONITOR",
                "metadata": {
                    "metric_type": "disk",
                    "current_value": system_metrics_snapshot.disk_usage_percent,
                    "threshold": self.config.disk_critical_threshold,
                    "timestamp": system_metrics_snapshot.timestamp
                }
            })
            actions_to_execute.append(("disk_critical", system_metrics_snapshot))

        elif system_metrics_snapshot.disk_usage_percent > self.config.disk_warning_threshold:
            alerts_to_create.append({
                "level": AlertLevel.WARNING,
                "type": AlertType.SYSTEM,
                "message": f"High disk usage: {system_metrics_snapshot.disk_usage_percent:.1f}%",
                "component": "DISK_MONITOR",
                "metadata": {
                    "metric_type": "disk",
                    "current_value": system_metrics_snapshot.disk_usage_percent,
                    "threshold": self.config.disk_warning_threshold,
                    "timestamp": system_metrics_snapshot.timestamp
                }
            })
            actions_to_execute.append(("disk_warning", system_metrics_snapshot))

        # 2.4: Alert oluşturma (nested lock yok)
        for alert_data in alerts_to_create:
            try:
                alert_manager_ref.create_alert(**alert_data)
            except Exception as e:
                logging.error(f"Alert creation failed: {e}")
        
        # 2.5: Action execution
        for action_type, metrics in actions_to_execute:
            try:
                self._execute_action(action_type, metrics)
            except Exception as e:
                logging.error(f"Action failed: {action_type} - {e}")

    def _execute_action(self, action_type: str, system_metrics):
        """Execute action based on action type"""
        try:
            if action_type == "memory_critical":
                self._memory_usage_critical_action(system_metrics)
            elif action_type == "memory_warning":
                self._memory_usage_warning_action(system_metrics)
            elif action_type == "cpu_critical":
                self._cpu_usage_critical_action(system_metrics)
            elif action_type == "cpu_warning":
                self._cpu_usage_warning_action(system_metrics)
            elif action_type == "disk_critical":
                self._disk_usage_critical_action(system_metrics)
            elif action_type == "disk_warning":
                self._disk_usage_warning_action(system_metrics)
        except Exception as e:
            logging.error(f"Action execution failed in _execute_action: {action_type} - {e}")

    @staticmethod
    def _memory_usage_warning_action(system_metrics):
        try:
            gc.collect()
        except Exception as e:
            logging.error(f"Memory warning action failed: {e}")

    @staticmethod
    def _memory_usage_critical_action(system_metrics):
        try:
            for _ in range(3):
                gc.collect()
        except Exception as e:
            logging.error(f"Memory critical action failed: {e}")

    @staticmethod
    def _cpu_usage_warning_action(system_metrics):
        try:
            pass  # CPU warning için şimdilik boş
        except Exception as e:
            logging.error(f"CPU warning action failed: {e}")

    @staticmethod
    def _cpu_usage_critical_action(system_metrics):
        try:
            pass  # CPU critical için şimdilik boş
        except Exception as e:
            logging.error(f"CPU critical action failed: {e}")

    @staticmethod
    def _disk_usage_warning_action(system_metrics):
        try:
            pass  # Disk warning için şimdilik boş
        except Exception as e:
            logging.error(f"Disk warning action failed: {e}")

    @staticmethod
    def _disk_usage_critical_action(system_metrics):
        try:
            pass  # Disk critical için şimdilik boş
        except Exception as e:
            logging.error(f"Disk critical action failed: {e}")

    def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Timeout korumalı system metrics"""
        if self._lock.acquire(timeout=self.lock_timeout):
            try:
                return self.system_metrics.to_dict() if self.system_metrics else None
            finally:
                self._lock.release()
        else:
            logging.error("System metrics lock timeout")
            return {"error": "Lock timeout", "timestamp": datetime.now().isoformat()}

    def get_component_metrics(self, component_name: str) -> Optional[Dict[str, Any]]:
        if not component_name:
            raise ValueError("Component name cannot be empty")
        
        # Lock içinde SADECE referans al
        component_ref = None
        with self._lock:
            if component_name not in self.components:
                return None
            component_ref = self.components[component_name]
        
        # Lock dışında metrics al
        try:
            metrics = component_ref.get_component_metrics()
            return metrics.to_dict()
        except Exception as e:
            error_msg = f"Component metrics failed for '{component_name}': {e}"
            logging.error(error_msg)
            
            # Async alert oluştur (nested lock riski yok)
            self._create_alert_safe(
                level=AlertLevel.WARNING,
                type=AlertType.COMPONENT,
                message=error_msg,
                component=component_name
            )
            
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _create_alert_safe(self, **kwargs):
        """Thread-safe alert creation"""
        try:
            if self.alert_manager:
                self.alert_manager.create_alert(**kwargs)
        except Exception as e:
            logging.error(f"Safe alert creation failed: {e}")

    def get_all_components_metrics(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            all_metrics = {}
            for name, component in self.components.items():
                try:
                    metrics = component.get_component_metrics()
                    all_metrics[name] = metrics.to_dict()
                except Exception as e:
                    all_metrics[name] = {"error": str(e)}
            return all_metrics

    def get_all_metrics(self) -> Dict[str, Any]:
        # Her bileşeni ayrı ayrı ve güvenli al
        system_metrics = None
        components_metrics = None
        alerts_summary = None
        
        # System metrics - kendi lock'unu kullanır
        system_metrics = self.get_system_metrics()
        
        # Components metrics - kendi lock'unu kullanır
        components_metrics = self.get_all_components_metrics()
        
        # Alert summary - AlertManager'ın lock'unu kullanır
        try:
            if self.alert_manager:
                alerts_summary = self.alert_manager.get_alert_summary()
        except Exception as e:
            logging.error(f"Failed to get alerts: {e}")
            alerts_summary = {"error": str(e)}
        
        return {
            "system_metrics": system_metrics,
            "components_metrics": components_metrics,
            "alerts": alerts_summary
        }


    def component_running_check(self, component_name: str) -> bool:
        with self._lock:
            if component_name in self.components:
                try:
                    return self.components[component_name].is_running()
                except Exception as e:
                    raise InternalError(message="Failed to check component running status", details=str(e))
            else:
                raise InternalError(message="Component '{}' is not registered".format(component_name))


    def all_components_running_check(self) -> Dict[str, bool]:
        with self._lock:
            status = {}
            for name, component in self.components.items():
                try:
                    status[name] = component.is_running()
                except Exception as e:
                    status[name] = False
            return status

    def export_metrics_json(self):
        return json.dumps(self.get_all_metrics(), indent=2, ensure_ascii=False, default=str)

    def get_config(self) -> MonitoringConfig:
        return self.config

    def get_registered_components(self) -> List[str]:
        with self._lock:
            return list(self.components.keys())

    def get_component_count(self) -> int:
        with self._lock:
            return len(self.components)

    def is_component_registered(self, component_name: str) -> bool:
        with self._lock:
            return component_name in self.components

    def get_system_uptime(self) -> float:
        return time.time() - self.system_start_time