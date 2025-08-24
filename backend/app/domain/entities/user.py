#!/usr/bin/env python3
"""
Entidad User para SEELE-E Backend

Define la entidad de dominio para usuarios del sistema,
incluyendo propiedades, validaciones y reglas de negocio.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...core.exceptions.base import ValidationException, BusinessLogicError


class UserRole(str, Enum):
    """
    Roles de usuario en el sistema.
    """
    ADMIN = "admin"
    USER = "user"
    API_CLIENT = "api_client"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """
    Estados de usuario.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class SubscriptionPlan(str, Enum):
    """
    Planes de suscripción.
    """
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class UserPreferences:
    """
    Preferencias del usuario.
    """
    language: str = "es"
    timezone: str = "America/Mexico_City"
    theme: str = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    sms_notifications: bool = False
    auto_process_credentials: bool = False
    preferred_ai_provider: Optional[str] = None
    max_concurrent_processes: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las preferencias a diccionario."""
        return {
            "language": self.language,
            "timezone": self.timezone,
            "theme": self.theme,
            "notifications_enabled": self.notifications_enabled,
            "email_notifications": self.email_notifications,
            "sms_notifications": self.sms_notifications,
            "auto_process_credentials": self.auto_process_credentials,
            "preferred_ai_provider": self.preferred_ai_provider,
            "max_concurrent_processes": self.max_concurrent_processes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Crea preferencias desde diccionario."""
        return cls(
            language=data.get("language", "es"),
            timezone=data.get("timezone", "America/Mexico_City"),
            theme=data.get("theme", "light"),
            notifications_enabled=data.get("notifications_enabled", True),
            email_notifications=data.get("email_notifications", True),
            sms_notifications=data.get("sms_notifications", False),
            auto_process_credentials=data.get("auto_process_credentials", False),
            preferred_ai_provider=data.get("preferred_ai_provider"),
            max_concurrent_processes=data.get("max_concurrent_processes", 5)
        )


@dataclass
class UserStats:
    """
    Estadísticas del usuario.
    """
    total_credentials_processed: int = 0
    total_api_calls: int = 0
    total_cost_usd: float = 0.0
    successful_extractions: int = 0
    failed_extractions: int = 0
    last_activity: Optional[datetime] = None
    credits_used: int = 0
    credits_remaining: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario."""
        return {
            "total_credentials_processed": self.total_credentials_processed,
            "total_api_calls": self.total_api_calls,
            "total_cost_usd": self.total_cost_usd,
            "successful_extractions": self.successful_extractions,
            "failed_extractions": self.failed_extractions,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "credits_used": self.credits_used,
            "credits_remaining": self.credits_remaining
        }
    
    @property
    def success_rate(self) -> float:
        """Calcula la tasa de éxito de extracciones."""
        total = self.successful_extractions + self.failed_extractions
        if total == 0:
            return 0.0
        return (self.successful_extractions / total) * 100
    
    @property
    def average_cost_per_extraction(self) -> float:
        """Calcula el costo promedio por extracción."""
        if self.total_credentials_processed == 0:
            return 0.0
        return self.total_cost_usd / self.total_credentials_processed


@dataclass
class User:
    """
    Entidad de dominio para usuarios del sistema SEELE-E.
    
    Representa un usuario con todas sus propiedades, validaciones
    y reglas de negocio asociadas.
    """
    
    # Identificadores
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    username: Optional[str] = None
    
    # Información personal
    first_name: str = ""
    last_name: str = ""
    company: Optional[str] = None
    phone: Optional[str] = None
    
    # Autenticación
    password_hash: str = ""
    is_email_verified: bool = False
    email_verification_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    
    # Estado y roles
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    
    # Preferencias y configuración
    preferences: UserPreferences = field(default_factory=UserPreferences)
    stats: UserStats = field(default_factory=UserStats)
    
    # API Keys
    api_keys: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    last_logout: Optional[datetime] = None
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validaciones después de la inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """
        Valida la entidad User según las reglas de negocio.
        
        Raises:
            ValidationException: Si alguna validación falla
        """
        errors = []
        
        # Validar email
        if not self.email:
            errors.append("Email es requerido")
        elif not self._is_valid_email(self.email):
            errors.append("Formato de email inválido")
        
        # Validar nombres
        if not self.first_name or len(self.first_name.strip()) < 2:
            errors.append("Nombre debe tener al menos 2 caracteres")
        
        if not self.last_name or len(self.last_name.strip()) < 2:
            errors.append("Apellido debe tener al menos 2 caracteres")
        
        # Validar username si está presente
        if self.username and not self._is_valid_username(self.username):
            errors.append("Username debe tener 3-50 caracteres alfanuméricos")
        
        # Validar teléfono si está presente
        if self.phone and not self._is_valid_phone(self.phone):
            errors.append("Formato de teléfono inválido")
        
        # Validar password hash
        if not self.password_hash:
            errors.append("Password hash es requerido")
        
        if errors:
            raise ValidationException(
                message="Errores de validación en User",
                details={"validation_errors": errors}
            )
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida formato de email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_username(self, username: str) -> bool:
        """Valida formato de username."""
        import re
        pattern = r'^[a-zA-Z0-9_]{3,50}$'
        return re.match(pattern, username) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Valida formato de teléfono."""
        import re
        # Acepta formatos: +52 55 1234 5678, 5551234567, etc.
        pattern = r'^\+?[1-9]\d{1,14}$'
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        return re.match(pattern, clean_phone) is not None
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self) -> str:
        """Retorna el nombre para mostrar (username o nombre completo)."""
        return self.username or self.full_name
    
    @property
    def is_active(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_verified(self) -> bool:
        """Verifica si el usuario está verificado."""
        return self.is_email_verified
    
    @property
    def last_login_at(self) -> Optional[datetime]:
        """Retorna la fecha del último login."""
        return self.last_login
    
    @property
    def is_locked(self) -> bool:
        """Verifica si el usuario está bloqueado."""
        return self.status == UserStatus.SUSPENDED
    
    @property
    def can_use_api(self) -> bool:
        """Verifica si el usuario puede usar la API."""
        return self.is_active and len(self.api_keys) > 0
    
    @property
    def subscription_limits(self) -> Dict[str, int]:
        """Retorna los límites según el plan de suscripción."""
        limits = {
            SubscriptionPlan.FREE: {
                "monthly_extractions": 100,
                "concurrent_processes": 1,
                "api_calls_per_minute": 10,
                "storage_mb": 100
            },
            SubscriptionPlan.BASIC: {
                "monthly_extractions": 1000,
                "concurrent_processes": 3,
                "api_calls_per_minute": 50,
                "storage_mb": 1000
            },
            SubscriptionPlan.PREMIUM: {
                "monthly_extractions": 10000,
                "concurrent_processes": 10,
                "api_calls_per_minute": 200,
                "storage_mb": 10000
            },
            SubscriptionPlan.ENTERPRISE: {
                "monthly_extractions": -1,  # Ilimitado
                "concurrent_processes": 50,
                "api_calls_per_minute": 1000,
                "storage_mb": 100000
            }
        }
        return limits.get(self.subscription_plan, limits[SubscriptionPlan.FREE])
    
    def activate(self) -> None:
        """Activa el usuario."""
        if self.status == UserStatus.SUSPENDED:
            raise BusinessLogicError(
                message="No se puede activar un usuario suspendido",
                details={"current_status": self.status.value}
            )
        
        self.status = UserStatus.ACTIVE
        self.is_email_verified = True
        self.email_verification_token = None
        self.updated_at = datetime.utcnow()
    
    def suspend(self, reason: str = "") -> None:
        """Suspende el usuario."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.metadata["suspension_reason"] = reason
            self.metadata["suspended_at"] = datetime.utcnow().isoformat()
    
    def deactivate(self) -> None:
        """Desactiva el usuario."""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def update_last_login(self) -> None:
        """Actualiza la fecha del último login."""
        self.last_login = datetime.utcnow()
        self.stats.last_activity = self.last_login
        self.updated_at = datetime.utcnow()
    
    def update_last_logout(self) -> None:
        """Actualiza la fecha del último logout."""
        self.last_logout = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_api_key(self, api_key: str) -> None:
        """Agrega una nueva API key."""
        if api_key in self.api_keys:
            raise BusinessLogicError(
                message="API key ya existe",
                details={"api_key_prefix": api_key[:10]}
            )
        
        self.api_keys.append(api_key)
        self.updated_at = datetime.utcnow()
    
    def remove_api_key(self, api_key: str) -> None:
        """Remueve una API key."""
        if api_key not in self.api_keys:
            raise BusinessLogicError(
                message="API key no encontrada",
                details={"api_key_prefix": api_key[:10]}
            )
        
        self.api_keys.remove(api_key)
        self.updated_at = datetime.utcnow()
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Actualiza las preferencias del usuario."""
        # Validar preferencias
        valid_keys = {
            "language", "timezone", "theme", "notifications_enabled",
            "email_notifications", "sms_notifications", "auto_process_credentials",
            "preferred_ai_provider", "max_concurrent_processes"
        }
        
        invalid_keys = set(preferences.keys()) - valid_keys
        if invalid_keys:
            raise ValidationException(
                message="Claves de preferencias inválidas",
                details={"invalid_keys": list(invalid_keys)}
            )
        
        # Actualizar preferencias
        for key, value in preferences.items():
            if hasattr(self.preferences, key):
                setattr(self.preferences, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def update_stats(self, **kwargs) -> None:
        """Actualiza las estadísticas del usuario."""
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
        
        self.stats.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_usage(self, cost: float = 0.0, success: bool = True) -> None:
        """Incrementa las estadísticas de uso."""
        self.stats.total_credentials_processed += 1
        self.stats.total_api_calls += 1
        self.stats.total_cost_usd += cost
        
        if success:
            self.stats.successful_extractions += 1
        else:
            self.stats.failed_extractions += 1
        
        self.stats.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def can_process_credential(self) -> bool:
        """Verifica si el usuario puede procesar una credencial más."""
        if not self.is_active:
            return False
        
        limits = self.subscription_limits
        monthly_limit = limits["monthly_extractions"]
        
        # Si es ilimitado (Enterprise)
        if monthly_limit == -1:
            return True
        
        # Verificar límite mensual
        # TODO: Implementar lógica para contar extracciones del mes actual
        return self.stats.total_credentials_processed < monthly_limit
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        data = {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "company": self.company,
            "phone": self.phone,
            "role": self.role.value,
            "status": self.status.value,
            "subscription_plan": self.subscription_plan.value,
            "is_email_verified": self.is_email_verified,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "can_use_api": self.can_use_api,
            "preferences": self.preferences.to_dict(),
            "stats": self.stats.to_dict(),
            "subscription_limits": self.subscription_limits,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "metadata": self.metadata
        }
        
        if include_sensitive:
            data.update({
                "password_hash": self.password_hash,
                "email_verification_token": self.email_verification_token,
                "password_reset_token": self.password_reset_token,
                "password_reset_expires": self.password_reset_expires.isoformat() if self.password_reset_expires else None,
                "api_keys": self.api_keys
            })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Crea una instancia desde diccionario."""
        # Convertir strings a enums
        if "role" in data and isinstance(data["role"], str):
            data["role"] = UserRole(data["role"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = UserStatus(data["status"])
        
        if "subscription_plan" in data and isinstance(data["subscription_plan"], str):
            data["subscription_plan"] = SubscriptionPlan(data["subscription_plan"])
        
        # Convertir strings a UUID
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])
        
        # Convertir strings a datetime
        datetime_fields = ["created_at", "updated_at", "last_login", "password_reset_expires"]
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convertir preferencias
        if "preferences" in data and isinstance(data["preferences"], dict):
            data["preferences"] = UserPreferences.from_dict(data["preferences"])
        
        # Convertir estadísticas
        if "stats" in data and isinstance(data["stats"], dict):
            stats_data = data["stats"]
            if "last_activity" in stats_data and isinstance(stats_data["last_activity"], str):
                stats_data["last_activity"] = datetime.fromisoformat(stats_data["last_activity"])
            data["stats"] = UserStats(**stats_data)
        
        return cls(**data)