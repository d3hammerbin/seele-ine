#!/usr/bin/env python3
"""
Entidad Credential para SEELE-E Backend

Define la entidad de dominio para credenciales INE procesadas,
incluyendo tipos, validaciones y reglas de negocio.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from decimal import Decimal

from ...core.exceptions.base import ValidationException, BusinessLogicError


class CredentialType(str, Enum):
    """
    Tipos de credenciales INE.
    """
    TIPO1 = "tipo1"  # Credencial antigua
    TIPO2 = "tipo2"  # Credencial intermedia
    TIPO3 = "tipo3"  # Credencial actual


class ProcessingStatus(str, Enum):
    """
    Estados de procesamiento de credenciales.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVIEWING = "reviewing"


class ExtractionMethod(str, Enum):
    """
    Métodos de extracción utilizados.
    """
    OCR_TESSERACT = "ocr_tesseract"
    OCR_GOOGLE_VISION = "ocr_google_vision"
    QR_PYZBAR = "qr_pyzbar"
    QR_OPENCV = "qr_opencv"
    QR_EXTRACTOR_PRO = "qr_extractor_pro"
    AI_OPENAI = "ai_openai"
    AI_DEEPSEEK = "ai_deepseek"
    AI_GEMINI = "ai_gemini"
    AI_CLAUDE = "ai_claude"
    HYBRID = "hybrid"


class Gender(str, Enum):
    """
    Géneros para credenciales INE.
    """
    MASCULINO = "M"
    FEMENINO = "F"
    NO_ESPECIFICADO = "X"


@dataclass
class PersonalInfo:
    """
    Información personal extraída de la credencial.
    """
    # Campos obligatorios
    nombre: str = ""
    apellido_paterno: str = ""
    apellido_materno: str = ""
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[Gender] = None
    
    # Campos opcionales
    curp: str = ""
    clave_elector: str = ""
    numero_emision: str = ""
    vigencia: Optional[date] = None
    
    # Dirección
    domicilio: str = ""
    seccion: str = ""
    localidad: str = ""
    municipio: str = ""
    estado: str = ""
    cp: str = ""
    
    def validate(self) -> List[str]:
        """Valida la información personal."""
        errors = []
        
        if not self.nombre or len(self.nombre.strip()) < 2:
            errors.append("Nombre es requerido y debe tener al menos 2 caracteres")
        
        if not self.apellido_paterno or len(self.apellido_paterno.strip()) < 2:
            errors.append("Apellido paterno es requerido")
        
        if self.fecha_nacimiento:
            today = date.today()
            if self.fecha_nacimiento > today:
                errors.append("Fecha de nacimiento no puede ser futura")
            
            age = today.year - self.fecha_nacimiento.year
            if age < 18 or age > 120:
                errors.append("Edad debe estar entre 18 y 120 años")
        
        if self.curp and not self._is_valid_curp(self.curp):
            errors.append("Formato de CURP inválido")
        
        if self.vigencia and self.vigencia < date.today():
            errors.append("Credencial vencida")
        
        return errors
    
    def _is_valid_curp(self, curp: str) -> bool:
        """Valida formato básico de CURP."""
        import re
        pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$'
        return len(curp) == 18 and re.match(pattern, curp.upper()) is not None
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo."""
        parts = [self.nombre, self.apellido_paterno, self.apellido_materno]
        return " ".join(part.strip() for part in parts if part.strip())
    
    @property
    def edad(self) -> Optional[int]:
        """Calcula la edad actual."""
        if not self.fecha_nacimiento:
            return None
        
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la credencial está vencida."""
        if not self.vigencia:
            return False
        return self.vigencia < date.today()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "nombre": self.nombre,
            "apellido_paterno": self.apellido_paterno,
            "apellido_materno": self.apellido_materno,
            "nombre_completo": self.nombre_completo,
            "fecha_nacimiento": self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            "edad": self.edad,
            "sexo": self.sexo.value if self.sexo else None,
            "curp": self.curp,
            "clave_elector": self.clave_elector,
            "numero_emision": self.numero_emision,
            "vigencia": self.vigencia.isoformat() if self.vigencia else None,
            "is_expired": self.is_expired,
            "domicilio": self.domicilio,
            "seccion": self.seccion,
            "localidad": self.localidad,
            "municipio": self.municipio,
            "estado": self.estado,
            "cp": self.cp
        }


@dataclass
class ProcessingMetrics:
    """
    Métricas del procesamiento de la credencial.
    """
    processing_time_seconds: float = 0.0
    ocr_confidence: float = 0.0
    qr_confidence: float = 0.0
    ai_confidence: float = 0.0
    extraction_methods_used: List[ExtractionMethod] = field(default_factory=list)
    ai_provider_used: Optional[str] = None
    cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    tokens_used: int = 0
    image_size_bytes: int = 0
    image_dimensions: Optional[Dict[str, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "processing_time_seconds": self.processing_time_seconds,
            "ocr_confidence": self.ocr_confidence,
            "qr_confidence": self.qr_confidence,
            "ai_confidence": self.ai_confidence,
            "extraction_methods_used": [method.value for method in self.extraction_methods_used],
            "ai_provider_used": self.ai_provider_used,
            "cost_usd": float(self.cost_usd),
            "tokens_used": self.tokens_used,
            "image_size_bytes": self.image_size_bytes,
            "image_dimensions": self.image_dimensions
        }


@dataclass
class QualityScore:
    """
    Puntuación de calidad de la extracción.
    """
    overall_score: float = 0.0  # 0-100
    completeness_score: float = 0.0  # Qué tan completa está la información
    accuracy_score: float = 0.0  # Qué tan precisa es la información
    consistency_score: float = 0.0  # Consistencia entre métodos
    confidence_score: float = 0.0  # Confianza general
    
    # Detalles por campo
    field_scores: Dict[str, float] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    suspicious_fields: List[str] = field(default_factory=list)
    
    @property
    def grade(self) -> str:
        """Retorna una calificación alfabética."""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"
    
    @property
    def is_high_quality(self) -> bool:
        """Verifica si es de alta calidad."""
        return self.overall_score >= 80 and len(self.missing_fields) <= 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "overall_score": self.overall_score,
            "completeness_score": self.completeness_score,
            "accuracy_score": self.accuracy_score,
            "consistency_score": self.consistency_score,
            "confidence_score": self.confidence_score,
            "grade": self.grade,
            "is_high_quality": self.is_high_quality,
            "field_scores": self.field_scores,
            "missing_fields": self.missing_fields,
            "suspicious_fields": self.suspicious_fields
        }


@dataclass
class Credential:
    """
    Entidad de dominio para credenciales INE procesadas.
    
    Representa una credencial con toda la información extraída,
    métricas de procesamiento y validaciones.
    """
    
    # Identificadores
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    
    # Información de la credencial
    credential_type: CredentialType = CredentialType.TIPO3
    personal_info: PersonalInfo = field(default_factory=PersonalInfo)
    
    # Estado del procesamiento
    status: ProcessingStatus = ProcessingStatus.PENDING
    
    # Archivos
    original_filename: str = ""
    file_path: str = ""
    file_size_bytes: int = 0
    file_hash: str = ""
    
    # Procesamiento
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)
    quality_score: QualityScore = field(default_factory=QualityScore)
    
    # Datos extraídos
    raw_ocr_text: str = ""
    raw_qr_data: str = ""
    raw_ai_response: str = ""
    
    # Errores y logs
    error_message: Optional[str] = None
    processing_logs: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones después de la inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """
        Valida la entidad Credential según las reglas de negocio.
        
        Raises:
            ValidationException: Si alguna validación falla
        """
        errors = []
        
        # Validar archivo
        if not self.original_filename:
            errors.append("Nombre de archivo original es requerido")
        
        if not self.file_path:
            errors.append("Ruta de archivo es requerida")
        
        if self.file_size_bytes <= 0:
            errors.append("Tamaño de archivo debe ser mayor a 0")
        
        # Validar información personal si está completa
        if self.status == ProcessingStatus.COMPLETED:
            personal_errors = self.personal_info.validate()
            errors.extend(personal_errors)
        
        # Validar fechas de procesamiento
        if self.processing_started_at and self.processing_completed_at:
            if self.processing_completed_at < self.processing_started_at:
                errors.append("Fecha de finalización no puede ser anterior al inicio")
        
        if errors:
            raise ValidationException(
                message="Errores de validación en Credential",
                details={"validation_errors": errors}
            )
    
    @property
    def is_processing(self) -> bool:
        """Verifica si está en procesamiento."""
        return self.status == ProcessingStatus.PROCESSING
    
    @property
    def is_completed(self) -> bool:
        """Verifica si el procesamiento está completo."""
        return self.status == ProcessingStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Verifica si el procesamiento falló."""
        return self.status == ProcessingStatus.FAILED
    
    @property
    def processing_duration(self) -> Optional[float]:
        """Calcula la duración del procesamiento en segundos."""
        if not self.processing_started_at or not self.processing_completed_at:
            return None
        
        delta = self.processing_completed_at - self.processing_started_at
        return delta.total_seconds()
    
    @property
    def file_size_mb(self) -> float:
        """Retorna el tamaño del archivo en MB."""
        return self.file_size_bytes / (1024 * 1024)
    
    def start_processing(self) -> None:
        """Inicia el procesamiento de la credencial."""
        if self.status != ProcessingStatus.PENDING:
            raise BusinessLogicError(
                message=f"No se puede iniciar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = ProcessingStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.add_log("Procesamiento iniciado")
    
    def complete_processing(
        self, 
        personal_info: PersonalInfo,
        metrics: ProcessingMetrics,
        quality_score: QualityScore
    ) -> None:
        """Completa el procesamiento exitosamente."""
        if self.status != ProcessingStatus.PROCESSING:
            raise BusinessLogicError(
                message=f"No se puede completar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = ProcessingStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
        self.personal_info = personal_info
        self.processing_metrics = metrics
        self.quality_score = quality_score
        self.updated_at = datetime.utcnow()
        
        # Calcular tiempo de procesamiento
        if self.processing_started_at:
            duration = (self.processing_completed_at - self.processing_started_at).total_seconds()
            self.processing_metrics.processing_time_seconds = duration
        
        self.add_log(f"Procesamiento completado exitosamente - Calidad: {quality_score.grade}")
    
    def fail_processing(self, error_message: str) -> None:
        """Marca el procesamiento como fallido."""
        if self.status not in [ProcessingStatus.PROCESSING, ProcessingStatus.PENDING]:
            raise BusinessLogicError(
                message=f"No se puede fallar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = ProcessingStatus.FAILED
        self.error_message = error_message
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.add_log(f"Procesamiento fallido: {error_message}")
    
    def cancel_processing(self, reason: str = "") -> None:
        """Cancela el procesamiento."""
        if self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            raise BusinessLogicError(
                message=f"No se puede cancelar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = ProcessingStatus.CANCELLED
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        cancel_msg = f"Procesamiento cancelado: {reason}" if reason else "Procesamiento cancelado"
        self.add_log(cancel_msg)
    
    def add_log(self, message: str) -> None:
        """Agrega un mensaje al log de procesamiento."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.processing_logs.append(log_entry)
    
    def update_raw_data(
        self, 
        ocr_text: str = None, 
        qr_data: str = None, 
        ai_response: str = None
    ) -> None:
        """Actualiza los datos raw extraídos."""
        if ocr_text is not None:
            self.raw_ocr_text = ocr_text
        
        if qr_data is not None:
            self.raw_qr_data = qr_data
        
        if ai_response is not None:
            self.raw_ai_response = ai_response
        
        self.updated_at = datetime.utcnow()
    
    def calculate_quality_score(self) -> QualityScore:
        """Calcula la puntuación de calidad basada en la información extraída."""
        quality = QualityScore()
        
        # Campos obligatorios para credencial INE
        required_fields = {
            "nombre": self.personal_info.nombre,
            "apellido_paterno": self.personal_info.apellido_paterno,
            "fecha_nacimiento": self.personal_info.fecha_nacimiento,
            "sexo": self.personal_info.sexo,
            "curp": self.personal_info.curp,
            "clave_elector": self.personal_info.clave_elector
        }
        
        # Calcular completeness
        filled_fields = sum(1 for value in required_fields.values() if value)
        quality.completeness_score = (filled_fields / len(required_fields)) * 100
        
        # Calcular accuracy basado en confianza de métodos
        confidences = [
            self.processing_metrics.ocr_confidence,
            self.processing_metrics.qr_confidence,
            self.processing_metrics.ai_confidence
        ]
        valid_confidences = [c for c in confidences if c > 0]
        if valid_confidences:
            quality.accuracy_score = sum(valid_confidences) / len(valid_confidences)
        
        # Calcular consistency (si múltiples métodos coinciden)
        methods_count = len(self.processing_metrics.extraction_methods_used)
        if methods_count > 1:
            quality.consistency_score = min(90, methods_count * 30)  # Más métodos = más consistencia
        else:
            quality.consistency_score = 70  # Score base para un método
        
        # Confidence score basado en métricas
        quality.confidence_score = quality.accuracy_score
        
        # Score general (promedio ponderado)
        quality.overall_score = (
            quality.completeness_score * 0.4 +
            quality.accuracy_score * 0.3 +
            quality.consistency_score * 0.2 +
            quality.confidence_score * 0.1
        )
        
        # Identificar campos faltantes
        for field_name, value in required_fields.items():
            if not value:
                quality.missing_fields.append(field_name)
        
        # Identificar campos sospechosos (baja confianza)
        for field_name, value in required_fields.items():
            if value and field_name in quality.field_scores:
                if quality.field_scores[field_name] < 50:
                    quality.suspicious_fields.append(field_name)
        
        self.quality_score = quality
        return quality
    
    def to_dict(self, include_raw_data: bool = False) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "credential_type": self.credential_type.value,
            "status": self.status.value,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "file_size_mb": self.file_size_mb,
            "file_hash": self.file_hash,
            "personal_info": self.personal_info.to_dict(),
            "processing_metrics": self.processing_metrics.to_dict(),
            "quality_score": self.quality_score.to_dict(),
            "processing_started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "processing_completed_at": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            "processing_duration": self.processing_duration,
            "error_message": self.error_message,
            "processing_logs": self.processing_logs,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "is_processing": self.is_processing,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed
        }
        
        if include_raw_data:
            data.update({
                "raw_ocr_text": self.raw_ocr_text,
                "raw_qr_data": self.raw_qr_data,
                "raw_ai_response": self.raw_ai_response
            })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Credential':
        """Crea una instancia desde diccionario."""
        # Convertir strings a enums
        if "credential_type" in data and isinstance(data["credential_type"], str):
            data["credential_type"] = CredentialType(data["credential_type"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ProcessingStatus(data["status"])
        
        # Convertir strings a UUID
        uuid_fields = ["id", "user_id"]
        for field in uuid_fields:
            if field in data and isinstance(data[field], str):
                data[field] = UUID(data[field])
        
        # Convertir strings a datetime
        datetime_fields = ["processing_started_at", "processing_completed_at", "created_at", "updated_at"]
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convertir objetos anidados
        if "personal_info" in data and isinstance(data["personal_info"], dict):
            personal_data = data["personal_info"]
            
            # Convertir fechas
            if "fecha_nacimiento" in personal_data and isinstance(personal_data["fecha_nacimiento"], str):
                personal_data["fecha_nacimiento"] = date.fromisoformat(personal_data["fecha_nacimiento"])
            
            if "vigencia" in personal_data and isinstance(personal_data["vigencia"], str):
                personal_data["vigencia"] = date.fromisoformat(personal_data["vigencia"])
            
            if "sexo" in personal_data and isinstance(personal_data["sexo"], str):
                personal_data["sexo"] = Gender(personal_data["sexo"])
            
            data["personal_info"] = PersonalInfo(**personal_data)
        
        if "processing_metrics" in data and isinstance(data["processing_metrics"], dict):
            metrics_data = data["processing_metrics"]
            
            # Convertir enums
            if "extraction_methods_used" in metrics_data:
                metrics_data["extraction_methods_used"] = [
                    ExtractionMethod(method) for method in metrics_data["extraction_methods_used"]
                ]
            
            # Convertir Decimal
            if "cost_usd" in metrics_data:
                metrics_data["cost_usd"] = Decimal(str(metrics_data["cost_usd"]))
            
            data["processing_metrics"] = ProcessingMetrics(**metrics_data)
        
        if "quality_score" in data and isinstance(data["quality_score"], dict):
            data["quality_score"] = QualityScore(**data["quality_score"])
        
        return cls(**data)