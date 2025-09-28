from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from miniflow.core.logger import get_logger

from miniflow.app.routes.bff.router import bff_router
# from miniflow.app.routes.bfd.router import bfd_router  # BFD router not implemented yet
from miniflow.app.routes.bfa.router import bfa_router
# from miniflow.app.routes.webhook.router import router as webhook_router  # Webhook router not implemented yet
from miniflow.app.middleware import (CorrelationMiddleware,
                                     LoggingMiddleware,
                                     ErrorHandlerMiddleware)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle management"""
    # Startup
    logger = get_logger("miniflow_core")
    if logger:
        logger.info("MiniFlow API starting up...")

    # Start cron service for scheduled triggers
    startup_service = None
    try:
        if hasattr(app.state, 'database_engine') and app.state.database_engine:
            from miniflow.database import DatabaseOrchestrator
            from miniflow.app.services.startup import StartupService
            
            # Create database orchestrator
            orchestrator = DatabaseOrchestrator(app.state.database_engine)
            
            # Create and start startup service
            startup_service = StartupService(orchestrator)
            startup_service.start_cron_service()
            
            # Store startup service in app state
            app.state.startup_service = startup_service
            
            if logger:
                logger.info("Cron service started successfully")
        else:
            if logger:
                logger.warning("Database engine not available, cron service not started")
    except Exception as e:
        if logger:
            logger.error(f"Error starting cron service: {str(e)}")

    yield

    # Shutdown
    if logger:
        logger.info("MiniFlow API shutting down...")
    
    # Stop cron service
    if startup_service:
        try:
            startup_service.stop_cron_service()
            if logger:
                logger.info("Cron service stopped successfully")
        except Exception as e:
            if logger:
                logger.error(f"Error stopping cron service: {str(e)}")
    

def create_app(database_engine=None) -> FastAPI:
    """FastAPI uygulaması factory"""
    app = FastAPI(
        title="MiniFlow API",
        description="Modular FastAPI Backend with Correlation Tracking",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Production'da güvenli origin'ler
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware'ler (sıra önemli!)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(CorrelationMiddleware)

    # Backend router'larını dahil et
    app.include_router(
        bff_router,
        prefix="/api/bff",
        tags=["Back for Frontend"]
    )

    # BFD router not implemented yet
    # app.include_router(
    #     bfd_router,
    #     prefix="/api/bfd", 
    #     tags=["Back for Developer"]
    # )
    
    app.include_router(
        bfa_router,
        prefix="/api/bfa",
        tags=["Back for Admin"]
    )
    
    # Webhook router (external services için) - TODO: Implement webhook router
    # app.include_router(
    #     webhook_router,
    #     prefix="/webhook",
    #     tags=["Webhooks"]
    # )

    # Database engine'i app state'e kaydet
    if database_engine:
        app.state.database_engine = database_engine
        logger = get_logger("miniflow_core")
        if logger:
            logger.info("Database engine injected into FastAPI app")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "miniflow-api"}

    return app

# Uvicorn reload için app instance oluştur
app = create_app()