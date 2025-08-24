#!/usr/bin/env python3
"""
Middleware de Seguridad para SEELE-E Backend

Implementa headers de seguridad, validaciones de entrada,
protección contra ataques comunes y auditoría de seguridad.
"""

import re
import json
import hashlib
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ...core.exceptions.base import ValidationException, AuthenticationException
from ...core.config.settings import get_settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware de seguridad que implementa:
    - Headers de seguridad HTTP
    - Validación de entrada
    - Protección contra ataques comunes
    - Auditoría de seguridad
    - Filtrado de contenido malicioso
    """
    
    def __init__(
        self,
        app,
        enable_security_headers: bool = True,
        enable_input_validation: bool = True,
        enable_audit_logging: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_file_types: List[str] = None
    ):
        """
        Inicializa el middleware de seguridad.
        
        Args:
            app: La aplicación FastAPI
            enable_security_headers: Habilitar headers de seguridad
            enable_input_validation: Habilitar validación de entrada
            enable_audit_logging: Habilitar logging de auditoría
            max_request_size: Tamaño máximo de petición en bytes
            allowed_file_types: Tipos de archivo permitidos
        """
        super().__init__(app)
        self.settings = get_settings()
        self.enable_security_headers = enable_security_headers
        self.enable_input_validation = enable_input_validation
        self.enable_audit_logging = enable_audit_logging
        self.max_request_size = max_request_size
        
        # Tipos de archivo permitidos para uploads
        self.allowed_file_types = allowed_file_types or [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain'
        ]
        
        # Patrones de ataques comunes
        self.attack_patterns = {
            'sql_injection': [
                r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
                r"(union|select|insert|delete|update|drop|create|alter)",
                r"(script|javascript|vbscript|onload|onerror)"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>.*?</iframe>"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c"
            ],
            'command_injection': [
                r"[;&|`$(){}\[\]]",
                r"(cat|ls|pwd|whoami|id|uname)",
                r"(rm|mv|cp|chmod|chown)"
            ]
        }
        
        # Compilar patrones regex
        self.compiled_patterns = {}
        for attack_type, patterns in self.attack_patterns.items():
            self.compiled_patterns[attack_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Headers de seguridad
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa la petición aplicando validaciones de seguridad.
        
        Args:
            request: La petición HTTP entrante
            call_next: El siguiente middleware o endpoint
            
        Returns:
            La respuesta HTTP con headers de seguridad
        """
        start_time = datetime.utcnow()
        
        # Skip security validations for WebSocket connections
        if self._is_websocket_request(request):
            return await call_next(request)
        
        try:
            # Validar tamaño de petición
            await self._validate_request_size(request)
            
            # Validar headers de seguridad
            await self._validate_security_headers(request)
            
            # Validar entrada contra ataques
            if self.enable_input_validation:
                await self._validate_input_security(request)
            
            # Procesar petición
            response = await call_next(request)
            
            # Agregar headers de seguridad
            if self.enable_security_headers:
                self._add_security_headers(response)
            
            # Log de auditoría
            if self.enable_audit_logging:
                await self._audit_log(request, response, start_time)
            
            return response
            
        except (ValidationException, AuthenticationException) as e:
            logger.warning(
                f"Violación de seguridad detectada - IP: {self._get_client_ip(request)} - "
                f"Path: {request.url.path} - Error: {e.message}"
            )
            
            # Log de auditoría para intentos maliciosos
            if self.enable_audit_logging:
                await self._audit_log_security_violation(request, e, start_time)
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.error_type,
                    "message": e.message,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error en middleware de seguridad: {e}")
            # En caso de error, continuar con la petición
            response = await call_next(request)
            if self.enable_security_headers:
                self._add_security_headers(response)
            return response
    
    async def _validate_request_size(self, request: Request):
        """
        Valida el tamaño de la petición.
        
        Args:
            request: La petición HTTP
        """
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size > self.max_request_size:
                raise ValidationException(
                    message=f"Petición demasiado grande: {size} bytes (máximo: {self.max_request_size})",
                    details={"size": size, "max_size": self.max_request_size}
                )
    
    async def _validate_security_headers(self, request: Request):
        """
        Valida headers de seguridad en la petición.
        
        Args:
            request: La petición HTTP
        """
        # Validar User-Agent
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) < 10:
            logger.warning(f"User-Agent sospechoso: '{user_agent}' desde IP {self._get_client_ip(request)}")
        
        # Validar Content-Type para peticiones con cuerpo
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type:
                raise ValidationException(
                    message="Content-Type requerido para peticiones con cuerpo",
                    details={"method": request.method}
                )
        
        # Detectar headers maliciosos
        suspicious_headers = [
            "x-forwarded-host", "x-original-url", "x-rewrite-url"
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                logger.warning(
                    f"Header sospechoso detectado: {header} = {request.headers[header]} "
                    f"desde IP {self._get_client_ip(request)}"
                )
    
    async def _validate_input_security(self, request: Request):
        """
        Valida la entrada contra patrones de ataques conocidos.
        
        Args:
            request: La petición HTTP
        """
        # Skip validation for health check endpoints
        if request.url.path in ["/health", "/api/v1/health", "/api/v1/credentials/health"]:
            return
            
        # Validar parámetros de query
        query_params = str(request.query_params)
        self._check_attack_patterns(query_params, "query_params")
        
        # Validar path
        path = str(request.url.path)
        self._check_attack_patterns(path, "path")
        
        # Validar headers (skip common browser and security headers)
        excluded_headers = [
            'authorization', 'cookie', 'accept', 'user-agent', 'host', 'content-type', 'content-length',
            'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform', 'sec-fetch-dest', 'sec-fetch-mode', 
            'sec-fetch-site', 'referer', 'accept-encoding', 'accept-language', 'origin', 'connection',
            'cache-control', 'pragma', 'upgrade-insecure-requests', 'x-request-id'
        ]
        for header_name, header_value in request.headers.items():
            if header_name.lower() not in excluded_headers:
                self._check_attack_patterns(str(header_value), f"header_{header_name}")
        
        # Validar cuerpo de la petición (si existe)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Solo validar si es JSON o form data
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Para JSON, necesitamos leer el cuerpo de manera especial
                    # ya que FastAPI lo procesará después
                    pass  # TODO: Implementar validación de JSON sin consumir el stream
                elif "application/x-www-form-urlencoded" in content_type:
                    pass  # TODO: Implementar validación de form data
            except Exception as e:
                logger.error(f"Error validando cuerpo de petición: {e}")
    
    def _check_attack_patterns(self, input_string: str, input_type: str):
        """
        Verifica patrones de ataques en una cadena de entrada.
        
        Args:
            input_string: La cadena a verificar
            input_type: Tipo de entrada (para logging)
        """
        if not input_string:
            return
        
        for attack_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(input_string):
                    raise ValidationException(
                        message=f"Patrón de ataque {attack_type} detectado en {input_type}",
                        details={
                            "attack_type": attack_type,
                            "input_type": input_type,
                            "pattern_matched": True
                        }
                    )
    
    def _add_security_headers(self, response: Response):
        """
        Agrega headers de seguridad a la respuesta.
        
        Args:
            response: La respuesta HTTP
        """
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value
        
        # Header personalizado para identificar la aplicación
        response.headers["X-Powered-By"] = "SEELE-E Security Framework"
        
        # Remover headers que revelan información del servidor
        headers_to_remove = ["server", "x-powered-by"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]
    
    async def _audit_log(self, request: Request, response: Response, start_time: datetime):
        """
        Registra información de auditoría para la petición.
        
        Args:
            request: La petición HTTP
            response: La respuesta HTTP
            start_time: Tiempo de inicio de la petición
        """
        try:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            audit_data = {
                "timestamp": start_time.isoformat(),
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "status_code": response.status_code,
                "duration_seconds": duration,
                "request_size": request.headers.get("content-length", 0),
                "response_size": len(response.body) if hasattr(response, 'body') else 0
            }
            
            # Log diferente según el status code
            if response.status_code >= 400:
                logger.warning(f"Petición con error: {json.dumps(audit_data)}")
            else:
                logger.info(f"Petición exitosa: {json.dumps(audit_data)}")
                
        except Exception as e:
            logger.error(f"Error en audit log: {e}")
    
    async def _audit_log_security_violation(
        self, 
        request: Request, 
        exception: Exception, 
        start_time: datetime
    ):
        """
        Registra violaciones de seguridad para análisis.
        
        Args:
            request: La petición HTTP
            exception: La excepción de seguridad
            start_time: Tiempo de inicio de la petición
        """
        try:
            violation_data = {
                "timestamp": start_time.isoformat(),
                "violation_type": "security_violation",
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "severity": "HIGH",
                "request_hash": self._generate_request_hash(request)
            }
            
            logger.error(f"VIOLACIÓN DE SEGURIDAD: {json.dumps(violation_data)}")
            
            # TODO: Enviar alerta a sistema de monitoreo
            # TODO: Considerar bloqueo automático de IP después de X violaciones
            
        except Exception as e:
            logger.error(f"Error en audit log de violación de seguridad: {e}")
    
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
    
    def _generate_request_hash(self, request: Request) -> str:
        """
        Genera un hash único para la petición (para detectar patrones).
        
        Args:
            request: La petición HTTP
            
        Returns:
            Hash MD5 de la petición
        """
        try:
            request_data = f"{request.method}:{request.url.path}:{request.query_params}"
            return hashlib.md5(request_data.encode()).hexdigest()
        except Exception:
            return "unknown"
    
    def _is_websocket_request(self, request: Request) -> bool:
        """
        Verifica si la petición es una conexión WebSocket.
        
        Args:
            request: La petición HTTP
            
        Returns:
            True si es una petición WebSocket, False en caso contrario
        """
        connection_header = request.headers.get("connection", "").lower()
        upgrade_header = request.headers.get("upgrade", "").lower()
        
        return (
            "upgrade" in connection_header and 
            upgrade_header == "websocket"
        )
    
    async def get_security_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del middleware de seguridad.
        
        Returns:
            Diccionario con información de estado
        """
        return {
            "status": "active",
            "security_headers_enabled": self.enable_security_headers,
            "input_validation_enabled": self.enable_input_validation,
            "audit_logging_enabled": self.enable_audit_logging,
            "max_request_size": self.max_request_size,
            "allowed_file_types": self.allowed_file_types,
            "attack_patterns_loaded": len(self.compiled_patterns),
            "security_headers_count": len(self.security_headers)
        }