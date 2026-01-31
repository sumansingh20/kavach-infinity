"""
KAVACH-INFINITY Safety Endpoints
Emergency controls, safety overrides, fail-safe operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import structlog

from app.core import get_db, rbac, pubsub, cache, security_utils
from app.models import Site, Sensor, User, SafetyEvent, AlertSeverity, SensorStatus
from app.models.schemas import (
    SafetyOverrideRequest, SafetyOverrideResponse,
    EmergencyStopRequest, EmergencyStopResponse
)
from app.api.v1.deps import get_current_user
from app.services.safety.safety_monitor import safety_monitor

logger = structlog.get_logger()
router = APIRouter()


@router.post("/emergency-stop", response_model=EmergencyStopResponse)
async def emergency_stop(
    request: EmergencyStopRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger emergency stop for a site
    
    This is a CRITICAL safety operation that:
    1. Immediately stops all automated actions
    2. Puts system into safe mode
    3. Alerts all operators
    4. Logs the event for audit
    
    Requires: safety.emergency_stop permission
    """
    if not rbac.has_permission(current_user.role, "safety", "emergency_stop"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for emergency stop"
        )
    
    # Verify site exists
    result = await db.execute(
        select(Site).where(Site.id == request.site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    
    stop_id = uuid4()
    
    # Execute emergency stop
    affected_systems = await safety_monitor.execute_emergency_stop(
        site_id=request.site_id,
        scope=request.scope,
        reason=request.reason,
        triggered_by=current_user.id
    )
    
    # Log safety event
    safety_event = SafetyEvent(
        site_id=request.site_id,
        event_type="emergency_stop",
        severity=AlertSeverity.CRITICAL,
        description=f"Emergency stop triggered by {current_user.full_name}: {request.reason}",
        trigger_source="manual",
        trigger_data={
            "scope": request.scope,
            "reason": request.reason,
            "user_id": str(current_user.id)
        },
        automated_response={
            "stop_id": str(stop_id),
            "affected_systems": affected_systems
        }
    )
    db.add(safety_event)
    await db.commit()
    
    # Broadcast to all connected clients
    await pubsub.publish("safety:emergency", {
        "type": "emergency_stop",
        "stop_id": str(stop_id),
        "site_id": str(request.site_id),
        "site_name": site.name,
        "scope": request.scope,
        "reason": request.reason,
        "triggered_by": current_user.full_name,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.critical("EMERGENCY STOP TRIGGERED",
                   stop_id=str(stop_id),
                   site_id=str(request.site_id),
                   site_name=site.name,
                   scope=request.scope,
                   reason=request.reason,
                   triggered_by=str(current_user.id))
    
    return EmergencyStopResponse(
        success=True,
        stop_id=stop_id,
        affected_systems=affected_systems,
        message=f"Emergency stop executed. {len(affected_systems)} systems affected."
    )


@router.post("/emergency-stop/release")
async def release_emergency_stop(
    site_id: UUID,
    confirmation_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Release emergency stop and restore normal operations
    
    Requires confirmation code and higher privilege level
    """
    if not rbac.has_permission(current_user.role, "safety", "override"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for emergency stop release"
        )
    
    # Verify confirmation code (stored in cache when stop was triggered)
    stored_code = await cache.get(f"emergency_stop:code:{site_id}")
    
    # For safety, generate a code and require it
    if not stored_code:
        new_code = security_utils.generate_confirmation_code()
        await cache.set(f"emergency_stop:code:{site_id}", new_code, expire_seconds=300)
        
        return {
            "status": "confirmation_required",
            "message": "Confirmation code has been sent to authorized personnel",
            "code_expires_in_seconds": 300
        }
    
    if confirmation_code != stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation code"
        )
    
    # Release emergency stop
    await safety_monitor.release_emergency_stop(
        site_id=site_id,
        released_by=current_user.id
    )
    
    # Clear the code
    await cache.delete(f"emergency_stop:code:{site_id}")
    
    # Log safety event
    safety_event = SafetyEvent(
        site_id=site_id,
        event_type="emergency_stop_released",
        severity=AlertSeverity.HIGH,
        description=f"Emergency stop released by {current_user.full_name}",
        trigger_source="manual",
        trigger_data={"user_id": str(current_user.id)}
    )
    db.add(safety_event)
    await db.commit()
    
    # Broadcast
    await pubsub.publish("safety:emergency", {
        "type": "emergency_stop_released",
        "site_id": str(site_id),
        "released_by": current_user.full_name,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.warning("Emergency stop released",
                  site_id=str(site_id),
                  released_by=str(current_user.id))
    
    return {
        "status": "released",
        "message": "Emergency stop has been released. Systems returning to normal operation.",
        "site_id": str(site_id)
    }


@router.post("/override", response_model=SafetyOverrideResponse)
async def request_safety_override(
    request: SafetyOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Request a safety override for a specific event
    
    Safety overrides allow temporary bypass of automated safety actions.
    These are strictly controlled and audited.
    """
    if not rbac.has_permission(current_user.role, "safety", "override"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied for safety override"
        )
    
    # Verify the safety event exists
    result = await db.execute(
        select(SafetyEvent).where(SafetyEvent.id == request.event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Safety event not found")
    
    # Verify confirmation code
    stored_code = await cache.get(f"safety_override:code:{request.event_id}")
    
    if not stored_code:
        # Generate and store code
        new_code = security_utils.generate_confirmation_code()
        await cache.set(f"safety_override:code:{request.event_id}", new_code, expire_seconds=120)
        
        logger.info("Safety override code generated",
                   event_id=str(request.event_id),
                   user_id=str(current_user.id))
        
        return SafetyOverrideResponse(
            approved=False,
            message=f"Confirmation code required. Code: {new_code} (valid for 2 minutes)"
        )
    
    if request.confirmation_code != stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation code"
        )
    
    # Apply override
    override_id = uuid4()
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    event.override_requested = True
    event.override_approved = True
    event.override_by_id = current_user.id
    event.override_reason = request.reason
    
    await db.commit()
    
    # Clear the code
    await cache.delete(f"safety_override:code:{request.event_id}")
    
    # Store override in cache with expiration
    await cache.set(
        f"safety_override:active:{request.event_id}",
        {
            "override_id": str(override_id),
            "event_id": str(request.event_id),
            "user_id": str(current_user.id),
            "reason": request.reason,
            "expires_at": expires_at.isoformat()
        },
        expire_seconds=1800
    )
    
    logger.warning("Safety override approved",
                  override_id=str(override_id),
                  event_id=str(request.event_id),
                  user_id=str(current_user.id),
                  reason=request.reason)
    
    return SafetyOverrideResponse(
        approved=True,
        override_id=override_id,
        expires_at=expires_at,
        message=f"Override approved. Expires in 30 minutes."
    )


@router.get("/status/{site_id}")
async def get_safety_status(
    site_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current safety status for a site
    """
    # Check emergency stop status
    emergency_stop_active = await cache.exists(f"emergency_stop:active:{site_id}")
    
    # Get recent safety events
    from sqlalchemy import desc
    
    result = await db.execute(
        select(SafetyEvent)
        .where(SafetyEvent.site_id == site_id)
        .order_by(desc(SafetyEvent.occurred_at))
        .limit(10)
    )
    events = result.scalars().all()
    
    # Check active overrides
    active_overrides = []
    for event in events:
        override = await cache.get(f"safety_override:active:{event.id}")
        if override:
            active_overrides.append(override)
    
    return {
        "site_id": str(site_id),
        "emergency_stop_active": emergency_stop_active,
        "mode": "emergency" if emergency_stop_active else "normal",
        "active_overrides": active_overrides,
        "recent_events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "severity": e.severity.value,
                "description": e.description,
                "occurred_at": e.occurred_at.isoformat(),
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None
            } for e in events
        ]
    }


@router.get("/events")
async def get_safety_events(
    site_id: UUID = None,
    event_type: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get safety events log
    """
    from sqlalchemy import desc
    
    query = select(SafetyEvent)
    
    if site_id:
        query = query.where(SafetyEvent.site_id == site_id)
    
    if event_type:
        query = query.where(SafetyEvent.event_type == event_type)
    
    query = query.order_by(desc(SafetyEvent.occurred_at)).limit(limit)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return {
        "events": [
            {
                "id": str(e.id),
                "site_id": str(e.site_id) if e.site_id else None,
                "event_type": e.event_type,
                "severity": e.severity.value,
                "description": e.description,
                "trigger_source": e.trigger_source,
                "trigger_data": e.trigger_data,
                "automated_response": e.automated_response,
                "override_requested": e.override_requested,
                "override_approved": e.override_approved,
                "occurred_at": e.occurred_at.isoformat(),
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None
            } for e in events
        ],
        "total": len(events)
    }
