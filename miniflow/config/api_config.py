"""
MiniFlow API Konfigürasyonu
FastAPI servis ayarları ve endpoint konfigürasyonları
"""

API_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "log_level": "info",  # Geliştirme modu için daha detaylı log
    "reload": True,  # 🔄 Otomatik reload aktif
    "workers": 1,
    "access_log": True,  # Geliştirme modu için access log aktif
    "app_title": "MiniFlow API",
    "app_description": "MiniFlow Core Services API",
    "app_version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json"
}