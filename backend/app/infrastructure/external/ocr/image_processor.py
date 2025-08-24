#!/usr/bin/env python3
"""
Image Processing Service

Implements image preprocessing and validation using OpenCV.
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from PIL import Image
import io

from .base import BaseImageProcessor
from ....core.config.settings import get_settings
from ....core.exceptions.base import ImageValidationError


class OpenCVImageProcessor(BaseImageProcessor):
    """
    Procesador de imágenes usando OpenCV.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.ine_width = self.settings.image_processing.INE_WIDTH
        self.ine_height = self.settings.image_processing.INE_HEIGHT
        self.ine_tolerance = self.settings.image_processing.INE_TOLERANCE
        self.max_image_size = self.settings.image_processing.MAX_IMAGE_SIZE_MB * 1024 * 1024
        self.allowed_formats = self.settings.image_processing.ALLOWED_IMAGE_FORMATS
    
    def preprocess_image(self, image: np.ndarray, **kwargs) -> np.ndarray:
        """
        Preprocesa una imagen para mejorar la extracción.
        
        Args:
            image: Imagen como array de NumPy
            **kwargs: Parámetros de procesamiento
                - resize: Redimensionar a tamaño específico (width, height)
                - denoise: Aplicar filtro de ruido (default: True)
                - enhance_contrast: Mejorar contraste (default: True)
                - normalize: Normalizar valores (default: True)
                - rotation_correction: Corregir rotación (default: False)
                
        Returns:
            Imagen procesada
        """
        processed = image.copy()
        
        # Redimensionar si se especifica
        resize = kwargs.get('resize')
        if resize:
            width, height = resize
            processed = cv2.resize(processed, (width, height), interpolation=cv2.INTER_LANCZOS4)
        
        # Aplicar filtro de ruido
        if kwargs.get('denoise', True):
            processed = self._apply_denoising(processed)
        
        # Mejorar contraste
        if kwargs.get('enhance_contrast', True):
            processed = self._enhance_contrast(processed)
        
        # Normalizar valores
        if kwargs.get('normalize', True):
            processed = self._normalize_image(processed)
        
        # Corregir rotación si se requiere
        if kwargs.get('rotation_correction', False):
            processed = self._correct_rotation(processed)
        
        return processed
    
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
        height, width = image.shape[:2]
        
        # Calcular rangos permitidos
        width_min = expected_width * (1 - tolerance)
        width_max = expected_width * (1 + tolerance)
        height_min = expected_height * (1 - tolerance)
        height_max = expected_height * (1 + tolerance)
        
        return (width_min <= width <= width_max and 
                height_min <= height <= height_max)
    
    def extract_regions(self, image: np.ndarray, regions: List[Dict[str, Any]]) -> List[np.ndarray]:
        """
        Extrae regiones específicas de una imagen.
        
        Args:
            image: Imagen fuente
            regions: Lista de regiones a extraer
                    [{"name": str, "x": int, "y": int, "width": int, "height": int}]
                    
        Returns:
            Lista de imágenes de las regiones extraídas
        """
        extracted_regions = []
        
        for region in regions:
            try:
                x = region['x']
                y = region['y']
                width = region['width']
                height = region['height']
                
                # Validar que la región esté dentro de la imagen
                img_height, img_width = image.shape[:2]
                if (x >= 0 and y >= 0 and 
                    x + width <= img_width and 
                    y + height <= img_height):
                    
                    roi = image[y:y+height, x:x+width]
                    extracted_regions.append(roi)
                else:
                    # Región inválida, agregar imagen vacía
                    extracted_regions.append(np.zeros((height, width, 3), dtype=np.uint8))
                    
            except Exception:
                # Error al extraer región, agregar imagen vacía
                extracted_regions.append(np.zeros((100, 100, 3), dtype=np.uint8))
        
        return extracted_regions
    
    def validate_ine_credential(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Valida si una imagen corresponde a una credencial INE válida.
        
        Args:
            image: Imagen a validar
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            'is_valid': False,
            'dimensions_valid': False,
            'aspect_ratio_valid': False,
            'quality_score': 0.0,
            'detected_type': None,
            'issues': []
        }
        
        try:
            height, width = image.shape[:2]
            
            # Validar dimensiones
            dimensions_valid = self.validate_image_dimensions(
                image, self.ine_width, self.ine_height, self.ine_tolerance
            )
            validation_result['dimensions_valid'] = dimensions_valid
            
            if not dimensions_valid:
                validation_result['issues'].append(
                    f"Dimensiones inválidas: {width}x{height}, esperado: {self.ine_width}x{self.ine_height}"
                )
            
            # Validar aspect ratio
            expected_ratio = self.ine_width / self.ine_height
            actual_ratio = width / height
            ratio_diff = abs(expected_ratio - actual_ratio) / expected_ratio
            
            aspect_ratio_valid = ratio_diff <= self.ine_tolerance
            validation_result['aspect_ratio_valid'] = aspect_ratio_valid
            
            if not aspect_ratio_valid:
                validation_result['issues'].append(
                    f"Aspect ratio inválido: {actual_ratio:.3f}, esperado: {expected_ratio:.3f}"
                )
            
            # Calcular score de calidad
            quality_score = self._calculate_image_quality(image)
            validation_result['quality_score'] = quality_score
            
            if quality_score < 0.5:
                validation_result['issues'].append(
                    f"Calidad de imagen baja: {quality_score:.2f}"
                )
            
            # Detectar tipo de credencial (básico)
            detected_type = self._detect_credential_type(image)
            validation_result['detected_type'] = detected_type
            
            # Determinar si es válida
            validation_result['is_valid'] = (
                dimensions_valid and 
                aspect_ratio_valid and 
                quality_score >= 0.5
            )
            
        except Exception as e:
            validation_result['issues'].append(f"Error en validación: {str(e)}")
        
        return validation_result
    
    def _apply_denoising(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica filtros de reducción de ruido.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen sin ruido
        """
        if len(image.shape) == 3:
            # Imagen en color
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            # Imagen en escala de grises
            return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste de la imagen.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen con contraste mejorado
        """
        if len(image.shape) == 3:
            # Convertir a LAB para mejorar solo la luminancia
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Aplicar CLAHE solo al canal L
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Recombinar canales
            enhanced_lab = cv2.merge([l, a, b])
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        else:
            # Imagen en escala de grises
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
    
    def _normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normaliza los valores de la imagen.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen normalizada
        """
        return cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
    
    def _correct_rotation(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige la rotación de la imagen usando detección de líneas.
        
        Args:
            image: Imagen original
            
        Returns:
            Imagen con rotación corregida
        """
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Detectar bordes
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detectar líneas usando transformada de Hough
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calcular ángulo promedio de las líneas horizontales
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = theta * 180 / np.pi
                    # Considerar solo líneas aproximadamente horizontales
                    if abs(angle - 90) < 45:
                        angles.append(angle - 90)
                
                if angles:
                    # Usar la mediana para ser robusto a outliers
                    rotation_angle = np.median(angles)
                    
                    # Solo corregir si la rotación es significativa
                    if abs(rotation_angle) > 0.5:
                        height, width = image.shape[:2]
                        center = (width // 2, height // 2)
                        
                        # Crear matriz de rotación
                        rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
                        
                        # Aplicar rotación
                        return cv2.warpAffine(image, rotation_matrix, (width, height), 
                                            flags=cv2.INTER_CUBIC, 
                                            borderMode=cv2.BORDER_REPLICATE)
            
        except Exception:
            pass
        
        return image
    
    def _calculate_image_quality(self, image: np.ndarray) -> float:
        """
        Calcula un score de calidad de la imagen.
        
        Args:
            image: Imagen a evaluar
            
        Returns:
            Score de calidad entre 0.0 y 1.0
        """
        try:
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Calcular varianza de Laplaciano (medida de nitidez)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalizar el score (valores típicos entre 0 y 1000)
            sharpness_score = min(1.0, laplacian_var / 500.0)
            
            # Calcular contraste usando desviación estándar
            contrast_score = min(1.0, gray.std() / 128.0)
            
            # Calcular brillo (evitar imágenes muy oscuras o muy claras)
            brightness = gray.mean() / 255.0
            brightness_score = 1.0 - abs(brightness - 0.5) * 2
            
            # Score combinado
            quality_score = (sharpness_score * 0.5 + 
                           contrast_score * 0.3 + 
                           brightness_score * 0.2)
            
            return quality_score
            
        except Exception:
            return 0.0
    
    def _detect_credential_type(self, image: np.ndarray) -> Optional[str]:
        """
        Detecta el tipo de credencial INE basado en características visuales.
        
        Args:
            image: Imagen de la credencial
            
        Returns:
            Tipo detectado o None si no se puede determinar
        """
        try:
            height, width = image.shape[:2]
            
            # Región donde típicamente está el QR (lado derecho)
            qr_region_x = int(width * 0.7)  # 70% del ancho
            qr_region = image[:, qr_region_x:]
            
            # Convertir a escala de grises
            if len(qr_region.shape) == 3:
                gray_qr = cv2.cvtColor(qr_region, cv2.COLOR_BGR2GRAY)
            else:
                gray_qr = qr_region.copy()
            
            # Buscar patrones de QR (cuadrados negros)
            # Aplicar umbralización
            _, binary = cv2.threshold(gray_qr, 127, 255, cv2.THRESH_BINARY)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Contar contornos cuadrados pequeños (característicos de QR)
            square_count = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 10000:  # Área razonable para elementos de QR
                    # Aproximar contorno
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Si tiene 4 vértices, podría ser un cuadrado
                    if len(approx) == 4:
                        square_count += 1
            
            # Si hay muchos cuadrados pequeños, probablemente hay QR
            if square_count > 10:
                return "type_1_or_2"  # Credenciales con QR
            else:
                return "type_3"  # Credencial sin QR
                
        except Exception:
            return None
    
    def create_thumbnail(self, image: np.ndarray, max_size: Tuple[int, int] = (200, 200)) -> np.ndarray:
        """
        Crea una miniatura de la imagen.
        
        Args:
            image: Imagen original
            max_size: Tamaño máximo (width, height)
            
        Returns:
            Imagen miniatura
        """
        height, width = image.shape[:2]
        max_width, max_height = max_size
        
        # Calcular factor de escala manteniendo aspect ratio
        scale = min(max_width / width, max_height / height)
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image.copy()