"""
Author: Sean Froning
Created Date: 8.17.2026
Main entrypoint for Fiery backend API
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fiery_python import (
    config,
    exception,
    logging,
    observability,
    middleware,
    limiter,
)
from core import health, lifespan
from integrations import InferenceRouter
from ml import router as ModelsRouter

# Setup structured logging
logging.setup_structured_logging()
observability.configure_sentry()
logger = logging.get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Focus backend API",
    lifespan=lifespan,
    description="Backend API for Focus full stack app",
    version="0.0.1",
)

# Register middleware
app.add_middleware(middleware)

# Register exception handlers
exception.register_exception_handlers(app)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Include routers
app.include_router(health.router)
app.include_router(InferenceRouter.router)
app.include_router(ModelsRouter.router)


# Root endpoint
@app.get("/")
def root():
    """Root endpoint with basic API information and configuration status"""

    return {
        "service": "Fiery backend API",
        "version": "0.0.1",
        "status": "running",
        "configuration": {
            "required_services": config.get_required_services_status(),
        },
        "endpoints": {"health": "/health", "ready": "/ready"},
    }
