#!/usr/bin/env python3
"""
AI Provider Factory

Factory for managing multiple AI providers with fallback support.
"""

import asyncio
from typing import Dict, List, Optional, Union
from loguru import logger

from .base import BaseAIProvider, AIRequest, AIResponse, AIProviderError
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .gemini_provider import GeminiProvider
from .claude_provider import ClaudeProvider
from ....domain.entities.processing_job import AIProvider
from ....core.config.settings import get_settings


class AIProviderFactory:
    """
    Factory for managing AI providers with automatic fallback.
    """
    
    # Orden de prioridad para fallback
    FALLBACK_ORDER = [
        AIProvider.OPENAI,
        AIProvider.DEEPSEEK,
        AIProvider.GEMINI,
        AIProvider.CLAUDE
    ]
    
    def __init__(self):
        self.settings = get_settings()
        self._providers: Dict[AIProvider, BaseAIProvider] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize_providers(self) -> None:
        """
        Initialize all configured AI providers.
        """
        async with self._lock:
            if self._initialized:
                logger.warning("AI providers already initialized")
                return
            
            try:
                logger.info("Initializing AI providers...")
                
                # Initialize OpenAI provider if configured
                if self.settings.ai_providers.OPENAI_API_KEY:
                    try:
                        await self._initialize_openai()
                    except Exception as e:
                        logger.warning(f"Failed to initialize OpenAI provider: {e}")
                
                # Initialize DeepSeek provider if configured
                if self.settings.ai_providers.DEEPSEEK_API_KEY:
                    try:
                        await self._initialize_deepseek()
                    except Exception as e:
                        logger.warning(f"Failed to initialize DeepSeek provider: {e}")
                
                # Initialize Gemini provider if configured
                if self.settings.ai_providers.GEMINI_API_KEY:
                    try:
                        await self._initialize_gemini()
                    except Exception as e:
                        logger.warning(f"Failed to initialize Gemini provider: {e}")
                
                # Initialize Claude provider if configured
                if self.settings.ai_providers.CLAUDE_API_KEY:
                    try:
                        await self._initialize_claude()
                    except Exception as e:
                        logger.warning(f"Failed to initialize Claude provider: {e}")
                
                self._initialized = True
                available_providers = [p.value for p in self._providers.keys()]
                logger.info(f"Initialized {len(self._providers)} AI providers: {available_providers}")
                
            except Exception as e:
                logger.error(f"Failed to initialize AI providers: {e}")
                # Don't raise, allow server to start without AI providers
                self._initialized = True
    
    async def _initialize_openai(self) -> None:
        """
        Initialize OpenAI provider.
        """
        try:
            provider = OpenAIProvider(
                api_key=self.settings.ai_providers.OPENAI_API_KEY,
                default_model=self.settings.ai_providers.OPENAI_MODEL,
                timeout=self.settings.ai_providers.AI_TIMEOUT,
                max_retries=self.settings.ai_providers.AI_MAX_RETRIES
            )
            await provider.initialize()
            self._providers[AIProvider.OPENAI] = provider
            logger.info("OpenAI provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
    
    async def _initialize_deepseek(self) -> None:
        """
        Initialize DeepSeek provider.
        """
        try:
            provider = DeepSeekProvider(
                api_key=self.settings.ai_providers.DEEPSEEK_API_KEY,
                default_model=self.settings.ai_providers.DEEPSEEK_MODEL,
                timeout=self.settings.ai_providers.AI_TIMEOUT,
                max_retries=self.settings.ai_providers.AI_MAX_RETRIES
            )
            await provider.initialize()
            self._providers[AIProvider.DEEPSEEK] = provider
            logger.info("DeepSeek provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek: {e}")
    
    async def _initialize_gemini(self) -> None:
        """
        Initialize Gemini provider.
        """
        try:
            provider = GeminiProvider(
                api_key=self.settings.ai_providers.GEMINI_API_KEY,
                default_model=self.settings.ai_providers.GEMINI_MODEL,
                timeout=self.settings.ai_providers.AI_TIMEOUT,
                max_retries=self.settings.ai_providers.AI_MAX_RETRIES
            )
            await provider.initialize()
            self._providers[AIProvider.GEMINI] = provider
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
    async def _initialize_claude(self) -> None:
        """
        Initialize Claude provider.
        """
        try:
            provider = ClaudeProvider(
                api_key=self.settings.ai_providers.CLAUDE_API_KEY,
                default_model=self.settings.ai_providers.CLAUDE_MODEL,
                timeout=self.settings.ai_providers.AI_TIMEOUT,
                max_retries=self.settings.ai_providers.AI_MAX_RETRIES
            )
            await provider.initialize()
            self._providers[AIProvider.CLAUDE] = provider
            logger.info("Claude provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude: {e}")
    
    async def process_request(
        self,
        request: AIRequest,
        preferred_provider: Optional[AIProvider] = None,
        enable_fallback: bool = True
    ) -> AIResponse:
        """
        Process a request using the specified provider with fallback support.
        
        Args:
            request: The AI request to process
            preferred_provider: Preferred provider to use first
            enable_fallback: Whether to enable fallback to other providers
            
        Returns:
            AI response from the successful provider
            
        Raises:
            AIProviderError: If all providers fail
        """
        if not self._initialized:
            await self.initialize_providers()
        
        if not self._providers:
            raise AIProviderError(
                "No AI providers available",
                AIProvider.OPENAI,  # Default for error reporting
                "no_providers_available"
            )
        
        # Determine provider order
        providers_to_try = self._get_provider_order(preferred_provider, enable_fallback)
        
        last_error = None
        
        for provider_enum in providers_to_try:
            if provider_enum not in self._providers:
                continue
            
            provider = self._providers[provider_enum]
            
            try:
                logger.debug(f"Attempting request with {provider_enum.value}")
                response = await provider.process_request(request)
                
                if response.success:
                    logger.info(f"Request successful with {provider_enum.value}")
                    return response
                else:
                    logger.warning(f"Request failed with {provider_enum.value}: {response.error_message}")
                    last_error = response.error_message
                    
            except Exception as e:
                logger.error(f"Error with {provider_enum.value}: {e}")
                last_error = str(e)
                continue
        
        # All providers failed
        raise AIProviderError(
            f"All AI providers failed. Last error: {last_error}",
            preferred_provider or AIProvider.OPENAI,
            "all_providers_failed"
        )
    
    def _get_provider_order(
        self,
        preferred_provider: Optional[AIProvider],
        enable_fallback: bool
    ) -> List[AIProvider]:
        """
        Get the order of providers to try.
        
        Args:
            preferred_provider: Preferred provider to try first
            enable_fallback: Whether to enable fallback
            
        Returns:
            List of providers in order of preference
        """
        if not enable_fallback:
            # Only try the preferred provider
            if preferred_provider and preferred_provider in self._providers:
                return [preferred_provider]
            else:
                # Use the first available provider
                available = self.get_available_providers()
                return [available[0]] if available else []
        
        # Build fallback order
        providers_order = []
        
        # Add preferred provider first if specified and available
        if preferred_provider and preferred_provider in self._providers:
            providers_order.append(preferred_provider)
        
        # Add remaining providers in fallback order
        for provider in self.FALLBACK_ORDER:
            if provider not in providers_order and provider in self._providers:
                providers_order.append(provider)
        
        return providers_order
    
    def get_available_providers(self) -> List[AIProvider]:
        """
        Get list of available providers.
        
        Returns:
            List of available provider enums
        """
        return [provider for provider in self._providers.keys() if self._providers[provider].is_available()]
    
    def get_primary_provider(self) -> Optional[AIProvider]:
        """
        Get the primary (highest priority) available provider.
        
        Returns:
            Primary provider enum or None if no providers available
        """
        available = self.get_available_providers()
        if not available:
            return None
        
        # Return first provider in fallback order that's available
        for provider in self.FALLBACK_ORDER:
            if provider in available:
                return provider
        
        # Fallback to first available
        return available[0]
    
    def get_provider(self, provider_type: AIProvider) -> Optional[BaseAIProvider]:
        """
        Get a specific provider instance.
        
        Args:
            provider_type: Type of provider to get
            
        Returns:
            Provider instance or None if not available
        """
        return self._providers.get(provider_type)
    
    def get_provider_info(self, provider_type: AIProvider) -> Dict[str, any]:
        """
        Get information about a specific provider.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            Provider information dictionary
        """
        if provider_type not in self._providers:
            return {"available": False, "error": "Provider not configured"}
        
        provider = self._providers[provider_type]
        
        return {
            "available": provider.is_available(),
            "name": provider.get_provider_name().value,
            "supported_models": provider.get_supported_models(),
            "usage_stats": provider.get_usage_stats().__dict__
        }
    
    def get_all_providers_info(self) -> Dict[str, Dict[str, any]]:
        """
        Get information about all providers.
        
        Returns:
            Dictionary with provider information
        """
        info = {}
        for provider_type in AIProvider:
            info[provider_type.value] = self.get_provider_info(provider_type)
        return info
    
    async def health_check(self) -> Dict[str, Dict[str, any]]:
        """
        Perform health check on all providers.
        
        Returns:
            Health status for each provider
        """
        if not self._initialized:
            await self.initialize_providers()
        
        health_status = {}
        
        for provider_type, provider in self._providers.items():
            try:
                # Perform a simple health check
                is_healthy = await provider.health_check()
                health_status[provider_type.value] = {
                    "healthy": is_healthy,
                    "available": provider.is_available(),
                    "error": None
                }
            except Exception as e:
                health_status[provider_type.value] = {
                    "healthy": False,
                    "available": False,
                    "error": str(e)
                }
        
        return health_status
    
    async def close_all(self) -> None:
        """
        Close all provider connections.
        """
        for provider in self._providers.values():
            try:
                await provider.close()
            except Exception as e:
                logger.error(f"Error closing provider: {e}")
        
        self._providers.clear()
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """
        Check if factory is initialized.
        
        Returns:
            True if initialized
        """
        return self._initialized
    
    def __len__(self) -> int:
        """
        Get number of available providers.
        
        Returns:
            Number of providers
        """
        return len(self._providers)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_providers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()


# Global factory instance
_factory_instance: Optional[AIProviderFactory] = None


def get_ai_factory() -> AIProviderFactory:
    """
    Get the global AI provider factory instance.
    
    Returns:
        AI provider factory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AIProviderFactory()
    return _factory_instance


async def initialize_ai_providers() -> AIProviderFactory:
    """
    Initialize the global AI provider factory.
    
    Returns:
        Initialized AI provider factory
    """
    factory = get_ai_factory()
    await factory.initialize_providers()
    return factory