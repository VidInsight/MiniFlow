from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from miniflow.core.logger import get_logger
from miniflow.core.logger.levels import LogLevel
from miniflow.core.exceptions import ValidationError, ResourceNotFound
from miniflow.core.logger.registry import LoggerRegistry, ModuleLoggerConfig, LoggerStrategy
from miniflow.config.logger_config import ALL_LOGGER_CONFIGS


class LoggerOperations:
    """BFA Logger administrative operations"""

    def __init__(self):
        self.registry = LoggerRegistry()
        self.logger = get_logger("operations")

        # ==================== LOGGER DISCOVERY ====================

    def get_available_loggers(self) -> List[Dict[str, Any]]:
        """Sistemdeki tüm logger'ları listele"""
        loggers_info = []

        # Registry'deki logger'lar (private access)
        registry_loggers = list(self.registry._loggers.keys()) if hasattr(self.registry, '_loggers') else []

        for logger_name in registry_loggers:
            try:
                # Config ve performance stats'ı güvenli bir şekilde al
                config = getattr(self.registry, '_configs', {}).get(logger_name)
                performance = getattr(self.registry, '_performance_stats', {}).get(logger_name, {})

                logger_info = {
                    "name": logger_name,
                    "type": "registry",
                    "level": config.level if config else "UNKNOWN",
                    "filename": config.filename if config else None,
                    "enabled": config.enabled if config else False,
                    "strategy": getattr(self.registry, '_strategy', 'UNKNOWN').value if hasattr(getattr(self.registry, '_strategy', None), 'value') else 'UNKNOWN',
                    "performance": performance,
                    "created_at": performance.get("created_at") if performance else None,
                    "log_count": performance.get("log_count", 0) if performance else 0,
                    "handlers": ["file", "console"] if config else []
                }
                loggers_info.append(logger_info)
            except Exception as e:
                # Hata durumunda minimal info ekle
                loggers_info.append({
                    "name": logger_name,
                    "type": "registry",
                    "level": "ERROR",
                    "enabled": False,
                    "error": str(e)
                })

        # Log dosyalarından algılama
        log_files = self._discover_log_files()
        for log_file in log_files:
            # Sadece registry'de olmayan dosyaları ekle
            if not any(l.get("filename") == log_file["path"] for l in loggers_info):
                # Logger config'den level bilgisini al
                logger_name = log_file["name"]
                config_level = "UNKNOWN"
                
                # Config'de var mı kontrol et (exact match)
                if logger_name in ALL_LOGGER_CONFIGS:
                    config_level = ALL_LOGGER_CONFIGS[logger_name]["level"]
                else:
                    # Prefix'li dosya için config key'i bul
                    # Örn: miniflow_miniflow_api.log -> miniflow_api
                    if logger_name.startswith("miniflow_"):
                        clean_name = logger_name.replace("miniflow_", "", 1)
                        if clean_name in ALL_LOGGER_CONFIGS:
                            config_level = ALL_LOGGER_CONFIGS[clean_name]["level"]
                
                loggers_info.append({
                    "name": logger_name,
                    "type": "file_only",
                    "level": config_level,
                    "filename": log_file["path"],
                    "enabled": True,
                    "file_size": log_file["size"],
                    "last_modified": log_file["last_modified"]
                })

        return sorted(loggers_info, key=lambda x: x["name"])

    def _discover_log_files(self) -> List[Dict[str, Any]]:
        """logs/ dizinindeki tüm log dosyalarını keşfet"""
        log_files = []
        logs_dir = Path("logs")

        if not logs_dir.exists():
            # Test ortamında temp dizin kullan
            import tempfile
            logs_dir = Path(tempfile.gettempdir()) / "miniflow_test_logs"
            if not logs_dir.exists():
                return log_files

        for log_file in logs_dir.glob("*.log"):
            try:
                stat = log_file.stat()
                log_files.append({
                    "name": log_file.stem,
                    "path": str(log_file),
                    "size": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except OSError:
                continue

        return log_files

        # ==================== LOGGER CONFIGURATION ====================

    def get_logger_config(self, logger_name: str) -> Dict[str, Any]:
        """Belirli bir logger'ın konfigürasyonunu getir"""
        try:
            # Config'i registry'den al
            config = getattr(self.registry, '_configs', {}).get(logger_name)
            
            if config:
                # Registry'de config var
                return {
                    "module_name": config.module_name,
                    "level": config.level,
                    "filename": config.filename,
                    "max_size_mb": config.max_size_mb,
                    "max_files": config.max_files,
                    "console_output": config.console_output,
                    "console_level": config.console_level,
                    "file_formatter": config.file_formatter,
                    "console_formatter": config.console_formatter,
                    "enabled": config.enabled,
                    "tags": list(config.tags),
                    "custom_fields": config.custom_fields
                }
            else:
                # File-based logger için default config
                available_loggers = self.get_available_loggers()
                file_logger = next((l for l in available_loggers if l["name"] == logger_name), None)
                
                if not file_logger:
                    raise ResourceNotFound(f"Logger not found: {logger_name}")
                
                # Default config for file-based logger
                return {
                    "module_name": logger_name,
                    "level": "INFO",  # Default level
                    "filename": file_logger.get("filename", f"logs/{logger_name}.log"),
                    "max_size_mb": 100,  # Default values
                    "max_files": 5,
                    "console_output": False,  # File-only logger
                    "console_level": "ERROR",
                    "file_formatter": "json",
                    "console_formatter": "plain",
                    "enabled": file_logger.get("enabled", True),
                    "tags": [],
                    "custom_fields": {},
                    "type": "file_only",  # Mark as file-only
                    "note": "This is a file-based logger without registry config"
                }
        except Exception as e:
            self.logger.error(f"Failed to get logger config for {logger_name}: {str(e)}")
            raise

    def update_logger_config(self, logger_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Logger konfigürasyonunu güncelle"""

        # Mevcut config'i al
        current_config = getattr(self.registry, '_configs', {}).get(logger_name)
        if not current_config:
            # File-based logger için update desteklenmiyor
            available_loggers = self.get_available_loggers()
            file_logger = next((l for l in available_loggers if l["name"] == logger_name), None)
            
            if file_logger and file_logger.get("type") == "file_only":
                raise ValidationError(f"Config updates not supported for file-based logger: {logger_name}. Only registry-based loggers can be updated.")
            else:
                raise ResourceNotFound(f"Logger not found: {logger_name}")

        # Validation - Sadece güvenli alanlar
        if "level" in updates:
            if updates["level"] not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                raise ValidationError("Invalid log level")
        
        # Handler recreation gerektiren alanları reddet
        unsafe_fields = ["max_size_mb", "max_files", "filename"]
        for field in unsafe_fields:
            if field in updates:
                raise ValidationError(f"Field '{field}' cannot be updated at runtime. Requires system restart.")

        # Config güncelle
        updated_config = ModuleLoggerConfig(
            module_name=current_config.module_name,
            level=updates.get("level", current_config.level),
            filename=updates.get("filename", current_config.filename),
            max_size_mb=updates.get("max_size_mb", current_config.max_size_mb),
            max_files=updates.get("max_files", current_config.max_files),
            console_output=updates.get("console_output", current_config.console_output),
            console_level=updates.get("console_level", current_config.console_level),
            file_formatter=updates.get("file_formatter", current_config.file_formatter),
            console_formatter=updates.get("console_formatter", current_config.console_formatter),
            enabled=updates.get("enabled", current_config.enabled),
            tags=getattr(current_config, 'tags', set()),
            custom_fields=getattr(current_config, 'custom_fields', {})
        )

        # Registry'ye kaydet
        self.registry.register_module_config(updated_config)
        
        # Manuel olarak registry'deki config'i güncelle (test ortamı için)
        if hasattr(self.registry, '_configs'):
            self.registry._configs[logger_name] = updated_config

        self.logger.info(
            f"Logger config updated: {logger_name}",
            extra={"logger_name": logger_name, "updates": updates}
        )

        return self.get_logger_config(logger_name)

        # ==================== LOG STREAMING ====================
        # ❌ REMOVED: Production ortamında risk oluşturuyor
        # Sebep: Memory leak, connection timeout, file rotation sorunları
        # Alternatif: SSH ile tail -f veya log dosyası indirme

        # ==================== LOG MANAGEMENT ====================

    def get_log_file_info(self, logger_name: str) -> Dict[str, Any]:
        """Log dosyası bilgilerini getir"""
        config = getattr(self.registry, '_configs', {}).get(logger_name)
        if not config or not config.filename:
            # Test ortamında temp dizin kullan
            logs_dir = Path("logs")
            if not logs_dir.exists():
                # Test ortamında temp dizin kullan
                import tempfile
                logs_dir = Path(tempfile.gettempdir()) / "miniflow_test_logs"
            log_file = logs_dir / f"{logger_name}.log"
        else:
            log_file = Path(config.filename)

        if not log_file.exists():
            raise ResourceNotFound(f"Log file not found: {log_file}")

        stat = log_file.stat()

        # Backup dosyalarını bul
        backup_files = []
        pattern = f"{log_file.stem}.*{log_file.suffix}"
        for backup in log_file.parent.glob(pattern):
            if backup != log_file:
                backup_stat = backup.stat()
                backup_files.append({
                    "name": backup.name,
                    "size": backup_stat.st_size,
                    "last_modified": datetime.fromtimestamp(backup_stat.st_mtime).isoformat()
                })

        return {
            "filename": str(log_file),
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "backup_files": sorted(backup_files, key=lambda x: x["last_modified"], reverse=True),
            "backup_count": len(backup_files)
        }

    def clear_log_file(self, logger_name: str) -> Dict[str, Any]:
        """Log dosyasını temizle"""
        config = getattr(self.registry, '_configs', {}).get(logger_name)
        if not config or not config.filename:
            # Test ortamında temp dizin kullan
            logs_dir = Path("logs")
            if not logs_dir.exists():
                # Test ortamında temp dizin kullan
                import tempfile
                logs_dir = Path(tempfile.gettempdir()) / "miniflow_test_logs"
            log_file = logs_dir / f"{logger_name}.log"
        else:
            log_file = Path(config.filename)

        if not log_file.exists():
            raise ResourceNotFound(f"Log file not found: {log_file}")

        old_size = log_file.stat().st_size

        # Dosyayı temizle
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("")

        self.logger.warning(
            f"Log file cleared: {log_file}",
            extra={"logger_name": logger_name, "old_size": old_size}
        )

        return {
            "cleared": True,
            "old_size": old_size,
            "filename": str(log_file)
        }

