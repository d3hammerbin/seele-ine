#!/usr/bin/env python3
"""
Credential Database Model

SQLAlchemy model for credential data persistence.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship

from ..base import BaseModel
from ....domain.entities.credential import (
    CredentialType, ProcessingStatus, ExtractionMethod, Gender
)


class CredentialModel(BaseModel):
    """Credential database model."""
    
    __tablename__ = "credentials"
    
    # Foreign key to user
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic credential information
    credential_type = Column(
        SQLEnum(CredentialType),
        nullable=False,
        default=CredentialType.TIPO3,
        index=True
    )
    
    processing_status = Column(
        SQLEnum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )
    
    extraction_method = Column(
        SQLEnum(ExtractionMethod),
        nullable=True,
        index=True
    )
    
    # File information
    original_filename = Column(
        String(255),
        nullable=False
    )
    
    file_path = Column(
        String(500),
        nullable=False
    )
    
    file_size = Column(
        Integer,
        nullable=False
    )
    
    file_hash = Column(
        String(64),  # SHA-256 hash
        nullable=False,
        index=True
    )
    
    mime_type = Column(
        String(100),
        nullable=False
    )
    
    # Processing information
    processing_started_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    processing_completed_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    processing_duration = Column(
        Float,  # Duration in seconds
        nullable=True
    )
    
    # Extracted personal information (stored as JSON)
    personal_info = Column(
        JSON,
        nullable=True
    )
    
    # Processing metrics (stored as JSON)
    processing_metrics = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Quality score
    quality_score = Column(
        Float,
        nullable=True
    )
    
    # Error information
    error_message = Column(
        Text,
        nullable=True
    )
    
    error_code = Column(
        String(50),
        nullable=True
    )
    
    error_details = Column(
        JSON,
        nullable=True
    )
    
    # Processing logs (stored as JSON array)
    processing_logs = Column(
        JSON,
        nullable=False,
        default=list
    )
    
    # Validation flags
    is_valid = Column(
        Boolean,
        nullable=True
    )
    
    validation_errors = Column(
        JSON,
        nullable=True
    )
    
    # Soft delete
    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Additional metadata
    extra_metadata = Column(
        JSON,
        nullable=False,
        default=dict
    )
    
    # Relationships
    user = relationship(
        "UserModel",
        back_populates="credentials"
    )
    
    processing_jobs = relationship(
        "ProcessingJobModel",
        back_populates="credential",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def to_domain_entity(self):
        """Convert database model to domain entity.
        
        Returns:
            Credential domain entity
        """
        from ....domain.entities.credential import (
            Credential, PersonalInfo, ProcessingMetrics, QualityScore
        )
        
        # Convert personal info
        personal_info = None
        if self.personal_info:
            info_data = self.personal_info
            personal_info = PersonalInfo(
                nombre=info_data.get('nombre', ''),
                apellido_paterno=info_data.get('apellido_paterno', ''),
                apellido_materno=info_data.get('apellido_materno', ''),
                curp=info_data.get('curp', ''),
                fecha_nacimiento=datetime.fromisoformat(info_data['fecha_nacimiento']) if info_data.get('fecha_nacimiento') else None,
                sexo=Gender(info_data['sexo']) if info_data.get('sexo') else None,
                domicilio=info_data.get('domicilio', ''),
                clave_elector=info_data.get('clave_elector', ''),
                seccion=info_data.get('seccion', ''),
                localidad=info_data.get('localidad', ''),
                municipio=info_data.get('municipio', ''),
                estado=info_data.get('estado', ''),
                vigencia=datetime.fromisoformat(info_data['vigencia']) if info_data.get('vigencia') else None,
                emision=datetime.fromisoformat(info_data['emision']) if info_data.get('emision') else None
            )
        
        # Convert processing metrics
        metrics_data = self.processing_metrics or {}
        processing_metrics = ProcessingMetrics(
            ocr_confidence=metrics_data.get('ocr_confidence', 0.0),
            qr_detected=metrics_data.get('qr_detected', False),
            qr_confidence=metrics_data.get('qr_confidence', 0.0),
            ai_confidence=metrics_data.get('ai_confidence', 0.0),
            processing_time=metrics_data.get('processing_time', 0.0),
            retry_count=metrics_data.get('retry_count', 0),
            validation_score=metrics_data.get('validation_score', 0.0)
        )
        
        # Convert quality score
        quality_score_obj = None
        if self.quality_score is not None:
            quality_score_obj = QualityScore(
                overall_score=self.quality_score,
                ocr_quality=metrics_data.get('ocr_quality', 0.0),
                data_completeness=metrics_data.get('data_completeness', 0.0),
                validation_score=metrics_data.get('validation_score', 0.0),
                confidence_score=metrics_data.get('confidence_score', 0.0)
            )
        
        return Credential(
            id=self.id,
            user_id=self.user_id,
            credential_type=self.credential_type,
            processing_status=self.processing_status,
            extraction_method=self.extraction_method,
            original_filename=self.original_filename,
            file_path=self.file_path,
            file_size=self.file_size,
            file_hash=self.file_hash,
            mime_type=self.mime_type,
            processing_started_at=self.processing_started_at,
            processing_completed_at=self.processing_completed_at,
            processing_duration=self.processing_duration,
            personal_info=personal_info,
            processing_metrics=processing_metrics,
            quality_score=quality_score_obj,
            error_message=self.error_message,
            error_code=self.error_code,
            error_details=self.error_details or {},
            processing_logs=self.processing_logs or [],
            is_valid=self.is_valid,
            validation_errors=self.validation_errors or [],
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            metadata=self.extra_metadata or {}
        )
    
    @classmethod
    def from_domain_entity(cls, credential):
        """Create database model from domain entity.
        
        Args:
            credential: Credential domain entity
            
        Returns:
            CredentialModel instance
        """
        # Convert personal info to dict
        personal_info_dict = None
        if credential.personal_info:
            info = credential.personal_info
            personal_info_dict = {
                'nombre': info.nombre,
                'apellido_paterno': info.apellido_paterno,
                'apellido_materno': info.apellido_materno,
                'curp': info.curp,
                'fecha_nacimiento': info.fecha_nacimiento.isoformat() if info.fecha_nacimiento else None,
                'sexo': info.sexo.value if info.sexo else None,
                'domicilio': info.domicilio,
                'clave_elector': info.clave_elector,
                'seccion': info.seccion,
                'localidad': info.localidad,
                'municipio': info.municipio,
                'estado': info.estado,
                'vigencia': info.vigencia.isoformat() if info.vigencia else None,
                'emision': info.emision.isoformat() if info.emision else None
            }
        
        # Convert processing metrics to dict
        metrics_dict = {
            'ocr_confidence': credential.processing_metrics.ocr_confidence,
            'qr_detected': credential.processing_metrics.qr_detected,
            'qr_confidence': credential.processing_metrics.qr_confidence,
            'ai_confidence': credential.processing_metrics.ai_confidence,
            'processing_time': credential.processing_metrics.processing_time,
            'retry_count': credential.processing_metrics.retry_count,
            'validation_score': credential.processing_metrics.validation_score
        }
        
        # Add quality score details to metrics if available
        if credential.quality_score:
            metrics_dict.update({
                'ocr_quality': credential.quality_score.ocr_quality,
                'data_completeness': credential.quality_score.data_completeness,
                'confidence_score': credential.quality_score.confidence_score
            })
        
        return cls(
            id=credential.id,
            user_id=credential.user_id,
            credential_type=credential.credential_type,
            processing_status=credential.processing_status,
            extraction_method=credential.extraction_method,
            original_filename=credential.original_filename,
            file_path=credential.file_path,
            file_size=credential.file_size,
            file_hash=credential.file_hash,
            mime_type=credential.mime_type,
            processing_started_at=credential.processing_started_at,
            processing_completed_at=credential.processing_completed_at,
            processing_duration=credential.processing_duration,
            personal_info=personal_info_dict,
            processing_metrics=metrics_dict,
            quality_score=credential.quality_score.overall_score if credential.quality_score else None,
            error_message=credential.error_message,
            error_code=credential.error_code,
            error_details=credential.error_details,
            processing_logs=credential.processing_logs,
            is_valid=credential.is_valid,
            validation_errors=credential.validation_errors,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            deleted_at=credential.deleted_at,
            extra_metadata=credential.metadata
        )
    
    def update_from_domain_entity(self, credential) -> None:
        """Update database model from domain entity.
        
        Args:
            credential: Credential domain entity
        """
        # Update basic fields
        self.credential_type = credential.credential_type
        self.processing_status = credential.processing_status
        self.extraction_method = credential.extraction_method
        self.original_filename = credential.original_filename
        self.file_path = credential.file_path
        self.file_size = credential.file_size
        self.file_hash = credential.file_hash
        self.mime_type = credential.mime_type
        self.processing_started_at = credential.processing_started_at
        self.processing_completed_at = credential.processing_completed_at
        self.processing_duration = credential.processing_duration
        self.error_message = credential.error_message
        self.error_code = credential.error_code
        self.error_details = credential.error_details
        self.processing_logs = credential.processing_logs
        self.is_valid = credential.is_valid
        self.validation_errors = credential.validation_errors
        self.deleted_at = credential.deleted_at
        self.extra_metadata = credential.metadata
        
        # Update personal info
        if credential.personal_info:
            info = credential.personal_info
            self.personal_info = {
                'nombre': info.nombre,
                'apellido_paterno': info.apellido_paterno,
                'apellido_materno': info.apellido_materno,
                'curp': info.curp,
                'fecha_nacimiento': info.fecha_nacimiento.isoformat() if info.fecha_nacimiento else None,
                'sexo': info.sexo.value if info.sexo else None,
                'domicilio': info.domicilio,
                'clave_elector': info.clave_elector,
                'seccion': info.seccion,
                'localidad': info.localidad,
                'municipio': info.municipio,
                'estado': info.estado,
                'vigencia': info.vigencia.isoformat() if info.vigencia else None,
                'emision': info.emision.isoformat() if info.emision else None
            }
        else:
            self.personal_info = None
        
        # Update processing metrics
        metrics_dict = {
            'ocr_confidence': credential.processing_metrics.ocr_confidence,
            'qr_detected': credential.processing_metrics.qr_detected,
            'qr_confidence': credential.processing_metrics.qr_confidence,
            'ai_confidence': credential.processing_metrics.ai_confidence,
            'processing_time': credential.processing_metrics.processing_time,
            'retry_count': credential.processing_metrics.retry_count,
            'validation_score': credential.processing_metrics.validation_score
        }
        
        # Add quality score details if available
        if credential.quality_score:
            self.quality_score = credential.quality_score.overall_score
            metrics_dict.update({
                'ocr_quality': credential.quality_score.ocr_quality,
                'data_completeness': credential.quality_score.data_completeness,
                'confidence_score': credential.quality_score.confidence_score
            })
        else:
            self.quality_score = None
        
        self.processing_metrics = metrics_dict
        
        # Update timestamps
        self.updated_at = credential.updated_at or datetime.utcnow()
    
    @property
    def is_processed(self) -> bool:
        """Check if credential is processed.
        
        Returns:
            True if credential is processed
        """
        return self.processing_status in [
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED
        ]
    
    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Get processing time in seconds.
        
        Returns:
            Processing time in seconds or None
        """
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return self.processing_duration
    
    @property
    def full_name(self) -> Optional[str]:
        """Get full name from personal info.
        
        Returns:
            Full name or None
        """
        if not self.personal_info:
            return None
        
        parts = [
            self.personal_info.get('nombre', ''),
            self.personal_info.get('apellido_paterno', ''),
            self.personal_info.get('apellido_materno', '')
        ]
        
        return ' '.join(part for part in parts if part).strip() or None
    
    def __repr__(self) -> str:
        """String representation of the credential model."""
        return f"<CredentialModel(id={self.id}, type={self.credential_type}, status={self.processing_status})>"