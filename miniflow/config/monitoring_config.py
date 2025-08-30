"""
MiniFlow Monitoring Konfigürasyonu
System monitoring servis ayarları ve threshold konfigürasyonları
"""

from miniflow.core.monitoring import MonitoringConfig

# Monitoring konfigürasyon parametreleri
MONITORING_CONFIG_DICT = {
    "monitoring_interval": 15.0,  # 15 saniye aralıklarla monitoring
    "memory_warning_threshold": 75.0,  # %75 memory kullanımında warning
    "memory_critical_threshold": 90.0,  # %90 memory kullanımında critical
    "cpu_warning_threshold": 80.0,  # %80 CPU kullanımında warning
    "cpu_critical_threshold": 95.0,  # %95 CPU kullanımında critical
    "disk_warning_threshold": 85.0,  # %85 disk kullanımında warning
    "disk_critical_threshold": 95.0,  # %95 disk kullanımında critical
    "max_alerts_history": 200,  # Son 200 alert'i sakla
    "enable_alerts": True,  # Alert sistemi aktif
    "max_monitoring_interval": 60.0,  # Maksimum 60 saniye interval
    "min_monitoring_interval": 5.0   # Minimum 5 saniye interval
}

# MonitoringConfig instance'ı oluştur
MONITORING_CONFIG = MonitoringConfig(
    monitoring_interval=MONITORING_CONFIG_DICT["monitoring_interval"],
    memory_warning_threshold=MONITORING_CONFIG_DICT["memory_warning_threshold"],
    memory_critical_threshold=MONITORING_CONFIG_DICT["memory_critical_threshold"],
    cpu_warning_threshold=MONITORING_CONFIG_DICT["cpu_warning_threshold"],
    cpu_critical_threshold=MONITORING_CONFIG_DICT["cpu_critical_threshold"],
    disk_warning_threshold=MONITORING_CONFIG_DICT["disk_warning_threshold"],
    disk_critical_threshold=MONITORING_CONFIG_DICT["disk_critical_threshold"],
    max_alerts_history=MONITORING_CONFIG_DICT["max_alerts_history"],
    enable_alerts=MONITORING_CONFIG_DICT["enable_alerts"],
    max_monitoring_interval=MONITORING_CONFIG_DICT["max_monitoring_interval"],
    min_monitoring_interval=MONITORING_CONFIG_DICT["min_monitoring_interval"]
)