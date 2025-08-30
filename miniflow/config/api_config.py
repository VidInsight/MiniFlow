"""
MiniFlow API Konfigürasyonu
FastAPI servis ayarları ve endpoint konfigürasyonları
"""

API_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "log_level": "warning",  # Uvicorn INFO mesajlarını gizle
    "reload": False,
    "workers": 1,
    "access_log": False,  # Access log'ları kapalı kalsın (gereksiz gürültü)
    "app_title": "MiniFlow API",
    "app_description": "MiniFlow Core Services API",
    "app_version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json"
}