"""
Main FastAPI Application

Entry point for the Google CRM Integration API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.config import settings
from app.api import auth_routes, lead_routes, insight_routes
from app.services.couchbase_service import couchbase_service
from app.services.kafka_service import kafka_service

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO" if not settings.debug else "DEBUG"
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Integration service for Google Ads, Google Analytics, Couchbase Cloud, and Confluent Cloud",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info(f"Starting {settings.app_name}...")

    try:
        # Connect to Couchbase
        logger.info("Connecting to Couchbase Cloud...")
        await couchbase_service.connect()

        # Connect to Kafka
        logger.info("Connecting to Confluent Cloud (Kafka)...")
        kafka_service.connect()

        logger.info("All services connected successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown"""
    logger.info("Shutting down services...")

    try:
        # Disconnect from Couchbase
        await couchbase_service.disconnect()

        # Disconnect from Kafka
        kafka_service.disconnect()

        logger.info("All services disconnected successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
        "couchbase_connected": couchbase_service._connected,
        "kafka_connected": kafka_service._connected
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "description": "Google CRM Integration API",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "auth": "/auth",
            "leads": "/leads",
            "insights": "/insights"
        }
    }


# Include routers
app.include_router(auth_routes.router)
app.include_router(lead_routes.router)
app.include_router(insight_routes.router)


# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info"
    )
