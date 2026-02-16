"""
KAVACH-INFINITY WebSocket Endpoints
Real-time data streaming and notifications
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Set
import json
import asyncio
from datetime import datetime
import structlog

from app.core import get_db, token_manager, pubsub
from app.services.realtime.websocket_manager import websocket_manager

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time updates
    
    Connect with: ws://host/api/v1/ws/connect?token=<jwt_token>
    
    Supported message types:
    - subscribe: Subscribe to channels (alerts, sensors, safety)
    - unsubscribe: Unsubscribe from channels
    - ping: Keep-alive
    """
    # Validate token
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    payload = token_manager.decode_token(token)
    if not payload:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    user_role = payload.get("role")
    
    # Accept connection
    await websocket.accept()
    
    # Register connection
    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=user_id,
        user_role=user_role
    )
    
    logger.info("WebSocket connected", 
               connection_id=connection_id, 
               user_id=user_id)
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "connection_id": connection_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Connected to KAVACH-INFINITY real-time stream"
    })
    
    try:
        # Start listening for messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0  # 60 second timeout for messages
                )
                
                message_type = data.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "subscribe":
                    channels = data.get("channels", [])
                    await websocket_manager.subscribe(connection_id, channels)
                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": channels,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message_type == "unsubscribe":
                    channels = data.get("channels", [])
                    await websocket_manager.unsubscribe(connection_id, channels)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "channels": channels,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({
                    "type": "keepalive",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", connection_id=connection_id)
    except Exception as e:
        logger.error("WebSocket error", connection_id=connection_id, error=str(e))
    finally:
        await websocket_manager.disconnect(connection_id)


@router.websocket("/alerts")
async def alerts_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Dedicated WebSocket for real-time alerts
    
    Automatically subscribes to all alert channels
    """
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    payload = token_manager.decode_token(token)
    if not payload:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    await websocket.accept()
    
    user_id = payload.get("sub")
    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=user_id,
        user_role=payload.get("role")
    )
    
    # Auto-subscribe to alerts
    await websocket_manager.subscribe(connection_id, ["alerts:new", "alerts:updates"])
    
    await websocket.send_json({
        "type": "connected",
        "channel": "alerts",
        "connection_id": connection_id,
        "message": "Subscribed to real-time alerts"
    })
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keepalive"})
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(connection_id)


@router.websocket("/sensors/{site_id}")
async def sensors_websocket(
    websocket: WebSocket,
    site_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket for real-time sensor data from a specific site
    """
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    payload = token_manager.decode_token(token)
    if not payload:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    await websocket.accept()
    
    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=payload.get("sub"),
        user_role=payload.get("role")
    )
    
    # Subscribe to site-specific sensor channel
    await websocket_manager.subscribe(connection_id, [f"sensors:{site_id}"])
    
    await websocket.send_json({
        "type": "connected",
        "channel": f"sensors:{site_id}",
        "message": f"Subscribed to sensor data for site {site_id}"
    })
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=10.0
                )
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keepalive"})
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(connection_id)


@router.websocket("/safety")
async def safety_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket for safety-critical notifications
    
    Includes emergency stops, safety overrides, and critical alerts
    """
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    payload = token_manager.decode_token(token)
    if not payload:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    await websocket.accept()
    
    connection_id = await websocket_manager.connect(
        websocket=websocket,
        user_id=payload.get("sub"),
        user_role=payload.get("role")
    )
    
    # Subscribe to safety channels
    await websocket_manager.subscribe(connection_id, [
        "safety:emergency",
        "safety:override",
        "alerts:critical"
    ])
    
    await websocket.send_json({
        "type": "connected",
        "channel": "safety",
        "message": "Subscribed to safety notifications"
    })
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "acknowledge":
                    # Handle safety acknowledgment
                    await websocket.send_json({
                        "type": "acknowledged",
                        "message_id": data.get("message_id")
                    })
                    
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keepalive"})
                
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(connection_id)
