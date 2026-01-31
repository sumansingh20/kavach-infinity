"""
KAVACH-INFINITY Alerts Endpoints
Alert management, acknowledgment, and resolution
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import structlog

from app.core import get_db, rbac, pubsub
from app.models import Alert, Site, Sensor, AlertAssignment, AlertComment, User
from app.models.schemas import (
    AlertCreate, AlertUpdate, AlertAcknowledge, AlertResolve,
    AlertResponse, AlertListResponse, AlertCommentCreate, AlertCommentResponse,
    AlertSeverity, AlertStatus
)
from app.api.v1.deps import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    site_id: Optional[UUID] = None,
    severity: Optional[AlertSeverity] = None,
    status_filter: Optional[AlertStatus] = None,
    source_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List alerts with filtering and pagination
    """
    if not rbac.has_permission(current_user.role, "alerts", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    query = select(Alert)
    count_query = select(func.count(Alert.id))
    
    filters = []
    
    if site_id:
        filters.append(Alert.site_id == site_id)
    
    if severity:
        filters.append(Alert.severity == severity)
    
    if status_filter:
        filters.append(Alert.status == status_filter)
    
    if source_type:
        filters.append(Alert.source_type == source_type)
    
    if from_date:
        filters.append(Alert.triggered_at >= from_date)
    
    if to_date:
        filters.append(Alert.triggered_at <= to_date)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Get total and counts by severity
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Critical count
    critical_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.status == AlertStatus.ACTIVE
        )
    )
    critical_count = critical_result.scalar()
    
    # High count
    high_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.severity == AlertSeverity.HIGH,
            Alert.status == AlertStatus.ACTIVE
        )
    )
    high_count = high_result.scalar()
    
    # Active count
    active_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.status == AlertStatus.ACTIVE)
    )
    active_count = active_result.scalar()
    
    # Get paginated results
    query = query.order_by(Alert.triggered_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Build response with site/sensor names
    alert_responses = []
    for alert in alerts:
        # Get site name
        site_result = await db.execute(
            select(Site.name).where(Site.id == alert.site_id)
        )
        site_name = site_result.scalar()
        
        # Get sensor name if applicable
        sensor_name = None
        if alert.sensor_id:
            sensor_result = await db.execute(
                select(Sensor.name).where(Sensor.id == alert.sensor_id)
            )
            sensor_name = sensor_result.scalar()
        
        alert_responses.append(AlertResponse(
            id=alert.id,
            site_id=alert.site_id,
            sensor_id=alert.sensor_id,
            alert_code=alert.alert_code,
            title=alert.title,
            description=alert.description,
            severity=alert.severity,
            status=alert.status,
            source_type=alert.source_type,
            source_model=alert.source_model,
            confidence_score=alert.confidence_score,
            risk_score=alert.risk_score,
            anomaly_score=alert.anomaly_score,
            recommended_actions=alert.recommended_actions or [],
            triggered_at=alert.triggered_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at,
            resolution_notes=alert.resolution_notes,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            site_name=site_name,
            sensor_name=sensor_name
        ))
    
    return AlertListResponse(
        items=alert_responses,
        total=total,
        page=page,
        page_size=page_size,
        critical_count=critical_count,
        high_count=high_count,
        active_count=active_count
    )


@router.get("/active")
async def get_active_alerts(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active alerts (for real-time dashboard)
    """
    if not rbac.has_permission(current_user.role, "alerts", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Alert)
        .where(Alert.status == AlertStatus.ACTIVE)
        .order_by(
            Alert.severity.desc(),  # Critical first
            Alert.triggered_at.desc()
        )
        .limit(limit)
    )
    alerts = result.scalars().all()
    
    return {
        "alerts": [
            {
                "id": str(a.id),
                "site_id": str(a.site_id),
                "alert_code": a.alert_code,
                "title": a.title,
                "severity": a.severity.value,
                "triggered_at": a.triggered_at.isoformat(),
                "confidence_score": a.confidence_score
            } for a in alerts
        ],
        "total": len(alerts)
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get alert details by ID
    """
    if not rbac.has_permission(current_user.role, "alerts", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    # Get site name
    site_result = await db.execute(
        select(Site.name).where(Site.id == alert.site_id)
    )
    site_name = site_result.scalar()
    
    sensor_name = None
    if alert.sensor_id:
        sensor_result = await db.execute(
            select(Sensor.name).where(Sensor.id == alert.sensor_id)
        )
        sensor_name = sensor_result.scalar()
    
    return AlertResponse(
        id=alert.id,
        site_id=alert.site_id,
        sensor_id=alert.sensor_id,
        alert_code=alert.alert_code,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        source_type=alert.source_type,
        source_model=alert.source_model,
        confidence_score=alert.confidence_score,
        risk_score=alert.risk_score,
        anomaly_score=alert.anomaly_score,
        recommended_actions=alert.recommended_actions or [],
        triggered_at=alert.triggered_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        resolution_notes=alert.resolution_notes,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        site_name=site_name,
        sensor_name=sensor_name
    )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    ack_data: AlertAcknowledge,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge an alert
    """
    if not rbac.has_permission(current_user.role, "alerts", "acknowledge"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    if alert.status != AlertStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot acknowledge alert with status: {alert.status.value}"
        )
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    
    # Create assignment
    assignment = AlertAssignment(
        alert_id=alert.id,
        user_id=current_user.id,
        notes=ack_data.notes
    )
    db.add(assignment)
    
    await db.commit()
    
    # Publish update
    await pubsub.publish("alerts:updates", {
        "type": "acknowledged",
        "alert_id": str(alert_id),
        "user_id": str(current_user.id),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info("Alert acknowledged", 
               alert_id=str(alert_id), 
               acknowledged_by=str(current_user.id))
    
    return {
        "message": "Alert acknowledged",
        "alert_id": str(alert_id),
        "status": AlertStatus.ACKNOWLEDGED.value,
        "acknowledged_at": alert.acknowledged_at.isoformat()
    }


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolve_data: AlertResolve,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve an alert
    """
    if not rbac.has_permission(current_user.role, "alerts", "resolve"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved"
        )
    
    if resolve_data.was_false_positive:
        alert.status = AlertStatus.FALSE_POSITIVE
    else:
        alert.status = AlertStatus.RESOLVED
    
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolve_data.resolution_notes
    alert.root_cause = resolve_data.root_cause
    
    await db.commit()
    
    # Publish update
    await pubsub.publish("alerts:updates", {
        "type": "resolved",
        "alert_id": str(alert_id),
        "user_id": str(current_user.id),
        "was_false_positive": resolve_data.was_false_positive,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info("Alert resolved", 
               alert_id=str(alert_id), 
               resolved_by=str(current_user.id),
               was_false_positive=resolve_data.was_false_positive)
    
    return {
        "message": "Alert resolved",
        "alert_id": str(alert_id),
        "status": alert.status.value,
        "resolved_at": alert.resolved_at.isoformat()
    }


@router.get("/{alert_id}/comments", response_model=List[AlertCommentResponse])
async def get_alert_comments(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comments for an alert
    """
    if not rbac.has_permission(current_user.role, "alerts", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(AlertComment)
        .where(AlertComment.alert_id == alert_id)
        .order_by(AlertComment.created_at)
    )
    comments = result.scalars().all()
    
    comment_responses = []
    for c in comments:
        user_name = None
        if c.user_id:
            user_result = await db.execute(
                select(User.full_name).where(User.id == c.user_id)
            )
            user_name = user_result.scalar()
        
        comment_responses.append(AlertCommentResponse(
            id=c.id,
            alert_id=c.alert_id,
            user_id=c.user_id,
            content=c.content,
            is_internal=c.is_internal,
            created_at=c.created_at,
            user_name=user_name
        ))
    
    return comment_responses


@router.post("/{alert_id}/comments", response_model=AlertCommentResponse)
async def add_alert_comment(
    alert_id: UUID,
    comment_data: AlertCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add comment to an alert
    """
    if not rbac.has_permission(current_user.role, "alerts", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    # Verify alert exists
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    comment = AlertComment(
        alert_id=alert_id,
        user_id=current_user.id,
        content=comment_data.content,
        is_internal=comment_data.is_internal
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return AlertCommentResponse(
        id=comment.id,
        alert_id=comment.alert_id,
        user_id=comment.user_id,
        content=comment.content,
        is_internal=comment.is_internal,
        created_at=comment.created_at,
        user_name=current_user.full_name
    )
