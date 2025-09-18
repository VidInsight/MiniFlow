"""
MiniFlow Logger Konfigürasyonları
Tüm MiniFlow componentleri için logger yapılandırmaları
"""

# Logger konfigürasyonları - temiz console için console output kapalı
MINIFLOW_CORE_LOGGER_CONFIG = {
    "level": "INFO",
    "filename": "logs/miniflow_core.log",
    "max_size_mb": 100,
    "max_files": 5,
    "console_output": False,  # Console'a hiç basma
    "console_level": "CRITICAL",
    "file_level": "INFO",
    "console_formatter": "plain",
    "file_formatter": "json"
}

MINIFLOW_API_LOGGER_CONFIG = {
    "level": "INFO",
    "filename": "logs/miniflow_api.log",
    "max_size_mb": 200,
    "max_files": 10,
    "console_output": True,  # Console'a hiç basma
    "console_level": "CRITICAL",
    "file_level": "INFO",
    "console_formatter": "plain",
    "file_formatter": "json"
}

DATABASE_ORCHESTRATION_LOGGER_CONFIG = {
    "level": "DEBUG",
    "filename": "logs/database_orchestration.log",
    "max_size_mb": 150,
    "max_files": 7,
    "console_output": False,  # Console'a hiç basma
    "console_level": "CRITICAL",
    "file_level": "DEBUG",
    "console_formatter": "plain",
    "file_formatter": "json"
}

INPUT_HANDLER_LOGGER_CONFIG = {
    "level": "DEBUG",
    "filename": "logs/input_handler.log",
    "max_size_mb": 50,
    "max_files": 5,
    "console_output": False,  # Console'a hiç basma
    "console_level": "CRITICAL",
    "file_level": "DEBUG",
    "console_formatter": "plain",
    "file_formatter": "json"
}

OUTPUT_HANDLER_LOGGER_CONFIG = {
    "level": "DEBUG",
    "filename": "logs/output_handler.log",
    "max_size_mb": 50,
    "max_files": 5,
    "console_output": True,  # Console'a output handler loglarını yazdır
    "console_level": "INFO",
    "file_level": "DEBUG",
    "console_formatter": "plain",
    "file_formatter": "json"
}

EXECUTION_ENGINE_LOGGER_CONFIG = {
    "level": "DEBUG",
    "filename": "logs/execution_engine.log",
    "max_size_mb": 100,
    "max_files": 8,
    "console_output": True,  # Console'a payload'ları yazdır
    "console_level": "DEBUG",
    "file_level": "DEBUG",
    "console_formatter": "plain",
    "file_formatter": "json"
}

# Tüm logger konfigürasyonlarını içeren sözlük
ALL_LOGGER_CONFIGS = {
    "miniflow_core": MINIFLOW_CORE_LOGGER_CONFIG,
    "miniflow_api": MINIFLOW_API_LOGGER_CONFIG,
    "database_orchestration": DATABASE_ORCHESTRATION_LOGGER_CONFIG,
    "input_handler": INPUT_HANDLER_LOGGER_CONFIG,
    "output_handler": OUTPUT_HANDLER_LOGGER_CONFIG,
    "execution_engine": EXECUTION_ENGINE_LOGGER_CONFIG
}