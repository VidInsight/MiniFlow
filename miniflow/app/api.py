from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from miniflow.core.logger import get_logger

from miniflow.app.routes.bff.router import bff_router
from miniflow.app.routes.bfd.router import bfd_router
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

    yield

    # Shutdown
    if logger:
        logger.info("MiniFlow API shutting down...")

def create_app() -> FastAPI:
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
    app.include_router(
        bfd_router,
        prefix="/api/bfd",
        tags=["Back for Developer"]
    )
    app.include_router(
        bfa_router,
        prefix="/api/bfa",
        tags=["Back for Admin"]
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "miniflow-api"}

    return app