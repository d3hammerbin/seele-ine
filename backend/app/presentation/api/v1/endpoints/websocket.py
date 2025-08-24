#!/usr/bin/env python3
"""
WebSocket Endpoints

Provides WebSocket endpoints for real-time communication including:
- Processing status updates
- Real-time notifications
- Live data streaming
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import asyncio
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .....core.config.settings import get_settings
from .....core.exceptions.base import AuthenticationException
from .....core.security.jwt_service import JWTService
from .....infrastructure.database.session import get_async_db_session
from .....infrastructure.repositories.user_repository_impl import UserRepositoryImpl

# Initialize router
router = APIRouter(tags=["WebSocket"])
settings = get_settings()


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasting.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> [connection_ids]
        
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str = None):
        """Accept a WebSocket connection and register it."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)
            
        logger.info(f"WebSocket connection established: {connection_id} (user: {user_id})")
        
    def disconnect(self, connection_id: str, user_id: str = None):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        if user_id and user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
                
        logger.info(f"WebSocket connection closed: {connection_id} (user: {user_id})")
        
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
                
    async def send_user_message(self, message: dict, user_id: str):
        """Send a message to all connections of a specific user."""
        if user_id in self.user_connections:
            connection_ids = self.user_connections[user_id].copy()
            for connection_id in connection_ids:
                await self.send_personal_message(message, connection_id)
                
    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections."""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)
            
    async def send_heartbeat(self):
        """Send heartbeat to all connections."""
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(heartbeat_message)


# Global connection manager
manager = ConnectionManager()


async def authenticate_websocket_user(token: str) -> str:
    """
    Authenticate user from WebSocket token.
    
    Args:
        token: JWT token from query parameter
        
    Returns:
        User ID if authentication successful
        
    Raises:
        AuthenticationException: If authentication fails
    """
    try:
        jwt_service = JWTService()
        payload = jwt_service.decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationException("Invalid token payload")
            
        return user_id
        
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        raise AuthenticationException("Authentication failed")


@router.websocket("/processing")
async def websocket_processing_endpoint(
    websocket: WebSocket,
    token: str = Query(None, description="JWT access token for authentication")
):
    """
    WebSocket endpoint for real-time processing updates.
    
    Provides real-time updates for:
    - Credential processing status
    - Processing progress
    - Error notifications
    - Completion notifications
    """
    connection_id = str(uuid4())
    user_id = None
    
    try:
        # Authenticate user if token provided
        if token:
            try:
                user_id = await authenticate_websocket_user(token)
            except AuthenticationException:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
                return
        else:
            # For now, allow unauthenticated connections for development
            # In production, you might want to require authentication
            logger.warning("WebSocket connection without authentication token")
            
        # Accept connection
        await manager.connect(websocket, connection_id, user_id)
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to processing updates"
        }
        await manager.send_personal_message(welcome_message, connection_id)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(pong_message, connection_id)
                    
                elif message_type == "subscribe":
                    # Handle subscription to specific events
                    events = message.get("events", [])
                    response = {
                        "type": "subscription_confirmed",
                        "events": events,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(response, connection_id)
                    
                else:
                    # Echo unknown messages for debugging
                    echo_message = {
                        "type": "echo",
                        "original_message": message,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await manager.send_personal_message(echo_message, connection_id)
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(error_message, connection_id)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                error_message = {
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_personal_message(error_message, connection_id)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(connection_id, user_id)


# Utility functions for sending updates from other parts of the application

async def send_processing_update(user_id: str, job_id: str, status: str, progress: float = None, message: str = None):
    """
    Send processing update to user's WebSocket connections.
    
    Args:
        user_id: ID of the user to notify
        job_id: ID of the processing job
        status: Current status of the job
        progress: Progress percentage (0-100)
        message: Optional message
    """
    update_message = {
        "type": "processing_update",
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await manager.send_user_message(update_message, user_id)


async def send_processing_completed(user_id: str, job_id: str, result: dict = None):
    """
    Send processing completion notification.
    
    Args:
        user_id: ID of the user to notify
        job_id: ID of the completed job
        result: Processing result data
    """
    completion_message = {
        "type": "processing_completed",
        "job_id": job_id,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await manager.send_user_message(completion_message, user_id)


async def send_processing_failed(user_id: str, job_id: str, error: str):
    """
    Send processing failure notification.
    
    Args:
        user_id: ID of the user to notify
        job_id: ID of the failed job
        error: Error message
    """
    failure_message = {
        "type": "processing_failed",
        "job_id": job_id,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await manager.send_user_message(failure_message, user_id)


# Background task for periodic heartbeat
async def heartbeat_task():
    """
    Background task to send periodic heartbeat messages.
    """
    while True:
        try:
            await manager.send_heartbeat()
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
        except Exception as e:
            logger.error(f"Heartbeat task error: {e}")
            await asyncio.sleep(30)


# Start heartbeat task when module is imported
# Note: In a production environment, you might want to manage this differently
try:
    asyncio.create_task(heartbeat_task())
except RuntimeError:
    # Handle case where event loop is not running yet
    pass