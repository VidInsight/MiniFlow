import threading
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Callable, List


class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    DEVICE = "DEVICE"
    NETWORK = "NETWORK"
    SYSTEM = "SYSTEM"
    COMPONENT = "COMPONENT"


@dataclass
class Alert:
    """Alert data structure"""
    level: AlertLevel
    type: AlertType
    message: str
    timestamp: str = None
    component: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.component is None:
            self.component = "SYSTEM"
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_level": self.level.value,
            "alert_type": self.type.value,
            "alert_message": self.message,
            "alert_timestamp": self.timestamp,
            "alert_component": self.component,
            "alert_metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create Alert instance from dictionary"""
        return cls(
            level=AlertLevel(data["alert_level"]),
            type=AlertType(data["alert_type"]),
            message=data["alert_message"],
            timestamp=data.get("alert_timestamp", datetime.now().isoformat()),
            component=data.get("alert_component", 'SYSTEM'),
            metadata=data.get("alert_metadata", {})
        )


class AlertManager:
    def __init__(self, max_history: int = 100, lock_timeout: float = 5.0):
        self.max_history: int = max_history
        self.lock_timeout = lock_timeout  # Yeni: timeout değeri
        self.alerts: List[Alert] = []
        self.alert_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def create_alert(self, **kwargs) -> bool:
        """Timeout korumalı alert oluşturma"""
        try:
            alert = Alert(**kwargs)
            alert_key = f"{alert.component}:{alert.level.value}"

            # Timeout ile lock al
            if self._lock.acquire(timeout=self.lock_timeout):
                try:
                    self.alert_counts[alert_key] = self.alert_counts.get(alert_key, 0) + 1
                    
                    if len(self.alerts) >= self.max_history:
                        self.alerts.pop(0)
                    
                    self.alerts.append(alert)
                finally:
                    self._lock.release()
            else:
                # Timeout durumunda fallback
                import logging
                logging.error(f"Alert creation timeout for: {alert.message}")
                return False
            
            return True
            
        except Exception as e:
            import logging
            logging.error(f"Alert creation error: {e}")
            return False

    def get_recent_alerts(self, count: int = 10) -> List[Alert]:
        with self._lock:
            return self.alerts[-count:]

    def clear_alerts(self):
        with self._lock:
            self.alerts.clear()
            self.alert_counts.clear()

    def get_alert_summary(self) -> Dict[str, int]:
        with self._lock:
            return self.alert_counts

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        with self._lock:
            return [alert for alert in self.alerts if alert.level == level]

    def get_alerts_by_type(self, type: AlertType) -> List[Alert]:
        with self._lock:
            return [alert for alert in self.alerts if alert.type == type]

    def get_alerts_by_component(self, component: str) -> List[Alert]:
        with self._lock:
            return [alert for alert in self.alerts if alert.component == component]

    def trim_alert_history(self, max_alerts: int = 50):
        with self._lock:
            original_count = len(self.alerts)
            if len(self.alerts) > max_alerts:
                self.alerts = self.alerts[-max_alerts:]

    def get_max_history(self) -> int:
        return self.max_history

    def set_max_history(self, max_history: int):
        self.max_history = max_history
        self.trim_alert_history(max_history)

    def export_alerts_json(self) -> str:
        import json
        with self._lock:
            alerts_data = [asdict(alert) for alert in self.alerts]
            return json.dumps(alerts_data, indent=2, ensure_ascii=False, default=str)