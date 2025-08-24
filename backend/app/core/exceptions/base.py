#!/usr/bin/env python3
"""
Excepciones base personalizadas para SEELE-E Backend

Define una jerarquía de excepciones específicas del dominio que proporcionan
información estructurada sobre errores y facilitan el manejo centralizado.
"""

from typing import Any, Dict, Optional
from fastapi import status


class SeeleException(Exception):
    """
    Excepción base para todas las excepciones personalizadas de SEELE-E.
    
    Proporciona una estructura común para el manejo de errores con:
    - Código de estado HTTP apropiado
    - Tipo de error para categorización
    - Código de error específico para identificación
    - Detalles adicionales opcionales
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "seele_error",
        error_code: str = "SEELE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"status_code={self.status_code}, "
            f"error_code='{self.error_code}'"
            f")"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la excepción a un diccionario para serialización.
        """
        return {
            "type": self.error_type,
            "message": self.message,
            "code": self.error_code,
            "status_code": self.status_code,
            "details": self.details
        }


class ValidationException(SeeleException):
    """
    Excepción para errores de validación de datos.
    """
    
    def __init__(
        self,
        message: str = "Los datos proporcionados no son válidos",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation_error",
            error_code="VALIDATION_ERROR",
            details=error_details
        )


class AuthenticationException(SeeleException):
    """
    Excepción para errores de autenticación.
    """
    
    def __init__(
        self,
        message: str = "Credenciales de autenticación inválidas",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="authentication_error",
            error_code="AUTH_ERROR",
            details=details
        )


class AuthorizationException(SeeleException):
    """
    Excepción para errores de autorización.
    """
    
    def __init__(
        self,
        message: str = "No tiene permisos para realizar esta acción",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="authorization_error",
            error_code="AUTHORIZATION_ERROR",
            details=error_details
        )


class RepositoryError(SeeleException):
    """
    Excepción para errores en operaciones de repositorio/base de datos.
    """
    
    def __init__(
        self,
        message: str = "Error en operación de base de datos",
        operation: Optional[str] = None,
        entity_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        if entity_type:
            error_details["entity_type"] = entity_type
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="repository_error",
            error_code="REPOSITORY_ERROR",
            details=error_details
        )


class NotFoundError(SeeleException):
    """
    Excepción para recursos no encontrados.
    """
    
    def __init__(
        self,
        message: str = "El recurso solicitado no fue encontrado",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not_found_error",
            error_code="NOT_FOUND",
            details=error_details
        )


class BusinessLogicError(SeeleException):
    """
    Excepción para errores de lógica de negocio.
    """
    
    def __init__(
        self,
        message: str,
        business_rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if business_rule:
            error_details["business_rule"] = business_rule
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="business_logic_error",
            error_code="BUSINESS_LOGIC_ERROR",
            details=error_details
        )


class ExternalServiceError(SeeleException):
    """
    Excepción para errores de servicios externos.
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        service_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if service_name:
            error_details["service_name"] = service_name
        if service_error:
            error_details["service_error"] = service_error
        
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_type="external_service_error",
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details
        )


class RateLimitError(SeeleException):
    """
    Excepción para errores de límite de velocidad.
    """
    
    def __init__(
        self,
        message: str = "Se ha excedido el límite de solicitudes",
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if limit:
            error_details["limit"] = limit
        if window:
            error_details["window"] = window
        if retry_after:
            error_details["retry_after"] = retry_after
        
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_type="rate_limit_error",
            error_code="RATE_LIMIT_EXCEEDED",
            details=error_details
        )


# Excepciones específicas del dominio SEELE-E

class CredentialProcessingError(SeeleException):
    """
    Excepción para errores en el procesamiento de credenciales.
    """
    
    def __init__(
        self,
        message: str,
        credential_type: Optional[str] = None,
        processing_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if credential_type:
            error_details["credential_type"] = credential_type
        if processing_stage:
            error_details["processing_stage"] = processing_stage
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="credential_processing_error",
            error_code="CREDENTIAL_PROCESSING_ERROR",
            details=error_details
        )


class ImageValidationError(ValidationException):
    """
    Excepción para errores de validación de imágenes.
    """
    
    def __init__(
        self,
        message: str,
        image_issue: Optional[str] = None,
        expected_dimensions: Optional[tuple] = None,
        actual_dimensions: Optional[tuple] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if image_issue:
            error_details["image_issue"] = image_issue
        if expected_dimensions:
            error_details["expected_dimensions"] = expected_dimensions
        if actual_dimensions:
            error_details["actual_dimensions"] = actual_dimensions
        
        super().__init__(
            message=message,
            details=error_details
        )
        self.error_code = "IMAGE_VALIDATION_ERROR"


class OCRProcessingError(ExternalServiceError):
    """
    Excepción para errores en el procesamiento OCR.
    """
    
    def __init__(
        self,
        message: str = "Error en el procesamiento OCR",
        ocr_engine: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            service_name=ocr_engine or "OCR",
            details=details
        )
        self.error_code = "OCR_PROCESSING_ERROR"


class QRProcessingError(ExternalServiceError):
    """
    Excepción para errores en el procesamiento de códigos QR.
    """
    
    def __init__(
        self,
        message: str = "Error en el procesamiento del código QR",
        qr_issue: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if qr_issue:
            error_details["qr_issue"] = qr_issue
        
        super().__init__(
            message=message,
            service_name="QR_PROCESSOR",
            details=error_details
        )
        self.error_code = "QR_PROCESSING_ERROR"


class AIProviderError(ExternalServiceError):
    """
    Excepción para errores de proveedores de IA.
    """
    
    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        api_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if model_name:
            error_details["model_name"] = model_name
        if api_error:
            error_details["api_error"] = api_error
        
        super().__init__(
            message=message,
            service_name=provider_name or "AI_PROVIDER",
            details=error_details
        )
        self.error_code = "AI_PROVIDER_ERROR"


class BillingError(BusinessLogicError):
    """
    Excepción para errores del sistema de facturación.
    """
    
    def __init__(
        self,
        message: str,
        billing_issue: Optional[str] = None,
        application_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if billing_issue:
            error_details["billing_issue"] = billing_issue
        if application_id:
            error_details["application_id"] = application_id
        
        super().__init__(
            message=message,
            business_rule="billing_rules",
            details=error_details
        )
        self.error_code = "BILLING_ERROR"


class InsufficientCreditsError(BillingError):
    """
    Excepción para créditos insuficientes.
    """
    
    def __init__(
        self,
        message: str = "Créditos insuficientes para realizar la operación",
        required_credits: Optional[float] = None,
        available_credits: Optional[float] = None,
        application_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_credits is not None:
            error_details["required_credits"] = required_credits
        if available_credits is not None:
            error_details["available_credits"] = available_credits
        
        super().__init__(
            message=message,
            billing_issue="insufficient_credits",
            application_id=application_id,
            details=error_details
        )
        self.error_code = "INSUFFICIENT_CREDITS"