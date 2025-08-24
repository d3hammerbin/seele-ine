#!/usr/bin/env python3
"""
Base OCR Service Interface

Defines the contract for OCR services in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from PIL import Image


@dataclass
class OCRResult:
    """
    Resultado del procesamiento OCR.
    """
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    processing_time: float
    method_used: str
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_boxes": self.bounding_boxes,
            "processing_time": self.processing_time,
            "method_used": self.method_used,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class QRResult:
    """
    Resultado del procesamiento de códigos QR.
    """
    data: Optional[str]
    qr_type: Optional[str]
    confidence: float
    processing_time: float
    method_used: str
    success: bool = True
    error_message: Optional[str] = None
    bounding_box: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            "data": self.data,
            "qr_type": self.qr_type,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "method_used": self.method_used,
            "success": self.success,
            "error_message": self.error_message,
            "bounding_box": self.bounding_box
        }


class BaseOCRService(ABC):
    """
    Interfaz base para servicios de OCR.
    """
    
    @abstractmethod
    async def extract_text(self, image: np.ndarray, **kwargs) -> OCRResult:
        """
        Extrae texto de una imagen.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros adicionales específicos del servicio
            
        Returns:
            OCRResult con el texto extraído y metadatos
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el servicio está disponible.
        
        Returns:
            True si el servicio está disponible
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        Obtiene el nombre del servicio.
        
        Returns:
            Nombre del servicio
        """
        pass


class BaseQRService(ABC):
    """
    Interfaz base para servicios de extracción de códigos QR.
    """
    
    @abstractmethod
    async def extract_qr(self, image: np.ndarray, **kwargs) -> QRResult:
        """
        Extrae códigos QR de una imagen.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros adicionales específicos del servicio
            
        Returns:
            QRResult con los datos del QR y metadatos
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el servicio está disponible.
        
        Returns:
            True si el servicio está disponible
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        Obtiene el nombre del servicio.
        
        Returns:
            Nombre del servicio
        """
        pass


class BaseImageProcessor(ABC):
    """
    Interfaz base para procesadores de imágenes.
    """
    
    @abstractmethod
    def preprocess_image(self, image: np.ndarray, **kwargs) -> np.ndarray:
        """
        Preprocesa una imagen para mejorar la extracción.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros de procesamiento
            
        Returns:
            Imagen procesada
        """
        pass
    
    @abstractmethod
    def validate_image_dimensions(self, image: np.ndarray, expected_width: int, expected_height: int, tolerance: float = 0.1) -> bool:
        """
        Valida las dimensiones de una imagen.
        
        Args:
            image: Imagen a validar
            expected_width: Ancho esperado
            expected_height: Alto esperado
            tolerance: Tolerancia permitida (0.1 = 10%)
            
        Returns:
            True si las dimensiones son válidas
        """
        pass
    
    @abstractmethod
    def extract_regions(self, image: np.ndarray, regions: List[Dict[str, Any]]) -> List[np.ndarray]:
        """
        Extrae regiones específicas de una imagen.
        
        Args:
            image: Imagen fuente
            regions: Lista de regiones a extraer con coordenadas
            
        Returns:
            Lista de imágenes de las regiones extraídas
        """
        pass