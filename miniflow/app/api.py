from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from miniflow.core.logger import get_logger

from miniflow.app.routes.bff.router import bff_router
# from miniflow.app.routes.bfd.router import bfd_router  # BFD router not implemented yet
from miniflow.app.routes.bfa.router import bfa_router
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

    # Initialize and start TriggerManager
    trigger_manager = None
    try:
        if hasattr(app.state, 'database_engine') and app.state.database_engine:
            from miniflow.database import DatabaseOrchestrator
            from miniflow.triggers import TriggerManager
            
            # Create database orchestrator
            orchestrator = DatabaseOrchestrator(app.state.database_engine)
            
            # Create and start trigger manager
            trigger_manager = TriggerManager(orchestrator)
            success = await trigger_manager.start()
            
            if success:
                # Store trigger manager in app state for dependency injection
                app.state.trigger_manager = trigger_manager
                if logger:
                    logger.info("TriggerManager started successfully")
            else:
                if logger:
                    logger.error("Failed to start TriggerManager")
        else:
            if logger:
                logger.warning("Database engine not available, TriggerManager not started")
    except Exception as e:
        if logger:
            logger.error(f"Error initializing TriggerManager: {str(e)}")

    yield

    # Shutdown
    if logger:
        logger.info("MiniFlow API shutting down...")
    
    # Stop TriggerManager
    if trigger_manager:
        try:
            await trigger_manager.stop()
            if logger:
                logger.info("TriggerManager stopped successfully")
        except Exception as e:
            if logger:
                logger.error(f"Error stopping TriggerManager: {str(e)}")

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