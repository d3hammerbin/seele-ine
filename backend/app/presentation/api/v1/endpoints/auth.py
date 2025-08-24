#!/usr/bin/env python3
"""
Authentication API Endpoints

Provides REST API endpoints for user authentication including:
- User registration and account activation
- User login and logout
- Token refresh and management
- Password reset and change
- Profile management
"""

from typing import Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .....core.config.settings import get_settings
from .....core.exceptions.base import (
    ValidationException, AuthenticationException, AuthorizationException,
    NotFoundError, BusinessLogicError
)
from .....core.security.dependencies import (
    get_current_user, get_current_admin_user, CurrentUser
)
from .....infrastructure.database.session import get_async_db_session
from .....infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from .....application.use_cases.auth_use_cases import AuthenticationUseCase
from .....application.dto.auth_dto import (
    UserRegistrationRequest, UserLoginRequest, TokenRefreshRequest,
    PasswordResetRequest, PasswordResetConfirmRequest, PasswordChangeRequest,
    AccountActivationRequest, UserProfileUpdateRequest,
    RegistrationResponse, LoginResponse, TokenRefreshResponse,
    PasswordResetResponse, PasswordResetConfirmResponse, PasswordChangeResponse,
    AccountActivationResponse, LogoutResponse, UserProfileUpdateResponse,
    UserResponse
)

# Initialize router
router = APIRouter(tags=["Authentication"])
security = HTTPBearer()
settings = get_settings()


# Dependency to get authentication use case
async def get_auth_use_case(
    db_session: AsyncSession = Depends(get_async_db_session)
) -> AuthenticationUseCase:
    """Get authentication use case with dependencies."""
    user_repository = UserRepositoryImpl(db_session)
    return AuthenticationUseCase(user_repository)


# Background task for sending emails
async def send_activation_email(email: str, token: str, full_name: str):
    """Background task to send account activation email."""
    # TODO: Implement email sending logic
    # This would typically use an email service like SendGrid, AWS SES, etc.
    print(f"Sending activation email to {email} with token {token} for {full_name}")


async def send_password_reset_email(email: str, token: str, full_name: str):
    """Background task to send password reset email."""
    # TODO: Implement email sending logic
    print(f"Sending password reset email to {email} with token {token} for {full_name}")


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account. An activation email will be sent."
)
async def register_user(
    request: UserRegistrationRequest,
    background_tasks: BackgroundTasks,
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> RegistrationResponse:
    """Register a new user account."""
    try:
        result = await auth_use_case.register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            phone=request.phone
        )
        
        # Send activation email in background
        if result.get("activation_token"):
            background_tasks.add_task(
                send_activation_email,
                request.email,
                result["activation_token"],
                request.full_name
            )
        
        return RegistrationResponse(
            user=UserResponse(**result["user"]),
            message="Registration successful. Please check your email to activate your account.",
            activation_required=True
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessLogicError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post(
    "/activate",
    response_model=AccountActivationResponse,
    summary="Activate user account",
    description="Activate a user account using the activation token sent via email."
)
async def activate_account(
    request: AccountActivationRequest,
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> AccountActivationResponse:
    """Activate a user account."""
    try:
        result = await auth_use_case.activate_account(request.token)
        
        return AccountActivationResponse(
            user=UserResponse(**result["user"]),
            message="Account activated successfully. You can now login.",
            login_required=True
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired activation token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account activation failed. Please try again."
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user and return access and refresh tokens."
)
async def login_user(
    request: UserLoginRequest,
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> LoginResponse:
    """Authenticate user and return tokens."""
    try:
        result = await auth_use_case.login_user(request)
        
        return LoginResponse(
            user=UserResponse(**result["user"]),
            tokens=result["tokens"],
            message="Login successful"
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh access token",
    description="Refresh access token using a valid refresh token."
)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> TokenRefreshResponse:
    """Refresh access token."""
    try:
        result = await auth_use_case.refresh_token(request)
        
        return TokenRefreshResponse(
            tokens=result["tokens"],
            message="Tokens refreshed successfully"
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again."
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Logout user and invalidate tokens."
)
async def logout_user(
    current_user: CurrentUser = Depends(get_current_user),
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> LogoutResponse:
    """Logout user and invalidate tokens."""
    try:
        await auth_use_case.logout_user(current_user.id)
        
        return LogoutResponse(
            message="Logged out successfully",
            logged_out_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )


@router.post(
    "/password/reset",
    response_model=PasswordResetResponse,
    summary="Request password reset",
    description="Request a password reset. An email with reset instructions will be sent."
)
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> PasswordResetResponse:
    """Request password reset."""
    try:
        result = await auth_use_case.request_password_reset(request.email)
        
        # Send password reset email in background
        if result.get("reset_token"):
            background_tasks.add_task(
                send_password_reset_email,
                request.email,
                result["reset_token"],
                result["user"]["full_name"]
            )
        
        return PasswordResetResponse(
            message="Password reset instructions sent to your email",
            email=request.email
        )
        
    except NotFoundError:
        # Don't reveal if email exists or not for security
        return PasswordResetResponse(
            message="If the email exists, password reset instructions have been sent",
            email=request.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed. Please try again."
        )


@router.post(
    "/password/reset/confirm",
    response_model=PasswordResetConfirmResponse,
    summary="Confirm password reset",
    description="Reset password using the token sent via email."
)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> PasswordResetConfirmResponse:
    """Confirm password reset."""
    try:
        await auth_use_case.reset_password(
            token=request.token,
            new_password=request.new_password
        )
        
        return PasswordResetConfirmResponse(
            message="Password reset successfully. Please login with your new password.",
            login_required=True
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )


@router.post(
    "/password/change",
    response_model=PasswordChangeResponse,
    summary="Change password",
    description="Change user password (requires authentication)."
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> PasswordChangeResponse:
    """Change user password."""
    try:
        await auth_use_case.change_password(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        return PasswordChangeResponse(
            message="Password changed successfully. Please login again.",
            logout_required=True
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the current authenticated user's profile information."
)
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user)
) -> UserResponse:
    """Get current user profile."""
    user = current_user.user_entity
    return UserResponse(
        id=current_user.user_id,
        email=current_user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=current_user.is_active,
        is_verified=user.is_verified,
        is_admin=current_user.is_admin,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at
    )


@router.put(
    "/me",
    response_model=UserProfileUpdateResponse,
    summary="Update user profile",
    description="Update the current authenticated user's profile information."
)
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> UserProfileUpdateResponse:
    """Update user profile."""
    try:
        result = await auth_use_case.update_user_profile(
            user_id=current_user.id,
            full_name=request.full_name,
            phone=request.phone
        )
        
        return UserProfileUpdateResponse(
            user=UserResponse(**result["user"]),
            message="Profile updated successfully"
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed. Please try again."
        )


# Admin-only endpoints

@router.get(
    "/users",
    response_model=Dict[str, Any],
    summary="List all users (Admin only)",
    description="Get a list of all users. Requires admin privileges."
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: CurrentUser = Depends(get_current_admin_user),
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> Dict[str, Any]:
    """List all users (admin only)."""
    try:
        result = await auth_use_case.list_users(skip=skip, limit=limit)
        
        return {
            "users": [UserResponse(**user) for user in result["users"]],
            "total": result["total"],
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users. Please try again."
        )


@router.put(
    "/users/{user_id}/status",
    response_model=Dict[str, Any],
    summary="Update user status (Admin only)",
    description="Activate or deactivate a user account. Requires admin privileges."
)
async def update_user_status(
    user_id: UUID,
    is_active: bool,
    current_admin: CurrentUser = Depends(get_current_admin_user),
    auth_use_case: AuthenticationUseCase = Depends(get_auth_use_case)
) -> Dict[str, Any]:
    """Update user status (admin only)."""
    try:
        result = await auth_use_case.update_user_status(
            user_id=user_id,
            is_active=is_active
        )
        
        return {
            "user": UserResponse(**result["user"]),
            "message": f"User {'activated' if is_active else 'deactivated'} successfully"
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User status update failed. Please try again."
        )