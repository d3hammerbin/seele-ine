#!/usr/bin/env python3
"""
API Key Management Use Cases

Implements business logic for API key operations including
generation, rotation, revocation, and management of CLIENT_KEY and CLIENT_SECRET pairs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from ...core.security.api_key_service import api_key_service
from ...core.exceptions.base import (
    ValidationException, AuthorizationException, BusinessLogicError,
    NotFoundError
)
from ...domain.entities.application import Application
from ...domain.entities.user import User
from ...domain.repositories.application_repository import ApplicationRepository
from ...domain.repositories.user_repository import UserRepository
from ...application.dto.api_key_dto import (
    APIKeyCreateRequest, APIKeyRotateRequest, APIKeyListResponse
)


class APIKeyManagementUseCase:
    """
    Use case for handling API key management operations.
    
    Handles:
    - API key generation (CLIENT_KEY and CLIENT_SECRET)
    - API key rotation and renewal
    - API key revocation and deactivation
    - API key listing and management
    """
    
    def __init__(
        self,
        application_repository: ApplicationRepository,
        user_repository: UserRepository
    ):
        """Initialize with repository dependencies."""
        self._application_repository = application_repository
        self._user_repository = user_repository
    
    async def create_api_key(
        self,
        user_id: UUID,
        request: APIKeyCreateRequest
    ) -> Dict[str, Any]:
        """
        Create a new API key pair for a user application.
        
        Args:
            user_id: User ID who owns the application
            request: API key creation request
            
        Returns:
            Dictionary with new API key information
            
        Raises:
            NotFoundError: If user not found
            ValidationException: If validation fails
            BusinessLogicError: If limits exceeded
        """
        # Verify user exists and is active
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        if not user.is_active:
            raise ValidationException("User account is not active")
        
        # Check user's application limit
        user_apps = await self._application_repository.get_by_user_id(user_id)
        max_applications = 10  # Configurable limit
        
        if len(user_apps) >= max_applications:
            raise BusinessLogicError(
                f"Maximum number of applications ({max_applications}) reached"
            )
        
        # Check for duplicate application name
        existing_app = await self._application_repository.get_by_name_and_user(
            request.name, user_id
        )
        if existing_app:
            raise ValidationException(
                "Application with this name already exists"
            )
        
        # Generate API key pair
        api_key_data = api_key_service.generate_api_key_pair(
            user_id=user_id,
            application_id=UUID(str(uuid4())),  # Will be set by entity
            name=request.name,
            description=request.description,
            expires_days=request.expires_days
        )
        
        # Create application entity
        application = Application.create(
            user_id=user_id,
            name=request.name,
            description=request.description,
            client_key=api_key_data["client_key"],
            api_key_secret_hash=api_key_data["secret_hash"],
            api_key_expires_at=api_key_data["expires_at"]
        )
        
        # Save application
        application = await self._application_repository.create(application)
        
        return {
            "application_id": application.id,
            "name": application.name,
            "description": application.description,
            "client_key": api_key_data["client_key"],
            "client_secret": api_key_data["client_secret"],  # Only shown once
            "expires_at": api_key_data["expires_at"],
            "created_at": application.created_at,
            "is_active": application.is_active,
            "warning": "Store the CLIENT_SECRET securely. It will not be shown again."
        }
    
    async def list_api_keys(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> APIKeyListResponse:
        """
        List all API keys for a user.
        
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive keys
            
        Returns:
            List of API key information (without secrets)
            
        Raises:
            NotFoundError: If user not found
        """
        # Verify user exists
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Get user applications
        applications = await self._application_repository.get_by_user_id(user_id)
        
        # Filter by active status if requested
        if not include_inactive:
            applications = [app for app in applications if app.is_active]
        
        # Format response
        api_keys = []
        for app in applications:
            api_keys.append({
                "application_id": app.id,
                "name": app.name,
                "description": app.description,
                "client_key": app.client_key,
                "expires_at": app.api_key_expires_at,
                "created_at": app.created_at,
                "updated_at": app.updated_at,
                "last_used_at": app.last_used_at,
                "usage_count": app.usage_count,
                "is_active": app.is_active,
                "is_expired": api_key_service.is_key_expired(app.api_key_expires_at)
            })
        
        return APIKeyListResponse(
            total=len(api_keys),
            api_keys=api_keys
        )
    
    async def get_api_key(
        self,
        user_id: UUID,
        application_id: UUID
    ) -> Dict[str, Any]:
        """
        Get specific API key information.
        
        Args:
            user_id: User ID
            application_id: Application ID
            
        Returns:
            API key information (without secret)
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
        """
        # Get application
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        # Verify ownership
        if application.user_id != user_id:
            raise AuthorizationException("Application does not belong to user")
        
        return {
            "application_id": application.id,
            "name": application.name,
            "description": application.description,
            "client_key": application.client_key,
            "expires_at": application.api_key_expires_at,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
            "last_used_at": application.last_used_at,
            "usage_count": application.usage_count,
            "is_active": application.is_active,
            "is_expired": api_key_service.is_key_expired(application.api_key_expires_at)
        }
    
    async def rotate_api_key(
        self,
        user_id: UUID,
        application_id: UUID,
        request: APIKeyRotateRequest
    ) -> Dict[str, Any]:
        """
        Rotate an existing API key (generate new CLIENT_SECRET).
        
        Args:
            user_id: User ID
            application_id: Application ID
            request: Rotation request
            
        Returns:
            New API key information with new CLIENT_SECRET
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
        """
        # Get application
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        # Verify ownership
        if application.user_id != user_id:
            raise AuthorizationException("Application does not belong to user")
        
        # Generate new API key data
        new_key_data = api_key_service.rotate_api_key(
            current_client_key=application.client_key,
            user_id=user_id,
            application_id=application_id,
            name=application.name,
            description=application.description
        )
        
        # Update application with new secret
        application.rotate_api_key(
            new_secret_hash=new_key_data["secret_hash"],
            new_expires_at=new_key_data["expires_at"]
        )
        
        # Save changes
        application = await self._application_repository.update(application)
        
        return {
            "application_id": application.id,
            "name": application.name,
            "client_key": application.client_key,  # Same CLIENT_KEY
            "client_secret": new_key_data["client_secret"],  # New CLIENT_SECRET
            "expires_at": application.api_key_expires_at,
            "rotated_at": application.updated_at,
            "warning": "Store the new CLIENT_SECRET securely. The old one is now invalid."
        }
    
    async def revoke_api_key(
        self,
        user_id: UUID,
        application_id: UUID
    ) -> Dict[str, Any]:
        """
        Revoke (deactivate) an API key.
        
        Args:
            user_id: User ID
            application_id: Application ID
            
        Returns:
            Revocation confirmation
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
        """
        # Get application
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        # Verify ownership
        if application.user_id != user_id:
            raise AuthorizationException("Application does not belong to user")
        
        # Deactivate application
        application.deactivate()
        
        # Save changes
        application = await self._application_repository.update(application)
        
        return {
            "application_id": application.id,
            "name": application.name,
            "client_key": application.client_key,
            "revoked_at": application.updated_at,
            "message": "API key has been revoked successfully"
        }
    
    async def reactivate_api_key(
        self,
        user_id: UUID,
        application_id: UUID
    ) -> Dict[str, Any]:
        """
        Reactivate a revoked API key.
        
        Args:
            user_id: User ID
            application_id: Application ID
            
        Returns:
            Reactivation confirmation
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
            ValidationException: If key is expired
        """
        # Get application
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        # Verify ownership
        if application.user_id != user_id:
            raise AuthorizationException("Application does not belong to user")
        
        # Check if key is expired
        if api_key_service.is_key_expired(application.api_key_expires_at):
            raise ValidationException(
                "Cannot reactivate expired API key. Please rotate the key first."
            )
        
        # Reactivate application
        application.reactivate()
        
        # Save changes
        application = await self._application_repository.update(application)
        
        return {
            "application_id": application.id,
            "name": application.name,
            "client_key": application.client_key,
            "reactivated_at": application.updated_at,
            "message": "API key has been reactivated successfully"
        }
    
    async def update_api_key_info(
        self,
        user_id: UUID,
        application_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update API key metadata (name and description).
        
        Args:
            user_id: User ID
            application_id: Application ID
            name: New name (optional)
            description: New description (optional)
            
        Returns:
            Updated API key information
            
        Raises:
            NotFoundError: If application not found
            AuthorizationException: If user doesn't own the application
            ValidationException: If name already exists
        """
        # Get application
        application = await self._application_repository.get_by_id(application_id)
        if not application:
            raise NotFoundError("Application not found")
        
        # Verify ownership
        if application.user_id != user_id:
            raise AuthorizationException("Application does not belong to user")
        
        # Check for duplicate name if changing
        if name and name != application.name:
            existing_app = await self._application_repository.get_by_name_and_user(
                name, user_id
            )
            if existing_app:
                raise ValidationException(
                    "Application with this name already exists"
                )
        
        # Update application info
        if name:
            application.update_name(name)
        if description is not None:  # Allow empty string
            application.update_description(description)
        
        # Save changes
        application = await self._application_repository.update(application)
        
        return {
            "application_id": application.id,
            "name": application.name,
            "description": application.description,
            "client_key": application.client_key,
            "updated_at": application.updated_at,
            "message": "API key information updated successfully"
        }