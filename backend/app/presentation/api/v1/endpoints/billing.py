#!/usr/bin/env python3
"""
Billing API Endpoints

FastAPI endpoints for billing, invoicing, and cost management operations.
Provides comprehensive billing functionality for the SEELE-E system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from .....core.security.dependencies import get_current_user_from_token as get_current_user, get_current_admin_user, CurrentUser
from .....infrastructure.database.session import get_async_db_session
# CurrentUser is imported from dependencies
from .....domain.entities.billing import BillingPeriod, TransactionType, CostCategory, AIProviderCost
from .....domain.services.billing_service import BillingService
from .....infrastructure.repositories.billing_repository_impl import BillingRepositoryImpl
from .....infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from .....infrastructure.repositories.application_repository_impl import ApplicationRepositoryImpl
from .....infrastructure.repositories.processing_job_repository_impl import ProcessingJobRepositoryImpl
from .....core.exceptions.base import NotFoundError, ValidationException, BillingError

router = APIRouter()

# Pydantic models for request/response
class BillingPeriodResponse(BaseModel):
    """Billing period response model."""
    id: UUID
    user_id: UUID
    application_id: Optional[UUID]
    period_type: BillingPeriod
    period_start: datetime
    period_end: datetime
    total_cost: float
    total_credits: float
    total_usage: int
    opening_balance: float
    closing_balance: float
    is_finalized: bool
    is_paid: bool
    is_overdue: bool
    payment_due_date: Optional[datetime]
    paid_at: Optional[datetime]
    payment_method: Optional[str]
    payment_reference: Optional[str]
    invoice_number: Optional[str]
    invoice_generated_at: Optional[datetime]
    invoice_sent_at: Optional[datetime]
    cost_breakdown: Dict[str, Any]
    usage_metrics: Dict[str, Any]
    transactions: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CostBreakdownResponse(BaseModel):
    """Cost breakdown response model."""
    ai_processing: float
    ocr_processing: float
    storage_costs: float
    api_calls: float
    premium_features: float
    subscription_fees: float
    provider_costs: Dict[str, float]
    category_costs: Dict[str, float]
    total_cost: float

class UsageStatsResponse(BaseModel):
    """Usage statistics response model."""
    period: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    total_cost: float
    average_cost_per_request: float
    total_tokens: int
    provider_usage: Dict[str, int]
    daily_breakdown: List[Dict[str, Any]]

class TransactionRequest(BaseModel):
    """Transaction creation request model."""
    transaction_type: TransactionType
    amount: float = Field(..., gt=0, description="Transaction amount in USD")
    description: str = Field(..., min_length=1, max_length=500)
    reference_id: Optional[str] = Field(None, max_length=100)
    application_id: Optional[UUID] = None

class InvoiceRequest(BaseModel):
    """Invoice generation request model."""
    billing_period_id: UUID
    include_usage_details: bool = True
    include_cost_breakdown: bool = True
    send_email: bool = False

class PaymentRequest(BaseModel):
    """Payment processing request model."""
    billing_period_id: UUID
    payment_method: str = Field(..., min_length=1, max_length=50)
    payment_reference: str = Field(..., min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)

class BillingReportRequest(BaseModel):
    """Billing report request model."""
    start_date: date
    end_date: date
    include_transactions: bool = True
    include_usage_metrics: bool = True
    include_cost_breakdown: bool = True
    group_by_application: bool = False
    format: str = Field(default="json", pattern="^(json|csv|pdf)$")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

# Dependency to get billing service
async def get_billing_service(db_session = Depends(get_async_db_session)) -> BillingService:
    """Get billing service instance."""
    billing_repo = BillingRepositoryImpl(db_session)
    user_repo = UserRepositoryImpl(db_session)
    app_repo = ApplicationRepositoryImpl(db_session)
    job_repo = ProcessingJobRepositoryImpl(db_session)
    
    return BillingService(
        billing_repository=billing_repo,
        user_repository=user_repo,
        application_repository=app_repo,
        processing_job_repository=job_repo
    )

@router.get("/current", response_model=BillingPeriodResponse)
async def get_current_billing_period(
    application_id: Optional[UUID] = Query(None, description="Application ID to filter by"),
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get current billing period for the authenticated user."""
    try:
        billing = await billing_service.get_current_billing_period(
            user_id=current_user.user_id,
            application_id=application_id
        )
        return billing
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing period: {str(e)}")

@router.get("/periods", response_model=List[BillingPeriodResponse])
async def get_billing_periods(
    application_id: Optional[UUID] = Query(None, description="Application ID to filter by"),
    period_type: Optional[BillingPeriod] = Query(None, description="Period type to filter by"),
    is_finalized: Optional[bool] = Query(None, description="Filter by finalized status"),
    is_paid: Optional[bool] = Query(None, description="Filter by payment status"),
    limit: int = Query(10, ge=1, le=100, description="Number of periods to return"),
    offset: int = Query(0, ge=0, description="Number of periods to skip"),
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get billing periods for the authenticated user."""
    try:
        periods = await billing_service.get_billing_periods(
            user_id=current_user.user_id,
            application_id=application_id,
            period_type=period_type,
            is_finalized=is_finalized,
            is_paid=is_paid,
            limit=limit,
            offset=offset
        )
        return periods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing periods: {str(e)}")

@router.get("/periods/{period_id}", response_model=BillingPeriodResponse)
async def get_billing_period(
    period_id: UUID = Path(..., description="Billing period ID"),
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get specific billing period by ID."""
    try:
        billing = await billing_service.get_billing_period_by_id(period_id)
        
        # Check if user owns this billing period
        if billing.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied to this billing period")
        
        return billing
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing period: {str(e)}")

@router.get("/balance", response_model=Dict[str, float])
async def get_user_balance(
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get current user balance."""
    try:
        balance = await billing_service.get_user_balance(current_user.user_id)
        return {
            "balance": float(balance),
            "currency": "USD"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")

@router.get("/usage-stats", response_model=UsageStatsResponse)
async def get_usage_statistics(
    period: BillingPeriod = Query(BillingPeriod.MONTHLY, description="Period for statistics"),
    application_id: Optional[UUID] = Query(None, description="Application ID to filter by"),
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get usage statistics for the authenticated user."""
    try:
        stats = await billing_service.get_usage_statistics(
            user_id=current_user.user_id,
            period=period,
            application_id=application_id
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage statistics: {str(e)}")

@router.get("/cost-breakdown", response_model=CostBreakdownResponse)
async def get_cost_breakdown(
    period: BillingPeriod = Query(BillingPeriod.MONTHLY, description="Period for cost breakdown"),
    application_id: Optional[UUID] = Query(None, description="Application ID to filter by"),
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get detailed cost breakdown for the authenticated user."""
    try:
        breakdown = await billing_service.get_cost_breakdown(
            user_id=current_user.user_id,
            period=period,
            application_id=application_id
        )
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost breakdown: {str(e)}")

@router.post("/transactions", response_model=BillingPeriodResponse)
async def add_transaction(
    transaction: TransactionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Add a transaction (credit/debit) to user's billing."""
    try:
        billing = await billing_service.add_transaction(
            user_id=current_user.user_id,
            application_id=transaction.application_id,
            transaction_type=transaction.transaction_type,
            amount=Decimal(str(transaction.amount)),
            description=transaction.description,
            reference_id=transaction.reference_id
        )
        return billing
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except BillingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add transaction: {str(e)}")

@router.post("/invoices/generate", response_model=Dict[str, Any])
async def generate_invoice(
    invoice_request: InvoiceRequest,
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Generate invoice for a billing period."""
    try:
        # First verify the billing period belongs to the user
        billing = await billing_service.get_billing_period_by_id(invoice_request.billing_period_id)
        if billing.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied to this billing period")
        
        invoice_data = await billing_service.generate_invoice(
            billing_period_id=invoice_request.billing_period_id,
            include_usage_details=invoice_request.include_usage_details,
            include_cost_breakdown=invoice_request.include_cost_breakdown,
            send_email=invoice_request.send_email
        )
        return invoice_data
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BillingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate invoice: {str(e)}")

@router.post("/payments/process", response_model=BillingPeriodResponse)
async def process_payment(
    payment_request: PaymentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Process payment for a billing period."""
    try:
        # First verify the billing period belongs to the user
        billing = await billing_service.get_billing_period_by_id(payment_request.billing_period_id)
        if billing.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied to this billing period")
        
        updated_billing = await billing_service.process_payment(
            billing_period_id=payment_request.billing_period_id,
            payment_method=payment_request.payment_method,
            payment_reference=payment_request.payment_reference,
            amount=Decimal(str(payment_request.amount)) if payment_request.amount else None
        )
        return updated_billing
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BillingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process payment: {str(e)}")

@router.get("/reports/generate")
async def generate_billing_report(
    report_request: BillingReportRequest = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Generate billing report for the specified date range."""
    try:
        report_data = await billing_service.generate_billing_report(
            user_id=current_user.user_id,
            start_date=report_request.start_date,
            end_date=report_request.end_date,
            include_transactions=report_request.include_transactions,
            include_usage_metrics=report_request.include_usage_metrics,
            include_cost_breakdown=report_request.include_cost_breakdown,
            group_by_application=report_request.group_by_application
        )
        
        if report_request.format == "json":
            return report_data
        elif report_request.format == "csv":
            # Convert to CSV format
            csv_content = await billing_service.export_report_as_csv(report_data)
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=billing_report_{report_request.start_date}_{report_request.end_date}.csv"}
            )
        elif report_request.format == "pdf":
            # Convert to PDF format
            pdf_content = await billing_service.export_report_as_pdf(report_data)
            return StreamingResponse(
                iter([pdf_content]),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=billing_report_{report_request.start_date}_{report_request.end_date}.pdf"}
            )
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

# Admin endpoints
@router.get("/admin/users/{user_id}/billing", response_model=List[BillingPeriodResponse])
async def get_user_billing_periods_admin(
    user_id: UUID = Path(..., description="User ID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: CurrentUser = Depends(get_current_admin_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get billing periods for any user (admin only)."""
    try:
        periods = await billing_service.get_billing_periods(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return periods
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user billing periods: {str(e)}")

@router.post("/admin/users/{user_id}/credit", response_model=BillingPeriodResponse)
async def add_user_credit_admin(
    user_id: UUID = Path(..., description="User ID"),
    amount: float = Query(..., gt=0, description="Credit amount to add"),
    description: str = Query(..., min_length=1, description="Credit description"),
    admin_user: CurrentUser = Depends(get_current_admin_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Add credit to user's account (admin only)."""
    try:
        billing = await billing_service.add_transaction(
            user_id=user_id,
            application_id=None,
            transaction_type=TransactionType.CREDIT,
            amount=Decimal(str(amount)),
            description=f"Admin credit: {description}",
            reference_id=f"admin_{admin_user.user_id}_{datetime.utcnow().timestamp()}"
        )
        return billing
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BillingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add credit: {str(e)}")

@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_billing_stats_admin(
    period: BillingPeriod = Query(BillingPeriod.MONTHLY, description="Period for statistics"),
    admin_user: CurrentUser = Depends(get_current_admin_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get overall billing statistics (admin only)."""
    try:
        stats = await billing_service.get_admin_billing_stats(period)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get billing stats: {str(e)}")