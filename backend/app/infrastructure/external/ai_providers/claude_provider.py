#!/usr/bin/env python3
"""
Claude Provider Implementation

Implements the Anthropic Claude API provider for text and vision processing.
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


class ClaudeProvider(BaseAIProvider):
    """
    Proveedor de IA para Anthropic Claude models.
    """
    
    # Modelos soportados
    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    
    # Costos por modelo (USD por 1K tokens)
    MODEL_COSTS = {
        "claude-3-5-sonnet-20241022": {
            "input": Decimal('0.003'),
            "output": Decimal('0.015')
        },
        "claude-3-5-haiku-20241022": {
            "input": Decimal('0.0008'),
            "output": Decimal('0.004')
        },
        "claude-3-opus-20240229": {
            "input": Decimal('0.015'),
            "output": Decimal('0.075')
        },
        "claude-3-sonnet-20240229": {
            "input": Decimal('0.003'),
            "output": Decimal('0.015')
        },
        "claude-3-haiku-20240307": {
            "input": Decimal('0.00025'),
            "output": Decimal('0.00125')
        }
    }
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.settings = get_settings()
        self.base_url = kwargs.get('base_url', 'https://api.anthropic.com/v1')
        self.default_model = kwargs.get('default_model', 'claude-3-5-haiku-20241022')
        self.session: Optional[aiohttp.ClientSession] = None
        self.anthropic_version = kwargs.get('anthropic_version', '2023-06-01')
    
    async def initialize(self) -> None:
        """
        Inicializa el cliente de Claude.
        """
        try:
            # Crear sesión HTTP
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.anthropic_version,
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
                f"Error inicializando Claude: {e}",
                AIProvider.CLAUDE,
                "initialization_failed"
            )
    
    async def _test_connection(self) -> None:
        """
        Prueba la conexión con Claude.
        """
        try:
            payload = {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 1,
                "messages": [
                    {"role": "user", "content": "test"}
                ]
            }
            
            async with self.session.post(
                f"{self.base_url}/messages",
                json=payload
            ) as response:
                if response.status == 401:
                    raise AIProviderAuthenticationError(
                        "API key de Claude inválida",
                        AIProvider.CLAUDE
                    )
                elif response.status != 200:
                    text = await response.text()
                    raise Exception(f"HTTP {response.status}: {text}")
                
        except AIProviderAuthenticationError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Error de conexión Claude: {e}",
                AIProvider.CLAUDE,
                "connection_test_failed"
            )
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Procesa una solicitud usando Claude.
        
        Args:
            request: Solicitud a procesar
            
        Returns:
            Respuesta de Claude
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
                payload, request.max_retries
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
        Prepara el payload para Claude.
        
        Args:
            request: Solicitud original
            model: Modelo a usar
            
        Returns:
            Payload formateado
        """
        content = []
        
        # Agregar texto
        content.append({
            "type": "text",
            "text": request.prompt
        })
        
        # Agregar imágenes si las hay
        if request.images and self._supports_vision(model):
            prepared_images = self._prepare_images(request.images)
            
            for image_data in prepared_images:
                # Claude espera imágenes en formato base64
                if image_data.startswith('data:'):
                    # Extraer el base64 del data URL
                    media_type, base64_data = image_data.split(',', 1)
                    media_type = media_type.split(':')[1].split(';')[0]
                else:
                    # Asumir que es base64 puro
                    base64_data = image_data
                    media_type = "image/jpeg"  # Default
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data
                    }
                })
        
        payload = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
        
        # Agregar parámetros específicos del proveedor
        payload.update(request.provider_specific_params)
        
        return payload
    
    def _supports_vision(self, model: str) -> bool:
        """
        Verifica si el modelo soporta visión.
        
        Args:
            model: Nombre del modelo
            
        Returns:
            True si soporta visión
        """
        # Todos los modelos Claude 3 soportan visión
        return model.startswith("claude-3")
    
    async def _make_request_with_retries(
        self,
        payload: Dict[str, Any],
        max_retries: int
    ) -> Dict[str, Any]:
        """
        Realiza la solicitud con reintentos automáticos.
        
        Args:
            payload: Payload de la solicitud
            max_retries: Número máximo de reintentos
            
        Returns:
            Respuesta de Claude
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(
                    f"{self.base_url}/messages",
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 401:
                        raise AIProviderAuthenticationError(
                            "API key de Claude inválida",
                            AIProvider.CLAUDE
                        )
                    
                    elif response.status == 429:
                        # Rate limit
                        retry_after = response.headers.get('retry-after')
                        if attempt < max_retries:
                            wait_time = int(retry_after) if retry_after else min(2 ** attempt, 60)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise AIProviderRateLimitError(
                                "Límite de velocidad Claude excedido",
                                AIProvider.CLAUDE,
                                retry_after=int(retry_after) if retry_after else None
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
            f"Claude request failed after {max_retries + 1} attempts: {last_exception}",
            AIProvider.CLAUDE,
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
        Procesa la respuesta de Claude.
        
        Args:
            response_data: Respuesta cruda de Claude
            model: Modelo utilizado
            processing_time: Tiempo de procesamiento
            request: Solicitud original
            
        Returns:
            Respuesta procesada
        """
        try:
            # Extraer contenido
            content_blocks = response_data.get("content", [])
            content = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    content += block.get("text", "")
            
            # Extraer estadísticas de uso
            usage = response_data.get("usage", {})
            usage_stats = AIUsageStats(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                images_processed=len(request.images),
                requests_made=1,
                processing_time_seconds=processing_time
            )
            
            # Calcular costo
            usage_stats.total_cost_usd = self.calculate_cost(usage_stats, model)
            
            return AIResponse(
                content=content,
                provider=AIProvider.CLAUDE,
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
                f"Error procesando respuesta Claude: {e}",
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
            model = "claude-3-5-haiku-20241022"  # Fallback
        
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
        return AIProvider.CLAUDE
    
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
        
        max_tokens_map = {
            "claude-3-5-sonnet-20241022": 8192,
            "claude-3-5-haiku-20241022": 8192,
            "claude-3-opus-20240229": 4096,
            "claude-3-sonnet-20240229": 4096,
            "claude-3-haiku-20240307": 4096
        }
        
        return {
            "name": model,
            "provider": "claude",
            "supports_vision": self._supports_vision(model),
            "supports_function_calling": True,
            "max_tokens": max_tokens_map.get(model, 4096),
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