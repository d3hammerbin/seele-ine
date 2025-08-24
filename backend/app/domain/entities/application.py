#!/usr/bin/env python3
"""
Entidad Application para SEELE-E Backend

Define la entidad de dominio para aplicaciones que consumen la API,
incluyendo API keys, límites, estadísticas y configuraciones.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from decimal import Decimal

from ...core.exceptions.base import ValidationException, BusinessLogicError


class ApplicationStatus(str, Enum):
    """
    Estados de aplicación.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_APPROVAL = "pending_approval"
    REVOKED = "revoked"


class ApplicationTier(str, Enum):
    """
    Niveles de aplicación con diferentes límites.
    """
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"
    PARTNER = "partner"


class APIKeyStatus(str, Enum):
    """
    Estados de API keys.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class APIKey:
    """
    Representa una API key de la aplicación.
    """
    id: UUID = field(default_factory=uuid4)
    key_hash: str = ""  # Hash de la key real
    key_prefix: str = ""  # Primeros caracteres para identificación
    name: str = ""
    description: str = ""
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    
    # Permisos y límites
    scopes: Set[str] = field(default_factory=set)
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # Restricciones
    allowed_ips: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    
    # Estadísticas
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_used: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        """Verifica si la API key está activa."""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la API key está expirada."""
        return self.expires_at and self.expires_at < datetime.utcnow()
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def increment_usage(self, success: bool = True) -> None:
        """Incrementa las estadísticas de uso."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.last_used = datetime.utcnow()
    
    def revoke(self, reason: str = "") -> None:
        """Revoca la API key."""
        self.status = APIKeyStatus.REVOKED
        self.revoked_at = datetime.utcnow()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = {
            "id": str(self.id),
            "key_prefix": self.key_prefix,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "scopes": list(self.scopes),
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "rate_limit_per_day": self.rate_limit_per_day,
            "allowed_ips": self.allowed_ips,
            "allowed_domains": self.allowed_domains,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_active": self.is_active,
            "is_expired": self.is_expired
        }
        
        if include_sensitive:
            data["key_hash"] = self.key_hash
        
        return data


@dataclass
class ApplicationLimits:
    """
    Límites de la aplicación.
    """
    # Límites de rate limiting
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    requests_per_month: int = 100000
    
    # Límites de procesamiento
    max_concurrent_processes: int = 5
    max_file_size_mb: int = 10
    max_files_per_request: int = 1
    
    # Límites de costo
    monthly_budget_usd: Optional[Decimal] = None
    cost_per_extraction_usd: Decimal = field(default_factory=lambda: Decimal('0.10'))
    
    # Límites de almacenamiento
    max_storage_mb: int = 1000
    retention_days: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "requests_per_day": self.requests_per_day,
            "requests_per_month": self.requests_per_month,
            "max_concurrent_processes": self.max_concurrent_processes,
            "max_file_size_mb": self.max_file_size_mb,
            "max_files_per_request": self.max_files_per_request,
            "monthly_budget_usd": float(self.monthly_budget_usd) if self.monthly_budget_usd else None,
            "cost_per_extraction_usd": float(self.cost_per_extraction_usd),
            "max_storage_mb": self.max_storage_mb,
            "retention_days": self.retention_days
        }


@dataclass
class ApplicationStats:
    """
    Estadísticas de la aplicación.
    """
    # Estadísticas de uso
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Estadísticas de procesamiento
    total_credentials_processed: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    
    # Estadísticas de costo
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    monthly_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Estadísticas de tiempo
    average_processing_time_seconds: float = 0.0
    total_processing_time_seconds: float = 0.0
    
    # Estadísticas de calidad
    average_quality_score: float = 0.0
    high_quality_extractions: int = 0
    
    # Timestamps
    last_request: Optional[datetime] = None
    last_successful_extraction: Optional[datetime] = None
    stats_reset_date: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito general."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def extraction_success_rate(self) -> float:
        """Calcula la tasa de éxito de extracciones."""
        total_extractions = self.successful_extractions + self.failed_extractions
        if total_extractions == 0:
            return 0.0
        return (self.successful_extractions / total_extractions) * 100
    
    @property
    def average_cost_per_extraction(self) -> float:
        """Calcula el costo promedio por extracción."""
        if self.total_credentials_processed == 0:
            return 0.0
        return float(self.total_cost_usd / self.total_credentials_processed)
    
    @property
    def quality_rate(self) -> float:
        """Calcula el porcentaje de extracciones de alta calidad."""
        if self.successful_extractions == 0:
            return 0.0
        return (self.high_quality_extractions / self.successful_extractions) * 100
    
    def increment_request(self, success: bool = True) -> None:
        """Incrementa las estadísticas de peticiones."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.last_request = datetime.utcnow()
    
    def increment_extraction(
        self, 
        success: bool = True, 
        cost: Decimal = None, 
        processing_time: float = 0.0,
        quality_score: float = 0.0
    ) -> None:
        """Incrementa las estadísticas de extracción."""
        self.total_credentials_processed += 1
        
        if success:
            self.successful_extractions += 1
            self.last_successful_extraction = datetime.utcnow()
            
            if quality_score >= 80:  # Considerado alta calidad
                self.high_quality_extractions += 1
            
            # Actualizar promedio de calidad
            if self.successful_extractions == 1:
                self.average_quality_score = quality_score
            else:
                self.average_quality_score = (
                    (self.average_quality_score * (self.successful_extractions - 1) + quality_score) /
                    self.successful_extractions
                )
        else:
            self.failed_extractions += 1
        
        # Actualizar costos
        if cost:
            self.total_cost_usd += cost
            # TODO: Calcular costo mensual basado en fecha
        
        # Actualizar tiempo de procesamiento
        if processing_time > 0:
            self.total_processing_time_seconds += processing_time
            self.average_processing_time_seconds = (
                self.total_processing_time_seconds / self.total_credentials_processed
            )
    
    def reset_monthly_stats(self) -> None:
        """Resetea las estadísticas mensuales."""
        self.monthly_cost_usd = Decimal('0.00')
        self.stats_reset_date = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "total_credentials_processed": self.total_credentials_processed,
            "successful_extractions": self.successful_extractions,
            "failed_extractions": self.failed_extractions,
            "extraction_success_rate": self.extraction_success_rate,
            "total_cost_usd": float(self.total_cost_usd),
            "monthly_cost_usd": float(self.monthly_cost_usd),
            "average_cost_per_extraction": self.average_cost_per_extraction,
            "average_processing_time_seconds": self.average_processing_time_seconds,
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "average_quality_score": self.average_quality_score,
            "high_quality_extractions": self.high_quality_extractions,
            "quality_rate": self.quality_rate,
            "last_request": self.last_request.isoformat() if self.last_request else None,
            "last_successful_extraction": self.last_successful_extraction.isoformat() if self.last_successful_extraction else None,
            "stats_reset_date": self.stats_reset_date.isoformat()
        }


@dataclass
class Application:
    """
    Entidad de dominio para aplicaciones que consumen la API SEELE-E.
    
    Representa una aplicación con sus configuraciones, límites,
    API keys y estadísticas de uso.
    """
    
    # Identificadores
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    
    # Información básica
    name: str = ""
    description: str = ""
    website_url: Optional[str] = None
    callback_url: Optional[str] = None
    
    # Estado y configuración
    status: ApplicationStatus = ApplicationStatus.PENDING_APPROVAL
    tier: ApplicationTier = ApplicationTier.DEVELOPMENT
    
    # Límites y configuración
    limits: ApplicationLimits = field(default_factory=ApplicationLimits)
    
    # API Keys
    api_keys: List[APIKey] = field(default_factory=list)
    
    # Estadísticas
    stats: ApplicationStats = field(default_factory=ApplicationStats)
    
    # Configuración avanzada
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    allowed_origins: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones después de la inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """
        Valida la entidad Application según las reglas de negocio.
        
        Raises:
            ValidationException: Si alguna validación falla
        """
        errors = []
        
        # Validar nombre
        if not self.name or len(self.name.strip()) < 3:
            errors.append("Nombre de aplicación debe tener al menos 3 caracteres")
        
        if len(self.name) > 100:
            errors.append("Nombre de aplicación no puede exceder 100 caracteres")
        
        # Validar descripción
        if not self.description or len(self.description.strip()) < 10:
            errors.append("Descripción debe tener al menos 10 caracteres")
        
        # Validar URLs si están presentes
        if self.website_url and not self._is_valid_url(self.website_url):
            errors.append("URL del sitio web inválida")
        
        if self.callback_url and not self._is_valid_url(self.callback_url):
            errors.append("URL de callback inválida")
        
        if self.webhook_url and not self._is_valid_url(self.webhook_url):
            errors.append("URL de webhook inválida")
        
        # Validar orígenes permitidos
        for origin in self.allowed_origins:
            if not self._is_valid_origin(origin):
                errors.append(f"Origen inválido: {origin}")
        
        if errors:
            raise ValidationException(
                message="Errores de validación en Application",
                details={"validation_errors": errors}
            )
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida formato de URL."""
        import re
        pattern = r'^https?://[\w\.-]+(?:\.[a-zA-Z]{2,})+(?:/.*)?$'
        return re.match(pattern, url) is not None
    
    def _is_valid_origin(self, origin: str) -> bool:
        """Valida formato de origen CORS."""
        if origin == "*":
            return True
        return self._is_valid_url(origin) or origin.startswith("http://localhost")
    
    @property
    def is_active(self) -> bool:
        """Verifica si la aplicación está activa."""
        return self.status == ApplicationStatus.ACTIVE
    
    @property
    def is_approved(self) -> bool:
        """Verifica si la aplicación está aprobada."""
        return self.status in [ApplicationStatus.ACTIVE, ApplicationStatus.INACTIVE]
    
    @property
    def active_api_keys(self) -> List[APIKey]:
        """Retorna las API keys activas."""
        return [key for key in self.api_keys if key.is_active]
    
    @property
    def tier_limits(self) -> Dict[str, Any]:
        """Retorna los límites según el tier."""
        tier_configs = {
            ApplicationTier.DEVELOPMENT: {
                "requests_per_minute": 10,
                "requests_per_day": 1000,
                "max_concurrent_processes": 1,
                "max_file_size_mb": 5,
                "monthly_budget_usd": 50
            },
            ApplicationTier.PRODUCTION: {
                "requests_per_minute": 100,
                "requests_per_day": 10000,
                "max_concurrent_processes": 5,
                "max_file_size_mb": 10,
                "monthly_budget_usd": 500
            },
            ApplicationTier.ENTERPRISE: {
                "requests_per_minute": 1000,
                "requests_per_day": 100000,
                "max_concurrent_processes": 20,
                "max_file_size_mb": 50,
                "monthly_budget_usd": 5000
            },
            ApplicationTier.PARTNER: {
                "requests_per_minute": 500,
                "requests_per_day": 50000,
                "max_concurrent_processes": 10,
                "max_file_size_mb": 25,
                "monthly_budget_usd": 2000
            }
        }
        return tier_configs.get(self.tier, tier_configs[ApplicationTier.DEVELOPMENT])
    
    def approve(self, approved_by: str = "") -> None:
        """Aprueba la aplicación."""
        if self.status != ApplicationStatus.PENDING_APPROVAL:
            raise BusinessLogicError(
                message=f"No se puede aprobar aplicación desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = ApplicationStatus.ACTIVE
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if approved_by:
            self.metadata["approved_by"] = approved_by
    
    def suspend(self, reason: str = "", suspended_by: str = "") -> None:
        """Suspende la aplicación."""
        if self.status == ApplicationStatus.REVOKED:
            raise BusinessLogicError(
                message="No se puede suspender una aplicación revocada",
                details={"current_status": self.status.value}
            )
        
        self.status = ApplicationStatus.SUSPENDED
        self.suspended_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.metadata["suspension_reason"] = reason
        if suspended_by:
            self.metadata["suspended_by"] = suspended_by
        
        # Desactivar todas las API keys
        for api_key in self.api_keys:
            if api_key.status == APIKeyStatus.ACTIVE:
                api_key.status = APIKeyStatus.INACTIVE
    
    def reactivate(self) -> None:
        """Reactiva la aplicación."""
        if self.status not in [ApplicationStatus.INACTIVE, ApplicationStatus.SUSPENDED]:
            raise BusinessLogicError(
                message=f"No se puede reactivar aplicación desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = ApplicationStatus.ACTIVE
        self.suspended_at = None
        self.updated_at = datetime.utcnow()
        
        # Reactivar API keys que estaban activas
        for api_key in self.api_keys:
            if api_key.status == APIKeyStatus.INACTIVE and not api_key.is_expired:
                api_key.status = APIKeyStatus.ACTIVE
    
    def revoke(self, reason: str = "", revoked_by: str = "") -> None:
        """Revoca permanentemente la aplicación."""
        self.status = ApplicationStatus.REVOKED
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.metadata["revocation_reason"] = reason
        if revoked_by:
            self.metadata["revoked_by"] = revoked_by
        
        # Revocar todas las API keys
        for api_key in self.api_keys:
            api_key.revoke(f"Application revoked: {reason}")
    
    def create_api_key(
        self, 
        name: str, 
        description: str = "",
        scopes: Set[str] = None,
        expires_in_days: Optional[int] = None
    ) -> APIKey:
        """Crea una nueva API key."""
        if not self.is_active:
            raise BusinessLogicError(
                message="No se pueden crear API keys para aplicaciones inactivas",
                details={"status": self.status.value}
            )
        
        # Límite de API keys por aplicación
        if len(self.api_keys) >= 10:
            raise BusinessLogicError(
                message="Límite de API keys alcanzado (máximo 10 por aplicación)",
                details={"current_count": len(self.api_keys)}
            )
        
        # Crear nueva API key
        api_key = APIKey(
            name=name,
            description=description,
            scopes=scopes or set(),
            rate_limit_per_minute=self.limits.requests_per_minute,
            rate_limit_per_hour=self.limits.requests_per_hour,
            rate_limit_per_day=self.limits.requests_per_day
        )
        
        if expires_in_days:
            api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        self.api_keys.append(api_key)
        self.updated_at = datetime.utcnow()
        
        return api_key
    
    def revoke_api_key(self, api_key_id: UUID, reason: str = "") -> None:
        """Revoca una API key específica."""
        api_key = next((key for key in self.api_keys if key.id == api_key_id), None)
        if not api_key:
            raise BusinessLogicError(
                message="API key no encontrada",
                details={"api_key_id": str(api_key_id)}
            )
        
        api_key.revoke(reason)
        self.updated_at = datetime.utcnow()
    
    def update_limits(self, new_limits: ApplicationLimits) -> None:
        """Actualiza los límites de la aplicación."""
        self.limits = new_limits
        self.updated_at = datetime.utcnow()
        
        # Actualizar límites en API keys activas
        for api_key in self.active_api_keys:
            api_key.rate_limit_per_minute = new_limits.requests_per_minute
            api_key.rate_limit_per_hour = new_limits.requests_per_hour
            api_key.rate_limit_per_day = new_limits.requests_per_day
    
    def increment_usage(
        self, 
        success: bool = True, 
        extraction_success: bool = None,
        cost: Decimal = None,
        processing_time: float = 0.0,
        quality_score: float = 0.0
    ) -> None:
        """Incrementa las estadísticas de uso."""
        self.stats.increment_request(success)
        
        if extraction_success is not None:
            self.stats.increment_extraction(
                success=extraction_success,
                cost=cost,
                processing_time=processing_time,
                quality_score=quality_score
            )
    
    def can_make_request(self) -> bool:
        """Verifica si la aplicación puede hacer una petición más."""
        if not self.is_active:
            return False
        
        # TODO: Implementar verificación de límites en tiempo real
        # Por ahora, solo verificar estado
        return True
    
    def is_over_budget(self) -> bool:
        """Verifica si la aplicación ha excedido su presupuesto mensual."""
        if not self.limits.monthly_budget_usd:
            return False
        
        return self.stats.monthly_cost_usd >= self.limits.monthly_budget_usd
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "website_url": self.website_url,
            "callback_url": self.callback_url,
            "status": self.status.value,
            "tier": self.tier.value,
            "limits": self.limits.to_dict(),
            "stats": self.stats.to_dict(),
            "allowed_origins": self.allowed_origins,
            "tier_limits": self.tier_limits,
            "is_active": self.is_active,
            "is_approved": self.is_approved,
            "is_over_budget": self.is_over_budget(),
            "active_api_keys_count": len(self.active_api_keys),
            "total_api_keys_count": len(self.api_keys),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "suspended_at": self.suspended_at.isoformat() if self.suspended_at else None,
            "metadata": self.metadata
        }
        
        # API keys (sin información sensible por defecto)
        data["api_keys"] = [key.to_dict(include_sensitive=include_sensitive) for key in self.api_keys]
        
        if include_sensitive:
            data.update({
                "webhook_url": self.webhook_url,
                "webhook_secret": self.webhook_secret
            })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Application':
        """Crea una instancia desde diccionario."""
        # Convertir strings a enums
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ApplicationStatus(data["status"])
        
        if "tier" in data and isinstance(data["tier"], str):
            data["tier"] = ApplicationTier(data["tier"])
        
        # Convertir strings a UUID
        uuid_fields = ["id", "user_id"]
        for field in uuid_fields:
            if field in data and isinstance(data[field], str):
                data[field] = UUID(data[field])
        
        # Convertir strings a datetime
        datetime_fields = ["created_at", "updated_at", "approved_at", "suspended_at"]
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convertir objetos anidados
        if "limits" in data and isinstance(data["limits"], dict):
            limits_data = data["limits"]
            
            # Convertir Decimal
            decimal_fields = ["monthly_budget_usd", "cost_per_extraction_usd"]
            for field in decimal_fields:
                if field in limits_data and limits_data[field] is not None:
                    limits_data[field] = Decimal(str(limits_data[field]))
            
            data["limits"] = ApplicationLimits(**limits_data)
        
        if "stats" in data and isinstance(data["stats"], dict):
            stats_data = data["stats"]
            
            # Convertir Decimal
            decimal_fields = ["total_cost_usd", "monthly_cost_usd"]
            for field in decimal_fields:
                if field in stats_data:
                    stats_data[field] = Decimal(str(stats_data[field]))
            
            # Convertir datetime
            datetime_fields = ["last_request", "last_successful_extraction", "stats_reset_date"]
            for field in datetime_fields:
                if field in stats_data and isinstance(stats_data[field], str):
                    stats_data[field] = datetime.fromisoformat(stats_data[field])
            
            data["stats"] = ApplicationStats(**stats_data)
        
        if "api_keys" in data and isinstance(data["api_keys"], list):
            api_keys = []
            for key_data in data["api_keys"]:
                if isinstance(key_data, dict):
                    # Convertir UUID
                    if "id" in key_data and isinstance(key_data["id"], str):
                        key_data["id"] = UUID(key_data["id"])
                    
                    # Convertir enum
                    if "status" in key_data and isinstance(key_data["status"], str):
                        key_data["status"] = APIKeyStatus(key_data["status"])
                    
                    # Convertir datetime
                    datetime_fields = ["created_at", "expires_at", "revoked_at", "last_used"]
                    for field in datetime_fields:
                        if field in key_data and isinstance(key_data[field], str):
                            key_data[field] = datetime.fromisoformat(key_data[field])
                    
                    # Convertir scopes a set
                    if "scopes" in key_data and isinstance(key_data["scopes"], list):
                        key_data["scopes"] = set(key_data["scopes"])
                    
                    api_keys.append(APIKey(**key_data))
            
            data["api_keys"] = api_keys
        
        return cls(**data)