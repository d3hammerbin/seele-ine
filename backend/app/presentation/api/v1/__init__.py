#!/usr/bin/env python3
"""
API v1 Router

Combines all v1 API endpoints into a single router.
"""

from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.api_keys import router as api_keys_router

# Create main v1 router
api_router = APIRouter(prefix="/v1")

# Include all endpoint routers
api_router.include_router(auth_router)
api_router.include_router(api_keys_router)

# Health check endpoint
@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Seele INE API"
    }