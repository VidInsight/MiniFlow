"""
MiniFlow Input Handler Konfigürasyonu
Input processing ve validation ayarları
"""

INPUT_HANDLER_CONFIG = {
    "max_input_size_mb": 100,
    "supported_formats": ["json", "xml", "csv", "txt"],
    "enable_validation": True,
    "strict_validation": False,
    "auto_convert_types": True,
    "encoding": "utf-8",
    "buffer_size": 8192,
    "enable_caching": True,
    "cache_ttl_seconds": 3600,  # 1 saat
    "max_cached_items": 1000,
    "enable_compression": True,
    "compression_level": 6,
    "timeout_seconds": 30.0
}
