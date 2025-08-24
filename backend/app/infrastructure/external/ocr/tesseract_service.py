#!/usr/bin/env python3
"""
Tesseract OCR Service Implementation

Implements OCR functionality using Tesseract engine.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
import numpy as np
from PIL import Image
import cv2

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

from .base import BaseOCRService, OCRResult
from ....core.exceptions.base import OCRProcessingError
from ....core.config.settings import get_settings


class TesseractOCRService(BaseOCRService):
    """
    Servicio de OCR usando Tesseract.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.tesseract_config = self.settings.image_processing.TESSERACT_CONFIG
        self.tesseract_lang = self.settings.image_processing.TESSERACT_LANG
        
        # Configurar path de Tesseract si es necesario (Windows)
        if not TESSERACT_AVAILABLE:
            raise OCRProcessingError(
                "Tesseract no está disponible. Instale pytesseract: pip install pytesseract",
                ocr_engine="tesseract"
            )
    
    async def extract_text(self, image: np.ndarray, **kwargs) -> OCRResult:
        """
        Extrae texto usando Tesseract OCR.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros adicionales
                - config: Configuración personalizada de Tesseract
                - lang: Idioma personalizado
                - preprocess: Si aplicar preprocesamiento (default: True)
                
        Returns:
            OCRResult con el texto extraído
        """
        start_time = time.time()
        
        try:
            # Obtener parámetros
            config = kwargs.get('config', self.tesseract_config)
            lang = kwargs.get('lang', self.tesseract_lang)
            preprocess = kwargs.get('preprocess', True)
            
            # Preprocesar imagen si es necesario
            processed_image = image
            if preprocess:
                processed_image = self._preprocess_image(image)
            
            # Convertir a PIL Image
            if len(processed_image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(processed_image)
            
            # Ejecutar OCR en un hilo separado para no bloquear
            loop = asyncio.get_event_loop()
            
            # Extraer texto
            text = await loop.run_in_executor(
                None,
                lambda: pytesseract.image_to_string(
                    pil_image,
                    lang=lang,
                    config=config
                ).strip()
            )
            
            # Obtener datos detallados con bounding boxes
            data = await loop.run_in_executor(
                None,
                lambda: pytesseract.image_to_data(
                    pil_image,
                    lang=lang,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )
            )
            
            # Procesar bounding boxes y calcular confianza
            bounding_boxes, avg_confidence = self._process_ocr_data(data)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                processing_time=processing_time,
                method_used="tesseract",
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                processing_time=processing_time,
                method_used="tesseract",
                success=False,
                error_message=str(e)
            )
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para mejorar el OCR.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen procesada
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Aplicar filtros para mejorar la calidad
        # Reducir ruido
        denoised = cv2.medianBlur(gray, 3)
        
        # Mejorar contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Binarización adaptativa
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def _process_ocr_data(self, data: Dict[str, List]) -> tuple[List[Dict[str, Any]], float]:
        """
        Procesa los datos de OCR para extraer bounding boxes y confianza.
        
        Args:
            data: Datos de pytesseract.image_to_data
            
        Returns:
            Tupla con (bounding_boxes, confianza_promedio)
        """
        bounding_boxes = []
        confidences = []
        
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            # Solo procesar palabras con confianza > 0
            confidence = int(data['conf'][i])
            if confidence > 0:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                text = data['text'][i].strip()
                
                if text:  # Solo incluir si hay texto
                    bounding_boxes.append({
                        'text': text,
                        'confidence': confidence,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'level': data['level'][i]
                    })
                    confidences.append(confidence)
        
        # Calcular confianza promedio
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return bounding_boxes, avg_confidence
    
    def is_available(self) -> bool:
        """
        Verifica si Tesseract está disponible.
        
        Returns:
            True si Tesseract está disponible
        """
        if not TESSERACT_AVAILABLE:
            return False
        
        try:
            # Intentar ejecutar Tesseract con una imagen de prueba
            test_image = np.ones((50, 200), dtype=np.uint8) * 255
            pil_image = Image.fromarray(test_image)
            pytesseract.image_to_string(pil_image)
            return True
        except Exception:
            return False
    
    def get_service_name(self) -> str:
        """
        Obtiene el nombre del servicio.
        
        Returns:
            Nombre del servicio
        """
        return "tesseract"
    
    def extract_specific_fields(self, image: np.ndarray, field_regions: Dict[str, Dict[str, int]]) -> Dict[str, str]:
        """
        Extrae campos específicos de regiones definidas en la imagen.
        
        Args:
            image: Imagen fuente
            field_regions: Diccionario con regiones por campo
                          {"campo": {"x": int, "y": int, "width": int, "height": int}}
                          
        Returns:
            Diccionario con los textos extraídos por campo
        """
        results = {}
        
        for field_name, region in field_regions.items():
            try:
                # Extraer región
                x, y, w, h = region['x'], region['y'], region['width'], region['height']
                roi = image[y:y+h, x:x+w]
                
                # Preprocesar región
                processed_roi = self._preprocess_image(roi)
                
                # Convertir a PIL
                if len(processed_roi.shape) == 3:
                    pil_roi = Image.fromarray(cv2.cvtColor(processed_roi, cv2.COLOR_BGR2RGB))
                else:
                    pil_roi = Image.fromarray(processed_roi)
                
                # Extraer texto
                text = pytesseract.image_to_string(
                    pil_roi,
                    lang=self.tesseract_lang,
                    config=self.tesseract_config
                ).strip()
                
                results[field_name] = text
                
            except Exception as e:
                results[field_name] = ""
        
        return results