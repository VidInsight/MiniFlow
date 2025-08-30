"""
BFA Monitoring Schemas
Admin monitoring yönetimi için Pydantic modelleri
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SystemMetricsResponse(BaseModel):
    """Sistem metrikleri response modeli"""
    timestamp: str = Field(description="Metric timestamp in ISO format")
    monitoring_uptime: float = Field(description="Monitoring system uptime in seconds")
    system_memory_percent: float = Field(description="System memory usage percentage")
    system_cpu_percent: float = Field(description="System CPU usage percentage")
    disk_usage_percent: float = Field(description="Disk usage percentage")
    active_threads: int = Field(description="Number of active threads")
    total_processes: int = Field(description="Total number of processes")
    registered_components: int = Field(description="Number of registered components")
    status: str = Field(description="Monitoring system status")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00.123456",
                "monitoring_uptime": 3600.5,
                "system_memory_percent": 67.8,
                "system_cpu_percent": 45.2,
                "disk_usage_percent": 23.1,
                "active_threads": 12,
                "total_processes": 156,
                "registered_components": 8,
                "status": "running"
            }
        }


class AlertResponse(BaseModel):
    """Alert response modeli"""
    alert_level: str = Field(description="Alert level (INFO, WARNING, CRITICAL)")
    alert_type: str = Field(description="Alert type (DEVICE, NETWORK, SYSTEM, COMPONENT)")
    alert_message: str = Field(description="Alert message")
    alert_timestamp: str = Field(description="Alert timestamp in ISO format")
    alert_component: str = Field(description="Component that generated the alert")
    alert_metadata: Dict[str, Any] = Field(description="Additional alert metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "alert_level": "CRITICAL",
                "alert_type": "SYSTEM",
                "alert_message": "Critical memory usage: 89.5%",
                "alert_timestamp": "2024-01-15T10:30:00.123456",
                "alert_component": "MEMORY_MONITOR",
                "alert_metadata": {
                    "metric_type": "memory",
                    "current_value": 89.5,
                    "threshold": 85.0
                }
            }
        }


class AlertSummary(BaseModel):
    """Alert özet modeli"""
    total_alerts: int = Field(description="Total number of alerts")
    critical_count: int = Field(description="Number of critical alerts")
    warning_count: int = Field(description="Number of warning alerts")
    info_count: int = Field(description="Number of info alerts")
    recent_alert: Optional[AlertResponse] = Field(None, description="Most recent alert")
    alert_counts: Dict[str, int] = Field(description="Detailed alert counts by component and level")

    class Config:
        json_schema_extra = {
            "example": {
                "total_alerts": 25,
                "critical_count": 3,
                "warning_count": 7,
                "info_count": 15,
                "recent_alert": {
                    "alert_level": "WARNING",
                    "alert_type": "SYSTEM",
                    "alert_message": "High CPU usage: 78.2%",
                    "alert_timestamp": "2024-01-15T10:30:00.123456",
                    "alert_component": "CPU_MONITOR",
                    "alert_metadata": {}
                },
                "alert_counts": {
                    "MEMORY_MONITOR:SYSTEM:CRITICAL": 2,
                    "CPU_MONITOR:SYSTEM:WARNING": 5
                }
            }
        }


class ComponentMetricsResponse(BaseModel):
    """Component metrikleri response modeli"""
    component_name: str = Field(description="Component name")
    component_health: str = Field(description="Component health status")
    uptime_seconds: float = Field(description="Component uptime in seconds")
    operations_total: int = Field(description="Total successful operations")
    operations_failed: int = Field(description="Total failed operations")
    success_rate: float = Field(description="Success rate percentage")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    custom_metrics: Dict[str, Any] = Field(description="Custom component metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "component_name": "database_manager",
                "component_health": "HEALTHY",
                "uptime_seconds": 7200.5,
                "operations_total": 1250,
                "operations_failed": 12,
                "success_rate": 99.05,
                "last_activity": "2024-01-15T10:30:00.123456",
                "custom_metrics": {
                    "connections_active": 45,
                    "query_avg_time_ms": 23.5
                }
            }
        }


class SystemHealthResponse(BaseModel):
    """Sistem sağlık durumu response modeli"""
    overall_status: str = Field(description="Overall system health status")
    system_metrics: SystemMetricsResponse = Field(description="Current system metrics")
    component_count: int = Field(description="Total number of components")
    healthy_components: int = Field(description="Number of healthy components")
    warning_components: int = Field(description="Number of components with warnings")
    critical_components: int = Field(description="Number of critical components")
    recent_alerts_count: int = Field(description="Number of recent alerts")
    monitoring_uptime: float = Field(description="Monitoring system uptime")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_status": "WARNING",
                "system_metrics": {
                    "timestamp": "2024-01-15T10:30:00.123456",
                    "monitoring_uptime": 3600.5,
                    "system_memory_percent": 67.8,
                    "system_cpu_percent": 45.2,
                    "disk_usage_percent": 23.1,
                    "active_threads": 12,
                    "total_processes": 156,
                    "registered_components": 8,
                    "status": "running"
                },
                "component_count": 8,
                "healthy_components": 6,
                "warning_components": 2,
                "critical_components": 0,
                "recent_alerts_count": 5,
                "monitoring_uptime": 3600.5
            }
        }


class MonitoringConfigUpdate(BaseModel):
    """
    Monitoring konfigürasyon güncelleme modeli
    SADECE RUNTIME'DA GÜVENLİ DEĞİŞTİRİLEBİLEN ALANLAR
    """
    monitoring_interval: Optional[float] = Field(
        None,
        description="Monitoring interval in seconds",
        ge=5.0,
        le=30.0
    )
    memory_warning_threshold: Optional[float] = Field(
        None,
        description="Memory warning threshold percentage",
        ge=0.0,
        le=100.0
    )
    memory_critical_threshold: Optional[float] = Field(
        None,
        description="Memory critical threshold percentage",
        ge=0.0,
        le=100.0
    )
    cpu_warning_threshold: Optional[float] = Field(
        None,
        description="CPU warning threshold percentage",
        ge=0.0,
        le=100.0
    )
    cpu_critical_threshold: Optional[float] = Field(
        None,
        description="CPU critical threshold percentage",
        ge=0.0,
        le=100.0
    )
    disk_warning_threshold: Optional[float] = Field(
        None,
        description="Disk warning threshold percentage",
        ge=0.0,
        le=100.0
    )
    disk_critical_threshold: Optional[float] = Field(
        None,
        description="Disk critical threshold percentage",
        ge=0.0,
        le=100.0
    )
    enable_alerts: Optional[bool] = Field(
        None,
        description="Enable or disable alert system"
    )
    max_alerts_history: Optional[int] = Field(
        None,
        description="Maximum number of alerts to keep in history",
        ge=10,
        le=1000
    )

    class Config:
        json_schema_extra = {
            "example": {
                "monitoring_interval": 15.0,
                "memory_warning_threshold": 75.0,
                "memory_critical_threshold": 90.0,
                "cpu_warning_threshold": 70.0,
                "cpu_critical_threshold": 85.0,
                "disk_warning_threshold": 85.0,
                "disk_critical_threshold": 95.0,
                "enable_alerts": True,
                "max_alerts_history": 200
            }
        }


class MonitoringConfigResponse(BaseModel):
    """Monitoring konfigürasyon response modeli"""
    monitoring_interval: float = Field(description="Monitoring interval in seconds")
    memory_warning_threshold: float = Field(description="Memory warning threshold percentage")
    memory_critical_threshold: float = Field(description="Memory critical threshold percentage")
    cpu_warning_threshold: float = Field(description="CPU warning threshold percentage")
    cpu_critical_threshold: float = Field(description="CPU critical threshold percentage")
    disk_warning_threshold: float = Field(description="Disk warning threshold percentage")
    disk_critical_threshold: float = Field(description="Disk critical threshold percentage")
    max_alerts_history: int = Field(description="Maximum alerts history")
    enable_alerts: bool = Field(description="Alert system enabled")
    max_monitoring_interval: float = Field(description="Maximum allowed monitoring interval")
    min_monitoring_interval: float = Field(description="Minimum allowed monitoring interval")

    class Config:
        json_schema_extra = {
            "example": {
                "monitoring_interval": 10.0,
                "memory_warning_threshold": 70.0,
                "memory_critical_threshold": 85.0,
                "cpu_warning_threshold": 70.0,
                "cpu_critical_threshold": 85.0,
                "disk_warning_threshold": 80.0,
                "disk_critical_threshold": 90.0,
                "max_alerts_history": 100,
                "enable_alerts": True,
                "max_monitoring_interval": 30.0,
                "min_monitoring_interval": 5.0
            }
        }


class MonitoringStatusResponse(BaseModel):
    """Monitoring sistem durumu response modeli"""
    running: bool = Field(description="Whether monitoring system is running")
    uptime_seconds: float = Field(description="System uptime in seconds")
    component_count: int = Field(description="Number of registered components")
    registered_components: List[str] = Field(description="List of registered component names")
    alert_manager_active: bool = Field(description="Whether alert manager is active")
    config: MonitoringConfigResponse = Field(description="Current monitoring configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "running": True,
                "uptime_seconds": 3600.5,
                "component_count": 8,
                "registered_components": [
                    "database_manager",
                    "api_gateway", 
                    "cache_service",
                    "message_queue"
                ],
                "alert_manager_active": True,
                "config": {
                    "monitoring_interval": 10.0,
                    "memory_warning_threshold": 70.0,
                    "memory_critical_threshold": 85.0,
                    "cpu_warning_threshold": 70.0,
                    "cpu_critical_threshold": 85.0,
                    "disk_warning_threshold": 80.0,
                    "disk_critical_threshold": 90.0,
                    "max_alerts_history": 100,
                    "enable_alerts": True,
                    "max_monitoring_interval": 30.0,
                    "min_monitoring_interval": 5.0
                }
            }
        }


class ClearAlertsResponse(BaseModel):
    """Alert temizleme response modeli"""
    cleared: int = Field(description="Number of alerts cleared")
    message: str = Field(description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "cleared": 25,
                "message": "Cleared 25 alerts"
            }
        }
