import time
import threading
from typing import Optional

# Core imports
from miniflow.core.logger import setup_logging, get_logger, shutdown_logging
from miniflow.core.monitoring import SystemMonitor

# Config imports
from miniflow.config.logger_config import ALL_LOGGER_CONFIGS
from miniflow.config.monitoring_config import MONITORING_CONFIG
from miniflow.config.api_config import API_CONFIG

# FastAPI imports
from miniflow.app import create_app
import uvicorn

# Database imports
from miniflow.database import get_sqlite_config, get_mysql_config, get_postgresql_config
from miniflow.database import DatabaseEngine, create_database_engine
from miniflow.database import DatabaseOrchestrator
from miniflow.database import Base

# Global singleton instances
_miniflow_core_instance: Optional['MiniflowCore'] = None
_miniflow_core_lock = threading.Lock()


class MiniflowCore:
    """Ana MiniFlow sınıfı - Logger, Monitoring ve API'yi yönetir"""

    def __init__(self):
        # Core parametreleri - config'den al
        self.app_name = "MiniFlow"
        self.app_version = "1.0.0"
        self.start_time = None
        
        # Config'leri yükle
        self.api_config = API_CONFIG

        # Servis durumları
        self.logger_started = False
        self.monitoring_started = False
        self.database_engine_started = False
        self.api_started = False
        self.input_handler_started = False
        self.output_handler_started = False
        self.execution_engine_started = False
        self.running = False

        # Servis instance'ları
        self.logger = None
        self.system_monitor = None
        self.fastapi_app = None
        self.database_engine = None
        self.database_orchestrator = None
        self.execution_engine = None
        self.input_handler = None
        self.output_handler = None

    def start_loggers(self):
        """Konfigrasyona göre logger'ları başlatır"""
        if self.logger_started:
            print("Loggers already started")
            return
        
        try:
            print(f"\n{time.asctime()} :: Starting logger services...")

            # Her component için logger'ı başlat
            for logger_name, config in ALL_LOGGER_CONFIGS.items():
                print(f"\t* Setting up {logger_name} logger...")

                setup_logging(**config)
                logger = get_logger(logger_name)
                logger.info(f"{logger_name} logger initialized successfully", extra={"config": config,"logger_name": logger_name})
                
                print(f"\t\t* {logger_name} logger ready")
            
            # Ana core logger'ı set et
            self.logger = get_logger("miniflow_core")
            self.logger_started = True

            print("All logger services started successfully")
            
        except Exception as e:
            print(f"Failed to start loggers: {e}")
            raise

    def start_monitoring(self):
        """Monitoring servisini başlat"""
        if self.monitoring_started:
            print("Monitoring already started")
            return

        if not self.logger_started:
            print("Logger must be started before monitoring")
            return

        try:
            print(f"\n{time.asctime()} :: Starting monitoring service")

            # SystemMonitor instance oluştur
            if self.system_monitor is None:
                self.system_monitor = SystemMonitor(MONITORING_CONFIG)
            
            self.system_monitor.start()
            self.monitoring_started = True

            # Monitoring başlangıç logları
            self.logger.info("Monitoring service started")
            self.logger.debug("Monitoring service config details", extra={"config": MONITORING_CONFIG.to_dict(),"uptime": 0})

            print(f"{time.asctime()} :: Monitoring service started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start monitoring: {e}")
            if self.logger:
                self.logger.error("Failed to start monitoring", extra={"error": str(e)})
            raise 
            
    def stop_monitoring(self):
        """Monitoring servisini durdur"""
        if not self.monitoring_started:
            print("Monitoring not started")
            return
        
        try:
            print(f"\n{time.asctime()} :: Stopping monitoring service...")

            self.system_monitor.stop()
            self.monitoring_started = False
            
            if self.logger:
                self.logger.info("Monitoring service stopped")

            print(f"{time.asctime()} :: Monitoring service stopped successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop monitoring: {e}")
            if self.logger:
                self.logger.error("Failed to stop monitoring", extra={"error": str(e)})

    def start_database_engine(self):
        if self.database_engine_started:
            print("Database engine already started")
            return

        if not self.logger_started:
            print("Logger must be started before database engine")
            return

        try:
            print(f"\n{time.asctime()} :: Starting database engine")

            # DatabaseEngine instance oluştur
            if self.database_engine is None:
                config = get_sqlite_config("miniflow_team_test")
                self.database_engine = create_database_engine(config, auto_start=True, create_tables=True)
                self.database_engine_started = True
            
            # DatabaseOrchestrator'ı başlat
            if self.database_orchestrator is None:
                self.database_orchestrator = DatabaseOrchestrator(self.database_engine)

            # Database başlangıç logları
            self.logger.info("Database engine started")
            self.logger.info("Database tables have been created")
            self.logger.debug("Database engine config details", extra={"database_name": "miniflow_team_test"})

            print(f"{time.asctime()} :: Database engine started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start database engine: {e}")
            if self.logger:
                self.logger.error("Failed to start database engine", extra={"error": str(e)})
            raise

    def stop_database_engine(self):
        if not self.database_engine_started:
            print("Database engine not started")
            return

        try:
            print(f"\n{time.asctime()} :: Stopping database engine service...")

            self.database_engine.stop()
            self.database_engine_started = False
            self.database_orchestrator = None

            if self.logger:
                self.logger.info("Database engine service stopped")

            print(f"{time.asctime()} :: Database engine service stopped successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop database engine: {e}")
            if self.logger:
                self.logger.error("Failed to stop database engine", extra={"error": str(e)})

    def start_api(self):
        """FastAPI servisini başlatır"""
        if self.api_started:
            print("API already started")
            return

        if not self.logger_started:
            print("Logger must be started before API")
            return
        
        try:
            print(f"\n{time.asctime()} :: Starting FastAPI service...")

            # Database engine'i app'e inject et
            self.fastapi_app = create_app(database_engine=self.database_engine)
            self.api_started = True

            # API başlangıç logları
            self.logger.info("FastAPI service initialized")
            self.logger.debug("FastAPI service config details", extra={
                               "host": self.api_config["host"],
                               "port": self.api_config["port"],
                               "endpoints": [
                                   "/api/bfa/logger/*",
                                   "/api/bfa/monitoring/*",
                                   "/api/bfd/*",
                                   "/api/bff/*",
                                   "/health"
                               ]
                           })
            
            print(f"{time.asctime()} :: FastAPI service started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start FastAPI: {e}")
            if self.logger:
                self.logger.error("Failed to start API", extra={"error": str(e)})
            raise
        
    def stop_api(self):
        """FastAPI servisini durdur"""
        if not self.api_started:
            print("API not started")
            return

        try:
            print(f"\n{time.asctime()} :: Stopping API service...")

            # API server durdurma (uvicorn server reference gerekli)
            self.api_started = False
            self.fastapi_app = None

            if self.logger:
                self.logger.info("FastAPI service stopped")

            print(f"{time.asctime()} :: API service stopped successfully")

        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop API: {e}")
            if self.logger:
                self.logger.error("Failed to stop API", extra={"error": str(e)})

    def start(self):
        """Tüm MiniFlow çekirdek servislerini başlatır"""
        if self.running:
            print("MiniFlow already running")
            return
        
        try:
            print(f"\nStarting {self.app_name} v{self.app_version}...")
            print(f"{time.asctime()} Starting {self.app_name} v{self.app_version}...")
            self.start_time = time.time()
            
            # 1. Logger'ları başlat
            self.start_loggers()
            
            # 2. Database Engine başlat
            self.start_database_engine()
            
            # 3. Monitoring'i başlat
            self.start_monitoring()

            # 4. API'yi başlat
            self.start_api()

            self.running = True
            
            # Başlangıç başarı mesajı
            if self.logger:
                self.logger.info(f"{self.app_name} started successfully", 
                               extra={
                                   "version": self.app_version,
                                   "start_time": self.start_time,
                                   "services": {
                                       "logger": self.logger_started,
                                       "monitoring": self.monitoring_started,
                                       "api": self.api_started
                                   }
                               })
            
            print(f"\n{time.asctime()} :: {self.app_name} started successfully!")
            print(f"\tServices Status:")
            print(f"\t* Logger: {'ACTIVE' if self.logger_started else 'DEACTIVE'}")
            print(f"\t* Database Engine: {'ACTIVE' if self.database_engine_started else 'DEACTIVE'}")
            print(f"\t* Monitoring: {'ACTIVE' if self.monitoring_started else 'DEACTIVE'}")
            print(f"\t* API: {'ACTIVE' if self.api_started else 'DEACTIVE'}")
            
        except Exception as e:
            print(f"Failed to start {self.app_name}: {e}")
            self.stop()
            raise

    def stop(self):
        """Tüm MiniFlow çekirdek servislerini durdurur"""
        if not self.running and not self.logger_started:
            print("WARNING: MiniFlow not running")
            return
        
        try:
            print(f"Stopping {self.app_name}...")
            
            # 1. API'yi durdur
            self.stop_api()

            # 2. Database Engine'i durdur
            self.stop_database_engine()

            # 2. Monitoring'i durdur
            self.stop_monitoring()
            
            # 3. Logger'ları durdur
            if self.logger_started and self.logger:
                uptime = time.time() - self.start_time if self.start_time else 0
                self.logger.info(f"{self.app_name} shutting down", 
                               extra={"uptime_seconds": uptime})
                
                shutdown_logging()
                self.logger_started = False
            
            self.running = False
            print(f"{self.app_name} stopped successfully")
            
        except Exception as e:
            print(f"Failed to stop {self.app_name}: {e}")

    def restart(self):
        """Tüm MiniFlow çekirdek servislerini yeniden başlatır"""
        print(f"{time.asctime()} :: Restarting MiniFlow...")

        try:
            self.stop()
            time.sleep(2)  # Kısa bekleme
            self.start()
            print(f"{time.asctime()} :: MiniFlow restarted successfully")

        except Exception as e:
            print(f"{time.asctime()} :: Failed to restart MiniFlow: {e}")
            raise

    def get_status(self):
        """MiniFlow çekirdek servislerinin durumunu döner"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "running": self.running,
            "services": {
                "logger": self.logger_started,
                "database_engine": self.database_engine_started,
                "monitoring": self.monitoring_started,
                "api": self.api_started,
                "input_handler": self.input_handler_started,
                "output_handler": self.output_handler_started,
                "execution_engine": self.execution_engine_started,
            },
            "uptime_seconds": time.time() - self.start_time if self.start_time else 0,
            "api_url": f"http://{self.api_config['host']}:{self.api_config['port']}" if self.api_started else None
        }
    
    def get_database_engine(self):
        """Database engine'i döndür"""
        if not self.database_engine_started:
            raise RuntimeError("Database engine not started")
        return self.database_engine
    
    def get_database_orchestrator(self):
        """Database orchestrator'ı döndür"""
        if not self.database_engine_started:
            raise RuntimeError("Database engine not started")
        return self.database_orchestrator

    def run_api_server(self):
        """Fast API server'ı çalıştır"""
        if not self.running:
            self.start()
        
        if not self.api_started:
            print("API not started")
            raise RuntimeError("API service not started")
        
        try:
            print(f"\n{time.asctime()} :: Starting FastAPI server...")
            print(f"\t* Server will be available at: http://{self.api_config['host']}:{self.api_config['port']}")
            print(f"\t* API documentation at: http://{self.api_config['host']}:{self.api_config['port']}/docs")
            print("Press Ctrl+C to stop the server")

            # Uvicorn server'ı başlat - reload için app string kullan
            if self.api_config["reload"]:
                # Reload modunda app string kullanılmalı
                uvicorn.run(
                    "miniflow.app.api:app",  # String import path
                    host=self.api_config["host"],
                    port=self.api_config["port"],
                    log_level=self.api_config["log_level"],
                    reload=self.api_config["reload"],
                    access_log=self.api_config.get("access_log", False)
                )
            else:
                # Production modunda app object kullan
                uvicorn.run(
                    self.fastapi_app,
                    host=self.api_config["host"],
                    port=self.api_config["port"],
                    log_level=self.api_config["log_level"],
                    reload=self.api_config["reload"],
                    access_log=self.api_config.get("access_log", False)
                )
            
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        except Exception as e:
            print(f"FastAPI server error: {e}")
            if self.logger:
                self.logger.error("FastAPI server error", extra={"error": str(e)})
        finally:
            self.stop()

    @classmethod
    def get_instance(cls) -> 'MiniflowCore':
        """Global MiniflowCore singleton getter"""
        global _miniflow_core_instance

        with _miniflow_core_lock:
            if _miniflow_core_instance is None:
                _miniflow_core_instance = cls()

            return _miniflow_core_instance


def main():
    """Komut yapısı"""
    import sys
    import os
    import subprocess
    
    # Argument kontrolü
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "daemon":
            # Background'da başlat ve PID döndür
            print("Starting MiniFlow daemon...")
            
            try:
                # Background process başlat
                process = subprocess.Popen([
                    sys.executable, "-m", "miniflow", "_run"
                ], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Completely detach
                )
                
                print(f"MiniFlow daemon started")
                print(f"PID: {process.pid}")
                print(f"Status: python -m miniflow status")
                print(f"Stop: kill {process.pid}")
                
            except Exception as e:
                print(f"Failed to start daemon: {e}")
                
        elif command == "_run":
            # Internal runner - daemon için
            miniflow = MiniflowCore()
            try:
                miniflow.run_api_server()
            except Exception as e:
                print(f"MiniFlow daemon error: {e}")
                
        elif command == "status":
            # Status check
            miniflow = MiniflowCore()
            
            print("MiniFlow Status:")
            try:
                status = miniflow.get_status()
                
                print(f"App: {status['app_name']} v{status['app_version']}")
                print(f"Running: {'Active' if status['running'] else 'Stopped'}")
                print(f"API: {status['api_url'] or 'Not available'}")
                print(f"Uptime: {status['uptime_seconds']:.1f}s")
                
                # Services status
                services = status['services']
                print(f"Services:")
                print(f"   Logger: {'Active' if services['logger'] else 'Inactive'}")
                print(f"   Monitoring: {'Active' if services['monitoring'] else 'Inactive'}")
                print(f"   API: {'Active' if services['api'] else 'Inactive'}")
                
            except Exception as e:
                print(f"Cannot check status: {e}")
                
        elif command in ["help", "--help", "-h"]:
            # Help
            print("MiniFlow Commands:")
            print("")
            print("  python -m miniflow          # Start (foreground)")
            print("  python -m miniflow daemon   # Start (background)")
            print("  python -m miniflow status   # Check status")
            print("  python -m miniflow help     # This help")
            print("")
            print("Examples:")
            print("  python -m miniflow daemon   # Returns PID: 12345")
            print("  kill 12345                  # Stop daemon")
            
        else:
            print(f"Unknown command: {command}")
            print("Use: python -m miniflow help")
            sys.exit(1)
    
    else:
        # Default: foreground başlat
        print("Starting MiniFlow (foreground)...")
        print("Press Ctrl+C to stop")
        print("Use 'daemon' for background mode")
        
        miniflow = MiniflowCore()
        try:
            miniflow.run_api_server()
        except KeyboardInterrupt:
            print("\nStopping MiniFlow...")
            miniflow.stop()
        except Exception as e:
            print(f"Error: {e}")
            miniflow.stop()


if __name__ == "__main__":
    main()