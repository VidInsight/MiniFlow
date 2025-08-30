from typing import Dict, List, Any, Optional

from miniflow.core.monitoring import (
    SystemMonitor, 
    MonitoringConfig, 
    AlertLevel
)
from miniflow.core.logger import get_logger
from miniflow.core.exceptions import (
    ValidationError, 
    ResourceNotFound, 
    InternalError
)


class MonitoringOperations:
    """BFA Monitoring administrative operations"""
    
    def __init__(self):
        self.logger = get_logger("monitoring_operations")
        # Global SystemMonitor instance'ı kullanacağız (singleton pattern)
        self._system_monitor: Optional[SystemMonitor] = None
    
    def _get_system_monitor(self) -> SystemMonitor:
        """Get or create SystemMonitor instance"""
        if self._system_monitor is None:
            # Global singleton instance kullan
            try:
                from miniflow.__main__ import get_system_monitor_instance
                self._system_monitor = get_system_monitor_instance()
                
                # Eğer başlatılmamışsa başlat
                if not self._system_monitor.running:
                    self._system_monitor.start()
                    
            except ImportError:
                # Fallback: Direct instance oluştur
                config = MonitoringConfig()
                self._system_monitor = SystemMonitor(config)
                if not self._system_monitor.running:
                    self._system_monitor.start()
                    
        return self._system_monitor
    
    # ==================== SYSTEM METRICS ====================
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Anlık sistem metriklerini getir"""
        try:
            monitor = self._get_system_monitor()
            metrics = monitor.get_system_metrics()
            
            if not metrics:
                raise ResourceNotFound("System metrics not available")
            
            # Status bilgisi ekle
            metrics["status"] = "running" if monitor.running else "stopped"
            
            self.logger.debug("System metrics retrieved")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {str(e)}")
            raise InternalError("Failed to retrieve system metrics", details=str(e))
    
    def get_all_components_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Tüm component metriklerini getir"""
        try:
            monitor = self._get_system_monitor()
            components_metrics = monitor.get_all_components_metrics()
            
            self.logger.debug(f"Retrieved metrics for {len(components_metrics)} components")
            return components_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get component metrics: {str(e)}")
            raise InternalError("Failed to retrieve component metrics", details=str(e))
    
    def get_component_metrics(self, component_name: str) -> Dict[str, Any]:
        """Belirli bir component'in metriklerini getir"""
        if not component_name or not component_name.strip():
            raise ValidationError("Component name cannot be empty")
        
        try:
            monitor = self._get_system_monitor()
            metrics = monitor.get_component_metrics(component_name.strip())
            
            if not metrics:
                raise ResourceNotFound(f"Component not found: {component_name}")
            
            self.logger.debug(f"Component metrics retrieved: {component_name}")
            return metrics
            
        except ResourceNotFound:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get component metrics for {component_name}: {str(e)}")
            raise InternalError(f"Failed to retrieve metrics for component: {component_name}", details=str(e))
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Monitoring sistem durumunu getir"""
        try:
            monitor = self._get_system_monitor()
            
            status_info = {
                "running": monitor.running,
                "uptime_seconds": monitor.get_system_uptime() if monitor.running else 0,
                "component_count": monitor.get_component_count(),
                "registered_components": monitor.get_registered_components(),
                "alert_manager_active": monitor.alert_manager is not None,
                "config": monitor.get_config().to_dict()
            }
            
            self.logger.debug("Monitoring status retrieved")
            return status_info
            
        except Exception as e:
            self.logger.error(f"Failed to get monitoring status: {str(e)}")
            raise InternalError("Failed to retrieve monitoring status", details=str(e))
    
    # ==================== ALERT MANAGEMENT ====================
    
    def get_all_alerts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Tüm uyarıları getir"""
        try:
            monitor = self._get_system_monitor()
            if not monitor.alert_manager:
                return []
            
            if limit:
                alerts = monitor.alert_manager.get_recent_alerts(limit)
            else:
                alerts = monitor.alert_manager.alerts
            
            # Alert'leri dict formatına çevir
            alerts_data = [alert.to_dict() for alert in alerts]
            
            self.logger.debug(f"Retrieved {len(alerts_data)} alerts")
            return alerts_data
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts: {str(e)}")
            raise InternalError("Failed to retrieve alerts", details=str(e))
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Son N uyarıyı getir"""
        if count < 1 or count > 100:
            raise ValidationError("Alert count must be between 1 and 100")
        
        try:
            monitor = self._get_system_monitor()
            if not monitor.alert_manager:
                return []
            
            alerts = monitor.alert_manager.get_recent_alerts(count)
            alerts_data = [alert.to_dict() for alert in alerts]
            
            self.logger.debug(f"Retrieved {len(alerts_data)} recent alerts")
            return alerts_data
            
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {str(e)}")
            raise InternalError("Failed to retrieve recent alerts", details=str(e))
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Uyarı özetini getir"""
        try:
            monitor = self._get_system_monitor()
            if not monitor.alert_manager:
                return {
                    "total_alerts": 0,
                    "critical_count": 0,
                    "warning_count": 0,
                    "info_count": 0,
                    "recent_alert": None
                }
            
            # Alert summary from manager
            alert_counts = monitor.alert_manager.get_alert_summary()
            
            # Calculate totals by level
            critical_count = sum(count for key, count in alert_counts.items() if ":CRITICAL" in key)
            warning_count = sum(count for key, count in alert_counts.items() if ":WARNING" in key)
            info_count = sum(count for key, count in alert_counts.items() if ":INFO" in key)
            
            # Get most recent alert
            recent_alerts = monitor.alert_manager.get_recent_alerts(1)
            recent_alert = recent_alerts[0].to_dict() if recent_alerts else None
            
            summary = {
                "total_alerts": len(monitor.alert_manager.alerts),
                "critical_count": critical_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "recent_alert": recent_alert,
                "alert_counts": alert_counts
            }
            
            self.logger.debug("Alert summary retrieved")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get alert summary: {str(e)}")
            raise InternalError("Failed to retrieve alert summary", details=str(e))
    
    def get_alerts_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Seviyeye göre uyarıları getir"""
        # Validate level
        valid_levels = ["INFO", "WARNING", "CRITICAL"]
        if level.upper() not in valid_levels:
            raise ValidationError(f"Invalid alert level. Must be one of: {valid_levels}")
        
        try:
            monitor = self._get_system_monitor()
            if not monitor.alert_manager:
                return []
            
            alert_level = AlertLevel(level.upper())
            alerts = monitor.alert_manager.get_alerts_by_level(alert_level)
            alerts_data = [alert.to_dict() for alert in alerts]
            
            self.logger.debug(f"Retrieved {len(alerts_data)} alerts for level {level}")
            return alerts_data
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts by level {level}: {str(e)}")
            raise InternalError(f"Failed to retrieve alerts for level: {level}", details=str(e))
    
    def get_alerts_by_component(self, component: str) -> List[Dict[str, Any]]:
        """Component'e göre uyarıları getir"""
        if not component or not component.strip():
            raise ValidationError("Component name cannot be empty")
        
        try:
            monitor = self._get_system_monitor()
            if not monitor.alert_manager:
                return []
            
            alerts = monitor.alert_manager.get_alerts_by_component(component.strip())
            alerts_data = [alert.to_dict() for alert in alerts]
            
            self.logger.debug(f"Retrieved {len(alerts_data)} alerts for component {component}")
            return alerts_data
            
        except Exception as e:
            self.logger.error(f"Failed to get alerts by component {component}: {str(e)}")
            raise InternalError(f"Failed to retrieve alerts for component: {component}", details=str(e))
    
    def clear_all_alerts(self) -> Dict[str, Any]:
        """Tüm uyarıları temizle"""
        try:
            monitor = self._get_system_monitor()
            if not monitor.alert_manager:
                return {"cleared": 0, "message": "No alert manager active"}
            
            old_count = len(monitor.alert_manager.alerts)
            monitor.alert_manager.clear_alerts()
            
            self.logger.warning(
                f"All alerts cleared by admin",
                extra={"cleared_count": old_count}
            )
            
            return {
                "cleared": old_count,
                "message": f"Cleared {old_count} alerts"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to clear alerts: {str(e)}")
            raise InternalError("Failed to clear alerts", details=str(e))
    
    # ==================== CONFIGURATION MANAGEMENT ====================
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Monitoring konfigürasyonunu getir"""
        try:
            monitor = self._get_system_monitor()
            config = monitor.get_config()
            
            self.logger.debug("Monitoring config retrieved")
            return config.to_dict()
            
        except Exception as e:
            self.logger.error(f"Failed to get monitoring config: {str(e)}")
            raise InternalError("Failed to retrieve monitoring config", details=str(e))
    
    def update_monitoring_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Monitoring konfigürasyonunu güncelle"""
        try:
            monitor = self._get_system_monitor()
            current_config = monitor.get_config()
            
            # Validation
            self._validate_config_updates(updates)
            
            # Yeni config oluştur
            config_dict = current_config.to_dict()
            config_dict.update(updates)
            
            # Create new config instance
            new_config = MonitoringConfig()
            new_config.from_dict(config_dict)
            
            # Update monitor config
            monitor.config = new_config
            
            # Restart alert manager if alert settings changed
            if 'enable_alerts' in updates or 'max_alerts_history' in updates:
                monitor._start_alert_manager()
            
            self.logger.info(
                f"Monitoring config updated",
                extra={"updates": updates}
            )
            
            return new_config.to_dict()
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update monitoring config: {str(e)}")
            raise InternalError("Failed to update monitoring config", details=str(e))
    
    def _validate_config_updates(self, updates: Dict[str, Any]) -> None:
        """Config update validation"""
        
        # Validate monitoring_interval
        if "monitoring_interval" in updates:
            value = updates["monitoring_interval"]
            if not isinstance(value, (int, float)) or value < 5.0 or value > 30.0:
                raise ValidationError("monitoring_interval must be between 5.0 and 30.0 seconds")
        
        # Validate threshold values
        threshold_fields = [
            "memory_warning_threshold", "memory_critical_threshold",
            "cpu_warning_threshold", "cpu_critical_threshold", 
            "disk_warning_threshold", "disk_critical_threshold"
        ]
        
        for field in threshold_fields:
            if field in updates:
                value = updates[field]
                if not isinstance(value, (int, float)) or value < 0.0 or value > 100.0:
                    raise ValidationError(f"{field} must be between 0.0 and 100.0")
        
        # Validate max_alerts_history
        if "max_alerts_history" in updates:
            value = updates["max_alerts_history"]
            if not isinstance(value, int) or value < 10 or value > 1000:
                raise ValidationError("max_alerts_history must be between 10 and 1000")
        
        # Validate enable_alerts
        if "enable_alerts" in updates:
            if not isinstance(updates["enable_alerts"], bool):
                raise ValidationError("enable_alerts must be a boolean")
        
        # Check threshold consistency
        if "memory_warning_threshold" in updates and "memory_critical_threshold" in updates:
            if updates["memory_warning_threshold"] >= updates["memory_critical_threshold"]:
                raise ValidationError("memory_warning_threshold must be less than memory_critical_threshold")
        
        if "cpu_warning_threshold" in updates and "cpu_critical_threshold" in updates:
            if updates["cpu_warning_threshold"] >= updates["cpu_critical_threshold"]:
                raise ValidationError("cpu_warning_threshold must be less than cpu_critical_threshold")
        
        if "disk_warning_threshold" in updates and "disk_critical_threshold" in updates:
            if updates["disk_warning_threshold"] >= updates["disk_critical_threshold"]:
                raise ValidationError("disk_warning_threshold must be less than disk_critical_threshold")
    
    # ==================== COMPONENT MANAGEMENT ====================
    
    def get_registered_components(self) -> List[str]:
        """Kayıtlı component'leri getir"""
        try:
            monitor = self._get_system_monitor()
            components = monitor.get_registered_components()
            
            self.logger.debug(f"Retrieved {len(components)} registered components")
            return components
            
        except Exception as e:
            self.logger.error(f"Failed to get registered components: {str(e)}")
            raise InternalError("Failed to retrieve registered components", details=str(e))
    
    def get_system_health(self) -> Dict[str, Any]:
        """Genel sistem sağlığını getir"""
        try:
            monitor = self._get_system_monitor()
            
            # System metrics
            system_metrics = monitor.get_system_metrics()
            if not system_metrics:
                system_metrics = {"error": "No system metrics available"}
            
            # Component health analysis
            components_metrics = monitor.get_all_components_metrics()
            
            healthy_count = 0
            warning_count = 0
            critical_count = 0
            
            for component_name, metrics in components_metrics.items():
                health = metrics.get("component_health", "UNKNOWN")
                if health == "HEALTHY":
                    healthy_count += 1
                elif health == "WARNING":
                    warning_count += 1
                elif health in ["CRITICAL", "UNUSABLE"]:
                    critical_count += 1
            
            total_components = len(components_metrics)
            
            # Overall health determination
            if critical_count > 0:
                overall_status = "CRITICAL"
            elif warning_count > 0:
                overall_status = "WARNING"
            elif healthy_count == total_components and total_components > 0:
                overall_status = "HEALTHY"
            else:
                overall_status = "UNKNOWN"
            
            # Recent alerts count
            recent_alerts_count = 0
            if monitor.alert_manager:
                recent_alerts = monitor.alert_manager.get_recent_alerts(10)
                recent_alerts_count = len(recent_alerts)
            
            health_info = {
                "overall_status": overall_status,
                "system_metrics": system_metrics,
                "component_count": total_components,
                "healthy_components": healthy_count,
                "warning_components": warning_count,
                "critical_components": critical_count,
                "recent_alerts_count": recent_alerts_count,
                "monitoring_uptime": monitor.get_system_uptime() if monitor.running else 0
            }
            
            self.logger.debug("System health retrieved")
            return health_info
            
        except Exception as e:
            self.logger.error(f"Failed to get system health: {str(e)}")
            raise InternalError("Failed to retrieve system health", details=str(e))
