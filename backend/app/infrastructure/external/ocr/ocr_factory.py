#!/usr/bin/env python3
"""
OCR Factory Service

Provides a unified interface for managing OCR, QR, and image processing services.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
import numpy as np
from PIL import Image
import cv2

from .base import BaseOCRService, BaseQRService, BaseImageProcessor, OCRResult, QRResult
from .tesseract_service import TesseractOCRService
from .qr_service import QRExtractionService
from .image_processor import OpenCVImageProcessor
from .qr_extractor_pro import QRExtractorProService
from ....core.config.settings import get_settings
from ....core.exceptions.base import OCRProcessingError, QRProcessingError
from ....domain.entities.credential import ExtractionMethod


class OCRServiceFactory:
    """
    Factory para gestionar servicios de OCR, QR e imagen.
    Proporciona una interfaz unificada para todos los servicios de procesamiento.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._ocr_services: Dict[str, BaseOCRService] = {}
        self._qr_services: Dict[str, BaseQRService] = {}
        self._image_processor: Optional[BaseImageProcessor] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Inicializa todos los servicios disponibles.
        """
        if self._initialized:
            return
            
        try:
            # Inicializar procesador de imágenes
            self._image_processor = OpenCVImageProcessor()
            
            # Inicializar servicios OCR
            await self._initialize_ocr_services()
            
            # Inicializar servicios QR
            await self._initialize_qr_services()
            
            self._initialized = True
            
        except Exception as e:
            raise OCRProcessingError(
                f"Error inicializando servicios OCR: {e}",
                ocr_issue="initialization_failed"
            )
    
    async def _initialize_ocr_services(self) -> None:
        """
        Inicializa los servicios de OCR disponibles.
        """
        # Tesseract OCR
        try:
            tesseract_service = TesseractOCRService(
                language=self.settings.image_processing.tesseract_language,
                config=self.settings.image_processing.tesseract_config
            )
            if tesseract_service.is_available():
                self._ocr_services['tesseract'] = tesseract_service
        except Exception as e:
            print(f"Warning: No se pudo inicializar Tesseract: {e}")
    
    async def _initialize_qr_services(self) -> None:
        """
        Inicializa los servicios de QR disponibles.
        """
        # Servicio QR básico
        try:
            qr_service = QRExtractionService(
                timeout=self.settings.image_processing.qr_timeout,
                max_attempts=self.settings.image_processing.qr_max_attempts
            )
            if qr_service.is_available():
                self._qr_services['basic'] = qr_service
        except Exception as e:
            print(f"Warning: No se pudo inicializar servicio QR básico: {e}")
        
        # QR Extractor Pro
        try:
            qr_pro_service = QRExtractorProService(
                api_key=getattr(self.settings.ai_providers, 'OPENAI_API_KEY', None),
                debug=False
            )
            if qr_pro_service.is_available():
                self._qr_services['pro'] = qr_pro_service
        except Exception as e:
            print(f"Warning: No se pudo inicializar QR Extractor Pro: {e}")
    
    async def extract_text(
        self,
        image: Union[np.ndarray, Image.Image, bytes],
        method: ExtractionMethod = ExtractionMethod.OCR_TESSERACT,
        **kwargs
    ) -> OCRResult:
        """
        Extrae texto de una imagen usando el método especificado.
        
        Args:
            image: Imagen a procesar
            method: Método de extracción a usar
            **kwargs: Parámetros adicionales
            
        Returns:
            OCRResult con el texto extraído
        """
        await self.initialize()
        
        # Convertir imagen a formato numpy
        image_array = await self._prepare_image(image)
        
        # Seleccionar servicio OCR
        service_name = self._get_ocr_service_name(method)
        if service_name not in self._ocr_services:
            raise OCRProcessingError(
                f"Servicio OCR '{service_name}' no disponible",
                ocr_issue="service_unavailable"
            )
        
        service = self._ocr_services[service_name]
        return await service.extract_text(image_array, **kwargs)
    
    async def extract_qr(
        self,
        image: Union[np.ndarray, Image.Image, bytes],
        method: ExtractionMethod = ExtractionMethod.QR_PYZBAR,
        **kwargs
    ) -> QRResult:
        """
        Extrae códigos QR de una imagen usando el método especificado.
        
        Args:
            image: Imagen a procesar
            method: Método de extracción a usar
            **kwargs: Parámetros adicionales
            
        Returns:
            QRResult con los datos del QR
        """
        await self.initialize()
        
        # Convertir imagen a formato numpy
        image_array = await self._prepare_image(image)
        
        # Seleccionar servicio QR
        service_name = self._get_qr_service_name(method)
        if service_name not in self._qr_services:
            raise QRProcessingError(
                f"Servicio QR '{service_name}' no disponible",
                qr_issue="service_unavailable"
            )
        
        service = self._qr_services[service_name]
        return await service.extract_qr(image_array, **kwargs)
    
    async def extract_with_fallback(
        self,
        image: Union[np.ndarray, Image.Image, bytes],
        extraction_type: str = "qr",
        **kwargs
    ) -> Union[OCRResult, QRResult]:
        """
        Extrae datos usando múltiples métodos con fallback automático.
        
        Args:
            image: Imagen a procesar
            extraction_type: Tipo de extracción ("ocr" o "qr")
            **kwargs: Parámetros adicionales
            
        Returns:
            Resultado de la extracción exitosa
        """
        await self.initialize()
        
        if extraction_type == "qr":
            # Intentar métodos QR en orden de preferencia
            methods = [
                ExtractionMethod.QR_EXTRACTOR_PRO,
                ExtractionMethod.QR_PYZBAR,
            ExtractionMethod.QR_OPENCV
            ]
            
            for method in methods:
                try:
                    result = await self.extract_qr(image, method, **kwargs)
                    if result.success and result.data:
                        return result
                except Exception as e:
                    print(f"Warning: Método {method} falló: {e}")
                    continue
            
            # Si todos fallan, retornar resultado fallido
            return QRResult(
                data=None,
                qr_type=None,
                confidence=0.0,
                processing_time=0.0,
                method_used="fallback_failed",
                success=False,
                error_message="Todos los métodos QR fallaron"
            )
        
        elif extraction_type == "ocr":
            # Intentar métodos OCR
            methods = [
                ExtractionMethod.OCR_TESSERACT,
            ExtractionMethod.OCR_GOOGLE_VISION
            ]
            
            for method in methods:
                try:
                    result = await self.extract_text(image, method, **kwargs)
                    if result.success and result.text:
                        return result
                except Exception as e:
                    print(f"Warning: Método {method} falló: {e}")
                    continue
            
            # Si todos fallan, retornar resultado fallido
            return OCRResult(
                text="",
                confidence=0.0,
                processing_time=0.0,
                method_used="fallback_failed",
                success=False,
                error_message="Todos los métodos OCR fallaron"
            )
        
        else:
            raise ValueError(f"Tipo de extracción no válido: {extraction_type}")
    
    async def process_image(
        self,
        image: Union[np.ndarray, Image.Image, bytes],
        operation: str,
        **kwargs
    ) -> np.ndarray:
        """
        Procesa una imagen usando el procesador de imágenes.
        
        Args:
            image: Imagen a procesar
            operation: Operación a realizar
            **kwargs: Parámetros adicionales
            
        Returns:
            Imagen procesada
        """
        await self.initialize()
        
        if not self._image_processor:
            raise OCRProcessingError(
                "Procesador de imágenes no disponible",
                ocr_issue="processor_unavailable"
            )
        
        # Convertir imagen a formato numpy
        image_array = await self._prepare_image(image)
        
        # Ejecutar operación
        if operation == "validate":
            return await self._image_processor.validate_image(image_array, **kwargs)
        elif operation == "preprocess":
            return await self._image_processor.preprocess_image(image_array, **kwargs)
        elif operation == "enhance":
            return await self._image_processor.enhance_image(image_array, **kwargs)
        elif operation == "extract_region":
            return await self._image_processor.extract_region(image_array, **kwargs)
        else:
            raise ValueError(f"Operación no válida: {operation}")
    
    async def _prepare_image(self, image: Union[np.ndarray, Image.Image, bytes]) -> np.ndarray:
        """
        Convierte la imagen al formato numpy array.
        
        Args:
            image: Imagen en cualquier formato soportado
            
        Returns:
            Imagen como numpy array
        """
        if isinstance(image, np.ndarray):
            return image
        elif isinstance(image, Image.Image):
            return np.array(image)
        elif isinstance(image, bytes):
            # Decodificar bytes a imagen
            nparr = np.frombuffer(image, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            raise ValueError(f"Formato de imagen no soportado: {type(image)}")
    
    def _get_ocr_service_name(self, method: ExtractionMethod) -> str:
        """
        Obtiene el nombre del servicio OCR para el método dado.
        
        Args:
            method: Método de extracción
            
        Returns:
            Nombre del servicio
        """
        mapping = {
            ExtractionMethod.OCR_TESSERACT: "tesseract",
            ExtractionMethod.OCR_GOOGLE_VISION: "google_vision"
        }
        return mapping.get(method, "tesseract")
    
    def _get_qr_service_name(self, method: ExtractionMethod) -> str:
        """
        Obtiene el nombre del servicio QR para el método dado.
        
        Args:
            method: Método de extracción
            
        Returns:
            Nombre del servicio
        """
        mapping = {
            ExtractionMethod.QR_PYZBAR: "basic",
            ExtractionMethod.QR_OPENCV: "basic",
            ExtractionMethod.QR_EXTRACTOR_PRO: "pro"
        }
        return mapping.get(method, "basic")
    
    def get_available_services(self) -> Dict[str, List[str]]:
        """
        Obtiene la lista de servicios disponibles.
        
        Returns:
            Diccionario con servicios disponibles por tipo
        """
        return {
            "ocr": list(self._ocr_services.keys()),
            "qr": list(self._qr_services.keys()),
            "image_processor": ["opencv"] if self._image_processor else []
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de todos los servicios.
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {}
        
        # Estadísticas de servicios QR
        for name, service in self._qr_services.items():
            if hasattr(service, 'get_stats'):
                stats[f"qr_{name}"] = service.get_stats()
        
        return stats


# Instancia global del factory
ocr_factory = OCRServiceFactory()


async def get_ocr_factory() -> OCRServiceFactory:
    """
    Obtiene la instancia del factory OCR.
    
    Returns:
        Instancia inicializada del factory
    """
    await ocr_factory.initialize()
    return ocr_factory