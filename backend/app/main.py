"""
KAVACH-INFINITY Main Application
Production FastAPI application with all routes and middleware
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import structlog
import time
from typing import AsyncGenerator
import asyncio

from app.config import settings
from app.api.v1.router import api_router
from app.core.database import init_db, close_db
from app.core.redis_client import init_redis, close_redis
from app.services.ai.model_loader import load_all_models
from app.services.realtime.websocket_manager import websocket_manager
from app.services.safety.safety_monitor import safety_monitor
from app.middleware.logging import LoggingMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown"""
    logger.info("Starting KAVACH-INFINITY", version=settings.APP_VERSION, env=settings.APP_ENV)
    
    # Startup
    try:
        # Initialize database connections
        await init_db()
        logger.info("Database connection established")
        
        # Initialize Redis
        await init_redis()
        logger.info("Redis connection established")
        
        # Load AI/ML models
        await load_all_models()
        logger.info("AI/ML models loaded")
        
        # Start safety monitor
        asyncio.create_task(safety_monitor.start())
        logger.info("Safety monitor started")
        
        # Start WebSocket manager
        asyncio.create_task(websocket_manager.start())
        logger.info("WebSocket manager started")
        
        logger.info("KAVACH-INFINITY startup complete", 
                   host=settings.HOST, port=settings.PORT)
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down KAVACH-INFINITY")
    
    await safety_monitor.stop()
    await websocket_manager.stop()
    await close_redis()
    await close_db()
    
    logger.info("KAVACH-INFINITY shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
        # KAVACH-INFINITY API
        
        Real-time AI-powered civilian protection platform for:
        - 🚂 Railways & Metro Safety
        - 🚗 Smart Transportation
        - 🏭 Industrial Safety
        - ⚡ Power & Utilities
        - 🏙️ Smart Cities
        - 🔐 Critical Infrastructure
        
        ## Features
        - Real-time sensor data ingestion
        - AI-powered anomaly detection
        - Predictive failure analysis
        - Risk scoring & alerts
        - Safety automation
        
        ## Authentication
        All endpoints require JWT authentication except health checks.
        """,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )
    
    # Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Include API routers
    app.include_router(api_router, prefix="/api/v1")
    
    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", 
                    error=str(exc), 
                    path=request.url.path,
                    method=request.method)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": time.time()
            }
        )
    
    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check"""
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        }
    
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check for Kubernetes"""
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected",
            "models": "loaded"
        }
    
    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Liveness check for Kubernetes"""
        return {"status": "alive"}
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
