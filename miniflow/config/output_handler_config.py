"""
MiniFlow Output Handler Konfigürasyonu
Output processing ve formatting ayarları
"""

OUTPUT_HANDLER_CONFIG = {
    "default_format": "json",
    "supported_formats": ["json", "xml", "csv", "txt", "yaml"],
    "enable_formatting": True,
    "pretty_print": True,
    "indent_size": 2,
    "encoding": "utf-8",
    "buffer_size": 8192,
    "enable_caching": True,
    "cache_ttl_seconds": 1800,  # 30 dakika
    "max_cached_items": 500,
    "enable_compression": True,
    "compression_level": 6,
    "timeout_seconds": 30.0,
    "enable_streaming": True,
    "chunk_size": 4096
}
