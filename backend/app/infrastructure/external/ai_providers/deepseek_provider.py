#!/usr/bin/env python3
"""
DeepSeek Provider Implementation

Implements the DeepSeek API provider for text and vision processing.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from decimal import Decimal
import aiohttp
import json

from .base import (
    BaseAIProvider, AIRequest, AIResponse, AIUsageStats,
    AIProviderError, AIProviderUnavailableError, AIProviderRateLimitError,
    AIProviderAuthenticationError, AIProviderTimeoutError
)
from ....domain.entities.processing_job import AIProvider
from ....core.config.settings import get_settings


class DeepSeekProvider(BaseAIProvider):
    """
    Proveedor de IA para DeepSeek models.
    """
    
    # Modelos soportados
    SUPPORTED_MODELS = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-vl-7b-chat",
        "deepseek-vl-1.3b-chat"
    ]
    
    # Costos por modelo (USD por 1K tokens)
    MODEL_COSTS = {
        "deepseek-chat": {
            "input": Decimal('0.00014'),
            "output": Decimal('0.00028')
        },
        "deepseek-coder": {
            "input": Decimal('0.00014'),
            "output": Decimal('0.00028')
        },
        "deepseek-vl-7b-chat": {
            "input": Decimal('0.0007'),
            "output": Decimal('0.0014')
        },
        "deepseek-vl-1.3b-chat": {
            "input": Decimal('0.0003'),
            "output": Decimal('0.0006')
        }
    }
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.settings = get_settings()
        self.base_url = kwargs.get('base_url', 'https://api.deepseek.com/v1')
        self.default_model = kwargs.get('default_model', 'deepseek-chat')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """
        Inicializa el cliente de DeepSeek.
        """
        try:
            # Crear sesión HTTP
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
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
                f"Error inicializando DeepSeek: {e}",
                AIProvider.DEEPSEEK,
                "initialization_failed"
            )
    
    async def _test_connection(self) -> None:
        """
        Prueba la conexión con DeepSeek.
        """
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                if response.status == 401:
                    raise AIProviderAuthenticationError(
                        "API key de DeepSeek inválida",
                        AIProvider.DEEPSEEK
                    )
                elif response.status != 200:
                    text = await response.text()
                    raise Exception(f"HTTP {response.status}: {text}")
                
        except AIProviderAuthenticationError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Error de conexión DeepSeek: {e}",
                AIProvider.DEEPSEEK,
                "connection_test_failed"
            )
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Procesa una solicitud usando DeepSeek.
        
        Args:
            request: Solicitud a procesar
            
        Returns:
            Respuesta de DeepSeek
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
        Prepara el payload para DeepSeek.
        
        Args:
            request: Solicitud original
            model: Modelo a usar
            
        Returns:
            Payload formateado
        """
        messages = []
        
        if request.images and model.startswith("deepseek-vl"):
            # Solicitud con imágenes (vision)
            content = [{"type": "text", "text": request.prompt}]
            
            # Preparar imágenes
            prepared_images = self._prepare_images(request.images)
            
            for image_data in prepared_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data
                    }
                })
            
            messages.append({
                "role": "user",
                "content": content
            })
        else:
            # Solicitud solo de texto
            messages.append({
                "role": "user",
                "content": request.prompt
            })
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }
        
        # Agregar parámetros específicos del proveedor
        payload.update(request.provider_specific_params)
        
        return payload
    
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
            Respuesta de DeepSeek
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 401:
                        raise AIProviderAuthenticationError(
                            "API key de DeepSeek inválida",
                            AIProvider.DEEPSEEK
                        )
                    
                    elif response.status == 429:
                        # Rate limit
                        retry_after = response.headers.get('Retry-After')
                        if attempt < max_retries:
                            wait_time = int(retry_after) if retry_after else min(2 ** attempt, 60)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise AIProviderRateLimitError(
                                "Límite de velocidad DeepSeek excedido",
                                AIProvider.DEEPSEEK,
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
            f"DeepSeek request failed after {max_retries + 1} attempts: {last_exception}",
            AIProvider.DEEPSEEK,
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
        Procesa la respuesta de DeepSeek.
        
        Args:
            response_data: Respuesta cruda de DeepSeek
            model: Modelo utilizado
            processing_time: Tiempo de procesamiento
            request: Solicitud original
            
        Returns:
            Respuesta procesada
        """
        try:
            # Extraer contenido
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extraer estadísticas de uso
            usage = response_data.get("usage", {})
            usage_stats = AIUsageStats(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                images_processed=len(request.images),
                requests_made=1,
                processing_time_seconds=processing_time
            )
            
            # Calcular costo
            usage_stats.total_cost_usd = self.calculate_cost(usage_stats, model)
            
            return AIResponse(
                content=content,
                provider=AIProvider.DEEPSEEK,
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
                f"Error procesando respuesta DeepSeek: {e}",
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
            model = "deepseek-chat"  # Fallback
        
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
        return AIProvider.DEEPSEEK
    
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
            "provider": "deepseek",
            "supports_vision": model.startswith("deepseek-vl"),
            "supports_function_calling": False,
            "max_tokens": 4096,
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