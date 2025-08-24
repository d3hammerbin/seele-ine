#!/usr/bin/env python3
"""
Base AI Provider Interface

Defines the base interface and data structures for AI providers.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import numpy as np
from PIL import Image

from ....domain.entities.processing_job import AIProvider


@dataclass
class AIUsageStats:
    """
    Estadísticas de uso de un proveedor de IA.
    """
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    images_processed: int = 0
    requests_made: int = 0
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    processing_time_seconds: float = 0.0
    
    def add_usage(self, other: 'AIUsageStats') -> None:
        """
        Suma las estadísticas de otro objeto AIUsageStats.
        
        Args:
            other: Otras estadísticas a sumar
        """
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens
        self.images_processed += other.images_processed
        self.requests_made += other.requests_made
        self.total_cost_usd += other.total_cost_usd
        self.processing_time_seconds += other.processing_time_seconds


@dataclass
class AIResponse:
    """
    Respuesta de un proveedor de IA.
    """
    # Datos de respuesta
    content: str
    provider: AIProvider
    model_used: str
    
    # Métricas de uso
    usage_stats: AIUsageStats
    
    # Metadatos
    success: bool = True
    error_message: Optional[str] = None
    response_time_seconds: float = 0.0
    request_id: Optional[str] = None
    
    # Datos adicionales específicos del proveedor
    raw_response: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    
    @property
    def cost_usd(self) -> Decimal:
        """
        Costo total de la respuesta en USD.
        
        Returns:
            Costo en USD
        """
        return self.usage_stats.total_cost_usd
    
    @property
    def total_tokens(self) -> int:
        """
        Total de tokens utilizados.
        
        Returns:
            Número total de tokens
        """
        return self.usage_stats.total_tokens


@dataclass
class AIRequest:
    """
    Solicitud a un proveedor de IA.
    """
    # Contenido de la solicitud
    prompt: str
    images: List[Union[np.ndarray, Image.Image, str]] = field(default_factory=list)
    
    # Parámetros del modelo
    temperature: float = 0.1
    max_tokens: int = 2000
    model: Optional[str] = None
    
    # Configuración de la solicitud
    timeout_seconds: int = 60
    max_retries: int = 3
    
    # Metadatos
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    application_id: Optional[str] = None
    
    # Configuración específica del proveedor
    provider_specific_params: Dict[str, Any] = field(default_factory=dict)


class BaseAIProvider(ABC):
    """
    Interfaz base para proveedores de IA.
    """
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.provider_name = self.get_provider_name()
        self.is_initialized = False
        self.usage_stats = AIUsageStats()
        self.config = kwargs
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Inicializa el proveedor de IA.
        
        Raises:
            Exception: Si la inicialización falla
        """
        pass
    
    @abstractmethod
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Procesa una solicitud de IA.
        
        Args:
            request: Solicitud a procesar
            
        Returns:
            Respuesta del proveedor de IA
            
        Raises:
            Exception: Si el procesamiento falla
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> AIProvider:
        """
        Obtiene el nombre del proveedor.
        
        Returns:
            Nombre del proveedor
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Obtiene la lista de modelos soportados.
        
        Returns:
            Lista de nombres de modelos
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, usage_stats: AIUsageStats) -> Decimal:
        """
        Calcula el costo de una solicitud.
        
        Args:
            usage_stats: Estadísticas de uso
            
        Returns:
            Costo en USD
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible.
        
        Returns:
            True si está disponible
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Verifica la salud del proveedor.
        
        Returns:
            True si el proveedor está saludable
        """
        try:
            # Solicitud simple de prueba
            test_request = AIRequest(
                prompt="Test",
                max_tokens=1,
                timeout_seconds=10
            )
            response = await self.process_request(test_request)
            return response.success
        except Exception:
            return False
    
    def get_usage_stats(self) -> AIUsageStats:
        """
        Obtiene las estadísticas de uso acumuladas.
        
        Returns:
            Estadísticas de uso
        """
        return self.usage_stats
    
    def reset_usage_stats(self) -> None:
        """
        Reinicia las estadísticas de uso.
        """
        self.usage_stats = AIUsageStats()
    
    def _update_usage_stats(self, response: AIResponse) -> None:
        """
        Actualiza las estadísticas de uso con una respuesta.
        
        Args:
            response: Respuesta del proveedor
        """
        self.usage_stats.add_usage(response.usage_stats)
    
    def _prepare_images(self, images: List[Union[np.ndarray, Image.Image, str]]) -> List[str]:
        """
        Prepara las imágenes para el proveedor (convierte a base64, etc.).
        
        Args:
            images: Lista de imágenes en varios formatos
            
        Returns:
            Lista de imágenes preparadas (generalmente base64)
        """
        import base64
        import io
        import cv2
        
        prepared_images = []
        
        for image in images:
            if isinstance(image, str):
                # Asumir que ya está en base64 o es una URL
                prepared_images.append(image)
            elif isinstance(image, np.ndarray):
                # Convertir numpy array a base64
                _, buffer = cv2.imencode('.png', image)
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                prepared_images.append(f"data:image/png;base64,{image_base64}")
            elif isinstance(image, Image.Image):
                # Convertir PIL Image a base64
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                prepared_images.append(f"data:image/png;base64,{image_base64}")
            else:
                raise ValueError(f"Formato de imagen no soportado: {type(image)}")
        
        return prepared_images
    
    def _create_error_response(
        self,
        request: AIRequest,
        error_message: str,
        processing_time: float = 0.0
    ) -> AIResponse:
        """
        Crea una respuesta de error.
        
        Args:
            request: Solicitud original
            error_message: Mensaje de error
            processing_time: Tiempo de procesamiento
            
        Returns:
            Respuesta de error
        """
        return AIResponse(
            content="",
            provider=self.get_provider_name(),
            model_used=request.model or "unknown",
            usage_stats=AIUsageStats(),
            success=False,
            error_message=error_message,
            response_time_seconds=processing_time,
            request_id=request.request_id
        )


class AIProviderError(Exception):
    """
    Excepción base para errores de proveedores de IA.
    """
    
    def __init__(self, message: str, provider: AIProvider, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.timestamp = time.time()


class AIProviderUnavailableError(AIProviderError):
    """
    Error cuando un proveedor no está disponible.
    """
    pass


class AIProviderRateLimitError(AIProviderError):
    """
    Error de límite de velocidad del proveedor.
    """
    
    def __init__(self, message: str, provider: AIProvider, retry_after: Optional[int] = None):
        super().__init__(message, provider, "rate_limit")
        self.retry_after = retry_after


class AIProviderAuthenticationError(AIProviderError):
    """
    Error de autenticación del proveedor.
    """
    
    def __init__(self, message: str, provider: AIProvider):
        super().__init__(message, provider, "authentication")


class AIProviderTimeoutError(AIProviderError):
    """
    Error de timeout del proveedor.
    """
    
    def __init__(self, message: str, provider: AIProvider, timeout_seconds: int):
        super().__init__(message, provider, "timeout")
        self.timeout_seconds = timeout_seconds