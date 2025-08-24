#!/usr/bin/env python3
"""
Manejadores de excepciones personalizados para SEELE-E Backend

Proporciona manejo centralizado y consistente de errores en toda la aplicación,
con logging automático y respuestas estructuradas para el cliente.
"""

import traceback
from typing import Union

from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError

from .base import (
    SeeleException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundError,
    BusinessLogicError,
    ExternalServiceError,
    RateLimitError
)


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Maneja errores de validación de Pydantic y FastAPI.
    
    Args:
        request: La petición HTTP que causó el error
        exc: La excepción de validación
        
    Returns:
        JSONResponse con detalles del error de validación
    """
    logger.warning(
        f"Error de validación en {request.method} {request.url.path}: {exc}"
    )
    
    errors = []
    
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
    else:
        # ValidationError de Pydantic
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": "Los datos proporcionados no son válidos",
                "details": errors,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def http_exception_handler(
    request: Request, 
    exc: HTTPException
) -> JSONResponse:
    """
    Maneja excepciones HTTP estándar de FastAPI.
    
    Args:
        request: La petición HTTP que causó el error
        exc: La excepción HTTP
        
    Returns:
        JSONResponse con detalles del error HTTP
    """
    logger.warning(
        f"Error HTTP {exc.status_code} en {request.method} {request.url.path}: {exc.detail}"
    )
    
    # Mapear códigos de estado a tipos de error
    error_types = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "unprocessable_entity",
        429: "rate_limit_exceeded",
        500: "internal_server_error",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "gateway_timeout"
    }
    
    error_type = error_types.get(exc.status_code, "http_error")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": error_type,
                "message": exc.detail,
                "status_code": exc.status_code,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def seele_exception_handler(
    request: Request, 
    exc: SeeleException
) -> JSONResponse:
    """
    Maneja excepciones personalizadas de SEELE-E.
    
    Args:
        request: La petición HTTP que causó el error
        exc: La excepción personalizada de SEELE-E
        
    Returns:
        JSONResponse con detalles del error personalizado
    """
    # Log con nivel apropiado según el tipo de excepción
    if isinstance(exc, (AuthenticationException, AuthorizationException)):
        logger.warning(
            f"Error de seguridad en {request.method} {request.url.path}: {exc.message}"
        )
    elif isinstance(exc, ExternalServiceError):
        logger.error(
            f"Error de servicio externo en {request.method} {request.url.path}: {exc.message}"
        )
    elif isinstance(exc, BusinessLogicError):
        logger.info(
            f"Error de lógica de negocio en {request.method} {request.url.path}: {exc.message}"
        )
    else:
        logger.warning(
            f"Error SEELE en {request.method} {request.url.path}: {exc.message}"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.error_type,
                "message": exc.message,
                "code": exc.error_code,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """
    Maneja excepciones no capturadas (fallback).
    
    Args:
        request: La petición HTTP que causó el error
        exc: La excepción no manejada
        
    Returns:
        JSONResponse con error genérico
    """
    # Log completo del error para debugging
    logger.error(
        f"Error no manejado en {request.method} {request.url.path}: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    
    # En desarrollo, incluir más detalles
    from ..config.settings import get_settings
    settings = get_settings()
    
    error_details = None
    if settings.DEBUG:
        error_details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc().split("\n")
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "Ha ocurrido un error interno del servidor",
                "details": error_details,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def rate_limit_exception_handler(
    request: Request, 
    exc: RateLimitError
) -> JSONResponse:
    """
    Maneja errores de límite de velocidad.
    
    Args:
        request: La petición HTTP que causó el error
        exc: La excepción de rate limiting
        
    Returns:
        JSONResponse con detalles del rate limit
    """
    logger.warning(
        f"Rate limit excedido para {request.client.host} en {request.method} {request.url.path}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "type": "rate_limit_exceeded",
                "message": exc.message,
                "retry_after": exc.retry_after,
                "limit": exc.limit,
                "window": exc.window,
                "request_id": getattr(request.state, "request_id", None)
            }
        },
        headers={
            "Retry-After": str(exc.retry_after),
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Window": str(exc.window)
        }
    )


async def handle_api_error(error: Exception, operation: str) -> dict:
    """Handle API errors and return appropriate error response.
    
    Args:
        error: The exception that occurred
        operation: The operation name where the error occurred
        
    Returns:
        Dictionary with error details
    """
    import logging
    from fastapi import HTTPException
    from ..exceptions.base import SeeleException
    
    logger = logging.getLogger(__name__)
    
    if isinstance(error, HTTPException):
        logger.warning(f"HTTP error in {operation}: {error.detail}")
        return {
            "error": True,
            "message": error.detail,
            "operation": operation,
            "status_code": error.status_code
        }
    elif isinstance(error, SeeleException):
        logger.error(f"Seele error in {operation}: {error.message}")
        return {
            "error": True,
            "message": error.message,
            "operation": operation,
            "error_code": error.error_code
        }
    else:
        logger.error(f"Unexpected error in {operation}: {str(error)}")
        return {
            "error": True,
            "message": "An unexpected error occurred",
            "operation": operation,
            "status_code": 500
        }


# Diccionario de manejadores para registro automático
EXCEPTION_HANDLERS = {
    RequestValidationError: validation_exception_handler,
    ValidationError: validation_exception_handler,
    HTTPException: http_exception_handler,
    SeeleException: seele_exception_handler,
    ValidationException: seele_exception_handler,
    AuthenticationException: seele_exception_handler,
    AuthorizationException: seele_exception_handler,
    NotFoundError: seele_exception_handler,
    BusinessLogicError: seele_exception_handler,
    ExternalServiceError: seele_exception_handler,
    RateLimitError: rate_limit_exception_handler,
    Exception: general_exception_handler
}


def register_exception_handlers(app):
    """
    Registra todos los manejadores de excepciones en la aplicación FastAPI.
    
    Args:
        app: La instancia de FastAPI
    """
    for exception_type, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)
    
    logger.info(f"Registrados {len(EXCEPTION_HANDLERS)} manejadores de excepciones")