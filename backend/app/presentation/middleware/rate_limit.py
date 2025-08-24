#!/usr/bin/env python3
"""
Middleware de Rate Limiting para SEELE-E Backend

Implementa control de velocidad de peticiones usando Redis como backend
con soporte para diferentes estrategias y límites por usuario/aplicación.
"""

import time
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from ...core.exceptions.base import RateLimitError
from ...core.config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware para control de velocidad de peticiones.
    
    Implementa diferentes estrategias de rate limiting:
    - Por IP (global)
    - Por API key (por aplicación)
    - Por usuario autenticado
    - Por endpoint específico
    
    Usa Redis para almacenar contadores distribuidos.
    """
    
    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        default_requests: int = 100,
        default_window: int = 60,
        exclude_paths: list = None
    ):
        """
        Inicializa el middleware de rate limiting.
        
        Args:
            app: La aplicación FastAPI
            redis_client: Cliente Redis (opcional, se crea automáticamente)
            default_requests: Número de peticiones por defecto
            default_window: Ventana de tiempo en segundos
            exclude_paths: Rutas excluidas del rate limiting
        """
        super().__init__(app)
        self.settings = get_settings()
        self.redis_client = redis_client
        self.default_requests = default_requests
        self.default_window = default_window
        
        # Rutas excluidas del rate limiting
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # Configuración de límites por endpoint
        self.endpoint_limits = {
            "/api/v1/auth/login": {"requests": 50, "window": 60},  # 50 por min (aumentado para pruebas)
            "/api/v1/auth/register": {"requests": 10, "window": 3600},  # 10 por hora
            "/api/v1/credentials/process": {"requests": 50, "window": 60},  # 50 por min
            "/api/v1/credentials/extract": {"requests": 30, "window": 60},  # 30 por min
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Verifica límites de velocidad antes de procesar la petición.
        
        Args:
            request: La petición HTTP entrante
            call_next: El siguiente middleware o endpoint
            
        Returns:
            La respuesta HTTP o error de rate limit
        """
        path = request.url.path
        
        # Excluir rutas específicas
        if path in self.exclude_paths:
            return await call_next(request)
        
        # Inicializar cliente Redis si no existe
        if not self.redis_client:
            await self._init_redis()
        
        try:
            # Verificar diferentes tipos de límites
            await self._check_ip_limit(request)
            await self._check_api_key_limit(request)
            await self._check_user_limit(request)
            await self._check_endpoint_limit(request)
            
            # Procesar petición
            response = await call_next(request)
            
            # Actualizar contadores después de petición exitosa
            await self._update_counters(request, response.status_code)
            
            return response
            
        except RateLimitError as e:
            logger.warning(
                f"Rate limit excedido - IP: {self._get_client_ip(request)} - "
                f"Path: {path} - Límite: {e.limit}/{e.window}s"
            )
            raise
        except Exception as e:
            logger.error(f"Error en rate limiting: {e}")
            # En caso de error, permitir la petición (fail-open)
            return await call_next(request)
    
    async def _init_redis(self):
        """
        Inicializa la conexión a Redis.
        """
        try:
            self.redis_client = redis.from_url(
                self.settings.redis.redis_url,
                decode_responses=True
            )
            # Verificar conexión
            await self.redis_client.ping()
            logger.info("Conexión a Redis establecida para rate limiting")
        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            self.redis_client = None
    
    async def _check_ip_limit(self, request: Request):
        """
        Verifica límite por dirección IP.
        
        Args:
            request: La petición HTTP
        """
        if not self.redis_client:
            return
        
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:ip:{client_ip}"
        
        await self._check_limit(
            key=key,
            requests=self.settings.security.RATE_LIMIT_REQUESTS,
            window=self.settings.security.RATE_LIMIT_WINDOW,
            identifier=f"IP {client_ip}"
        )
    
    async def _check_api_key_limit(self, request: Request):
        """
        Verifica límite por API key.
        
        Args:
            request: La petición HTTP
        """
        if not self.redis_client:
            return
        
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return
        
        # TODO: Obtener límites específicos de la aplicación desde la BD
        # Por ahora usar límites por defecto
        key = f"rate_limit:api_key:{api_key[:10]}..."  # Truncar para logs
        
        await self._check_limit(
            key=f"rate_limit:api_key:{api_key}",
            requests=200,  # Límite más alto para API keys
            window=60,
            identifier=f"API Key {api_key[:10]}..."
        )
    
    async def _check_user_limit(self, request: Request):
        """
        Verifica límite por usuario autenticado.
        
        Args:
            request: La petición HTTP
        """
        if not self.redis_client:
            return
        
        # TODO: Extraer user_id del token JWT
        # user_id = await self._get_user_id_from_token(request)
        # if user_id:
        #     key = f"rate_limit:user:{user_id}"
        #     await self._check_limit(key, 500, 60, f"User {user_id}")
        pass
    
    async def _check_endpoint_limit(self, request: Request):
        """
        Verifica límite específico por endpoint.
        
        Args:
            request: La petición HTTP
        """
        if not self.redis_client:
            return
        
        path = request.url.path
        endpoint_config = self.endpoint_limits.get(path)
        
        if endpoint_config:
            client_ip = self._get_client_ip(request)
            key = f"rate_limit:endpoint:{path}:{client_ip}"
            
            await self._check_limit(
                key=key,
                requests=endpoint_config["requests"],
                window=endpoint_config["window"],
                identifier=f"Endpoint {path} for IP {client_ip}"
            )
    
    async def _check_limit(
        self, 
        key: str, 
        requests: int, 
        window: int, 
        identifier: str
    ):
        """
        Verifica un límite específico usando sliding window.
        
        Args:
            key: Clave Redis para el contador
            requests: Número máximo de peticiones
            window: Ventana de tiempo en segundos
            identifier: Identificador para logs
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Usar pipeline para operaciones atómicas
            pipe = self.redis_client.pipeline()
            
            # Limpiar entradas antiguas
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Contar peticiones en la ventana actual
            pipe.zcard(key)
            
            # Ejecutar pipeline
            results = await pipe.execute()
            current_requests = results[1]
            
            # Verificar límite
            if current_requests >= requests:
                # Calcular tiempo hasta que se libere una petición
                oldest_request = await self.redis_client.zrange(
                    key, 0, 0, withscores=True
                )
                
                if oldest_request:
                    retry_after = int(oldest_request[0][1]) + window - current_time
                    retry_after = max(1, retry_after)  # Mínimo 1 segundo
                else:
                    retry_after = window
                
                raise RateLimitError(
                    message=f"Límite de velocidad excedido para {identifier}",
                    limit=requests,
                    window=window,
                    retry_after=retry_after
                )
            
            # Registrar la petición actual
            await self.redis_client.zadd(key, {str(current_time): current_time})
            
            # Establecer TTL para limpieza automática
            await self.redis_client.expire(key, window + 60)
            
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Error verificando límite {identifier}: {e}")
            # En caso de error, permitir la petición
    
    async def _update_counters(self, request: Request, status_code: int):
        """
        Actualiza contadores adicionales después de procesar la petición.
        
        Args:
            request: La petición HTTP
            status_code: Código de estado de la respuesta
        """
        if not self.redis_client:
            return
        
        try:
            # Contadores de métricas
            current_time = int(time.time())
            client_ip = self._get_client_ip(request)
            
            # Contador de peticiones por status code
            status_key = f"metrics:status:{status_code}:{client_ip}"
            await self.redis_client.incr(status_key)
            await self.redis_client.expire(status_key, 3600)  # 1 hora
            
            # Contador de peticiones por endpoint
            endpoint_key = f"metrics:endpoint:{request.url.path}:{client_ip}"
            await self.redis_client.incr(endpoint_key)
            await self.redis_client.expire(endpoint_key, 3600)
            
        except Exception as e:
            logger.error(f"Error actualizando contadores: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtiene la IP real del cliente considerando proxies.
        
        Args:
            request: La petición HTTP
            
        Returns:
            La dirección IP del cliente
        """
        # Verificar headers de proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def get_rate_limit_status(self, request: Request) -> Dict[str, Any]:
        """
        Obtiene el estado actual de rate limiting para una petición.
        
        Args:
            request: La petición HTTP
            
        Returns:
            Diccionario con información de rate limiting
        """
        if not self.redis_client:
            return {"status": "unavailable", "reason": "Redis not connected"}
        
        try:
            client_ip = self._get_client_ip(request)
            current_time = int(time.time())
            window = self.settings.security.RATE_LIMIT_WINDOW
            window_start = current_time - window
            
            # Obtener contadores actuales
            ip_key = f"rate_limit:ip:{client_ip}"
            
            # Limpiar entradas antiguas
            await self.redis_client.zremrangebyscore(ip_key, 0, window_start)
            
            # Contar peticiones actuales
            current_requests = await self.redis_client.zcard(ip_key)
            
            return {
                "status": "active",
                "current_requests": current_requests,
                "limit": self.settings.security.RATE_LIMIT_REQUESTS,
                "window": window,
                "remaining": max(0, self.settings.security.RATE_LIMIT_REQUESTS - current_requests),
                "reset_time": current_time + window
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de rate limit: {e}")
            return {"status": "error", "reason": str(e)}