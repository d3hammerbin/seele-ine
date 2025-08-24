#!/usr/bin/env python3
"""
Gemini Provider Implementation

Implements the Google Gemini API provider for text and vision processing.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from decimal import Decimal
import aiohttp
import json
import base64

from .base import (
    BaseAIProvider, AIRequest, AIResponse, AIUsageStats,
    AIProviderError, AIProviderUnavailableError, AIProviderRateLimitError,
    AIProviderAuthenticationError, AIProviderTimeoutError
)
from ....domain.entities.processing_job import AIProvider
from ....core.config.settings import get_settings


class GeminiProvider(BaseAIProvider):
    """
    Proveedor de IA para Google Gemini models.
    """
    
    # Modelos soportados
    SUPPORTED_MODELS = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-1.0-pro-vision"
    ]
    
    # Costos por modelo (USD por 1K tokens)
    MODEL_COSTS = {
        "gemini-1.5-pro": {
            "input": Decimal('0.00125'),
            "output": Decimal('0.00375')
        },
        "gemini-1.5-flash": {
            "input": Decimal('0.000075'),
            "output": Decimal('0.0003')
        },
        "gemini-1.0-pro": {
            "input": Decimal('0.0005'),
            "output": Decimal('0.0015')
        },
        "gemini-1.0-pro-vision": {
            "input": Decimal('0.00025'),
            "output": Decimal('0.0005')
        }
    }
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.settings = get_settings()
        self.base_url = kwargs.get('base_url', 'https://generativelanguage.googleapis.com/v1beta')
        self.default_model = kwargs.get('default_model', 'gemini-1.5-flash')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """
        Inicializa el cliente de Gemini.
        """
        try:
            # Crear sesión HTTP
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            # Verificar que la API key funciona
            await self._test_connection()
            
            self.is_initialized = True
            
        except Exception as e:
            if self.session:
                await self.session.close()
            raise AIProviderError(
                f"Error inicializando Gemini: {e}",
                AIProvider.GEMINI,
                "initialization_failed"
            )
    
    async def _test_connection(self) -> None:
        """
        Prueba la conexión con Gemini.
        """
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": "test"}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 1
                }
            }
            
            url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 400:
                    data = await response.json()
                    if "API_KEY_INVALID" in str(data):
                        raise AIProviderAuthenticationError(
                            "API key de Gemini inválida",
                            AIProvider.GEMINI
                        )
                elif response.status != 200:
                    text = await response.text()
                    raise Exception(f"HTTP {response.status}: {text}")
                
        except AIProviderAuthenticationError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Error de conexión Gemini: {e}",
                AIProvider.GEMINI,
                "connection_test_failed"
            )
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Procesa una solicitud usando Gemini.
        
        Args:
            request: Solicitud a procesar
            
        Returns:
            Respuesta de Gemini
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Seleccionar modelo
            model = request.model or self.default_model
            if model not in self.SUPPORTED_MODELS:
                model = self.default_model
            
            # Preparar payload
            payload = await self._prepare_payload(request, model)
            
            # Realizar solicitud con reintentos
            response_data = await self._make_request_with_retries(
                payload, model, request.max_retries
            )
            
            # Procesar respuesta
            processing_time = time.time() - start_time
            ai_response = self._process_response(
                response_data, model, processing_time, request
            )
            
            # Actualizar estadísticas
            self._update_usage_stats(ai_response)
            
            return ai_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(request, str(e), processing_time)
    
    async def _prepare_payload(self, request: AIRequest, model: str) -> Dict[str, Any]:
        """
        Prepara el payload para Gemini.
        
        Args:
            request: Solicitud original
            model: Modelo a usar
            
        Returns:
            Payload formateado
        """
        parts = []
        
        # Agregar texto
        parts.append({"text": request.prompt})
        
        # Agregar imágenes si las hay
        if request.images and self._supports_vision(model):
            prepared_images = self._prepare_images(request.images)
            
            for image_data in prepared_images:
                # Gemini espera imágenes en formato base64
                if image_data.startswith('data:'):
                    # Extraer el base64 del data URL
                    mime_type, base64_data = image_data.split(',', 1)
                    mime_type = mime_type.split(':')[1].split(';')[0]
                else:
                    # Asumir que es base64 puro
                    base64_data = image_data
                    mime_type = "image/jpeg"  # Default
                
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                })
        
        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "topP": 0.8,
                "topK": 10
            }
        }
        
        # Agregar parámetros específicos del proveedor
        if request.provider_specific_params:
            if "generationConfig" in request.provider_specific_params:
                payload["generationConfig"].update(
                    request.provider_specific_params["generationConfig"]
                )
            
            # Otros parámetros específicos
            for key, value in request.provider_specific_params.items():
                if key != "generationConfig":
                    payload[key] = value
        
        return payload
    
    def _supports_vision(self, model: str) -> bool:
        """
        Verifica si el modelo soporta visión.
        
        Args:
            model: Nombre del modelo
            
        Returns:
            True si soporta visión
        """
        return model in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro-vision"]
    
    async def _make_request_with_retries(
        self,
        payload: Dict[str, Any],
        model: str,
        max_retries: int
    ) -> Dict[str, Any]:
        """
        Realiza la solicitud con reintentos automáticos.
        
        Args:
            payload: Payload de la solicitud
            model: Modelo a usar
            max_retries: Número máximo de reintentos
            
        Returns:
            Respuesta de Gemini
        """
        last_exception = None
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(url, json=payload) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 400:
                        data = await response.json()
                        if "API_KEY_INVALID" in str(data):
                            raise AIProviderAuthenticationError(
                                "API key de Gemini inválida",
                                AIProvider.GEMINI
                            )
                        else:
                            raise Exception(f"Bad request: {data}")
                    
                    elif response.status == 429:
                        # Rate limit
                        if attempt < max_retries:
                            wait_time = min(2 ** attempt, 60)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise AIProviderRateLimitError(
                                "Límite de velocidad Gemini excedido",
                                AIProvider.GEMINI
                            )
                    
                    elif response.status >= 500:
                        # Error del servidor, reintentar
                        last_exception = Exception(f"Server error: {response.status}")
                        if attempt < max_retries:
                            await asyncio.sleep(2 ** attempt)
                            continue
                    
                    else:
                        # Otros errores
                        text = await response.text()
                        raise Exception(f"HTTP {response.status}: {text}")
                        
            except (AIProviderAuthenticationError, AIProviderRateLimitError):
                raise
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    break
        
        # Si llegamos aquí, todos los intentos fallaron
        raise AIProviderError(
            f"Gemini request failed after {max_retries + 1} attempts: {last_exception}",
            AIProvider.GEMINI,
            "request_failed"
        )
    
    def _process_response(
        self,
        response_data: Dict[str, Any],
        model: str,
        processing_time: float,
        request: AIRequest
    ) -> AIResponse:
        """
        Procesa la respuesta de Gemini.
        
        Args:
            response_data: Respuesta cruda de Gemini
            model: Modelo utilizado
            processing_time: Tiempo de procesamiento
            request: Solicitud original
            
        Returns:
            Respuesta procesada
        """
        try:
            # Extraer contenido
            candidates = response_data.get("candidates", [])
            if not candidates:
                raise Exception("No candidates in response")
            
            content_parts = candidates[0].get("content", {}).get("parts", [])
            content = ""
            for part in content_parts:
                if "text" in part:
                    content += part["text"]
            
            # Extraer estadísticas de uso
            usage_metadata = response_data.get("usageMetadata", {})
            usage_stats = AIUsageStats(
                input_tokens=usage_metadata.get("promptTokenCount", 0),
                output_tokens=usage_metadata.get("candidatesTokenCount", 0),
                total_tokens=usage_metadata.get("totalTokenCount", 0),
                images_processed=len(request.images),
                requests_made=1,
                processing_time_seconds=processing_time
            )
            
            # Calcular costo
            usage_stats.total_cost_usd = self.calculate_cost(usage_stats, model)
            
            return AIResponse(
                content=content,
                provider=AIProvider.GEMINI,
                model_used=model,
                usage_stats=usage_stats,
                success=True,
                response_time_seconds=processing_time,
                request_id=request.request_id,
                raw_response=response_data
            )
            
        except Exception as e:
            return self._create_error_response(
                request,
                f"Error procesando respuesta Gemini: {e}",
                processing_time
            )
    
    def calculate_cost(self, usage_stats: AIUsageStats, model: Optional[str] = None) -> Decimal:
        """
        Calcula el costo de una solicitud.
        
        Args:
            usage_stats: Estadísticas de uso
            model: Modelo utilizado
            
        Returns:
            Costo en USD
        """
        model = model or self.default_model
        
        if model not in self.MODEL_COSTS:
            model = "gemini-1.5-flash"  # Fallback
        
        costs = self.MODEL_COSTS[model]
        
        input_cost = (Decimal(str(usage_stats.input_tokens)) / 1000) * costs["input"]
        output_cost = (Decimal(str(usage_stats.output_tokens)) / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def get_provider_name(self) -> AIProvider:
        """
        Obtiene el nombre del proveedor.
        
        Returns:
            Nombre del proveedor
        """
        return AIProvider.GEMINI
    
    def get_supported_models(self) -> List[str]:
        """
        Obtiene la lista de modelos soportados.
        
        Returns:
            Lista de nombres de modelos
        """
        return self.SUPPORTED_MODELS.copy()
    
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible.
        
        Returns:
            True si está disponible
        """
        return (
            self.api_key is not None and
            len(self.api_key.strip()) > 0 and
            self.is_initialized
        )
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Obtiene información sobre un modelo específico.
        
        Args:
            model: Nombre del modelo
            
        Returns:
            Información del modelo
        """
        if model not in self.SUPPORTED_MODELS:
            return {}
        
        return {
            "name": model,
            "provider": "gemini",
            "supports_vision": self._supports_vision(model),
            "supports_function_calling": True,
            "max_tokens": 8192 if "1.5" in model else 2048,
            "cost_per_1k_input": float(self.MODEL_COSTS.get(model, {}).get("input", 0)),
            "cost_per_1k_output": float(self.MODEL_COSTS.get(model, {}).get("output", 0))
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.is_initialized:
            await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def close(self) -> None:
        """
        Cierra la sesión HTTP.
        """
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False