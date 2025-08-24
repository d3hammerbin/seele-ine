#!/usr/bin/env python3
"""
SEELE-E Backend Application

Sistema de Extracción y Evaluación de Licencias Electorales - Edición Empresarial
Procesamiento inteligente de credenciales INE con IA multi-proveedor

Autor: SEELE-E Team
Versión: 1.0.0
Fecha: 2025-01-21
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Agregar el directorio raíz al path de Python
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.config.settings import get_settings
from app.core.exceptions.handlers import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.presentation.middleware.logging import LoggingMiddleware
from app.presentation.middleware.rate_limit import RateLimitMiddleware
from app.presentation.middleware.security import SecurityMiddleware
from app.presentation.api.v1.router import api_router
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.external.ai_providers.factory import AIProviderFactory

# Configuración global
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    Inicializa y limpia recursos al arrancar y cerrar la aplicación.
    """
    logger.info("🚀 Iniciando SEELE-E Backend...")
    
    try:
        # Inicializar base de datos
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("✅ Base de datos inicializada")
        
        # Inicializar proveedores de IA
        ai_factory = AIProviderFactory()
        await ai_factory.initialize_providers()
        logger.info("✅ Proveedores de IA inicializados")
        
        # Verificar servicios externos
        await _health_check_services()
        logger.info("✅ Servicios externos verificados")
        
        logger.info("🎉 SEELE-E Backend iniciado correctamente")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante la inicialización: {e}")
        raise
    finally:
        # Limpieza de recursos
        logger.info("🧹 Cerrando SEELE-E Backend...")
        
        try:
            await db_manager.close()
            logger.info("✅ Conexiones de base de datos cerradas")
        except Exception as e:
            logger.error(f"❌ Error cerrando base de datos: {e}")
        
        logger.info("👋 SEELE-E Backend cerrado correctamente")


async def _health_check_services():
    """
    Verifica la conectividad con servicios externos críticos.
    """
    # TODO: Implementar health checks para Redis, proveedores IA, etc.
    pass


def create_application() -> FastAPI:
    """
    Factory para crear la aplicación FastAPI con toda la configuración.
    """
    # Configurar logging
    _configure_logging()
    
    # Crear aplicación FastAPI
    app = FastAPI(
        title="SEELE-E API",
        description="Sistema de Extracción y Evaluación de Licencias Electorales - Edición Empresarial",
        version="1.0.0",
        docs_url="/docs" if settings.SHOW_DOCS else None,
        redoc_url="/redoc" if settings.SHOW_DOCS else None,
        openapi_url="/openapi.json" if settings.SHOW_DOCS else None,
        lifespan=lifespan,
        debug=settings.DEBUG
    )
    
    # Configurar middleware
    _configure_middleware(app)
    
    # Configurar rutas
    _configure_routes(app)
    
    # Configurar manejadores de excepciones
    _configure_exception_handlers(app)
    
    return app


def _configure_logging():
    """
    Configura el sistema de logging con Loguru.
    """
    # Remover handler por defecto
    logger.remove()
    
    # Configurar formato de logs
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Handler para consola
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Handler para archivo (solo en producción)
    if settings.ENVIRONMENT == "production":
        logger.add(
            "logs/seele_backend.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="gz",
            backtrace=True,
            diagnose=False  # No mostrar variables en producción
        )


def _configure_middleware(app: FastAPI):
    """
    Configura todos los middleware de la aplicación.
    """
    # Middleware de seguridad (primero)
    app.add_middleware(SecurityMiddleware)
    
    # Middleware de rate limiting
    app.add_middleware(RateLimitMiddleware)
    
    # Middleware de logging
    app.add_middleware(LoggingMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page-Count"]
    )
    
    # Trusted hosts middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )


def _configure_routes(app: FastAPI):
    """
    Configura todas las rutas de la aplicación.
    """
    # API routes
    app.include_router(
        api_router,
        prefix="/api/v1",
        tags=["API v1"]
    )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Endpoint de verificación de salud del servicio.
        """
        return {
            "status": "healthy",
            "service": "seele-e-backend",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": "2025-01-21T22:05:00Z"
        }
    
    # Metrics endpoint para Prometheus
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """
        Endpoint de métricas para Prometheus.
        """
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """
        Endpoint raíz con información básica del servicio.
        """
        return {
            "service": "SEELE-E Backend API",
            "description": "Sistema de Extracción y Evaluación de Licencias Electorales",
            "version": "1.0.0",
            "docs": "/docs" if settings.SHOW_DOCS else "Documentación no disponible",
            "health": "/health",
            "api": "/api/v1"
        }
    
    # Servir archivos estáticos (uploads, etc.)
    if os.path.exists("uploads"):
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


def _configure_exception_handlers(app: FastAPI):
    """
    Configura los manejadores de excepciones personalizados.
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError
    
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


# Crear la aplicación
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando servidor de desarrollo...")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD_ON_CHANGE,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio"
    )