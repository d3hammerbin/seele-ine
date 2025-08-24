#!/usr/bin/env python3
"""
API Key Data Transfer Objects (DTOs)

Defines request and response structures for API key management operations
including creation, rotation, listing, and management of CLIENT_KEY and CLIENT_SECRET pairs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class APIKeyCreateRequest(BaseModel):
    """Request model for API key creation."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Application name",
        example="My Web App"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Application description",
        example="Web application for processing INE credentials"
    )
    expires_days: Optional[int] = Field(
        default=365,
        ge=1,
        le=3650,  # Max 10 years
        description="API key expiration in days (1-3650)",
        example=365
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate application name."""
        # Remove extra whitespace
        v = v.strip()
        
        if not v:
            raise ValueError('Application name cannot be empty')
        
        # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Application name can only contain letters, numbers, spaces, hyphens, and underscores')
        
        return v


class APIKeyRotateRequest(BaseModel):
    """Request model for API key rotation."""
    
    expires_days: Optional[int] = Field(
        default=365,
        ge=1,
        le=3650,
        description="New API key expiration in days (1-3650)",
        example=365
    )
    reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Reason for rotation",
        example="Scheduled rotation"
    )


class APIKeyUpdateRequest(BaseModel):
    """Request model for API key metadata update."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="New application name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="New application description"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate application name."""
        if v is None:
            return v
        
        # Remove extra whitespace
        v = v.strip()
        
        if not v:
            raise ValueError('Application name cannot be empty')
        
        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Application name can only contain letters, numbers, spaces, hyphens, and underscores')
        
        return v


# Response Models

class APIKeyInfo(BaseModel):
    """Model for API key information (without secret)."""
    
    application_id: UUID
    name: str
    description: Optional[str]
    client_key: str
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    usage_count: int
    is_active: bool
    is_expired: bool
    
    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Response model for API key creation."""
    
    application_id: UUID
    name: str
    description: Optional[str]
    client_key: str = Field(
        ...,
        description="CLIENT_KEY for API authentication",
        example="sk_live_1234567890abcdef"
    )
    client_secret: str = Field(
        ...,
        description="CLIENT_SECRET for API authentication (shown only once)",
        example="cs_live_abcdef1234567890"
    )
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool
    warning: str = Field(
        default="Store the CLIENT_SECRET securely. It will not be shown again.",
        description="Security warning"
    )


class APIKeyListResponse(BaseModel):
    """Response model for API key listing."""
    
    total: int = Field(
        ...,
        description="Total number of API keys",
        example=5
    )
    api_keys: List[APIKeyInfo] = Field(
        ...,
        description="List of API key information"
    )


class APIKeyDetailResponse(BaseModel):
    """Response model for API key details."""
    
    application_id: UUID
    name: str
    description: Optional[str]
    client_key: str
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    usage_count: int
    is_active: bool
    is_expired: bool


class APIKeyRotateResponse(BaseModel):
    """Response model for API key rotation."""
    
    application_id: UUID
    name: str
    client_key: str = Field(
        ...,
        description="CLIENT_KEY (unchanged)"
    )
    client_secret: str = Field(
        ...,
        description="New CLIENT_SECRET (shown only once)",
        example="cs_live_newabcdef1234567890"
    )
    expires_at: Optional[datetime]
    rotated_at: datetime
    warning: str = Field(
        default="Store the new CLIENT_SECRET securely. The old one is now invalid.",
        description="Security warning"
    )


class APIKeyRevokeResponse(BaseModel):
    """Response model for API key revocation."""
    
    application_id: UUID
    name: str
    client_key: str
    revoked_at: datetime
    message: str = Field(
        default="API key has been revoked successfully",
        description="Success message"
    )


class APIKeyReactivateResponse(BaseModel):
    """Response model for API key reactivation."""
    
    application_id: UUID
    name: str
    client_key: str
    reactivated_at: datetime
    message: str = Field(
        default="API key has been reactivated successfully",
        description="Success message"
    )


class APIKeyUpdateResponse(BaseModel):
    """Response model for API key metadata update."""
    
    application_id: UUID
    name: str
    description: Optional[str]
    client_key: str
    updated_at: datetime
    message: str = Field(
        default="API key information updated successfully",
        description="Success message"
    )


class APIKeyUsageStats(BaseModel):
    """Model for API key usage statistics."""
    
    application_id: UUID
    name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    last_request_at: Optional[datetime]
    requests_today: int
    requests_this_month: int
    average_requests_per_day: float
    
    class Config:
        from_attributes = True


class APIKeyUsageStatsResponse(BaseModel):
    """Response model for API key usage statistics."""
    
    stats: List[APIKeyUsageStats]
    total_applications: int
    period_start: datetime
    period_end: datetime
    generated_at: datetime


class APIKeyValidationRequest(BaseModel):
    """Request model for API key validation."""
    
    client_key: str = Field(
        ...,
        description="CLIENT_KEY to validate",
        example="sk_live_1234567890abcdef"
    )
    client_secret: str = Field(
        ...,
        description="CLIENT_SECRET to validate",
        example="cs_live_abcdef1234567890"
    )
    signature: Optional[str] = Field(
        None,
        description="Request signature for additional validation"
    )
    timestamp: Optional[int] = Field(
        None,
        description="Request timestamp for signature validation"
    )


class APIKeyValidationResponse(BaseModel):
    """Response model for API key validation."""
    
    is_valid: bool = Field(
        ...,
        description="Whether the API key is valid"
    )
    application_id: Optional[UUID] = Field(
        None,
        description="Application ID if key is valid"
    )
    application_name: Optional[str] = Field(
        None,
        description="Application name if key is valid"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Key expiration time if valid"
    )
    is_expired: bool = Field(
        default=False,
        description="Whether the key is expired"
    )
    is_active: bool = Field(
        default=False,
        description="Whether the key is active"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors if invalid"
    )
    validated_at: datetime = Field(
        ...,
        description="Validation timestamp"
    )


class BulkAPIKeyActionRequest(BaseModel):
    """Request model for bulk API key actions."""
    
    application_ids: List[UUID] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of application IDs to perform action on"
    )
    action: str = Field(
        ...,
        description="Action to perform: 'revoke', 'reactivate', or 'delete'",
        pattern="^(revoke|reactivate|delete)$"
    )
    reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Reason for bulk action"
    )


class BulkAPIKeyActionResponse(BaseModel):
    """Response model for bulk API key actions."""
    
    total_requested: int
    successful: int
    failed: int
    results: List[Dict[str, Any]] = Field(
        ...,
        description="Detailed results for each application"
    )
    action: str
    performed_at: datetime
    message: str