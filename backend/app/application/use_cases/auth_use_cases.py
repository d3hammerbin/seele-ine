#!/usr/bin/env python3
"""
Authentication Use Cases

Implements business logic for user authentication operations including
registration, login, token refresh, password reset, and account activation.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import secrets

from ...core.security.jwt_service import jwt_service
from ...core.exceptions.base import (
    ValidationException, AuthenticationException, BusinessLogicError,
    NotFoundError
)
from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ...application.dto.auth_dto import (
    UserRegistrationRequest, UserLoginRequest, TokenRefreshRequest,
    PasswordResetRequest, AccountActivationRequest
)


class AuthenticationUseCase:
    """
    Use case for handling user authentication operations.
    
    Handles:
    - User registration and activation
    - User login and logout
    - Token refresh
    - Password reset
    - Account management
    """
    
    def __init__(self, user_repository: UserRepository):
        """Initialize with user repository dependency."""
        self._user_repository = user_repository
    
    async def register_user(self, request: UserRegistrationRequest) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            request: User registration data
            
        Returns:
            Dictionary with registration result
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicError: If user already exists
        """
        # Check if user already exists
        existing_user = await self._user_repository.get_by_email(request.email)
        if existing_user:
            raise BusinessLogicError("User with this email already exists")
        
        # Validate password strength
        self._validate_password_strength(request.password)
        
        # Hash password
        password_hash = jwt_service.hash_password(request.password)
        
        # Generate activation token
        activation_token = secrets.token_urlsafe(32)
        
        # Split full_name into first_name and last_name
        name_parts = request.full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "Usuario"
        
        # Generate username from email (part before @)
        # Replace invalid characters with underscores to match validation rules
        username = request.email.split('@')[0]
        # Replace dots and other non-alphanumeric characters with underscores
        import re
        username = re.sub(r'[^a-zA-Z0-9_]', '_', username)
        # Ensure username is within valid length (3-50 characters)
        if len(username) < 3:
            username = username + "_user"
        elif len(username) > 50:
            username = username[:50]
        
        # Create user entity
        try:
            # Debug logging before creating user
            print(f"DEBUG - Creating user with:")
            print(f"  email: {request.email}")
            print(f"  username: {username}")
            print(f"  password_hash length: {len(password_hash) if password_hash else 0}")
            print(f"  first_name: '{first_name}' (length: {len(first_name)})")
            print(f"  last_name: '{last_name}' (length: {len(last_name)})")
            print(f"  phone: {request.phone}")
            
            user = User(
                email=request.email,
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                phone=request.phone,
                email_verification_token=activation_token
            )
        except ValidationException as e:
            # Log detailed validation errors for debugging
            print(f"DEBUG - Validation error details: {e.details}")
            print(f"DEBUG - User data: email={request.email}, username={username}, first_name='{first_name}', last_name='{last_name}', phone={request.phone}")
            raise
        
        # Save user
        user = await self._user_repository.create(user)
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login_at": user.last_login
            },
            "activation_token": activation_token,
            "message": "User registered successfully. Please check your email for activation instructions."
        }
    
    async def login_user(self, request: UserLoginRequest) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens.
        
        Args:
            request: User login credentials
            
        Returns:
            Dictionary with tokens and user info
            
        Raises:
            AuthenticationException: If authentication fails
        """
        # Get user by email
        user = await self._user_repository.get_by_email(request.email)
        if not user:
            raise AuthenticationException("Invalid email or password")
        
        # Verify password
        if not jwt_service.verify_password(request.password, user.password_hash):
            raise AuthenticationException("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationException("Account is not activated")
        
        # Check if account is locked
        if user.is_locked:
            raise AuthenticationException("Account is locked")
        
        # Update last login
        user.update_last_login()
        await self._user_repository.update(user)
        
        # Generate tokens
        access_token = jwt_service.create_access_token(
            subject=str(user.id),
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
        
        refresh_token = jwt_service.create_refresh_token(
            subject=str(user.id),
            user_id=user.id
        )
        
        return {
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 30 * 60,  # 30 minutes in seconds
                "expires_at": datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=30 * 60)
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "last_login_at": user.last_login_at
            }
        }
    
    async def refresh_token(self, request: TokenRefreshRequest) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            request: Token refresh request
            
        Returns:
            Dictionary with new tokens
            
        Raises:
            AuthenticationException: If refresh token is invalid
        """
        try:
            # Decode refresh token
            payload = jwt_service.decode_token(request.refresh_token)
            jwt_service.verify_token_type(payload, "refresh")
            
            # Get user
            user_id = UUID(payload["user_id"])
            user = await self._user_repository.get_by_id(user_id)
            
            if not user:
                raise AuthenticationException("User not found")
            
            if not user.is_active:
                raise AuthenticationException("Account is not active")
            
            # Generate new tokens with user information
            tokens = jwt_service.refresh_access_token(
                request.refresh_token,
                user_email=user.email,
                user_is_active=user.is_active,
                user_is_admin=user.is_admin
            )
            
            # Update tokens with user info
            tokens["expires_in"] = 30 * 60  # 30 minutes
            tokens["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])
            
            return {
                "tokens": tokens,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_admin": user.is_admin
                }
            }
            
        except Exception as e:
            raise AuthenticationException(f"Invalid refresh token: {str(e)}")
    
    async def activate_account(self, request: AccountActivationRequest) -> Dict[str, Any]:
        """
        Activate user account using activation token.
        
        Args:
            request: Account activation request
            
        Returns:
            Dictionary with activation result
            
        Raises:
            ValidationException: If token is invalid
            NotFoundError: If user not found
        """
        # Find user by activation token
        user = await self._user_repository.get_by_activation_token(request.activation_token)
        if not user:
            raise ValidationException("Invalid activation token")
        
        # Check if already activated
        if user.is_active:
            raise ValidationException("Account is already activated")
        
        # Activate account
        user.activate_account()
        await self._user_repository.update(user)
        
        return {
            "message": "Account activated successfully",
            "user_id": user.id,
            "email": user.email
        }
    
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset for user.
        
        Args:
            email: User email address
            
        Returns:
            Dictionary with reset token (in production, send via email)
            
        Raises:
            NotFoundError: If user not found
        """
        # Get user by email
        user = await self._user_repository.get_by_email(email)
        if not user:
            # Don't reveal if email exists for security
            return {
                "message": "If the email exists, a password reset link has been sent"
            }
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.now(timezone.utc).replace(microsecond=0) + \
                       datetime.timedelta(hours=1)  # 1 hour expiry
        
        # Update user with reset token
        user.set_password_reset_token(reset_token, reset_expires)
        await self._user_repository.update(user)
        
        return {
            "message": "Password reset link has been sent to your email",
            "reset_token": reset_token  # In production, send via email
        }
    
    async def reset_password(self, request: PasswordResetRequest) -> Dict[str, Any]:
        """
        Reset user password using reset token.
        
        Args:
            request: Password reset request
            
        Returns:
            Dictionary with reset result
            
        Raises:
            ValidationException: If token is invalid or expired
        """
        # Find user by reset token
        user = await self._user_repository.get_by_reset_token(request.reset_token)
        if not user:
            raise ValidationException("Invalid or expired reset token")
        
        # Check if token is expired
        if user.password_reset_expires_at < datetime.now(timezone.utc):
            raise ValidationException("Reset token has expired")
        
        # Validate new password
        self._validate_password_strength(request.new_password)
        
        # Hash new password
        password_hash = jwt_service.hash_password(request.new_password)
        
        # Update password and clear reset token
        user.reset_password(password_hash)
        await self._user_repository.update(user)
        
        return {
            "message": "Password reset successfully",
            "user_id": user.id
        }
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Change user password (requires current password).
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            Dictionary with change result
            
        Raises:
            NotFoundError: If user not found
            AuthenticationException: If current password is wrong
            ValidationException: If new password is invalid
        """
        # Get user
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not jwt_service.verify_password(current_password, user.password_hash):
            raise AuthenticationException("Current password is incorrect")
        
        # Validate new password
        self._validate_password_strength(new_password)
        
        # Check if new password is different
        if jwt_service.verify_password(new_password, user.password_hash):
            raise ValidationException("New password must be different from current password")
        
        # Hash new password
        password_hash = jwt_service.hash_password(new_password)
        
        # Update password
        user.change_password(password_hash)
        await self._user_repository.update(user)
        
        return {
            "message": "Password changed successfully",
            "user_id": user.id
        }
    
    async def logout_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Cierra la sesión de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con información del logout
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Actualizar fecha de último logout
        logout_time = datetime.now(timezone.utc)
        await self._user_repository.update_last_logout(user_id, logout_time)
        
        return {
            "message": "Logged out successfully",
            "logged_out_at": logout_time
        }
    
    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
            
        Raises:
            ValidationException: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValidationException("Password must be less than 128 characters")
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            raise ValidationException("Password must contain at least one uppercase letter")
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            raise ValidationException("Password must contain at least one lowercase letter")
        
        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            raise ValidationException("Password must contain at least one number")
        
        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise ValidationException("Password must contain at least one special character")