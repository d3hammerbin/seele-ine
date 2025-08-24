#!/usr/bin/env python3
"""
Middleware de logging para SEELE-E Backend

Captura y registra información detallada sobre todas las peticiones HTTP,
incluyendo métricas de rendimiento, headers relevantes y manejo de errores.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging automático de peticiones HTTP.
    
    Funcionalidades:
    - Asigna un ID único a cada petición
    - Registra detalles de la petición (método, URL, headers, IP)
    - Mide tiempo de respuesta
    - Registra código de estado y tamaño de respuesta
    - Maneja errores y excepciones
    - Filtra información sensible
    """
    
    def __init__(self, app, exclude_paths: list = None):
        """
        Inicializa el middleware de logging.
        
        Args:
            app: La aplicación FastAPI
            exclude_paths: Lista de rutas a excluir del logging detallado
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/favicon.ico",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa la petición y registra información relevante.
        
        Args:
            request: La petición HTTP entrante
            call_next: El siguiente middleware o endpoint
            
        Returns:
            La respuesta HTTP procesada
        """
        # Generar ID único para la petición
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Información básica de la petición
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Verificar si debe excluirse del logging detallado
        should_log_details = path not in self.exclude_paths
        
        # Timestamp de inicio
        start_time = time.time()
        
        # Log de petición entrante
        if should_log_details:
            logger.info(
                f"[{request_id}] {method} {path} - IP: {client_ip} - UA: {user_agent[:100]}"
            )
            
            # Log headers relevantes (filtrados)
            relevant_headers = self._filter_headers(request.headers)
            if relevant_headers:
                logger.debug(f"[{request_id}] Headers: {relevant_headers}")
            
            # Log query parameters
            if request.query_params:
                logger.debug(f"[{request_id}] Query params: {dict(request.query_params)}")
        
        # Variables para métricas
        status_code = 500
        response_size = 0
        error_message = None
        
        try:
            # Procesar la petición
            response = await call_next(request)
            status_code = response.status_code
            
            # Calcular tamaño de respuesta
            if hasattr(response, 'body'):
                response_size = len(response.body) if response.body else 0
            elif isinstance(response, StreamingResponse):
                response_size = -1  # Streaming response, tamaño desconocido
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"[{request_id}] Error procesando petición: {error_message}")
            raise
        
        finally:
            # Calcular tiempo de respuesta
            process_time = time.time() - start_time
            
            # Log de respuesta
            if should_log_details or status_code >= 400:
                log_level = self._get_log_level(status_code)
                
                size_info = f"{response_size}B" if response_size >= 0 else "streaming"
                
                log_message = (
                    f"[{request_id}] {method} {path} - "
                    f"Status: {status_code} - "
                    f"Time: {process_time:.3f}s - "
                    f"Size: {size_info} - "
                    f"IP: {client_ip}"
                )
                
                if error_message:
                    log_message += f" - Error: {error_message}"
                
                if log_level == "error":
                    logger.error(log_message)
                elif log_level == "warning":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)
            
            # Métricas adicionales para monitoreo
            self._record_metrics(
                method=method,
                path=path,
                status_code=status_code,
                process_time=process_time,
                response_size=response_size
            )
        
        # Agregar headers de respuesta útiles
        if hasattr(response, 'headers'):
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtiene la IP real del cliente considerando proxies.
        
        Args:
            request: La petición HTTP
            
        Returns:
            La dirección IP del cliente
        """
        # Verificar headers de proxy comunes
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Tomar la primera IP (cliente original)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback a la IP de conexión directa
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _filter_headers(self, headers) -> dict:
        """
        Filtra headers relevantes excluyendo información sensible.
        
        Args:
            headers: Headers de la petición
            
        Returns:
            Diccionario con headers filtrados
        """
        # Headers relevantes para logging
        relevant_headers = [
            "content-type",
            "content-length",
            "accept",
            "accept-language",
            "accept-encoding",
            "x-api-key",  # Solo para identificar el tipo, no el valor
            "x-application-id",
            "x-request-source"
        ]
        
        # Headers sensibles que NO deben loggearse
        sensitive_headers = [
            "authorization",
            "cookie",
            "x-api-key",  # Loggear existencia pero no valor
            "x-auth-token"
        ]
        
        filtered = {}
        
        for key, value in headers.items():
            key_lower = key.lower()
            
            if key_lower in sensitive_headers:
                if key_lower == "x-api-key":
                    filtered[key] = "[API_KEY_PROVIDED]" if value else "[NO_API_KEY]"
                else:
                    filtered[key] = "[REDACTED]"
            elif key_lower in relevant_headers:
                filtered[key] = value
        
        return filtered
    
    def _get_log_level(self, status_code: int) -> str:
        """
        Determina el nivel de log basado en el código de estado.
        
        Args:
            status_code: Código de estado HTTP
            
        Returns:
            Nivel de log apropiado
        """
        if status_code >= 500:
            return "error"
        elif status_code >= 400:
            return "warning"
        else:
            return "info"
    
    def _record_metrics(self, method: str, path: str, status_code: int, 
                       process_time: float, response_size: int):
        """
        Registra métricas para monitoreo (Prometheus, etc.).
        
        Args:
            method: Método HTTP
            path: Ruta de la petición
            status_code: Código de estado de respuesta
            process_time: Tiempo de procesamiento en segundos
            response_size: Tamaño de la respuesta en bytes
        """
        try:
            # TODO: Implementar métricas de Prometheus
            # from prometheus_client import Counter, Histogram, Gauge
            
            # Ejemplo de métricas que se podrían registrar:
            # - Contador de peticiones por método/path/status
            # - Histograma de tiempos de respuesta
            # - Gauge de peticiones activas
            # - Contador de bytes transferidos
            
            pass
            
        except Exception as e:
            logger.warning(f"Error registrando métricas: {e}")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware para mantener contexto de petición disponible globalmente.
    
    Útil para acceder a información de la petición desde cualquier parte
    del código sin pasar explícitamente el objeto request.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Establece el contexto de petición y lo limpia al finalizar.
        
        Args:
            request: La petición HTTP entrante
            call_next: El siguiente middleware o endpoint
            
        Returns:
            La respuesta HTTP procesada
        """
        # Establecer contexto global (usando contextvars si es necesario)
        # TODO: Implementar contexto global con contextvars
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Limpiar contexto
            pass