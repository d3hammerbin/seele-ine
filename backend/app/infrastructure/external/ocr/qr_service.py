#!/usr/bin/env python3
"""
QR Code Extraction Service

Implements QR code extraction using pyzbar and OpenCV.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    pyzbar = None

from .base import BaseQRService, QRResult
from ....core.exceptions.base import QRProcessingError
from ....core.config.settings import get_settings


class QRExtractionService(BaseQRService):
    """
    Servicio de extracción de códigos QR usando pyzbar y OpenCV.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.qr_timeout = self.settings.image_processing.QR_TIMEOUT
        self.max_attempts = self.settings.image_processing.QR_MAX_ATTEMPTS
        
        if not PYZBAR_AVAILABLE:
            raise QRProcessingError(
                "pyzbar no está disponible. Instale pyzbar: pip install pyzbar",
                qr_issue="missing_dependency"
            )
    
    async def extract_qr(self, image: np.ndarray, **kwargs) -> QRResult:
        """
        Extrae códigos QR de una imagen.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros adicionales
                - region: Región específica para buscar QR {"x": int, "y": int, "width": int, "height": int}
                - enhance: Si aplicar mejoras de imagen (default: True)
                - validate_ine: Si validar que sea un QR de INE (default: True)
                
        Returns:
            QRResult con los datos del QR
        """
        start_time = time.time()
        
        try:
            # Obtener parámetros
            region = kwargs.get('region')
            enhance = kwargs.get('enhance', True)
            validate_ine = kwargs.get('validate_ine', True)
            
            # Extraer región si se especifica
            work_image = image
            if region:
                x, y, w, h = region['x'], region['y'], region['width'], region['height']
                work_image = image[y:y+h, x:x+w]
            
            # Ejecutar extracción en un hilo separado
            loop = asyncio.get_event_loop()
            
            qr_data, confidence, bounding_box = await loop.run_in_executor(
                None,
                self._extract_qr_sync,
                work_image,
                enhance,
                validate_ine
            )
            
            processing_time = time.time() - start_time
            
            # Ajustar bounding box si se usó una región
            if region and bounding_box:
                bounding_box['x'] += region['x']
                bounding_box['y'] += region['y']
            
            return QRResult(
                data=qr_data,
                qr_type="ine" if qr_data and self._is_valid_ine_qr(qr_data) else "unknown",
                confidence=confidence,
                processing_time=processing_time,
                method_used="pyzbar",
                success=qr_data is not None,
                bounding_box=bounding_box
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return QRResult(
                data=None,
                qr_type=None,
                confidence=0.0,
                processing_time=processing_time,
                method_used="pyzbar",
                success=False,
                error_message=str(e)
            )
    
    def _extract_qr_sync(self, image: np.ndarray, enhance: bool, validate_ine: bool) -> Tuple[Optional[str], float, Optional[Dict[str, Any]]]:
        """
        Extrae QR de forma síncrona con múltiples estrategias.
        
        Args:
            image: Imagen a procesar
            enhance: Si aplicar mejoras
            validate_ine: Si validar formato INE
            
        Returns:
            Tupla con (datos_qr, confianza, bounding_box)
        """
        strategies = [
            ("original", image),
        ]
        
        if enhance:
            strategies.extend([
                ("enhanced", self._enhance_image(image)),
                ("binary", self._binarize_image(image)),
                ("contrast", self._enhance_contrast(image)),
                ("gaussian", self._apply_gaussian_blur(image))
            ])
        
        best_result = None
        best_confidence = 0.0
        best_bounding_box = None
        
        for strategy_name, processed_image in strategies:
            try:
                qr_codes = pyzbar.decode(processed_image)
                
                for qr in qr_codes:
                    qr_data = qr.data.decode('utf-8')
                    
                    # Validar si es QR de INE si se requiere
                    if validate_ine and not self._is_valid_ine_qr(qr_data):
                        continue
                    
                    # Calcular confianza basada en la calidad del QR
                    confidence = self._calculate_qr_confidence(qr, strategy_name)
                    
                    if confidence > best_confidence:
                        best_result = qr_data
                        best_confidence = confidence
                        best_bounding_box = {
                            'x': qr.rect.left,
                            'y': qr.rect.top,
                            'width': qr.rect.width,
                            'height': qr.rect.height,
                            'strategy': strategy_name
                        }
                
                # Si encontramos un resultado con alta confianza, no seguir buscando
                if best_confidence > 0.9:
                    break
                    
            except Exception:
                continue
        
        return best_result, best_confidence, best_bounding_box
    
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
        
        # Aplicar filtro Gaussiano para reducir ruido
        enhanced = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Binarización adaptativa
        enhanced = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return enhanced
    
    def _binarize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Binariza la imagen usando umbralización de Otsu.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen binarizada
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste de la imagen.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen con contraste mejorado
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Aplicar CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return enhanced
    
    def _apply_gaussian_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica desenfoque Gaussiano suave.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen con desenfoque aplicado
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        return cv2.GaussianBlur(gray, (5, 5), 0)
    
    def _calculate_qr_confidence(self, qr_code, strategy: str) -> float:
        """
        Calcula la confianza del código QR basada en varios factores.
        
        Args:
            qr_code: Objeto QR de pyzbar
            strategy: Estrategia usada para detectar el QR
            
        Returns:
            Confianza entre 0.0 y 1.0
        """
        base_confidence = 0.7  # Confianza base para QR detectado
        
        # Bonificación por estrategia
        strategy_bonus = {
            "original": 0.3,
            "enhanced": 0.2,
            "binary": 0.15,
            "contrast": 0.1,
            "gaussian": 0.05
        }.get(strategy, 0.0)
        
        # Bonificación por tamaño del QR (QRs más grandes suelen ser más confiables)
        size_bonus = min(0.1, (qr_code.rect.width * qr_code.rect.height) / 10000)
        
        # Bonificación por longitud de datos (QRs de INE tienen longitud específica)
        data_length = len(qr_code.data)
        length_bonus = 0.1 if 50 <= data_length <= 200 else 0.0
        
        total_confidence = min(1.0, base_confidence + strategy_bonus + size_bonus + length_bonus)
        return total_confidence
    
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
    
    def extract_qr_from_region(self, image: np.ndarray, x: int, y: int, width: int, height: int) -> Optional[str]:
        """
        Extrae QR de una región específica de la imagen.
        
        Args:
            image: Imagen fuente
            x, y: Coordenadas de la región
            width, height: Dimensiones de la región
            
        Returns:
            Datos del QR si se encuentra, None en caso contrario
        """
        try:
            # Extraer región
            region = image[y:y+height, x:x+width]
            
            # Usar el método principal con la región
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.extract_qr(region, enhance=True, validate_ine=True)
            )
            
            loop.close()
            
            return result.data if result.success else None
            
        except Exception:
            return None
    
    def is_available(self) -> bool:
        """
        Verifica si el servicio de QR está disponible.
        
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
        return "pyzbar"