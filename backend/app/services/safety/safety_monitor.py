"""
KAVACH-INFINITY Safety Monitor
Automated safety response system
"""

import asyncio
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import SafetyEvent, Alert, AlertSeverity
from app.services.realtime.websocket_manager import ws_manager

logger = structlog.get_logger()


class SafetyMonitor:
    """
    Automated safety monitoring and response system
    
    Responsibilities:
    1. Monitor safety-critical events
    2. Trigger automated responses
    3. Coordinate emergency stops
    4. Track safety compliance
    """
    
    def __init__(self):
        self.active_stops: Dict[str, Dict] = {}  # site_id -> stop info
        self.safety_overrides: Dict[str, Dict] = {}
        self.confirmation_codes: Dict[str, Dict] = {}  # code -> action info
        
        logger.info("Safety monitor initialized")
    
    async def process_critical_alert(
        self,
        alert: Alert,
        db: AsyncSession
    ) -> Optional[Dict]:
        """
        Process critical severity alert and trigger safety actions
        """
        if alert.severity != AlertSeverity.CRITICAL:
            return None
        
        site_id = str(alert.site_id)
        
        # Check for automatic emergency stop conditions
        if self._should_auto_stop(alert):
            return await self.trigger_emergency_stop(
                site_id=site_id,
                reason=f"Auto-triggered by critical alert: {alert.title}",
                db=db,
                auto_triggered=True
            )
        
        return None
    
    def _should_auto_stop(self, alert: Alert) -> bool:
        """Determine if alert should trigger automatic stop"""
        # Auto-stop conditions
        auto_stop_types = [
            "collision_imminent",
            "fire_detected",
            "gas_leak",
            "structural_failure",
            "intrusion_safety_zone"
        ]
        
        if alert.alert_type in auto_stop_types:
            return True
        
        return False
    
    async def trigger_emergency_stop(
        self,
        site_id: str,
        reason: str,
        db: AsyncSession,
        auto_triggered: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger emergency stop for a site
        """
        stop_id = str(uuid4())
        
        stop_info = {
            "id": stop_id,
            "site_id": site_id,
            "reason": reason,
            "triggered_at": datetime.utcnow().isoformat(),
            "triggered_by": user_id or "SYSTEM",
            "auto_triggered": auto_triggered,
            "status": "active"
        }
        
        self.active_stops[site_id] = stop_info
        
        # Publish to all connected clients
        await ws_manager.publish_safety_event(
            event_type="emergency_stop",
            data=stop_info
        )
        
        logger.critical("Emergency stop triggered",
                       stop_id=stop_id,
                       site_id=site_id,
                       reason=reason,
                       auto=auto_triggered)
        
        return stop_info
    
    async def release_emergency_stop(
        self,
        site_id: str,
        confirmation_code: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Release emergency stop after verification
        """
        if site_id not in self.active_stops:
            return {"error": "No active emergency stop for this site"}
        
        # Verify confirmation code
        if confirmation_code not in self.confirmation_codes:
            return {"error": "Invalid confirmation code"}
        
        code_info = self.confirmation_codes[confirmation_code]
        if code_info["action"] != "release_stop" or code_info["site_id"] != site_id:
            return {"error": "Confirmation code not valid for this action"}
        
        # Clear the stop
        stop_info = self.active_stops.pop(site_id)
        stop_info["released_at"] = datetime.utcnow().isoformat()
        stop_info["released_by"] = user_id
        stop_info["status"] = "released"
        
        # Clear confirmation code
        del self.confirmation_codes[confirmation_code]
        
        # Notify all clients
        await ws_manager.publish_safety_event(
            event_type="stop_released",
            data=stop_info
        )
        
        logger.info("Emergency stop released",
                   site_id=site_id,
                   released_by=user_id)
        
        return stop_info
    
    def generate_confirmation_code(
        self,
        action: str,
        site_id: str,
        user_id: str
    ) -> str:
        """Generate a one-time confirmation code for safety-critical actions"""
        import random
        import string
        
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        self.confirmation_codes[code] = {
            "action": action,
            "site_id": site_id,
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": datetime.utcnow().isoformat()  # Should add expiry
        }
        
        return code
    
    async def set_safety_override(
        self,
        site_id: str,
        override_type: str,
        user_id: str,
        reason: str,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Set a temporary safety override
        """
        override_id = str(uuid4())
        
        override_info = {
            "id": override_id,
            "site_id": site_id,
            "type": override_type,
            "reason": reason,
            "set_by": user_id,
            "set_at": datetime.utcnow().isoformat(),
            "expires_at": datetime.utcnow().isoformat(),  # Add duration
            "duration_minutes": duration_minutes,
            "active": True
        }
        
        key = f"{site_id}_{override_type}"
        self.safety_overrides[key] = override_info
        
        logger.warning("Safety override set",
                      override_id=override_id,
                      site_id=site_id,
                      type=override_type,
                      reason=reason)
        
        return override_info
    
    def is_site_stopped(self, site_id: str) -> bool:
        """Check if site has active emergency stop"""
        return site_id in self.active_stops
    
    def get_active_stops(self) -> List[Dict]:
        """Get all active emergency stops"""
        return list(self.active_stops.values())
    
    def get_safety_status(self, site_id: str) -> Dict[str, Any]:
        """Get comprehensive safety status for a site"""
        stopped = site_id in self.active_stops
        
        overrides = [
            v for k, v in self.safety_overrides.items()
            if k.startswith(site_id) and v.get("active")
        ]
        
        return {
            "site_id": site_id,
            "emergency_stop": stopped,
            "stop_info": self.active_stops.get(site_id),
            "active_overrides": overrides,
            "safety_level": "critical" if stopped else ("warning" if overrides else "normal")
        }


# Singleton instance
safety_monitor = SafetyMonitor()
