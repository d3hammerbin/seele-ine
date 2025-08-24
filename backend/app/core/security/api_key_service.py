#!/usr/bin/env python3
"""
API Key Service for Application Authentication

Handles CLIENT_KEY and CLIENT_SECRET generation, validation, and management.
Provides secure API key authentication for external applications.
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

from ..config.settings import get_settings
from ..exceptions.base import AuthenticationException, ValidationException


class APIKeyService:
    """
    Service for handling API key operations.
    
    Provides methods for:
    - API key generation (CLIENT_KEY and CLIENT_SECRET)
    - API key validation and authentication
    - Key rotation and revocation
    - Signature verification for secure requests
    """
    
    def __init__(self):
        """Initialize API key service with settings."""
        self.settings = get_settings()
        
    def generate_api_key_pair(
        self,
        user_id: UUID,
        application_id: UUID,
        name: str,
        description: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a new CLIENT_KEY and CLIENT_SECRET pair.
        
        Args:
            user_id: User UUID who owns the key
            application_id: Application UUID the key belongs to
            name: Human-readable name for the key
            description: Optional description
            expires_days: Custom expiration in days
            
        Returns:
            Dictionary with key information
        """
        # Generate CLIENT_KEY (public identifier)
        client_key = self._generate_client_key()
        
        # Generate CLIENT_SECRET (private key)
        client_secret = self._generate_client_secret()
        
        # Calculate expiration
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=self.settings.security.API_KEY_EXPIRE_DAYS
            )
        
        # Hash the secret for storage
        secret_hash = self._hash_secret(client_secret)
        
        return {
            "id": uuid4(),
            "user_id": user_id,
            "application_id": application_id,
            "name": name,
            "description": description,
            "client_key": client_key,
            "client_secret": client_secret,  # Only returned once
            "secret_hash": secret_hash,  # For storage
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "last_used_at": None,
            "usage_count": 0
        }
    
    def _generate_client_key(self) -> str:
        """
        Generate a CLIENT_KEY (public identifier).
        
        Format: seele_ck_[32 random chars]
        
        Returns:
            CLIENT_KEY string
        """
        random_part = secrets.token_urlsafe(24)[:32]  # 32 chars
        return f"seele_ck_{random_part}"
    
    def _generate_client_secret(self) -> str:
        """
        Generate a CLIENT_SECRET (private key).
        
        Format: seele_cs_[64 random chars]
        
        Returns:
            CLIENT_SECRET string
        """
        random_part = secrets.token_urlsafe(48)[:64]  # 64 chars
        return f"seele_cs_{random_part}"
    
    def _hash_secret(self, secret: str) -> str:
        """
        Hash a CLIENT_SECRET for secure storage.
        
        Args:
            secret: CLIENT_SECRET to hash
            
        Returns:
            Hashed secret string
        """
        # Use PBKDF2 with salt for secure hashing
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt, 100000)
        return salt.hex() + ':' + key.hex()
    
    def verify_secret(self, secret: str, secret_hash: str) -> bool:
        """
        Verify a CLIENT_SECRET against its hash.
        
        Args:
            secret: Plain CLIENT_SECRET
            secret_hash: Stored hash to verify against
            
        Returns:
            True if secret matches
        """
        try:
            salt_hex, key_hex = secret_hash.split(':')
            salt = bytes.fromhex(salt_hex)
            stored_key = bytes.fromhex(key_hex)
            
            # Hash the provided secret with the same salt
            new_key = hashlib.pbkdf2_hmac('sha256', secret.encode(), salt, 100000)
            
            # Use constant-time comparison
            return hmac.compare_digest(stored_key, new_key)
        except (ValueError, TypeError):
            return False
    
    def validate_api_key_format(self, client_key: str, client_secret: str) -> bool:
        """
        Validate the format of CLIENT_KEY and CLIENT_SECRET.
        
        Args:
            client_key: CLIENT_KEY to validate
            client_secret: CLIENT_SECRET to validate
            
        Returns:
            True if both keys have valid format
            
        Raises:
            ValidationException: If format is invalid
        """
        # Validate CLIENT_KEY format
        if not client_key.startswith('seele_ck_'):
            raise ValidationException("Invalid CLIENT_KEY format")
        
        if len(client_key) != 41:  # seele_ck_ (9) + 32 chars
            raise ValidationException("Invalid CLIENT_KEY length")
        
        # Validate CLIENT_SECRET format
        if not client_secret.startswith('seele_cs_'):
            raise ValidationException("Invalid CLIENT_SECRET format")
        
        if len(client_secret) != 73:  # seele_cs_ (9) + 64 chars
            raise ValidationException("Invalid CLIENT_SECRET length")
        
        return True
    
    def create_request_signature(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: str,
        client_secret: str
    ) -> str:
        """
        Create a request signature for API authentication.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body (empty string for GET)
            timestamp: Unix timestamp string
            client_secret: CLIENT_SECRET for signing
            
        Returns:
            HMAC signature string
        """
        # Create string to sign
        string_to_sign = f"{method}\n{path}\n{body}\n{timestamp}"
        
        # Create HMAC signature
        signature = hmac.new(
            client_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_request_signature(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: str,
        signature: str,
        client_secret: str,
        max_age_seconds: int = 300  # 5 minutes
    ) -> bool:
        """
        Verify a request signature.
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: Request timestamp
            signature: Provided signature
            client_secret: CLIENT_SECRET for verification
            max_age_seconds: Maximum age of request in seconds
            
        Returns:
            True if signature is valid
            
        Raises:
            AuthenticationException: If signature is invalid or expired
        """
        # Check timestamp age
        try:
            request_time = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
            current_time = datetime.now(timezone.utc)
            age = (current_time - request_time).total_seconds()
            
            if age > max_age_seconds:
                raise AuthenticationException("Request timestamp too old")
            
            if age < -60:  # Allow 1 minute clock skew
                raise AuthenticationException("Request timestamp in the future")
                
        except (ValueError, TypeError):
            raise AuthenticationException("Invalid timestamp format")
        
        # Calculate expected signature
        expected_signature = self.create_request_signature(
            method, path, body, timestamp, client_secret
        )
        
        # Use constant-time comparison
        if not hmac.compare_digest(signature, expected_signature):
            raise AuthenticationException("Invalid request signature")
        
        return True
    
    def is_key_expired(self, expires_at: datetime) -> bool:
        """
        Check if an API key is expired.
        
        Args:
            expires_at: Key expiration datetime
            
        Returns:
            True if key is expired
        """
        return datetime.now(timezone.utc) > expires_at
    
    def rotate_api_key(
        self,
        current_client_key: str,
        user_id: UUID,
        application_id: UUID,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rotate an existing API key (generate new CLIENT_SECRET).
        
        Args:
            current_client_key: Current CLIENT_KEY to rotate
            user_id: User UUID
            application_id: Application UUID
            name: Key name
            description: Key description
            
        Returns:
            New key information with same CLIENT_KEY but new CLIENT_SECRET
        """
        # Generate new CLIENT_SECRET only
        new_client_secret = self._generate_client_secret()
        secret_hash = self._hash_secret(new_client_secret)
        
        # Extend expiration
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.settings.security.API_KEY_EXPIRE_DAYS
        )
        
        return {
            "client_key": current_client_key,  # Keep same CLIENT_KEY
            "client_secret": new_client_secret,  # New CLIENT_SECRET
            "secret_hash": secret_hash,
            "expires_at": expires_at,
            "rotated_at": datetime.now(timezone.utc)
        }


# Global API key service instance
api_key_service = APIKeyService()