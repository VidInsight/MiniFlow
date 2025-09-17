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

# Engine imports
from miniflow.engine import EngineManager

# Handler imports
from miniflow.scheduler.input_handler import InputHandler, InputHandlerConfig
from miniflow.scheduler.output_handler import OutputHandler, OutputHandlerConfig

# Trigger imports
from miniflow.triggers import TriggerManager

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
        self.trigger_manager_started = False
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
        self.trigger_manager = None

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

    def start_execution_engine(self):
        """Execution engine'i başlat"""
        if self.execution_engine_started:
            print("Execution engine already started")
            return

        if not self.database_engine_started:
            print("Database engine must be started before execution engine")
            return

        try:
            print(f"\n{time.asctime()} :: Starting execution engine...")

            # MockExecutionEngine instance oluştur
            if self.execution_engine is None:
                self.execution_engine = EngineManager()
            
            self.execution_engine.start()
            self.execution_engine_started = True

            # Execution engine başlangıç logları
            self.logger.info("Execution engine started")
            self.logger.debug("Execution engine config details", extra={
                "processing_delay": 1.0,
                "success_rate": 0.95,
                "max_queue_size": 1000
            })

            print(f"{time.asctime()} :: Execution engine started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start execution engine: {e}")
            if self.logger:
                self.logger.error("Failed to start execution engine", extra={"error": str(e)})
            raise

    def stop_execution_engine(self):
        """Execution engine'i durdur"""
        if not self.execution_engine_started:
            print("Execution engine not started")
            return

        try:
            print(f"\n{time.asctime()} :: Stopping execution engine...")

            self.execution_engine.stop()
            self.execution_engine_started = False
            self.execution_engine = None

            if self.logger:
                self.logger.info("Execution engine stopped")

            print(f"{time.asctime()} :: Execution engine stopped successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop execution engine: {e}")
            if self.logger:
                self.logger.error("Failed to stop execution engine", extra={"error": str(e)})

    def start_output_handler(self):
        """Output handler'ı başlat"""
        if self.output_handler_started:
            print("Output handler already started")
            return

        if not self.execution_engine_started:
            print("Execution engine must be started before output handler")
            return

        try:
            print(f"\n{time.asctime()} :: Starting output handler...")

            # OutputHandlerConfig oluştur
            output_config = OutputHandlerConfig(
                batch_size=50,
                worker_threads=4,
                min_polling_interval=0.1,
                max_polling_interval=5.0,
                current_polling_interval=0.5
            )

            # OutputHandler instance oluştur
            if self.output_handler is None:
                self.output_handler = OutputHandler(
                    config=output_config,
                    orchestrator=self.database_orchestrator,
                    exec_engine=self.execution_engine
                )
            
            self.output_handler.start()
            self.output_handler_started = True

            # Output handler başlangıç logları
            self.logger.info("Output handler started")
            self.logger.debug("Output handler config details", extra=output_config.to_dict())

            print(f"{time.asctime()} :: Output handler started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start output handler: {e}")
            if self.logger:
                self.logger.error("Failed to start output handler", extra={"error": str(e)})
            raise

    def stop_output_handler(self):
        """Output handler'ı durdur"""
        if not self.output_handler_started:
            print("Output handler not started")
            return

        try:
            print(f"\n{time.asctime()} :: Stopping output handler...")

            self.output_handler.stop()
            self.output_handler_started = False
            self.output_handler = None

            if self.logger:
                self.logger.info("Output handler stopped")

            print(f"{time.asctime()} :: Output handler stopped successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop output handler: {e}")
            if self.logger:
                self.logger.error("Failed to stop output handler", extra={"error": str(e)})

    def start_input_handler(self):
        """Input handler'ı başlat"""
        if self.input_handler_started:
            print("Input handler already started")
            return

        if not self.execution_engine_started:
            print("Execution engine must be started before input handler")
            return

        try:
            print(f"\n{time.asctime()} :: Starting input handler...")

            # InputHandlerConfig oluştur
            input_config = InputHandlerConfig(
                batch_size=50,
                worker_threads=4,
                min_polling_interval=0.1,
                max_polling_interval=5.0,
                current_polling_interval=1.0
            )

            # InputHandler instance oluştur
            if self.input_handler is None:
                self.input_handler = InputHandler(
                    config=input_config,
                    orchestrator=self.database_orchestrator,
                    exec_engine=self.execution_engine
                )
            
            self.input_handler.start()
            self.input_handler_started = True

            # Input handler başlangıç logları
            self.logger.info("Input handler started")
            self.logger.debug("Input handler config details", extra=input_config.to_dict())

            print(f"{time.asctime()} :: Input handler started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start input handler: {e}")
            if self.logger:
                self.logger.error("Failed to start input handler", extra={"error": str(e)})
            raise

    def stop_input_handler(self):
        """Input handler'ı durdur"""
        if not self.input_handler_started:
            print("Input handler not started")
            return

        try:
            print(f"\n{time.asctime()} :: Stopping input handler...")

            self.input_handler.stop()
            self.input_handler_started = False
            self.input_handler = None

            if self.logger:
                self.logger.info("Input handler stopped")

            print(f"{time.asctime()} :: Input handler stopped successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop input handler: {e}")
            if self.logger:
                self.logger.error("Failed to stop input handler", extra={"error": str(e)})

    def start_trigger_manager(self):
        """Trigger manager'ı başlat"""
        if self.trigger_manager_started:
            print("Trigger manager already started")
            return

        if not self.database_engine_started:
            print("Database engine must be started before trigger manager")
            return

        try:
            print(f"\n{time.asctime()} :: Starting trigger manager...")

            # TriggerManager instance oluştur
            if self.trigger_manager is None:
                self.trigger_manager = TriggerManager(self.database_orchestrator)
            
            # TriggerManager'ı başlat (async method olduğu için sync wrapper kullan)
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.trigger_manager.start())
            finally:
                loop.close()
            
            self.trigger_manager_started = True

            # Trigger manager başlangıç logları
            self.logger.info("Trigger manager started")
            self.logger.debug("Trigger manager config details", extra=self.trigger_manager.get_component_config())

            print(f"{time.asctime()} :: Trigger manager started successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to start trigger manager: {e}")
            if self.logger:
                self.logger.error("Failed to start trigger manager", extra={"error": str(e)})
            raise

    def stop_trigger_manager(self):
        """Trigger manager'ı durdur"""
        if not self.trigger_manager_started:
            print("Trigger manager not started")
            return

        try:
            print(f"\n{time.asctime()} :: Stopping trigger manager...")

            # TriggerManager'ı durdur (async method olduğu için sync wrapper kullan)
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.trigger_manager.stop())
            finally:
                loop.close()
            
            self.trigger_manager_started = False
            self.trigger_manager = None

            if self.logger:
                self.logger.info("Trigger manager stopped")

            print(f"{time.asctime()} :: Trigger manager stopped successfully")
        except Exception as e:
            print(f"{time.asctime()} :: Failed to stop trigger manager: {e}")
            if self.logger:
                self.logger.error("Failed to stop trigger manager", extra={"error": str(e)})

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
            
            # 3. Execution Engine başlat
            self.start_execution_engine()
            
            # 4. Output Handler başlat
            self.start_output_handler()
            
            # 5. Input Handler başlat
            self.start_input_handler()
            
            # 6. Trigger Manager başlat
            self.start_trigger_manager()
            
            # 7. Monitoring'i başlat
            self.start_monitoring()

            # 8. API'yi başlat
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
            print(f"\t* Execution Engine: {'ACTIVE' if self.execution_engine_started else 'DEACTIVE'}")
            print(f"\t* Output Handler: {'ACTIVE' if self.output_handler_started else 'DEACTIVE'}")
            print(f"\t* Input Handler: {'ACTIVE' if self.input_handler_started else 'DEACTIVE'}")
            print(f"\t* Trigger Manager: {'ACTIVE' if self.trigger_manager_started else 'DEACTIVE'}")
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

            # 2. Input Handler'ı durdur
            self.stop_input_handler()
            
            # 3. Output Handler'ı durdur
            self.stop_output_handler()
            
            # 4. Trigger Manager'ı durdur
            self.stop_trigger_manager()
            
            # 5. Execution Engine'i durdur
            self.stop_execution_engine()

            # 6. Database Engine'i durdur
            self.stop_database_engine()

            # 7. Monitoring'i durdur
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
                "trigger_manager": self.trigger_manager_started,
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
                print(f"   Database Engine: {'Active' if services['database_engine'] else 'Inactive'}")
                print(f"   Execution Engine: {'Active' if services['execution_engine'] else 'Inactive'}")
                print(f"   Output Handler: {'Active' if services['output_handler'] else 'Inactive'}")
                print(f"   Input Handler: {'Active' if services['input_handler'] else 'Inactive'}")
                print(f"   Trigger Manager: {'Active' if services['trigger_manager'] else 'Inactive'}")
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