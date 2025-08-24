#!/usr/bin/env python3
"""
OpenAI Provider Implementation

Implements the OpenAI API provider for text and vision processing.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from decimal import Decimal
import openai
from openai import AsyncOpenAI

from .base import (
    BaseAIProvider, AIRequest, AIResponse, AIUsageStats,
    AIProviderError, AIProviderUnavailableError, AIProviderRateLimitError,
    AIProviderAuthenticationError, AIProviderTimeoutError
)
from ....domain.entities.processing_job import AIProvider
from ....core.config.settings import get_settings


class OpenAIProvider(BaseAIProvider):
    """
    Proveedor de IA para OpenAI GPT models.
    """
    
    # Modelos soportados
    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4-vision-preview",
        "gpt-3.5-turbo"
    ]
    
    # Costos por modelo (USD por 1K tokens)
    MODEL_COSTS = {
        "gpt-4o": {
            "input": Decimal('0.005'),
            "output": Decimal('0.015')
        },
        "gpt-4o-mini": {
            "input": Decimal('0.00015'),
            "output": Decimal('0.0006')
        },
        "gpt-4-turbo": {
            "input": Decimal('0.01'),
            "output": Decimal('0.03')
        },
        "gpt-4-vision-preview": {
            "input": Decimal('0.01'),
            "output": Decimal('0.03')
        },
        "gpt-3.5-turbo": {
            "input": Decimal('0.0005'),
            "output": Decimal('0.0015')
        }
    }
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.settings = get_settings()
        self.client: Optional[AsyncOpenAI] = None
        self.default_model = kwargs.get('default_model', 'gpt-4o-mini')
        self.base_url = kwargs.get('base_url', None)
        self.organization = kwargs.get('organization', None)
    
    async def initialize(self) -> None:
        """
        Inicializa el cliente de OpenAI.
        """
        try:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                organization=self.organization,
                timeout=60.0
            )
            
            # Verificar que la API key funciona
            await self._test_connection()
            
            self.is_initialized = True
            
        except Exception as e:
            raise AIProviderError(
                f"Error inicializando OpenAI: {e}",
                AIProvider.OPENAI,
                "initialization_failed"
            )
    
    async def _test_connection(self) -> None:
        """
        Prueba la conexión con OpenAI.
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            if not response:
                raise Exception("No response from OpenAI")
        except openai.AuthenticationError as e:
            raise AIProviderAuthenticationError(
                f"Error de autenticación OpenAI: {e}",
                AIProvider.OPENAI
            )
        except Exception as e:
            raise AIProviderError(
                f"Error de conexión OpenAI: {e}",
                AIProvider.OPENAI,
                "connection_test_failed"
            )
    
    async def process_request(self, request: AIRequest) -> AIResponse:
        """
        Procesa una solicitud usando OpenAI.
        
        Args:
            request: Solicitud a procesar
            
        Returns:
            Respuesta de OpenAI
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Seleccionar modelo
            model = request.model or self.default_model
            if model not in self.SUPPORTED_MODELS:
                model = self.default_model
            
            # Preparar mensajes
            messages = await self._prepare_messages(request)
            
            # Configurar parámetros
            params = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                **request.provider_specific_params
            }
            
            # Realizar solicitud con reintentos
            response = await self._make_request_with_retries(params, request.max_retries)
            
            # Procesar respuesta
            processing_time = time.time() - start_time
            ai_response = self._process_response(response, model, processing_time, request)
            
            # Actualizar estadísticas
            self._update_usage_stats(ai_response)
            
            return ai_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            return self._create_error_response(request, str(e), processing_time)
    
    async def _prepare_messages(self, request: AIRequest) -> List[Dict[str, Any]]:
        """
        Prepara los mensajes para OpenAI.
        
        Args:
            request: Solicitud original
            
        Returns:
            Lista de mensajes formateados
        """
        messages = []
        
        if request.images:
            # Solicitud con imágenes (vision)
            content = [{"type": "text", "text": request.prompt}]
            
            # Preparar imágenes
            prepared_images = self._prepare_images(request.images)
            
            for image_data in prepared_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data,
                        "detail": "high"  # Para mejor calidad de análisis
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
        
        return messages
    
    async def _make_request_with_retries(
        self,
        params: Dict[str, Any],
        max_retries: int
    ) -> Any:
        """
        Realiza la solicitud con reintentos automáticos.
        
        Args:
            params: Parámetros de la solicitud
            max_retries: Número máximo de reintentos
            
        Returns:
            Respuesta de OpenAI
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.chat.completions.create(**params)
                return response
                
            except openai.RateLimitError as e:
                last_exception = e
                if attempt < max_retries:
                    # Esperar antes del siguiente intento
                    wait_time = min(2 ** attempt, 60)  # Backoff exponencial
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise AIProviderRateLimitError(
                        f"Límite de velocidad OpenAI: {e}",
                        AIProvider.OPENAI,
                        retry_after=getattr(e, 'retry_after', None)
                    )
            
            except openai.AuthenticationError as e:
                raise AIProviderAuthenticationError(
                    f"Error de autenticación OpenAI: {e}",
                    AIProvider.OPENAI
                )
            
            except openai.APITimeoutError as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise AIProviderTimeoutError(
                        f"Timeout OpenAI: {e}",
                        AIProvider.OPENAI,
                        timeout_seconds=60
                    )
            
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    break
        
        # Si llegamos aquí, todos los intentos fallaron
        raise AIProviderError(
            f"OpenAI request failed after {max_retries + 1} attempts: {last_exception}",
            AIProvider.OPENAI,
            "request_failed"
        )
    
    def _process_response(
        self,
        response: Any,
        model: str,
        processing_time: float,
        request: AIRequest
    ) -> AIResponse:
        """
        Procesa la respuesta de OpenAI.
        
        Args:
            response: Respuesta cruda de OpenAI
            model: Modelo utilizado
            processing_time: Tiempo de procesamiento
            request: Solicitud original
            
        Returns:
            Respuesta procesada
        """
        try:
            # Extraer contenido
            content = response.choices[0].message.content or ""
            
            # Extraer estadísticas de uso
            usage = response.usage
            usage_stats = AIUsageStats(
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                images_processed=len(request.images),
                requests_made=1,
                processing_time_seconds=processing_time
            )
            
            # Calcular costo
            usage_stats.total_cost_usd = self.calculate_cost(usage_stats, model)
            
            return AIResponse(
                content=content,
                provider=AIProvider.OPENAI,
                model_used=model,
                usage_stats=usage_stats,
                success=True,
                response_time_seconds=processing_time,
                request_id=request.request_id,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            return self._create_error_response(
                request,
                f"Error procesando respuesta OpenAI: {e}",
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
            model = "gpt-4o-mini"  # Fallback
        
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
        return AIProvider.OPENAI
    
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
            "provider": "openai",
            "supports_vision": "vision" in model or model.startswith("gpt-4"),
            "supports_function_calling": model != "gpt-3.5-turbo",
            "max_tokens": 4096 if "gpt-3.5" in model else 8192,
            "cost_per_1k_input": float(self.MODEL_COSTS.get(model, {}).get("input", 0)),
            "cost_per_1k_output": float(self.MODEL_COSTS.get(model, {}).get("output", 0))
        }
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de modelos disponibles desde la API.
        
        Returns:
            Lista de modelos disponibles
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            models_response = await self.client.models.list()
            available_models = []
            
            for model in models_response.data:
                if model.id in self.SUPPORTED_MODELS:
                    available_models.append({
                        "id": model.id,
                        "object": model.object,
                        "created": model.created,
                        "owned_by": model.owned_by
                    })
            
            return available_models
            
        except Exception as e:
            raise AIProviderError(
                f"Error obteniendo modelos OpenAI: {e}",
                AIProvider.OPENAI,
                "models_fetch_failed"
            )