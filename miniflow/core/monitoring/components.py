from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from miniflow.core.exceptions import InternalError

class ComponentHealth(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNUSABLE = "UNUSABLE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ComponentMetrics:
    component_name: str
    uptime_seconds: float = 0
    operations_total: int = 0
    operations_failed: int = 0
    last_activity: Optional[str] = None
    custom_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}

    @property
    def success_rate(self) -> float:
        total = self.operations_total + self.operations_failed
        return (self.operations_total / total * 100) if total > 0 else 100

    @property
    def health(self) -> str:
        if self.success_rate > 90.0:
            return ComponentHealth.HEALTHY.value
        elif self.success_rate > 75.0:
            return ComponentHealth.WARNING.value
        elif self.success_rate > 50.0:
            return ComponentHealth.CRITICAL.value
        elif self.success_rate > 0.0:
            return ComponentHealth.UNUSABLE.value
        else:
            return ComponentHealth.UNKNOWN.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_name": self.component_name,
            "component_health": self.health,
            "uptime_seconds": self.uptime_seconds,
            "operations_total": self.operations_total,
            "operations_failed": self.operations_failed,
            "last_activity": self.last_activity,
            "custom_metrics": self.custom_metrics,
            "success_rate": self.success_rate
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentMetrics':
        return cls(
            component_name=data["component_name"],
            uptime_seconds=data.get("uptime_seconds", 0),
            operations_total=data.get("operations_total", 0),
            operations_failed=data.get("operations_failed", 0),
            last_activity=data.get("last_activity"),
            custom_metrics=data.get("custom_metrics", {})
        )


class MonitorableComponent(ABC):
    @abstractmethod
    def get_component_name(self) -> str:
        """Component ismini döndür"""
        pass

    @abstractmethod
    def get_component_metrics(self) -> ComponentMetrics:
        """Component metrics'ini döndür"""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Component çalışıyor mu?"""
        pass

    @abstractmethod
    def start(self) -> bool:
        """Start component"""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop component"""
        pass

    @abstractmethod
    def get_component_config(self) -> Dict[str, Any]:
        """Get component configuration"""
        pass

    @abstractmethod
    def set_component_config(self) -> Dict[str, Any]:
        """Set component configuration"""
        pass

    def restart(self) -> bool:
        try:
            self.stop()
            self.start()
            return True
        except Exception as e:
            raise InternalError(message="Failed to restart monitoring service", details=str(e))