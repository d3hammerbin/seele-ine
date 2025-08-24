#!/usr/bin/env python3
"""
Entidad ProcessingJob para SEELE-E Backend

Define la entidad de dominio para trabajos de procesamiento de credenciales,
incluyendo estados, métricas, resultados y configuraciones.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from decimal import Decimal

from ...core.exceptions.base import ValidationException, BusinessLogicError


class JobStatus(str, Enum):
    """
    Estados del trabajo de procesamiento.
    """
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """
    Prioridades del trabajo.
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ProcessingStage(str, Enum):
    """
    Etapas del procesamiento.
    """
    VALIDATION = "validation"
    IMAGE_PREPROCESSING = "image_preprocessing"
    OCR_EXTRACTION = "ocr_extraction"
    QR_EXTRACTION = "qr_extraction"
    AI_PROCESSING = "ai_processing"
    DATA_VALIDATION = "data_validation"
    QUALITY_CHECK = "quality_check"
    STORAGE = "storage"
    NOTIFICATION = "notification"
    COMPLETED = "completed"


class AIProvider(str, Enum):
    """
    Proveedores de IA disponibles.
    """
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    CLAUDE = "claude"


@dataclass
class ProcessingConfig:
    """
    Configuración del procesamiento.
    """
    # Configuración de imagen
    max_image_size_mb: int = 10
    allowed_formats: Set[str] = field(default_factory=lambda: {"jpg", "jpeg", "png", "pdf"})
    enhance_image: bool = True
    auto_rotate: bool = True
    
    # Configuración de OCR
    ocr_language: str = "spa"
    ocr_confidence_threshold: float = 0.7
    use_multiple_ocr_engines: bool = True
    
    # Configuración de QR
    qr_detection_enabled: bool = True
    qr_enhancement: bool = True
    
    # Configuración de IA
    preferred_ai_provider: AIProvider = AIProvider.OPENAI
    ai_fallback_enabled: bool = True
    ai_fallback_providers: List[AIProvider] = field(default_factory=lambda: [AIProvider.DEEPSEEK, AIProvider.GEMINI])
    ai_temperature: float = 0.1
    ai_max_tokens: int = 2000
    
    # Configuración de calidad
    min_quality_score: float = 70.0
    require_all_fields: bool = True
    validate_curp: bool = True
    validate_dates: bool = True
    
    # Configuración de reintentos
    max_retries: int = 3
    retry_delay_seconds: int = 30
    exponential_backoff: bool = True
    
    # Configuración de timeout
    processing_timeout_minutes: int = 10
    ai_timeout_seconds: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "max_image_size_mb": self.max_image_size_mb,
            "allowed_formats": list(self.allowed_formats),
            "enhance_image": self.enhance_image,
            "auto_rotate": self.auto_rotate,
            "ocr_language": self.ocr_language,
            "ocr_confidence_threshold": self.ocr_confidence_threshold,
            "use_multiple_ocr_engines": self.use_multiple_ocr_engines,
            "qr_detection_enabled": self.qr_detection_enabled,
            "qr_enhancement": self.qr_enhancement,
            "preferred_ai_provider": self.preferred_ai_provider.value,
            "ai_fallback_enabled": self.ai_fallback_enabled,
            "ai_fallback_providers": [p.value for p in self.ai_fallback_providers],
            "ai_temperature": self.ai_temperature,
            "ai_max_tokens": self.ai_max_tokens,
            "min_quality_score": self.min_quality_score,
            "require_all_fields": self.require_all_fields,
            "validate_curp": self.validate_curp,
            "validate_dates": self.validate_dates,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "exponential_backoff": self.exponential_backoff,
            "processing_timeout_minutes": self.processing_timeout_minutes,
            "ai_timeout_seconds": self.ai_timeout_seconds
        }


@dataclass
class ProcessingMetrics:
    """
    Métricas del procesamiento.
    """
    # Tiempos de procesamiento
    total_processing_time_seconds: float = 0.0
    image_preprocessing_time_seconds: float = 0.0
    ocr_processing_time_seconds: float = 0.0
    qr_processing_time_seconds: float = 0.0
    ai_processing_time_seconds: float = 0.0
    validation_time_seconds: float = 0.0
    
    # Métricas de calidad
    ocr_confidence_score: float = 0.0
    ai_confidence_score: float = 0.0
    overall_quality_score: float = 0.0
    
    # Métricas de costo
    ocr_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    ai_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    storage_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Métricas de uso
    ai_tokens_used: int = 0
    ai_provider_used: Optional[AIProvider] = None
    fallback_providers_tried: List[AIProvider] = field(default_factory=list)
    
    # Métricas de imagen
    original_image_size_bytes: int = 0
    processed_image_size_bytes: int = 0
    image_dimensions: Optional[tuple] = None
    image_format: str = ""
    
    # Contadores
    retry_count: int = 0
    ocr_attempts: int = 0
    ai_attempts: int = 0
    
    def calculate_total_cost(self) -> None:
        """Calcula el costo total."""
        self.total_cost_usd = self.ocr_cost_usd + self.ai_cost_usd + self.storage_cost_usd
    
    def add_ai_cost(self, cost: Decimal, tokens: int, provider: AIProvider) -> None:
        """Añade costo de IA."""
        self.ai_cost_usd += cost
        self.ai_tokens_used += tokens
        self.ai_provider_used = provider
        self.calculate_total_cost()
    
    def add_fallback_attempt(self, provider: AIProvider) -> None:
        """Registra intento de fallback."""
        if provider not in self.fallback_providers_tried:
            self.fallback_providers_tried.append(provider)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "image_preprocessing_time_seconds": self.image_preprocessing_time_seconds,
            "ocr_processing_time_seconds": self.ocr_processing_time_seconds,
            "qr_processing_time_seconds": self.qr_processing_time_seconds,
            "ai_processing_time_seconds": self.ai_processing_time_seconds,
            "validation_time_seconds": self.validation_time_seconds,
            "ocr_confidence_score": self.ocr_confidence_score,
            "ai_confidence_score": self.ai_confidence_score,
            "overall_quality_score": self.overall_quality_score,
            "ocr_cost_usd": float(self.ocr_cost_usd),
            "ai_cost_usd": float(self.ai_cost_usd),
            "storage_cost_usd": float(self.storage_cost_usd),
            "total_cost_usd": float(self.total_cost_usd),
            "ai_tokens_used": self.ai_tokens_used,
            "ai_provider_used": self.ai_provider_used.value if self.ai_provider_used else None,
            "fallback_providers_tried": [p.value for p in self.fallback_providers_tried],
            "original_image_size_bytes": self.original_image_size_bytes,
            "processed_image_size_bytes": self.processed_image_size_bytes,
            "image_dimensions": self.image_dimensions,
            "image_format": self.image_format,
            "retry_count": self.retry_count,
            "ocr_attempts": self.ocr_attempts,
            "ai_attempts": self.ai_attempts
        }


@dataclass
class ProcessingError:
    """
    Error de procesamiento.
    """
    stage: ProcessingStage
    error_type: str
    error_message: str
    error_code: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "stage": self.stage.value,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "is_recoverable": self.is_recoverable
        }


@dataclass
class ProcessingResult:
    """
    Resultado del procesamiento.
    """
    # Datos extraídos
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    
    # Datos de OCR
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_bounding_boxes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Datos de QR
    qr_data: Optional[str] = None
    qr_type: Optional[str] = None
    qr_confidence: float = 0.0
    
    # Validaciones
    validation_results: Dict[str, bool] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    
    # Archivos generados
    processed_image_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "extracted_data": self.extracted_data,
            "ocr_text": self.ocr_text,
            "ocr_confidence": self.ocr_confidence,
            "ocr_bounding_boxes": self.ocr_bounding_boxes,
            "qr_data": self.qr_data,
            "qr_type": self.qr_type,
            "qr_confidence": self.qr_confidence,
            "validation_results": self.validation_results,
            "validation_errors": self.validation_errors,
            "processed_image_path": self.processed_image_path,
            "thumbnail_path": self.thumbnail_path
        }


@dataclass
class ProcessingJob:
    """
    Entidad de dominio para trabajos de procesamiento de credenciales.
    
    Representa un trabajo de procesamiento con su configuración,
    estado, métricas y resultados.
    """
    
    # Identificadores
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    application_id: UUID = field(default_factory=uuid4)
    credential_id: Optional[UUID] = None
    
    # Información del trabajo
    name: str = ""
    description: str = ""
    
    # Estado y prioridad
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    current_stage: ProcessingStage = ProcessingStage.VALIDATION
    
    # Configuración
    config: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    # Archivos de entrada
    input_file_path: str = ""
    input_file_name: str = ""
    input_file_size_bytes: int = 0
    input_file_hash: str = ""
    
    # Métricas y resultados
    metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)
    result: Optional[ProcessingResult] = None
    
    # Errores y logs
    errors: List[ProcessingError] = field(default_factory=list)
    processing_logs: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Configuración de reintentos
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    
    # Worker información
    worker_id: Optional[str] = None
    queue_name: str = "default"
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones después de la inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """
        Valida la entidad ProcessingJob según las reglas de negocio.
        
        Raises:
            ValidationException: Si alguna validación falla
        """
        errors = []
        
        # Validar archivo de entrada
        if not self.input_file_path:
            errors.append("Ruta del archivo de entrada es requerida")
        
        if not self.input_file_name:
            errors.append("Nombre del archivo de entrada es requerido")
        
        if self.input_file_size_bytes <= 0:
            errors.append("Tamaño del archivo debe ser mayor a 0")
        
        # Validar configuración
        if self.config.max_image_size_mb <= 0:
            errors.append("Tamaño máximo de imagen debe ser mayor a 0")
        
        if self.config.processing_timeout_minutes <= 0:
            errors.append("Timeout de procesamiento debe ser mayor a 0")
        
        # Validar límites
        max_file_size_bytes = self.config.max_image_size_mb * 1024 * 1024
        if self.input_file_size_bytes > max_file_size_bytes:
            errors.append(f"Archivo excede el tamaño máximo permitido ({self.config.max_image_size_mb}MB)")
        
        # Validar formato de archivo
        if self.input_file_name:
            file_extension = self.input_file_name.split('.')[-1].lower()
            if file_extension not in self.config.allowed_formats:
                errors.append(f"Formato de archivo no permitido: {file_extension}")
        
        if errors:
            raise ValidationException(
                message="Errores de validación en ProcessingJob",
                details={"validation_errors": errors}
            )
    
    @property
    def is_active(self) -> bool:
        """Verifica si el trabajo está activo (en procesamiento)."""
        return self.status in [JobStatus.QUEUED, JobStatus.PROCESSING, JobStatus.RETRYING]
    
    @property
    def is_completed(self) -> bool:
        """Verifica si el trabajo está completado."""
        return self.status == JobStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Verifica si el trabajo falló."""
        return self.status in [JobStatus.FAILED, JobStatus.TIMEOUT, JobStatus.CANCELLED]
    
    @property
    def can_retry(self) -> bool:
        """Verifica si el trabajo puede ser reintentado."""
        if self.status not in [JobStatus.FAILED, JobStatus.TIMEOUT]:
            return False
        
        if self.retry_count >= self.max_retries:
            return False
        
        # Verificar si hay errores recuperables
        recoverable_errors = [error for error in self.errors if error.is_recoverable]
        return len(recoverable_errors) > 0
    
    @property
    def processing_time_seconds(self) -> float:
        """Calcula el tiempo total de procesamiento."""
        if not self.started_at:
            return 0.0
        
        end_time = self.completed_at or self.failed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_timeout(self) -> bool:
        """Verifica si el trabajo ha excedido el timeout."""
        if not self.started_at or self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False
        
        timeout_minutes = self.config.processing_timeout_minutes
        timeout_time = self.started_at + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > timeout_time
    
    def start_processing(self, worker_id: str = "") -> None:
        """Inicia el procesamiento del trabajo."""
        if self.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RETRYING]:
            raise BusinessLogicError(
                message=f"No se puede iniciar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.current_stage = ProcessingStage.VALIDATION
        
        if worker_id:
            self.worker_id = worker_id
        
        self.add_log(f"Procesamiento iniciado por worker {worker_id or 'unknown'}")
    
    def complete_processing(self, result: ProcessingResult) -> None:
        """Completa el procesamiento exitosamente."""
        if self.status != JobStatus.PROCESSING:
            raise BusinessLogicError(
                message=f"No se puede completar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.current_stage = ProcessingStage.COMPLETED
        self.result = result
        
        # Actualizar métricas finales
        self.metrics.total_processing_time_seconds = self.processing_time_seconds
        
        self.add_log("Procesamiento completado exitosamente")
    
    def fail_processing(self, error: ProcessingError) -> None:
        """Marca el procesamiento como fallido."""
        if self.status not in [JobStatus.PROCESSING, JobStatus.RETRYING]:
            raise BusinessLogicError(
                message=f"No se puede fallar procesamiento desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.errors.append(error)
        
        # Verificar si se puede reintentar
        if self.can_retry and error.is_recoverable:
            self.schedule_retry()
        else:
            self.status = JobStatus.FAILED
            self.failed_at = datetime.utcnow()
            self.add_log(f"Procesamiento fallido: {error.error_message}")
    
    def timeout_processing(self) -> None:
        """Marca el procesamiento como timeout."""
        if self.status != JobStatus.PROCESSING:
            return
        
        self.status = JobStatus.TIMEOUT
        self.failed_at = datetime.utcnow()
        
        timeout_error = ProcessingError(
            stage=self.current_stage,
            error_type="TimeoutError",
            error_message=f"Procesamiento excedió el timeout de {self.config.processing_timeout_minutes} minutos",
            is_recoverable=True
        )
        self.errors.append(timeout_error)
        
        self.add_log(f"Procesamiento timeout después de {self.processing_time_seconds} segundos")
        
        # Intentar reintento si es posible
        if self.can_retry:
            self.schedule_retry()
    
    def cancel_processing(self, reason: str = "") -> None:
        """Cancela el procesamiento."""
        if self.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]:
            return
        
        self.status = JobStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        
        if reason:
            self.metadata["cancellation_reason"] = reason
        
        self.add_log(f"Procesamiento cancelado: {reason}")
    
    def schedule_retry(self) -> None:
        """Programa un reintento del procesamiento."""
        if not self.can_retry:
            raise BusinessLogicError(
                message="No se puede programar reintento",
                details={
                    "retry_count": self.retry_count,
                    "max_retries": self.max_retries,
                    "status": self.status.value
                }
            )
        
        self.status = JobStatus.RETRYING
        self.retry_count += 1
        
        # Calcular delay con backoff exponencial
        base_delay = self.config.retry_delay_seconds
        if self.config.exponential_backoff:
            delay = base_delay * (2 ** (self.retry_count - 1))
        else:
            delay = base_delay
        
        self.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        
        self.add_log(f"Reintento #{self.retry_count} programado para {self.next_retry_at}")
    
    def update_stage(self, stage: ProcessingStage) -> None:
        """Actualiza la etapa actual del procesamiento."""
        if self.status != JobStatus.PROCESSING:
            return
        
        self.current_stage = stage
        self.add_log(f"Etapa actualizada: {stage.value}")
    
    def add_error(self, error: ProcessingError) -> None:
        """Añade un error al trabajo."""
        self.errors.append(error)
        self.add_log(f"Error en {error.stage.value}: {error.error_message}")
    
    def add_log(self, message: str) -> None:
        """Añade un mensaje al log de procesamiento."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.processing_logs.append(log_entry)
        
        # Limitar logs a últimas 100 entradas
        if len(self.processing_logs) > 100:
            self.processing_logs = self.processing_logs[-100:]
    
    def update_metrics(self, **kwargs) -> None:
        """Actualiza las métricas del trabajo."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
    
    def get_progress_percentage(self) -> float:
        """Calcula el porcentaje de progreso basado en la etapa actual."""
        stage_progress = {
            ProcessingStage.VALIDATION: 10,
            ProcessingStage.IMAGE_PREPROCESSING: 20,
            ProcessingStage.OCR_EXTRACTION: 40,
            ProcessingStage.QR_EXTRACTION: 50,
            ProcessingStage.AI_PROCESSING: 70,
            ProcessingStage.DATA_VALIDATION: 85,
            ProcessingStage.QUALITY_CHECK: 90,
            ProcessingStage.STORAGE: 95,
            ProcessingStage.NOTIFICATION: 98,
            ProcessingStage.COMPLETED: 100
        }
        
        return stage_progress.get(self.current_stage, 0)
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "application_id": str(self.application_id),
            "credential_id": str(self.credential_id) if self.credential_id else None,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "current_stage": self.current_stage.value,
            "config": self.config.to_dict(),
            "input_file_name": self.input_file_name,
            "input_file_size_bytes": self.input_file_size_bytes,
            "metrics": self.metrics.to_dict(),
            "result": self.result.to_dict() if self.result else None,
            "errors": [error.to_dict() for error in self.errors],
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "queue_name": self.queue_name,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "can_retry": self.can_retry,
            "is_timeout": self.is_timeout,
            "processing_time_seconds": self.processing_time_seconds,
            "progress_percentage": self.get_progress_percentage(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "metadata": self.metadata
        }
        
        if include_sensitive:
            data.update({
                "input_file_path": self.input_file_path,
                "input_file_hash": self.input_file_hash,
                "worker_id": self.worker_id,
                "processing_logs": self.processing_logs[-10:]  # Últimos 10 logs
            })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingJob':
        """Crea una instancia desde diccionario."""
        # Convertir strings a enums
        enum_fields = {
            "status": JobStatus,
            "priority": JobPriority,
            "current_stage": ProcessingStage
        }
        
        for field, enum_class in enum_fields.items():
            if field in data and isinstance(data[field], str):
                data[field] = enum_class(data[field])
        
        # Convertir strings a UUID
        uuid_fields = ["id", "user_id", "application_id", "credential_id"]
        for field in uuid_fields:
            if field in data and isinstance(data[field], str):
                data[field] = UUID(data[field])
        
        # Convertir strings a datetime
        datetime_fields = [
            "created_at", "started_at", "completed_at", 
            "failed_at", "cancelled_at", "next_retry_at"
        ]
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convertir objetos anidados
        if "config" in data and isinstance(data["config"], dict):
            config_data = data["config"]
            
            # Convertir enums en config
            if "preferred_ai_provider" in config_data:
                config_data["preferred_ai_provider"] = AIProvider(config_data["preferred_ai_provider"])
            
            if "ai_fallback_providers" in config_data:
                config_data["ai_fallback_providers"] = [
                    AIProvider(p) for p in config_data["ai_fallback_providers"]
                ]
            
            if "allowed_formats" in config_data:
                config_data["allowed_formats"] = set(config_data["allowed_formats"])
            
            data["config"] = ProcessingConfig(**config_data)
        
        if "metrics" in data and isinstance(data["metrics"], dict):
            metrics_data = data["metrics"]
            
            # Convertir Decimal
            decimal_fields = ["ocr_cost_usd", "ai_cost_usd", "storage_cost_usd", "total_cost_usd"]
            for field in decimal_fields:
                if field in metrics_data:
                    metrics_data[field] = Decimal(str(metrics_data[field]))
            
            # Convertir enum
            if "ai_provider_used" in metrics_data and metrics_data["ai_provider_used"]:
                metrics_data["ai_provider_used"] = AIProvider(metrics_data["ai_provider_used"])
            
            if "fallback_providers_tried" in metrics_data:
                metrics_data["fallback_providers_tried"] = [
                    AIProvider(p) for p in metrics_data["fallback_providers_tried"]
                ]
            
            data["metrics"] = ProcessingMetrics(**metrics_data)
        
        if "result" in data and isinstance(data["result"], dict):
            data["result"] = ProcessingResult(**data["result"])
        
        if "errors" in data and isinstance(data["errors"], list):
            errors = []
            for error_data in data["errors"]:
                if isinstance(error_data, dict):
                    # Convertir enum
                    if "stage" in error_data:
                        error_data["stage"] = ProcessingStage(error_data["stage"])
                    
                    # Convertir datetime
                    if "timestamp" in error_data and isinstance(error_data["timestamp"], str):
                        error_data["timestamp"] = datetime.fromisoformat(error_data["timestamp"])
                    
                    errors.append(ProcessingError(**error_data))
            
            data["errors"] = errors
        
        return cls(**data)