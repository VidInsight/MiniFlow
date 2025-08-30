from dataclasses import dataclass, asdict


@dataclass
class MonitoringConfig:
    """Basic monitoring configuration"""
    monitoring_interval: float = 10.0
    memory_warning_threshold: float = 70.0
    memory_critical_threshold: float = 85.0
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 85.0
    disk_warning_threshold: float = 80.0
    disk_critical_threshold: float = 90.0
    max_alerts_history: int = 100

    # Aksiyon ayarları
    enable_alerts: bool = True
    max_monitoring_interval: float = 30.0
    min_monitoring_interval: float = 5.0

    def __post_init__(self):
        if self.monitoring_interval > self.max_monitoring_interval:
            self.monitoring_interval = self.max_monitoring_interval
        elif self.monitoring_interval < self.min_monitoring_interval:
            self.monitoring_interval = self.min_monitoring_interval

    def to_dict(self):
        return {
            "monitoring_interval": self.monitoring_interval,
            "memory_warning_threshold": self.memory_warning_threshold,
            "memory_critical_threshold": self.memory_critical_threshold,
            "cpu_warning_threshold": self.cpu_warning_threshold,
            "cpu_critical_threshold": self.cpu_critical_threshold,
            "disk_warning_threshold": self.disk_warning_threshold,
            "disk_critical_threshold": self.disk_critical_threshold,
            "max_alerts_history": self.max_alerts_history,
            "enable_alerts": self.enable_alerts,
            'max_monitoring_interval': self.max_monitoring_interval,
            'min_monitoring_interval': self.min_monitoring_interval
        }

    def from_dict(self, data):
        self.monitoring_interval = data.get("monitoring_interval", 10.0)
        self.memory_warning_threshold = data.get("memory_warning_threshold", 70.0)
        self.memory_critical_threshold = data.get("memory_critical_threshold", 85.0)
        self.cpu_warning_threshold = data.get("cpu_warning_threshold", 70.0)
        self.cpu_critical_threshold = data.get("cpu_critical_threshold", 85.0)
        self.disk_warning_threshold = data.get("disk_warning_threshold", 80.0)
        self.disk_critical_threshold = data.get("disk_critical_threshold", 90.0)
        self.max_alerts_history = data.get("max_alerts_history", 100)
        self.enable_alerts = data.get("enable_alerts", True)
        self.max_monitoring_interval = data.get("max_monitoring_interval", 30.0)
        self.min_monitoring_interval = data.get("min_monitoring_interval", 5.0)


@dataclass
class SystemMetrics:
    timestamp: str
    system_memory_percent: float
    system_cpu_percent: float
    disk_usage_percent: float
    active_threads: int
    total_processes: int
    registered_components: int
    monitoring_uptime: float

    def to_dict(self):
        return asdict(self)
