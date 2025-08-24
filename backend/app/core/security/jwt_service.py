#!/usr/bin/env python3
"""
JWT Service for Authentication

Handles JWT token generation, validation, and refresh token management.
Provides secure authentication mechanisms for the SEELE-E system.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from uuid import UUID
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

from ..config.settings import get_settings
from ..exceptions.base import AuthenticationException, ValidationException


class JWTService:
    """
    Service for handling JWT token operations.
    
    Provides methods for:
    - Token generation (access and refresh)
    - Token validation and decoding
    - Password hashing and verification
    - Token refresh operations
    """
    
    def __init__(self):
        """Initialize JWT service with settings and password context."""
        self.settings = get_settings()
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=self.settings.security.PASSWORD_HASH_ROUNDS
        )
        
    def create_access_token(
        self,
        subject: Union[str, UUID],
        user_id: UUID,
        email: str,
        is_active: bool = True,
        is_admin: bool = False,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new JWT access token.
        
        Args:
            subject: Token subject (usually user ID)
            user_id: User UUID
            email: User email
            is_active: Whether user is active
            is_admin: Whether user has admin privileges
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.settings.security.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
        payload = {
            "sub": str(subject),
            "user_id": str(user_id),
            "email": email,
            "is_active": is_active,
            "is_admin": is_admin,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        return jwt.encode(
            payload,
            self.settings.security.JWT_SECRET_KEY,
            algorithm=self.settings.security.JWT_ALGORITHM
        )
    
    def create_refresh_token(
        self,
        subject: Union[str, UUID],
        user_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a new JWT refresh token.
        
        Args:
            subject: Token subject (usually user ID)
            user_id: User UUID
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.settings.security.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
            
        payload = {
            "sub": str(subject),
            "user_id": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            self.settings.security.JWT_SECRET_KEY,
            algorithm=self.settings.security.JWT_ALGORITHM
        )
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.security.JWT_SECRET_KEY,
                algorithms=[self.settings.security.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationException("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationException(f"Invalid token: {str(e)}")
    
    def verify_token_type(self, payload: Dict[str, Any], expected_type: str) -> bool:
        """
        Verify that the token is of the expected type.
        
        Args:
            payload: Decoded token payload
            expected_type: Expected token type ('access' or 'refresh')
            
        Returns:
            True if token type matches
            
        Raises:
            AuthenticationException: If token type doesn't match
        """
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationException(
                f"Invalid token type. Expected {expected_type}, got {token_type}"
            )
        return True
    
    def get_user_id_from_token(self, token: str) -> UUID:
        """
        Extract user ID from a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User UUID
            
        Raises:
            AuthenticationException: If token is invalid
        """
        payload = self.decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationException("Token does not contain user ID")
        
        try:
            return UUID(user_id)
        except ValueError:
            raise AuthenticationException("Invalid user ID format in token")
    
    def refresh_access_token(self, refresh_token: str, user_email: str = "", user_is_active: bool = True, user_is_admin: bool = False) -> Dict[str, str]:
        """
        Generate a new access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            user_email: User email (should be provided by caller)
            user_is_active: User active status (should be provided by caller)
            user_is_admin: User admin status (should be provided by caller)
            
        Returns:
            Dictionary with new access and refresh tokens
            
        Raises:
            AuthenticationException: If refresh token is invalid
        """
        payload = self.decode_token(refresh_token)
        self.verify_token_type(payload, "refresh")
        
        user_id = UUID(payload["user_id"])
        
        # Create new tokens
        new_access_token = self.create_access_token(
            subject=payload["sub"],
            user_id=user_id,
            email=user_email,
            is_active=user_is_active,
            is_admin=user_is_admin
        )
        
        new_refresh_token = self.create_refresh_token(
            subject=payload["sub"],
            user_id=user_id
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without raising an exception.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.security.JWT_SECRET_KEY,
                algorithms=[self.settings.security.JWT_ALGORITHM]
            )
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)
            return True
        except jwt.InvalidTokenError:
            return True


# Global JWT service instance
jwt_service = JWTService()