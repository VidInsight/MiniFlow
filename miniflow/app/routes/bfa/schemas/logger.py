"""
BFA Logger Schemas
Admin logger yönetimi için Pydantic modelleri
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LoggerConfigUpdate(BaseModel):
    """
    Logger konfigürasyon güncelleme modeli
    SADECE RUNTIME'DA GÜVENLİ DEĞİŞTİRİLEBİLEN ALANLAR
    """
    # ✅ Runtime'da güvenli değiştirilебilir
    level: Optional[str] = Field(
        None, 
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    console_output: Optional[bool] = Field(
        None, 
        description="Enable console output"
    )
    console_level: Optional[str] = Field(
        None, 
        description="Console log level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    file_formatter: Optional[str] = Field(
        None,
        description="File formatter type",
        pattern="^(json|plain)$"
    )
    console_formatter: Optional[str] = Field(
        None,
        description="Console formatter type", 
        pattern="^(json|plain)$"
    )
    enabled: Optional[bool] = Field(
        None, 
        description="Enable/disable logger"
    )
    
    # ❌ REMOVED: Handler recreation gerektiren alanlar
    # max_size_mb: Handler yeniden oluşturulması gerekli
    # max_files: Handler yeniden oluşturulması gerekli  
    # filename: Yeni dosya handler gerekli

    class Config:
        json_schema_extra = {
            "example": {
                "level": "DEBUG",
                "console_output": True,
                "console_level": "ERROR", 
                "file_formatter": "json",
                "console_formatter": "plain",
                "enabled": True
            }
        }


class LoggerInfo(BaseModel):
    """Logger bilgi modeli"""
    name: str = Field(description="Logger name/identifier")
    type: str = Field(description="Logger type (registry, file_only)")
    level: str = Field(description="Current log level")
    filename: Optional[str] = Field(None, description="Log file path")
    enabled: bool = Field(description="Whether logger is enabled")
    log_count: Optional[int] = Field(0, description="Total log count")
    strategy: Optional[str] = Field(None, description="Logging strategy")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance stats")
    created_at: Optional[str] = Field(None, description="Logger creation time")
    file_size: Optional[int] = Field(None, description="Log file size in bytes")
    last_modified: Optional[str] = Field(None, description="Last modification time")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "miniflow_core",
                "type": "registry",
                "level": "INFO",
                "filename": "logs/miniflow.log",
                "enabled": True,
                "log_count": 1250,
                "strategy": "centralized"
            }
        }


class BackupFileInfo(BaseModel):
    """Backup dosya bilgi modeli"""
    name: str = Field(description="Backup file name")
    size: int = Field(description="File size in bytes")
    last_modified: str = Field(description="Last modification timestamp")


class LogFileInfo(BaseModel):
    """Log dosyası detay bilgi modeli"""
    filename: str = Field(description="Full path to log file")
    size: int = Field(description="File size in bytes")
    size_mb: float = Field(description="File size in MB")
    last_modified: str = Field(description="Last modification timestamp")
    backup_count: int = Field(description="Number of backup files")
    backup_files: List[BackupFileInfo] = Field(description="List of backup files")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "/path/to/logs/miniflow.log",
                "size": 52428800,
                "size_mb": 50.0,
                "last_modified": "2024-01-15T10:30:00",
                "backup_count": 3,
                "backup_files": [
                    {
                        "name": "miniflow.1.log",
                        "size": 104857600,
                        "last_modified": "2024-01-14T10:30:00"
                    }
                ]
            }
        }


class LoggerSystemInfo(BaseModel):
    """Logger sistem bilgi modeli"""
    strategy: str = Field(description="Current logging strategy")
    total_loggers: int = Field(description="Total number of registered loggers")
    total_log_files: int = Field(description="Total number of log files")
    total_size_mb: float = Field(description="Total size of all log files in MB")
    logs_directory: str = Field(description="Logs directory path")
    available_levels: List[str] = Field(description="Available log levels")
    available_strategies: List[str] = Field(description="Available logging strategies")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy": "centralized",
                "total_loggers": 5,
                "total_log_files": 12,
                "total_size_mb": 245.8,
                "logs_directory": "/path/to/logs",
                "available_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "available_strategies": ["centralized", "module_based", "hybrid", "custom"]
            }
        }


class LoggerConfig(BaseModel):
    """Logger tam konfigürasyon modeli (read-only)"""
    module_name: str = Field(description="Module name")
    level: str = Field(description="Log level")
    filename: Optional[str] = Field(None, description="Log file path")
    max_size_mb: int = Field(description="Maximum file size in MB")
    max_files: int = Field(description="Maximum number of backup files")
    console_output: bool = Field(description="Console output enabled")
    console_level: str = Field(description="Console log level")
    file_formatter: str = Field(description="File formatter type")
    console_formatter: str = Field(description="Console formatter type")
    enabled: bool = Field(description="Logger enabled status")
    tags: List[str] = Field(description="Logger tags")
    custom_fields: Dict[str, Any] = Field(description="Custom fields")

    class Config:
        json_schema_extra = {
            "example": {
                "module_name": "miniflow_core",
                "level": "INFO",
                "filename": "logs/miniflow.log",
                "max_size_mb": 100,
                "max_files": 5,
                "console_output": True,
                "console_level": "ERROR",
                "file_formatter": "json",
                "console_formatter": "plain",
                "enabled": True,
                "tags": ["core", "production"],
                "custom_fields": {"environment": "production"}
            }
        }
