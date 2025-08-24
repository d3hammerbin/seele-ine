#!/usr/bin/env python3
"""
Authentication Dependencies for FastAPI

Provides dependency functions for JWT and API key authentication.
Used to protect endpoints and extract user information from requests.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .jwt_service import jwt_service
from .api_key_service import api_key_service
from ..exceptions.base import AuthenticationException, AuthorizationException
from ...infrastructure.database.session import get_async_db_session
from ...infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from ...infrastructure.repositories.application_repository_impl import ApplicationRepositoryImpl
from ...domain.entities.user import User
from ...domain.entities.application import Application


# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """
    Container for current authenticated user information.
    """
    
    def __init__(
        self,
        user_id: UUID,
        email: str,
        is_active: bool,
        is_admin: bool,
        user_entity: Optional[User] = None
    ):
        self.user_id = user_id
        self.email = email
        self.is_active = is_active
        self.is_admin = is_admin
        self.user_entity = user_entity


class CurrentApplication:
    """
    Container for current authenticated application information.
    """
    
    def __init__(
        self,
        application_id: UUID,
        user_id: UUID,
        client_key: str,
        name: str,
        is_active: bool,
        application_entity: Optional[Application] = None
    ):
        self.application_id = application_id
        self.user_id = user_id
        self.client_key = client_key
        self.name = name
        self.is_active = is_active
        self.application_entity = application_entity


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db_session)
) -> CurrentUser:
    """
    Extract current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        CurrentUser instance
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Decode JWT token
        payload = jwt_service.decode_token(credentials.credentials)
        jwt_service.verify_token_type(payload, "access")
        
        # Extract user information
        user_id = UUID(payload["user_id"])
        email = payload["email"]
        is_active = payload.get("is_active", True)
        is_admin = payload.get("is_admin", False)
        
        # Verify user is still active in database
        user_repo = UserRepositoryImpl(db)
        user_entity = await user_repo.get_by_id(user_id)
        
        if not user_entity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user_entity.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        return CurrentUser(
            user_id=user_id,
            email=email,
            is_active=is_active,
            is_admin=is_admin,
            user_entity=user_entity
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db_session)
) -> Optional[CurrentUser]:
    """
    Extract current user from JWT token (optional).
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        CurrentUser instance or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user_from_token(credentials, db)
    except HTTPException:
        return None


async def get_current_admin_user(
    current_user: CurrentUser = Depends(get_current_user_from_token)
) -> CurrentUser:
    """
    Ensure current user has admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        CurrentUser instance with admin privileges
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def get_current_application_from_api_key(
    request: Request,
    db: AsyncSession = Depends(get_async_db_session)
) -> CurrentApplication:
    """
    Extract current application from API key authentication.
    
    Expected headers:
    - X-Client-Key: CLIENT_KEY
    - X-Client-Secret: CLIENT_SECRET
    - X-Timestamp: Unix timestamp
    - X-Signature: Request signature
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        CurrentApplication instance
        
    Raises:
        HTTPException: If authentication fails
    """
    # Extract headers
    client_key = request.headers.get("X-Client-Key")
    client_secret = request.headers.get("X-Client-Secret")
    timestamp = request.headers.get("X-Timestamp")
    signature = request.headers.get("X-Signature")
    
    if not all([client_key, client_secret, timestamp, signature]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key authentication headers"
        )
    
    try:
        # Validate API key format
        api_key_service.validate_api_key_format(client_key, client_secret)
        
        # Get application from database
        app_repo = ApplicationRepositoryImpl(db)
        application = await app_repo.get_by_client_key(client_key)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid CLIENT_KEY"
            )
        
        if not application.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Application is inactive"
            )
        
        # Check if API key is expired
        if api_key_service.is_key_expired(application.api_key_expires_at):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired"
            )
        
        # Verify CLIENT_SECRET
        if not api_key_service.verify_secret(client_secret, application.api_key_secret_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid CLIENT_SECRET"
            )
        
        # Get request body for signature verification
        body = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            body = body_bytes.decode("utf-8")
        
        # Verify request signature
        api_key_service.verify_request_signature(
            method=request.method,
            path=str(request.url.path),
            body=body,
            timestamp=timestamp,
            signature=signature,
            client_secret=client_secret
        )
        
        # Update last used timestamp
        application.update_last_used()
        await app_repo.update(application)
        
        return CurrentApplication(
            application_id=application.id,
            user_id=application.user_id,
            client_key=client_key,
            name=application.name,
            is_active=application.is_active,
            application_entity=application
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key authentication"
        )


async def get_current_user_or_application(
    request: Request,
    db: AsyncSession = Depends(get_async_db_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from either JWT token or API key authentication.
    
    Tries JWT first, then API key authentication.
    
    Args:
        request: FastAPI request object
        db: Database session
        credentials: HTTP authorization credentials
        
    Returns:
        Dictionary with authentication info
        
    Raises:
        HTTPException: If both authentication methods fail
    """
    # Try JWT authentication first
    if credentials:
        try:
            current_user = await get_current_user_from_token(credentials, db)
            return {
                "type": "user",
                "user_id": current_user.user_id,
                "email": current_user.email,
                "is_admin": current_user.is_admin,
                "user": current_user
            }
        except HTTPException:
            pass  # Try API key authentication
    
    # Try API key authentication
    try:
        current_app = await get_current_application_from_api_key(request, db)
        return {
            "type": "application",
            "user_id": current_app.user_id,
            "application_id": current_app.application_id,
            "client_key": current_app.client_key,
            "application": current_app
        }
    except HTTPException:
        pass
    
    # Both authentication methods failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (JWT token or API key)",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_api_key_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db_session)
) -> User:
    """
    Get User entity from API key authentication.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User entity of the application owner
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get current application from API key
    current_app = await get_current_application_from_api_key(request, db)
    
    # Get the user who owns this application
    user_repo = UserRepositoryImpl(db)
    user = await user_repo.get_by_id(current_app.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Application owner not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Application owner account is inactive"
        )
    
    return user


# Convenience aliases
get_current_user = get_current_user_from_token
get_admin_user = get_current_admin_user
get_current_app = get_current_application_from_api_key