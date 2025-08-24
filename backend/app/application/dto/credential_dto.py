#!/usr/bin/env python3
"""
Credential Data Transfer Objects (DTOs)

Defines request and response structures for credential processing operations
including upload, validation, classification, extraction, and processing.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from fastapi import UploadFile

from ...domain.entities.credential import CredentialType, ProcessingStatus, ExtractionMethod, Gender


# Request Models

class CredentialUploadRequest(BaseModel):
    """Request model for credential upload."""
    
    credential_type: Optional[CredentialType] = Field(
        None,
        description="Type of credential (auto-detected if not provided)",
        example="tipo3"
    )
    extract_qr: bool = Field(
        default=True,
        description="Whether to extract QR code from credential"
    )
    preferred_ai_provider: Optional[str] = Field(
        None,
        description="Preferred AI provider for extraction",
        example="openai"
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.HYBRID,
        description="Extraction method to use"
    )
    validate_dimensions: bool = Field(
        default=True,
        description="Whether to validate image dimensions (790x490px)"
    )


class CredentialValidationRequest(BaseModel):
    """Request model for credential validation."""
    
    check_dimensions: bool = Field(
        default=True,
        description="Check if image has correct dimensions (790x490px)"
    )
    check_format: bool = Field(
        default=True,
        description="Check if image format is supported"
    )
    check_quality: bool = Field(
        default=True,
        description="Check image quality for OCR processing"
    )


class CredentialClassificationRequest(BaseModel):
    """Request model for credential classification."""
    
    use_ai_fallback: bool = Field(
        default=True,
        description="Use AI providers if local classification fails"
    )


class CredentialExtractionRequest(BaseModel):
    """Request model for credential data extraction."""
    
    credential_type: CredentialType = Field(
        ...,
        description="Type of credential to extract data from"
    )
    extract_front: bool = Field(
        default=True,
        description="Extract data from front of credential"
    )
    extract_back: bool = Field(
        default=True,
        description="Extract data from back of credential"
    )
    extract_qr: bool = Field(
        default=True,
        description="Extract QR code data"
    )
    preferred_ai_provider: Optional[str] = Field(
        None,
        description="Preferred AI provider for extraction"
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.HYBRID,
        description="Extraction method to use"
    )


class CredentialProcessRequest(BaseModel):
    """Request model for complete credential processing."""
    
    credential_type: Optional[CredentialType] = Field(
        None,
        description="Type of credential (auto-detected if not provided)"
    )
    extract_qr: bool = Field(
        default=True,
        description="Whether to extract QR code from credential"
    )
    validate_dimensions: bool = Field(
        default=True,
        description="Whether to validate image dimensions"
    )
    preferred_ai_provider: Optional[str] = Field(
        None,
        description="Preferred AI provider for extraction"
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.HYBRID,
        description="Extraction method to use"
    )


class OCRExtractionRequest(BaseModel):
    """Request model for OCR data extraction."""
    
    side: str = Field(
        ...,
        description="Side of credential to process (front/back)",
        pattern="^(front|back)$"
    )
    credential_type: CredentialType = Field(
        ...,
        description="Type of credential"
    )
    use_ai_fallback: bool = Field(
        default=True,
        description="Use AI providers if OCR fails"
    )


class QRExtractionRequest(BaseModel):
    """Request model for QR code extraction."""
    
    credential_type: CredentialType = Field(
        ...,
        description="Type of credential"
    )
    use_enhanced_detection: bool = Field(
        default=True,
        description="Use enhanced QR detection algorithms"
    )


# Response Models

class PersonalInfoResponse(BaseModel):
    """Response model for personal information."""
    
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    curp: Optional[str] = None
    fecha_nacimiento: Optional[datetime] = None
    sexo: Optional[Gender] = None
    domicilio: Optional[str] = None
    clave_elector: Optional[str] = None
    seccion: Optional[str] = None
    localidad: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    vigencia: Optional[datetime] = None
    emision: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProcessingMetricsResponse(BaseModel):
    """Response model for processing metrics."""
    
    ocr_confidence: float = 0.0
    qr_detected: bool = False
    qr_confidence: float = 0.0
    ai_confidence: float = 0.0
    processing_time: float = 0.0
    retry_count: int = 0
    validation_score: float = 0.0
    
    class Config:
        from_attributes = True


class QualityScoreResponse(BaseModel):
    """Response model for quality score."""
    
    overall_score: float = 0.0
    ocr_quality: float = 0.0
    data_completeness: float = 0.0
    confidence_score: float = 0.0
    
    class Config:
        from_attributes = True


class CredentialResponse(BaseModel):
    """Response model for credential information."""
    
    id: UUID
    user_id: UUID
    credential_type: CredentialType
    processing_status: ProcessingStatus
    extraction_method: Optional[ExtractionMethod]
    original_filename: str
    file_size: int
    file_hash: str
    mime_type: str
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_duration: Optional[float]
    personal_info: Optional[PersonalInfoResponse]
    processing_metrics: ProcessingMetricsResponse
    quality_score: Optional[QualityScoreResponse]
    error_message: Optional[str]
    error_code: Optional[str]
    processing_logs: List[str]
    is_valid: Optional[bool]
    validation_errors: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CredentialUploadResponse(BaseModel):
    """Response model for credential upload."""
    
    credential: CredentialResponse
    processing_job_id: UUID
    message: str = Field(
        default="Credential uploaded successfully and queued for processing",
        description="Success message"
    )
    estimated_processing_time: int = Field(
        ...,
        description="Estimated processing time in seconds"
    )


class CredentialValidationResponse(BaseModel):
    """Response model for credential validation."""
    
    is_valid: bool
    validation_errors: List[str]
    image_dimensions: Dict[str, int]
    file_size: int
    mime_type: str
    quality_score: float
    message: str


class CredentialClassificationResponse(BaseModel):
    """Response model for credential classification."""
    
    credential_type: CredentialType
    confidence: float
    detection_method: str
    alternative_types: List[Dict[str, Union[str, float]]]
    message: str


class OCRExtractionResponse(BaseModel):
    """Response model for OCR extraction."""
    
    extracted_text: str
    confidence: float
    extraction_method: str
    processing_time: float
    structured_data: Dict[str, Any]
    message: str


class QRExtractionResponse(BaseModel):
    """Response model for QR extraction."""
    
    qr_data: str
    is_valid_ine_qr: bool
    confidence: float
    extraction_method: str
    processing_time: float
    message: str


class CredentialProcessResponse(BaseModel):
    """Response model for complete credential processing."""
    
    credential: CredentialResponse
    processing_summary: Dict[str, Any]
    cost_breakdown: Dict[str, float]
    message: str = Field(
        default="Credential processed successfully",
        description="Success message"
    )


class CredentialHistoryResponse(BaseModel):
    """Response model for credential processing history."""
    
    credentials: List[CredentialResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    total_pages: int


class CredentialStatsResponse(BaseModel):
    """Response model for credential statistics."""
    
    total_processed: int
    successful_extractions: int
    failed_extractions: int
    average_processing_time: float
    by_credential_type: Dict[str, int]
    by_extraction_method: Dict[str, int]
    by_status: Dict[str, int]
    cost_summary: Dict[str, float]


class CredentialRetryRequest(BaseModel):
    """Request model for credential retry."""
    
    extraction_method: Optional[ExtractionMethod] = Field(
        None,
        description="New extraction method to try"
    )
    preferred_ai_provider: Optional[str] = Field(
        None,
        description="Preferred AI provider for retry"
    )


class CredentialRetryResponse(BaseModel):
    """Response model for credential retry."""
    
    processing_job_id: UUID
    message: str = Field(
        default="Credential queued for retry processing",
        description="Success message"
    )
    estimated_processing_time: int = Field(
        ...,
        description="Estimated processing time in seconds"
    )