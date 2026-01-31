"""
KAVACH-INFINITY WebSocket Manager
Real-time connection management and broadcasting
"""

import asyncio
import json
from typing import Dict, List, Set, Any, Optional
from uuid import UUID
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    
    Features:
    - Multi-room support (per site, per topic)
    - User authentication tracking
    - Broadcast and targeted messaging
    - Connection health monitoring
    """
    
    def __init__(self):
        # Main connections: connection_id -> websocket
        self.connections: Dict[str, WebSocket] = {}
        
        # User connections: user_id -> set of connection_ids
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Room subscriptions: room_name -> set of connection_ids
        self.rooms: Dict[str, Set[str]] = {}
        
        # Connection metadata
        self.metadata: Dict[str, Dict] = {}
        
        # Stats
        self.total_connections = 0
        self.total_messages_sent = 0
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        rooms: Optional[List[str]] = None
    ) -> None:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        self.connections[connection_id] = websocket
        self.total_connections += 1
        
        # Track by user
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        # Join rooms
        if rooms:
            for room in rooms:
                await self.join_room(connection_id, room)
        
        # Store metadata
        self.metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "rooms": rooms or [],
            "last_activity": datetime.utcnow().isoformat()
        }
        
        logger.info("WebSocket connected",
                   connection_id=connection_id,
                   user_id=user_id,
                   rooms=rooms)
    
    def disconnect(self, connection_id: str) -> None:
        """Clean up a disconnected WebSocket"""
        if connection_id not in self.connections:
            return
        
        # Get metadata
        meta = self.metadata.get(connection_id, {})
        user_id = meta.get("user_id")
        
        # Remove from connections
        del self.connections[connection_id]
        
        # Remove from user tracking
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from all rooms
        for room_name, members in list(self.rooms.items()):
            members.discard(connection_id)
            if not members:
                del self.rooms[room_name]
        
        # Clean up metadata
        if connection_id in self.metadata:
            del self.metadata[connection_id]
        
        logger.info("WebSocket disconnected", connection_id=connection_id)
    
    async def join_room(self, connection_id: str, room_name: str) -> None:
        """Add connection to a room"""
        if room_name not in self.rooms:
            self.rooms[room_name] = set()
        self.rooms[room_name].add(connection_id)
        
        if connection_id in self.metadata:
            if "rooms" not in self.metadata[connection_id]:
                self.metadata[connection_id]["rooms"] = []
            if room_name not in self.metadata[connection_id]["rooms"]:
                self.metadata[connection_id]["rooms"].append(room_name)
    
    async def leave_room(self, connection_id: str, room_name: str) -> None:
        """Remove connection from a room"""
        if room_name in self.rooms:
            self.rooms[room_name].discard(connection_id)
            if not self.rooms[room_name]:
                del self.rooms[room_name]
        
        if connection_id in self.metadata:
            rooms = self.metadata[connection_id].get("rooms", [])
            if room_name in rooms:
                rooms.remove(room_name)
    
    async def send_personal(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False
        
        try:
            websocket = self.connections[connection_id]
            await websocket.send_json(message)
            self.total_messages_sent += 1
            
            # Update activity
            if connection_id in self.metadata:
                self.metadata[connection_id]["last_activity"] = datetime.utcnow().isoformat()
            
            return True
        except Exception as e:
            logger.error("Failed to send message",
                        connection_id=connection_id,
                        error=str(e))
            self.disconnect(connection_id)
            return False
    
    async def send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> int:
        """Send message to all connections of a user"""
        if user_id not in self.user_connections:
            return 0
        
        sent = 0
        for conn_id in list(self.user_connections[user_id]):
            if await self.send_personal(conn_id, message):
                sent += 1
        
        return sent
    
    async def broadcast_to_room(
        self,
        room_name: str,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None
    ) -> int:
        """Broadcast message to all connections in a room"""
        if room_name not in self.rooms:
            return 0
        
        exclude = exclude or set()
        sent = 0
        
        for conn_id in list(self.rooms[room_name]):
            if conn_id in exclude:
                continue
            if await self.send_personal(conn_id, message):
                sent += 1
        
        return sent
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None
    ) -> int:
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        sent = 0
        
        for conn_id in list(self.connections.keys()):
            if conn_id in exclude:
                continue
            if await self.send_personal(conn_id, message):
                sent += 1
        
        return sent
    
    async def publish_alert(
        self,
        alert: Dict[str, Any],
        site_id: str
    ) -> int:
        """Publish new alert to relevant subscribers"""
        message = {
            "type": "alert",
            "event": "new_alert",
            "data": alert,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to site room and global alerts room
        sent = await self.broadcast_to_room(f"site_{site_id}", message)
        sent += await self.broadcast_to_room("alerts", message)
        
        logger.info("Alert published",
                   alert_id=alert.get("id"),
                   sent_to=sent)
        
        return sent
    
    async def publish_sensor_data(
        self,
        sensor_id: str,
        site_id: str,
        data: Dict[str, Any]
    ) -> int:
        """Publish sensor reading update"""
        message = {
            "type": "sensor_data",
            "event": "reading",
            "sensor_id": sensor_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to site room and sensor room
        sent = await self.broadcast_to_room(f"site_{site_id}", message)
        sent += await self.broadcast_to_room(f"sensor_{sensor_id}", message)
        
        return sent
    
    async def publish_safety_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> int:
        """Publish safety event to all clients"""
        message = {
            "type": "safety",
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "critical"
        }
        
        # Safety events go to everyone
        return await self.broadcast(message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "active_connections": len(self.connections),
            "active_users": len(self.user_connections),
            "active_rooms": len(self.rooms),
            "total_connections": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "rooms": {
                name: len(members) 
                for name, members in self.rooms.items()
            }
        }
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user has active connections"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0


# Singleton instance
ws_manager = ConnectionManager()
