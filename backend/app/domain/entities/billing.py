#!/usr/bin/env python3
"""
Entidad Billing para SEELE-E Backend

Define las entidades de dominio para facturación, costos, transacciones
y reportes financieros del sistema.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from decimal import Decimal, ROUND_HALF_UP

from ...core.exceptions.base import ValidationException, BusinessLogicError


class TransactionType(str, Enum):
    """
    Tipos de transacción.
    """
    CHARGE = "charge"
    REFUND = "refund"
    CREDIT = "credit"
    DEBIT = "debit"
    ADJUSTMENT = "adjustment"


class TransactionStatus(str, Enum):
    """
    Estados de transacción.
    """
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class BillingPeriod(str, Enum):
    """
    Períodos de facturación.
    """
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    PAY_AS_YOU_GO = "pay_as_you_go"


class CostCategory(str, Enum):
    """
    Categorías de costo.
    """
    OCR_PROCESSING = "ocr_processing"
    AI_PROCESSING = "ai_processing"
    IMAGE_STORAGE = "image_storage"
    DATA_STORAGE = "data_storage"
    API_REQUESTS = "api_requests"
    BANDWIDTH = "bandwidth"
    PREMIUM_FEATURES = "premium_features"
    SUPPORT = "support"


class AIProviderCost(str, Enum):
    """
    Proveedores de IA para costos.
    """
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    CLAUDE = "claude"


@dataclass
class CostBreakdown:
    """
    Desglose de costos por categoría.
    """
    # Costos de procesamiento
    ocr_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    ai_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Costos de almacenamiento
    image_storage_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    data_storage_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Costos de API
    api_requests_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    bandwidth_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Costos adicionales
    premium_features_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    support_cost_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Desglose por proveedor de IA
    ai_provider_costs: Dict[AIProviderCost, Decimal] = field(default_factory=dict)
    
    @property
    def total_processing_cost(self) -> Decimal:
        """Costo total de procesamiento."""
        return self.ocr_cost_usd + self.ai_cost_usd
    
    @property
    def total_storage_cost(self) -> Decimal:
        """Costo total de almacenamiento."""
        return self.image_storage_cost_usd + self.data_storage_cost_usd
    
    @property
    def total_api_cost(self) -> Decimal:
        """Costo total de API."""
        return self.api_requests_cost_usd + self.bandwidth_cost_usd
    
    @property
    def total_additional_cost(self) -> Decimal:
        """Costo total adicional."""
        return self.premium_features_cost_usd + self.support_cost_usd
    
    @property
    def total_cost(self) -> Decimal:
        """Costo total."""
        return (
            self.total_processing_cost +
            self.total_storage_cost +
            self.total_api_cost +
            self.total_additional_cost
        )
    
    def add_cost(self, category: CostCategory, amount: Decimal, provider: AIProviderCost = None) -> None:
        """Añade costo a una categoría específica."""
        if category == CostCategory.OCR_PROCESSING:
            self.ocr_cost_usd += amount
        elif category == CostCategory.AI_PROCESSING:
            self.ai_cost_usd += amount
            if provider:
                if provider not in self.ai_provider_costs:
                    self.ai_provider_costs[provider] = Decimal('0.00')
                self.ai_provider_costs[provider] += amount
        elif category == CostCategory.IMAGE_STORAGE:
            self.image_storage_cost_usd += amount
        elif category == CostCategory.DATA_STORAGE:
            self.data_storage_cost_usd += amount
        elif category == CostCategory.API_REQUESTS:
            self.api_requests_cost_usd += amount
        elif category == CostCategory.BANDWIDTH:
            self.bandwidth_cost_usd += amount
        elif category == CostCategory.PREMIUM_FEATURES:
            self.premium_features_cost_usd += amount
        elif category == CostCategory.SUPPORT:
            self.support_cost_usd += amount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "ocr_cost_usd": float(self.ocr_cost_usd),
            "ai_cost_usd": float(self.ai_cost_usd),
            "image_storage_cost_usd": float(self.image_storage_cost_usd),
            "data_storage_cost_usd": float(self.data_storage_cost_usd),
            "api_requests_cost_usd": float(self.api_requests_cost_usd),
            "bandwidth_cost_usd": float(self.bandwidth_cost_usd),
            "premium_features_cost_usd": float(self.premium_features_cost_usd),
            "support_cost_usd": float(self.support_cost_usd),
            "total_processing_cost": float(self.total_processing_cost),
            "total_storage_cost": float(self.total_storage_cost),
            "total_api_cost": float(self.total_api_cost),
            "total_additional_cost": float(self.total_additional_cost),
            "total_cost": float(self.total_cost),
            "ai_provider_costs": {
                provider.value: float(cost) 
                for provider, cost in self.ai_provider_costs.items()
            }
        }


@dataclass
class UsageMetrics:
    """
    Métricas de uso para facturación.
    """
    # Métricas de procesamiento
    total_credentials_processed: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    
    # Métricas de API
    total_api_requests: int = 0
    successful_api_requests: int = 0
    failed_api_requests: int = 0
    
    # Métricas de almacenamiento
    total_images_stored: int = 0
    total_storage_bytes: int = 0
    average_image_size_bytes: int = 0
    
    # Métricas de IA
    total_ai_tokens_used: int = 0
    ai_requests_by_provider: Dict[AIProviderCost, int] = field(default_factory=dict)
    ai_tokens_by_provider: Dict[AIProviderCost, int] = field(default_factory=dict)
    
    # Métricas de tiempo
    total_processing_time_seconds: float = 0.0
    average_processing_time_seconds: float = 0.0
    
    # Métricas de calidad
    average_quality_score: float = 0.0
    high_quality_extractions: int = 0
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito de extracciones."""
        total = self.successful_extractions + self.failed_extractions
        if total == 0:
            return 0.0
        return (self.successful_extractions / total) * 100
    
    @property
    def api_success_rate(self) -> float:
        """Tasa de éxito de API."""
        if self.total_api_requests == 0:
            return 0.0
        return (self.successful_api_requests / self.total_api_requests) * 100
    
    @property
    def quality_rate(self) -> float:
        """Tasa de extracciones de alta calidad."""
        if self.successful_extractions == 0:
            return 0.0
        return (self.high_quality_extractions / self.successful_extractions) * 100
    
    def add_processing_metrics(
        self, 
        success: bool, 
        processing_time: float = 0.0,
        quality_score: float = 0.0
    ) -> None:
        """Añade métricas de procesamiento."""
        self.total_credentials_processed += 1
        
        if success:
            self.successful_extractions += 1
            if quality_score >= 80:  # Alta calidad
                self.high_quality_extractions += 1
            
            # Actualizar promedio de calidad
            if self.successful_extractions == 1:
                self.average_quality_score = quality_score
            else:
                total_score = self.average_quality_score * (self.successful_extractions - 1) + quality_score
                self.average_quality_score = total_score / self.successful_extractions
        else:
            self.failed_extractions += 1
        
        # Actualizar tiempo de procesamiento
        if processing_time > 0:
            self.total_processing_time_seconds += processing_time
            self.average_processing_time_seconds = (
                self.total_processing_time_seconds / self.total_credentials_processed
            )
    
    def add_api_metrics(self, success: bool) -> None:
        """Añade métricas de API."""
        self.total_api_requests += 1
        if success:
            self.successful_api_requests += 1
        else:
            self.failed_api_requests += 1
    
    def add_storage_metrics(self, image_size_bytes: int) -> None:
        """Añade métricas de almacenamiento."""
        self.total_images_stored += 1
        self.total_storage_bytes += image_size_bytes
        self.average_image_size_bytes = self.total_storage_bytes // self.total_images_stored
    
    def add_ai_metrics(self, provider: AIProviderCost, tokens_used: int) -> None:
        """Añade métricas de IA."""
        self.total_ai_tokens_used += tokens_used
        
        if provider not in self.ai_requests_by_provider:
            self.ai_requests_by_provider[provider] = 0
            self.ai_tokens_by_provider[provider] = 0
        
        self.ai_requests_by_provider[provider] += 1
        self.ai_tokens_by_provider[provider] += tokens_used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "total_credentials_processed": self.total_credentials_processed,
            "successful_extractions": self.successful_extractions,
            "failed_extractions": self.failed_extractions,
            "success_rate": self.success_rate,
            "total_api_requests": self.total_api_requests,
            "successful_api_requests": self.successful_api_requests,
            "failed_api_requests": self.failed_api_requests,
            "api_success_rate": self.api_success_rate,
            "total_images_stored": self.total_images_stored,
            "total_storage_bytes": self.total_storage_bytes,
            "average_image_size_bytes": self.average_image_size_bytes,
            "total_ai_tokens_used": self.total_ai_tokens_used,
            "ai_requests_by_provider": {
                provider.value: count 
                for provider, count in self.ai_requests_by_provider.items()
            },
            "ai_tokens_by_provider": {
                provider.value: tokens 
                for provider, tokens in self.ai_tokens_by_provider.items()
            },
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "average_processing_time_seconds": self.average_processing_time_seconds,
            "average_quality_score": self.average_quality_score,
            "high_quality_extractions": self.high_quality_extractions,
            "quality_rate": self.quality_rate
        }


@dataclass
class Transaction:
    """
    Representa una transacción financiera.
    """
    # Identificadores
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    application_id: UUID = field(default_factory=uuid4)
    billing_period_id: Optional[UUID] = None
    
    # Información de la transacción
    transaction_type: TransactionType = TransactionType.CHARGE
    status: TransactionStatus = TransactionStatus.PENDING
    
    # Montos
    amount_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    tax_amount_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_amount_usd: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Descripción y categoría
    description: str = ""
    category: CostCategory = CostCategory.API_REQUESTS
    
    # Detalles del procesamiento
    processing_job_id: Optional[UUID] = None
    credential_id: Optional[UUID] = None
    
    # Información de pago
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Cálculos después de la inicialización."""
        if self.total_amount_usd == Decimal('0.00'):
            self.total_amount_usd = self.amount_usd + self.tax_amount_usd
    
    @property
    def is_completed(self) -> bool:
        """Verifica si la transacción está completada."""
        return self.status == TransactionStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Verifica si la transacción está pendiente."""
        return self.status == TransactionStatus.PENDING
    
    def complete(self, payment_reference: str = "") -> None:
        """Marca la transacción como completada."""
        if self.status != TransactionStatus.PENDING:
            raise BusinessLogicError(
                message=f"No se puede completar transacción desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = TransactionStatus.COMPLETED
        self.processed_at = datetime.utcnow()
        
        if payment_reference:
            self.payment_reference = payment_reference
    
    def fail(self, reason: str = "") -> None:
        """Marca la transacción como fallida."""
        if self.status not in [TransactionStatus.PENDING]:
            raise BusinessLogicError(
                message=f"No se puede fallar transacción desde estado {self.status.value}",
                details={"current_status": self.status.value}
            )
        
        self.status = TransactionStatus.FAILED
        self.processed_at = datetime.utcnow()
        
        if reason:
            self.metadata["failure_reason"] = reason
    
    def refund(self, refund_amount: Decimal = None, reason: str = "") -> 'Transaction':
        """Crea una transacción de reembolso."""
        if self.status != TransactionStatus.COMPLETED:
            raise BusinessLogicError(
                message="Solo se pueden reembolsar transacciones completadas",
                details={"current_status": self.status.value}
            )
        
        if self.transaction_type != TransactionType.CHARGE:
            raise BusinessLogicError(
                message="Solo se pueden reembolsar cargos",
                details={"transaction_type": self.transaction_type.value}
            )
        
        refund_amount = refund_amount or self.total_amount_usd
        
        if refund_amount > self.total_amount_usd:
            raise BusinessLogicError(
                message="El monto de reembolso no puede ser mayor al monto original",
                details={
                    "refund_amount": float(refund_amount),
                    "original_amount": float(self.total_amount_usd)
                }
            )
        
        # Crear transacción de reembolso
        refund_transaction = Transaction(
            user_id=self.user_id,
            application_id=self.application_id,
            billing_period_id=self.billing_period_id,
            transaction_type=TransactionType.REFUND,
            status=TransactionStatus.COMPLETED,
            amount_usd=refund_amount,
            total_amount_usd=refund_amount,
            description=f"Reembolso de transacción {self.id}",
            category=self.category,
            processing_job_id=self.processing_job_id,
            credential_id=self.credential_id,
            metadata={
                "original_transaction_id": str(self.id),
                "refund_reason": reason
            }
        )
        
        # Marcar transacción original como reembolsada
        self.status = TransactionStatus.REFUNDED
        self.metadata["refunded_at"] = datetime.utcnow().isoformat()
        self.metadata["refund_transaction_id"] = str(refund_transaction.id)
        
        return refund_transaction
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "application_id": str(self.application_id),
            "billing_period_id": str(self.billing_period_id) if self.billing_period_id else None,
            "transaction_type": self.transaction_type.value,
            "status": self.status.value,
            "amount_usd": float(self.amount_usd),
            "tax_amount_usd": float(self.tax_amount_usd),
            "total_amount_usd": float(self.total_amount_usd),
            "description": self.description,
            "category": self.category.value,
            "processing_job_id": str(self.processing_job_id) if self.processing_job_id else None,
            "credential_id": str(self.credential_id) if self.credential_id else None,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "is_completed": self.is_completed,
            "is_pending": self.is_pending,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "metadata": self.metadata
        }


@dataclass
class BillingPeriodData:
    """
    Datos de un período de facturación.
    """
    # Identificadores
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    application_id: UUID = field(default_factory=uuid4)
    
    # Período
    period_type: BillingPeriod = BillingPeriod.MONTHLY
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Costos y métricas
    cost_breakdown: CostBreakdown = field(default_factory=CostBreakdown)
    usage_metrics: UsageMetrics = field(default_factory=UsageMetrics)
    
    # Transacciones
    transactions: List[Transaction] = field(default_factory=list)
    
    # Estado
    is_closed: bool = False
    closed_at: Optional[datetime] = None
    
    # Límites y presupuesto
    budget_limit_usd: Optional[Decimal] = None
    alert_threshold_percentage: float = 80.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_current_period(self) -> bool:
        """Verifica si es el período actual."""
        now = datetime.utcnow()
        return self.period_start <= now <= self.period_end
    
    @property
    def is_over_budget(self) -> bool:
        """Verifica si se excedió el presupuesto."""
        if not self.budget_limit_usd:
            return False
        return self.cost_breakdown.total_cost >= self.budget_limit_usd
    
    @property
    def budget_usage_percentage(self) -> float:
        """Porcentaje de uso del presupuesto."""
        if not self.budget_limit_usd or self.budget_limit_usd == 0:
            return 0.0
        return float((self.cost_breakdown.total_cost / self.budget_limit_usd) * 100)
    
    @property
    def should_alert(self) -> bool:
        """Verifica si se debe enviar alerta de presupuesto."""
        return self.budget_usage_percentage >= self.alert_threshold_percentage
    
    @property
    def days_remaining(self) -> int:
        """Días restantes en el período."""
        if self.is_closed:
            return 0
        
        now = datetime.utcnow()
        if now > self.period_end:
            return 0
        
        return (self.period_end - now).days
    
    @property
    def total_transactions_amount(self) -> Decimal:
        """Monto total de transacciones completadas."""
        return sum(
            t.total_amount_usd for t in self.transactions 
            if t.is_completed and t.transaction_type == TransactionType.CHARGE
        )
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Añade una transacción al período."""
        transaction.billing_period_id = self.id
        self.transactions.append(transaction)
        self.updated_at = datetime.utcnow()
    
    def add_cost(
        self, 
        category: CostCategory, 
        amount: Decimal, 
        provider: AIProviderCost = None,
        description: str = ""
    ) -> Transaction:
        """Añade un costo y crea la transacción correspondiente."""
        # Añadir al desglose de costos
        self.cost_breakdown.add_cost(category, amount, provider)
        
        # Crear transacción
        transaction = Transaction(
            user_id=self.user_id,
            application_id=self.application_id,
            billing_period_id=self.id,
            transaction_type=TransactionType.CHARGE,
            status=TransactionStatus.COMPLETED,
            amount_usd=amount,
            total_amount_usd=amount,
            description=description or f"Costo de {category.value}",
            category=category,
            processed_at=datetime.utcnow()
        )
        
        self.add_transaction(transaction)
        return transaction
    
    def close_period(self) -> None:
        """Cierra el período de facturación."""
        if self.is_closed:
            raise BusinessLogicError(
                message="El período ya está cerrado",
                details={"period_id": str(self.id)}
            )
        
        self.is_closed = True
        self.closed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def generate_next_period(self) -> 'BillingPeriodData':
        """Genera el siguiente período de facturación."""
        if not self.is_closed:
            raise BusinessLogicError(
                message="No se puede generar el siguiente período sin cerrar el actual",
                details={"period_id": str(self.id)}
            )
        
        # Calcular fechas del siguiente período
        if self.period_type == BillingPeriod.MONTHLY:
            next_start = self.period_end
            next_end = next_start + timedelta(days=30)
        elif self.period_type == BillingPeriod.QUARTERLY:
            next_start = self.period_end
            next_end = next_start + timedelta(days=90)
        elif self.period_type == BillingPeriod.YEARLY:
            next_start = self.period_end
            next_end = next_start + timedelta(days=365)
        else:  # PAY_AS_YOU_GO
            next_start = datetime.utcnow()
            next_end = next_start + timedelta(days=30)  # Default a mensual
        
        return BillingPeriodData(
            user_id=self.user_id,
            application_id=self.application_id,
            period_type=self.period_type,
            period_start=next_start,
            period_end=next_end,
            budget_limit_usd=self.budget_limit_usd,
            alert_threshold_percentage=self.alert_threshold_percentage
        )
    
    def to_dict(self, include_transactions: bool = True) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "application_id": str(self.application_id),
            "period_type": self.period_type.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "cost_breakdown": self.cost_breakdown.to_dict(),
            "usage_metrics": self.usage_metrics.to_dict(),
            "is_closed": self.is_closed,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "budget_limit_usd": float(self.budget_limit_usd) if self.budget_limit_usd else None,
            "alert_threshold_percentage": self.alert_threshold_percentage,
            "is_current_period": self.is_current_period,
            "is_over_budget": self.is_over_budget,
            "budget_usage_percentage": self.budget_usage_percentage,
            "should_alert": self.should_alert,
            "days_remaining": self.days_remaining,
            "total_transactions_amount": float(self.total_transactions_amount),
            "transactions_count": len(self.transactions),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if include_transactions:
            data["transactions"] = [t.to_dict() for t in self.transactions]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BillingPeriodData':
        """Crea una instancia desde diccionario."""
        # Convertir strings a enums
        if "period_type" in data and isinstance(data["period_type"], str):
            data["period_type"] = BillingPeriod(data["period_type"])
        
        # Convertir strings a UUID
        uuid_fields = ["id", "user_id", "application_id"]
        for field in uuid_fields:
            if field in data and isinstance(data[field], str):
                data[field] = UUID(data[field])
        
        # Convertir strings a datetime
        datetime_fields = ["period_start", "period_end", "closed_at", "created_at", "updated_at"]
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convertir Decimal
        if "budget_limit_usd" in data and data["budget_limit_usd"] is not None:
            data["budget_limit_usd"] = Decimal(str(data["budget_limit_usd"]))
        
        # Convertir objetos anidados
        if "cost_breakdown" in data and isinstance(data["cost_breakdown"], dict):
            breakdown_data = data["cost_breakdown"]
            
            # Convertir Decimal
            decimal_fields = [
                "ocr_cost_usd", "ai_cost_usd", "image_storage_cost_usd", 
                "data_storage_cost_usd", "api_requests_cost_usd", "bandwidth_cost_usd",
                "premium_features_cost_usd", "support_cost_usd"
            ]
            for field in decimal_fields:
                if field in breakdown_data:
                    breakdown_data[field] = Decimal(str(breakdown_data[field]))
            
            # Convertir ai_provider_costs
            if "ai_provider_costs" in breakdown_data:
                provider_costs = {}
                for provider_str, cost in breakdown_data["ai_provider_costs"].items():
                    provider_costs[AIProviderCost(provider_str)] = Decimal(str(cost))
                breakdown_data["ai_provider_costs"] = provider_costs
            
            data["cost_breakdown"] = CostBreakdown(**breakdown_data)
        
        if "usage_metrics" in data and isinstance(data["usage_metrics"], dict):
            metrics_data = data["usage_metrics"]
            
            # Convertir diccionarios de proveedores
            for field in ["ai_requests_by_provider", "ai_tokens_by_provider"]:
                if field in metrics_data:
                    provider_dict = {}
                    for provider_str, value in metrics_data[field].items():
                        provider_dict[AIProviderCost(provider_str)] = value
                    metrics_data[field] = provider_dict
            
            data["usage_metrics"] = UsageMetrics(**metrics_data)
        
        if "transactions" in data and isinstance(data["transactions"], list):
            transactions = []
            for trans_data in data["transactions"]:
                if isinstance(trans_data, dict):
                    # Convertir enums
                    if "transaction_type" in trans_data:
                        trans_data["transaction_type"] = TransactionType(trans_data["transaction_type"])
                    if "status" in trans_data:
                        trans_data["status"] = TransactionStatus(trans_data["status"])
                    if "category" in trans_data:
                        trans_data["category"] = CostCategory(trans_data["category"])
                    
                    # Convertir UUID
                    uuid_fields = ["id", "user_id", "application_id", "billing_period_id", "processing_job_id", "credential_id"]
                    for field in uuid_fields:
                        if field in trans_data and isinstance(trans_data[field], str):
                            trans_data[field] = UUID(trans_data[field])
                    
                    # Convertir Decimal
                    decimal_fields = ["amount_usd", "tax_amount_usd", "total_amount_usd"]
                    for field in decimal_fields:
                        if field in trans_data:
                            trans_data[field] = Decimal(str(trans_data[field]))
                    
                    # Convertir datetime
                    datetime_fields = ["created_at", "processed_at"]
                    for field in datetime_fields:
                        if field in trans_data and isinstance(trans_data[field], str):
                            trans_data[field] = datetime.fromisoformat(trans_data[field])
                    
                    transactions.append(Transaction(**trans_data))
            
            data["transactions"] = transactions
        
        return cls(**data)