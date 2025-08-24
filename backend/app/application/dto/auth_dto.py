#!/usr/bin/env python3
"""
Authentication Data Transfer Objects (DTOs)

Defines request and response structures for authentication operations
including registration, login, token refresh, and password management.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegistrationRequest(BaseModel):
    """Request model for user registration."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
        example="SecurePassword123!"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User full name",
        example="John Doe"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="User phone number",
        example="+1234567890"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        
        # Remove spaces and common separators
        phone_clean = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check if it's a valid phone number format
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone_clean):
            raise ValueError('Invalid phone number format')
        
        return v


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        description="User password",
        example="SecurePassword123!"
    )
    remember_me: bool = Field(
        default=False,
        description="Whether to extend token expiration"
    )


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )


class PasswordResetRequest(BaseModel):
    """Request model for password reset initiation."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )


class PasswordResetConfirmRequest(BaseModel):
    """Request model for password reset confirmation."""
    
    token: str = Field(
        ...,
        description="Password reset token",
        example="abc123def456"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
        example="NewSecurePassword123!"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


class PasswordChangeRequest(BaseModel):
    """Request model for password change."""
    
    current_password: str = Field(
        ...,
        description="Current password",
        example="CurrentPassword123!"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
        example="NewSecurePassword123!"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v


class AccountActivationRequest(BaseModel):
    """Request model for account activation."""
    
    token: str = Field(
        ...,
        description="Account activation token",
        example="abc123def456"
    )


# Response Models

class UserResponse(BaseModel):
    """Response model for user information."""
    
    id: UUID
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    
    access_token: str = Field(
        ...,
        description="JWT access token",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        example=3600
    )
    expires_at: datetime = Field(
        ...,
        description="Access token expiration timestamp"
    )


class LoginResponse(BaseModel):
    """Response model for successful login."""
    
    user: UserResponse
    tokens: TokenResponse
    message: str = Field(
        default="Login successful",
        description="Success message"
    )


class RegistrationResponse(BaseModel):
    """Response model for successful registration."""
    
    user: UserResponse
    message: str = Field(
        default="Registration successful. Please check your email to activate your account.",
        description="Success message"
    )
    activation_required: bool = Field(
        default=True,
        description="Whether account activation is required"
    )


class TokenRefreshResponse(BaseModel):
    """Response model for token refresh."""
    
    tokens: TokenResponse
    message: str = Field(
        default="Tokens refreshed successfully",
        description="Success message"
    )


class PasswordResetResponse(BaseModel):
    """Response model for password reset initiation."""
    
    message: str = Field(
        default="Password reset instructions sent to your email",
        description="Success message"
    )
    email: str = Field(
        ...,
        description="Email address where reset instructions were sent"
    )


class PasswordResetConfirmResponse(BaseModel):
    """Response model for password reset confirmation."""
    
    message: str = Field(
        default="Password reset successfully",
        description="Success message"
    )
    login_required: bool = Field(
        default=True,
        description="Whether user needs to login again"
    )


class PasswordChangeResponse(BaseModel):
    """Response model for password change."""
    
    message: str = Field(
        default="Password changed successfully",
        description="Success message"
    )
    logout_required: bool = Field(
        default=True,
        description="Whether user should logout and login again"
    )


class AccountActivationResponse(BaseModel):
    """Response model for account activation."""
    
    message: str = Field(
        default="Account activated successfully",
        description="Success message"
    )
    user: UserResponse
    login_required: bool = Field(
        default=True,
        description="Whether user needs to login"
    )


class LogoutResponse(BaseModel):
    """Response model for logout."""
    
    message: str = Field(
        default="Logged out successfully",
        description="Success message"
    )
    logged_out_at: datetime = Field(
        ...,
        description="Logout timestamp"
    )


class UserProfileUpdateRequest(BaseModel):
    """Request model for user profile update."""
    
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="User full name"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="User phone number"
    )
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is None:
            return v
        
        # Remove spaces and common separators
        phone_clean = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check if it's a valid phone number format
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone_clean):
            raise ValueError('Invalid phone number format')
        
        return v


class UserProfileUpdateResponse(BaseModel):
    """Response model for user profile update."""
    
    user: UserResponse
    message: str = Field(
        default="Profile updated successfully",
        description="Success message"
    )