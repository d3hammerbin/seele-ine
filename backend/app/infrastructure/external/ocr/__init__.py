#!/usr/bin/env python3
"""
OCR Services Module

Provides OCR, QR extraction, and image processing services.
"""

from .base import BaseOCRService, BaseQRService, BaseImageProcessor, OCRResult, QRResult
from .tesseract_service import TesseractOCRService
from .qr_service import QRExtractionService
from .image_processor import OpenCVImageProcessor
from .qr_extractor_pro import QRExtractorProService
from .ocr_factory import OCRServiceFactory, get_ocr_factory

__all__ = [
    # Base classes
    'BaseOCRService',
    'BaseQRService', 
    'BaseImageProcessor',
    'OCRResult',
    'QRResult',
    
    # Service implementations
    'TesseractOCRService',
    'QRExtractionService',
    'OpenCVImageProcessor',
    'QRExtractorProService',
    
    # Factory
    'OCRServiceFactory',
    'get_ocr_factory'
]