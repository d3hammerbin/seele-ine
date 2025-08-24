#!/usr/bin/env python3
"""
API v1 Router

Main router that includes all API v1 endpoints.
This router is included in the main FastAPI application.
"""

from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.api_keys import router as api_keys_router
from .endpoints.credentials import router as credentials_router
from .endpoints.billing import router as billing_router
from .endpoints.websocket import router as websocket_router

# Create main API v1 router
api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# Include API key management endpoints
api_router.include_router(
    api_keys_router,
    prefix="/api-keys",
    tags=["API Keys"]
)

# Include credential processing endpoints
api_router.include_router(
    credentials_router,
    prefix="/credentials",
    tags=["Credentials"]
)

# Include billing endpoints
api_router.include_router(
    billing_router,
    prefix="/billing",
    tags=["Billing"]
)

# Include WebSocket endpoints
api_router.include_router(
    websocket_router,
    prefix="/ws",
    tags=["WebSocket"]
)

# Health check endpoint for API v1
@api_router.get("/health", tags=["Health"])
async def api_health():
    """
    API v1 health check endpoint.
    """
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "seele-e-api"
    }