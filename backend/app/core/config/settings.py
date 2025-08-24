#!/usr/bin/env python3
"""
Configuración principal de SEELE-E Backend

Maneja todas las configuraciones de la aplicación usando Pydantic Settings
con soporte para variables de entorno y validación automática.
"""

import os
from functools import lru_cache
from typing import List, Optional, Union
from pathlib import Path

from pydantic import Field, field_validator, AnyHttpUrl, ConfigDict
from pydantic_settings import BaseSettings

# Ruta al archivo .env en el directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"


class DatabaseSettings(BaseSettings):
    """
    Configuración de base de datos PostgreSQL.
    """
    DB_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    DB_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    DB_NAME: str = Field(default="seele_ine_db", env="POSTGRES_DB")
    DB_USER: str = Field(default="seele_user", env="POSTGRES_USER")
    DB_PASSWORD: str = Field(default="seele_password", env="POSTGRES_PASSWORD")
    DB_SCHEMA: str = Field(default="public", env="DB_SCHEMA")
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_prefix="",
        env_file=ENV_FILE_PATH
    )
    
    # Pool de conexiones
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    # SSL y configuraciones avanzadas
    DB_SSL_MODE: str = Field(default="prefer", env="DB_SSL_MODE")
    DB_TIMEZONE: str = Field(default="America/Mexico_City", env="DB_TIMEZONE")
    
    @property
    def database_url(self) -> str:
        """
        Construye la URL de conexión a la base de datos (async).
        Usa SQLite para desarrollo si PostgreSQL no está disponible.
        """
        import os
        # Usar DATABASE_URL directamente si está disponible
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
        # Fallback a la construcción manual
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def sync_database_url(self) -> str:
        """
        URL de conexión síncrona para Alembic.
        Usa SQLite para desarrollo si PostgreSQL no está disponible.
        """
        import os
        # Usar DATABASE_URL directamente si está disponible, pero cambiar asyncpg por psycopg2
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')
        # Fallback a la construcción manual
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class RedisSettings(BaseSettings):
    """
    Configuración de Redis para cache y sesiones.
    """
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_SSL: bool = Field(default=False, env="REDIS_SSL")
    
    # Cache y sesiones
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hora
    SESSION_TTL: int = Field(default=86400, env="SESSION_TTL")  # 24 horas
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )
     
    @property
    def redis_url(self) -> str:
        """
        Construye la URL de conexión a Redis.
        """
        protocol = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class SecuritySettings(BaseSettings):
    """
    Configuración de seguridad y autenticación.
    """
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # API Keys
    API_KEY_EXPIRE_DAYS: int = Field(default=365, env="API_KEY_EXPIRE_DAYS")
    
    # Password hashing
    PASSWORD_HASH_ALGORITHM: str = Field(default="bcrypt", env="PASSWORD_HASH_ALGORITHM")
    PASSWORD_HASH_ROUNDS: int = Field(default=12, env="PASSWORD_HASH_ROUNDS")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # segundos
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )
     
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY debe tener al menos 32 caracteres")
        return v


class AIProviderSettings(BaseSettings):
    """
    Configuración de proveedores de IA.
    """
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-vision-preview", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL: str = Field(default="deepseek-vl-7b-chat", env="DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com/v1", env="DEEPSEEK_BASE_URL")
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-pro-vision", env="GEMINI_MODEL")
    
    # Anthropic Claude
    CLAUDE_API_KEY: Optional[str] = Field(default=None, env="CLAUDE_API_KEY")
    CLAUDE_MODEL: str = Field(default="claude-3-sonnet-20240229", env="CLAUDE_MODEL")
    
    # Configuración general
    AI_TIMEOUT: int = Field(default=30, env="AI_TIMEOUT")  # segundos
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")
    AI_FALLBACK_ENABLED: bool = Field(default=True, env="AI_FALLBACK_ENABLED")
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )
     
    @property
    def available_providers(self) -> List[str]:
        """
        Lista de proveedores disponibles basado en las API keys configuradas.
        """
        providers = []
        if self.OPENAI_API_KEY:
            providers.append("openai")
        if self.DEEPSEEK_API_KEY:
            providers.append("deepseek")
        if self.GEMINI_API_KEY:
            providers.append("gemini")
        if self.CLAUDE_API_KEY:
            providers.append("claude")
        return providers


class ImageProcessingSettings(BaseSettings):
    """
    Configuración para procesamiento de imágenes y OCR.
    """
    # Validación de imágenes
    MAX_IMAGE_SIZE_MB: int = Field(default=10, env="MAX_IMAGE_SIZE_MB")
    ALLOWED_IMAGE_FORMATS: List[str] = Field(
        default=["JPEG", "JPG", "PNG", "WEBP"],
        env="ALLOWED_IMAGE_FORMATS"
    )
    
    # Dimensiones de credenciales INE
    INE_WIDTH: int = Field(default=790, env="INE_WIDTH")
    INE_HEIGHT: int = Field(default=490, env="INE_HEIGHT")
    INE_TOLERANCE: float = Field(default=0.1, env="INE_TOLERANCE")  # 10% tolerancia
    
    # OCR Configuration
    TESSERACT_LANG: str = Field(default="spa", env="TESSERACT_LANG")
    TESSERACT_CONFIG: str = Field(
        default="--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        env="TESSERACT_CONFIG"
    )
    
    # QR Processing
    QR_TIMEOUT: int = Field(default=10, env="QR_TIMEOUT")
    QR_MAX_ATTEMPTS: int = Field(default=3, env="QR_MAX_ATTEMPTS")
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )
    



class FileStorageSettings(BaseSettings):
    """
    Configuración de almacenamiento de archivos.
    """
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    TEMP_DIR: str = Field(default="temp", env="TEMP_DIR")
    CREDENTIALS_DIR: str = Field(default="credentials", env="CREDENTIALS_DIR")
    
    # Limpieza automática
    TEMP_FILE_TTL_HOURS: int = Field(default=24, env="TEMP_FILE_TTL_HOURS")
    AUTO_CLEANUP_ENABLED: bool = Field(default=True, env="AUTO_CLEANUP_ENABLED")
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )
     
    def __post_init__(self):
        """
        Crear directorios si no existen.
        """
        for directory in [self.UPLOAD_DIR, self.TEMP_DIR, self.CREDENTIALS_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)


class MonitoringSettings(BaseSettings):
    """
    Configuración de monitoreo y métricas.
    """
    # Prometheus
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_PORT: int = Field(default=8001, env="METRICS_PORT")
    
    # Health checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Alertas
    ALERT_WEBHOOK_URL: Optional[str] = Field(default=None, env="ALERT_WEBHOOK_URL")
    ALERT_EMAIL_ENABLED: bool = Field(default=False, env="ALERT_EMAIL_ENABLED")
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )


class Settings(BaseSettings):
    """
    Configuración principal que agrupa todas las configuraciones.
    """
    # Información básica de la aplicación
    APP_NAME: str = Field(default="SEELE-E Backend", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Configuración del servidor
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    RELOAD_ON_CHANGE: bool = Field(default=True, env="RELOAD_ON_CHANGE")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS y seguridad
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # Documentación
    SHOW_DOCS: bool = Field(default=True, env="SHOW_DOCS")
    
    # Configuraciones específicas
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    ai_providers: AIProviderSettings = AIProviderSettings()
    image_processing: ImageProcessingSettings = ImageProcessingSettings()
    file_storage: FileStorageSettings = FileStorageSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    model_config = ConfigDict(
        case_sensitive=True,
        extra="ignore",
        env_file=ENV_FILE_PATH
    )
        
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed = ["development", "testing", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT debe ser uno de: {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL debe ser uno de: {allowed}")
        return v.upper()
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    Factory function para obtener la configuración.
    Usa cache para evitar recargar la configuración en cada llamada.
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()


# Funciones de utilidad
def get_database_url() -> str:
    """
    Obtiene la URL de conexión a la base de datos.
    """
    return settings.database.database_url


def get_redis_url() -> str:
    """
    Obtiene la URL de conexión a Redis.
    """
    return settings.redis.redis_url


def is_ai_provider_available(provider: str) -> bool:
    """
    Verifica si un proveedor de IA está disponible.
    """
    return provider in settings.ai_providers.available_providers


def get_upload_path(filename: str) -> Path:
    """
    Construye la ruta completa para un archivo de upload.
    """
    return Path(settings.file_storage.UPLOAD_DIR) / filename


def get_temp_path(filename: str) -> Path:
    """
    Construye la ruta completa para un archivo temporal.
    """
    return Path(settings.file_storage.TEMP_DIR) / filename