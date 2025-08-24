#!/usr/bin/env python3
"""
QR Extractor Pro Service

Adapts the reference QR extractor script for use in the infrastructure layer.
"""

import time
import asyncio
import base64
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2
import requests

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    pyzbar = None

from .base import BaseQRService, QRResult
from ....core.exceptions.base import QRProcessingError
from ....core.config.settings import get_settings


class QRExtractorProService(BaseQRService):
    """
    Servicio avanzado de extracción de códigos QR con múltiples estrategias.
    Basado en el script qr_extractor_pro.py de referencia.
    """
    
    def __init__(self, api_key: Optional[str] = None, debug: bool = False):
        self.settings = get_settings()
        self.api_key = api_key or getattr(self.settings.ai_providers, 'OPENAI_API_KEY', None)
        self.debug = debug
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'methods_used': {}
        }
        
        if not PYZBAR_AVAILABLE:
            raise QRProcessingError(
                "pyzbar no está disponible. Instale pyzbar: pip install pyzbar",
                qr_issue="missing_dependency"
            )
    
    async def extract_qr(self, image: np.ndarray, **kwargs) -> QRResult:
        """
        Extrae códigos QR usando múltiples estrategias.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros adicionales
                - use_api: Si usar API de IA como fallback (default: True)
                - validate_ine: Si validar formato INE (default: True)
                
        Returns:
            QRResult con los datos del QR
        """
        start_time = time.time()
        
        try:
            use_api = kwargs.get('use_api', True)
            validate_ine = kwargs.get('validate_ine', True)
            
            # Ejecutar extracción en un hilo separado
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                None,
                self._process_image_sync,
                image,
                use_api,
                validate_ine
            )
            
            processing_time = time.time() - start_time
            
            if result['success']:
                return QRResult(
                    data=result['qr_data'],
                    qr_type="ine" if result['qr_data'] and self._is_valid_ine_qr(result['qr_data']) else "unknown",
                    confidence=result['confidence'],
                    processing_time=processing_time,
                    method_used=result['method_used'],
                    success=True
                )
            else:
                return QRResult(
                    data=None,
                    qr_type=None,
                    confidence=0.0,
                    processing_time=processing_time,
                    method_used=result.get('method_used', 'unknown'),
                    success=False,
                    error_message=result.get('error', 'Unknown error')
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return QRResult(
                data=None,
                qr_type=None,
                confidence=0.0,
                processing_time=processing_time,
                method_used="qr_extractor_pro",
                success=False,
                error_message=str(e)
            )
    
    def _process_image_sync(self, image: np.ndarray, use_api: bool, validate_ine: bool) -> Dict[str, Any]:
        """
        Procesa la imagen de forma síncrona usando múltiples estrategias.
        
        Args:
            image: Imagen a procesar
            use_api: Si usar API como fallback
            validate_ine: Si validar formato INE
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        self.stats['total_processed'] += 1
        
        # Estrategias de extracción de regiones
        extraction_strategies = [
            ("exact_region", self._extract_region_exact),
            ("right_region", self._extract_region_right),
            ("right_top", self._extract_region_right_top),
            ("right_bottom", self._extract_region_right_bottom),
            ("center_right", self._extract_region_center_right),
            ("full_image", self._extract_region_full)
        ]
        
        # Intentar extracción local primero
        for strategy_name, extraction_func in extraction_strategies:
            try:
                region = extraction_func(image)
                if region is not None:
                    qr_data = self._read_qr_local(region)
                    if qr_data and (not validate_ine or self._is_valid_ine_qr(qr_data)):
                        self.stats['successful'] += 1
                        self.stats['methods_used'][strategy_name] = self.stats['methods_used'].get(strategy_name, 0) + 1
                        
                        return {
                            'success': True,
                            'qr_data': qr_data,
                            'method_used': f"local_{strategy_name}",
                            'confidence': 0.9,  # Alta confianza para métodos locales
                            'tokens_used': 0,
                            'cost': 0.0
                        }
            except Exception as e:
                self._log_debug(f"Error en estrategia {strategy_name}: {e}")
                continue
        
        # Si falla la extracción local y se permite API, intentar con IA
        if use_api and self.api_key:
            try:
                qr_data, tokens, cost = self._ask_api_qr(image)
                if qr_data and (not validate_ine or self._is_valid_ine_qr(qr_data)):
                    self.stats['successful'] += 1
                    self.stats['total_tokens'] += tokens
                    self.stats['total_cost'] += cost
                    self.stats['methods_used']['api'] = self.stats['methods_used'].get('api', 0) + 1
                    
                    return {
                        'success': True,
                        'qr_data': qr_data,
                        'method_used': 'api_openai',
                        'confidence': 0.8,  # Confianza media para API
                        'tokens_used': tokens,
                        'cost': cost
                    }
            except Exception as e:
                self._log_debug(f"Error en API: {e}")
        
        # Si todo falla
        self.stats['failed'] += 1
        return {
            'success': False,
            'error': 'No se pudo extraer código QR con ninguna estrategia',
            'method_used': 'none'
        }
    
    def _extract_region_exact(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrae región exacta del QR (560px-723px, altura completa).
        
        Args:
            image: Imagen fuente
            
        Returns:
            Región extraída o None si es inválida
        """
        height, width = image.shape[:2]
        
        # Coordenadas exactas basadas en análisis previo
        start_x = max(0, 560)
        end_x = min(width, 723)
        
        if start_x >= end_x:
            return None
            
        region = image[:, start_x:end_x]
        return region
    
    def _extract_region_right(self, image: np.ndarray) -> np.ndarray:
        """
        Extrae región derecha (70% del ancho hacia la derecha).
        
        Args:
            image: Imagen fuente
            
        Returns:
            Región derecha
        """
        height, width = image.shape[:2]
        start_x = int(width * 0.7)
        
        return image[:, start_x:]
    
    def _extract_region_right_top(self, image: np.ndarray) -> np.ndarray:
        """
        Extrae región superior derecha.
        
        Args:
            image: Imagen fuente
            
        Returns:
            Región superior derecha
        """
        height, width = image.shape[:2]
        start_x = int(width * 0.7)
        end_y = int(height * 0.5)
        
        return image[:end_y, start_x:]
    
    def _extract_region_right_bottom(self, image: np.ndarray) -> np.ndarray:
        """
        Extrae región inferior derecha.
        
        Args:
            image: Imagen fuente
            
        Returns:
            Región inferior derecha
        """
        height, width = image.shape[:2]
        start_x = int(width * 0.7)
        start_y = int(height * 0.5)
        
        return image[start_y:, start_x:]
    
    def _extract_region_center_right(self, image: np.ndarray) -> np.ndarray:
        """
        Extrae región central derecha.
        
        Args:
            image: Imagen fuente
            
        Returns:
            Región central derecha
        """
        height, width = image.shape[:2]
        start_x = int(width * 0.7)
        start_y = int(height * 0.25)
        end_y = int(height * 0.75)
        
        return image[start_y:end_y, start_x:]
    
    def _extract_region_full(self, image: np.ndarray) -> np.ndarray:
        """
        Extrae la imagen completa.
        
        Args:
            image: Imagen fuente
            
        Returns:
            Imagen completa
        """
        return image
    
    def _read_qr_local(self, image: np.ndarray) -> Optional[str]:
        """
        Lee QR usando pyzbar localmente.
        
        Args:
            image: Imagen a procesar
            
        Returns:
            Datos del QR o None si no se encuentra
        """
        try:
            # Intentar con imagen original
            qr_codes = pyzbar.decode(image)
            
            if qr_codes:
                for qr in qr_codes:
                    qr_data = qr.data.decode('utf-8')
                    if self._is_valid_ine_qr(qr_data):
                        return qr_data
                        
            # Intentar con imagen mejorada
            enhanced = self._enhance_image(image)
            qr_codes = pyzbar.decode(enhanced)
            
            if qr_codes:
                for qr in qr_codes:
                    qr_data = qr.data.decode('utf-8')
                    if self._is_valid_ine_qr(qr_data):
                        return qr_data
                        
        except Exception as e:
            self._log_debug(f"Error en lectura local: {e}")
            
        return None
    
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Mejora la imagen para mejor detección de QR.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen mejorada
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Aplicar filtros de mejora
        enhanced = cv2.GaussianBlur(gray, (3, 3), 0)
        enhanced = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return enhanced
    
    def _is_valid_ine_qr(self, qr_data: str) -> bool:
        """
        Valida si el QR es válido para credenciales INE.
        
        Args:
            qr_data: Datos del código QR
            
        Returns:
            True si es un QR válido de INE
        """
        return (
            qr_data.startswith('http://qr.ine.mx/') and 
            len(qr_data) > 30 and
            '/P/' in qr_data
        )
    
    def _ask_api_qr(self, image: np.ndarray) -> Tuple[Optional[str], int, float]:
        """
        Consulta API de OpenAI para extraer QR.
        
        Args:
            image: Imagen a procesar
            
        Returns:
            Tupla con (datos_qr, tokens_usados, costo)
        """
        if not self.api_key:
            return None, 0, 0.0
            
        try:
            # Convertir imagen a base64
            _, buffer = cv2.imencode('.png', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extrae únicamente la URL del código QR de esta imagen. Responde solo con la URL completa, sin texto adicional."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                qr_data = result['choices'][0]['message']['content'].strip()
                
                # Calcular tokens y costo
                tokens_used = result['usage']['total_tokens']
                cost = tokens_used * 0.00015  # Precio aproximado por token
                
                return qr_data, tokens_used, cost
            else:
                self._log_debug(f"Error en API: {response.status_code} - {response.text}")
                return None, 0, 0.0
                
        except Exception as e:
            self._log_debug(f"Error en consulta API: {e}")
            return None, 0, 0.0
    
    def _log_debug(self, message: str) -> None:
        """
        Registra mensajes de debug si está habilitado.
        
        Args:
            message: Mensaje a registrar
        """
        if self.debug:
            print(f"[QR_EXTRACTOR_PRO] {message}")
    
    def is_available(self) -> bool:
        """
        Verifica si el servicio está disponible.
        
        Returns:
            True si pyzbar está disponible
        """
        return PYZBAR_AVAILABLE
    
    def get_service_name(self) -> str:
        """
        Obtiene el nombre del servicio.
        
        Returns:
            Nombre del servicio
        """
        return "qr_extractor_pro"
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesamiento.
        
        Returns:
            Diccionario con estadísticas
        """
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """
        Reinicia las estadísticas.
        """
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'methods_used': {}
        }