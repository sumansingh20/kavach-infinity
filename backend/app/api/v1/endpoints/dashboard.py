"""
KAVACH-INFINITY Dashboard Endpoints
Real-time dashboard data and statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import structlog

from app.core import get_db, rbac, cache
from app.models import Site, Sensor, Alert, User, SensorStatus, AlertStatus, AlertSeverity, DomainType
from app.models.schemas import DashboardStats, SiteHealthSummary, ChartData, AlertTrend
from app.api.v1.deps import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get main dashboard statistics
    """
    # Try cache first
    cached = await cache.get("dashboard:stats")
    if cached:
        return DashboardStats(**cached)
    
    # Total sites
    total_sites_result = await db.execute(select(func.count(Site.id)))
    total_sites = total_sites_result.scalar()
    
    # Active sites
    active_sites_result = await db.execute(
        select(func.count(Site.id)).where(Site.is_active == True)
    )
    active_sites = active_sites_result.scalar()
    
    # Total sensors
    total_sensors_result = await db.execute(select(func.count(Sensor.id)))
    total_sensors = total_sensors_result.scalar()
    
    # Online sensors
    online_sensors_result = await db.execute(
        select(func.count(Sensor.id)).where(Sensor.status == SensorStatus.ONLINE)
    )
    online_sensors = online_sensors_result.scalar()
    
    # Offline sensors
    offline_sensors_result = await db.execute(
        select(func.count(Sensor.id)).where(Sensor.status == SensorStatus.OFFLINE)
    )
    offline_sensors = offline_sensors_result.scalar()
    
    # Active alerts
    active_alerts_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.status == AlertStatus.ACTIVE)
    )
    active_alerts = active_alerts_result.scalar()
    
    # Critical alerts
    critical_alerts_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.status == AlertStatus.ACTIVE,
            Alert.severity == AlertSeverity.CRITICAL
        )
    )
    critical_alerts = critical_alerts_result.scalar()
    
    # High alerts
    high_alerts_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.status == AlertStatus.ACTIVE,
            Alert.severity == AlertSeverity.HIGH
        )
    )
    high_alerts = high_alerts_result.scalar()
    
    # Alerts last 24 hours
    yesterday = datetime.utcnow() - timedelta(hours=24)
    alerts_24h_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.triggered_at >= yesterday)
    )
    alerts_last_24h = alerts_24h_result.scalar()
    
    # Incidents last 7 days
    last_week = datetime.utcnow() - timedelta(days=7)
    incidents_7d_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.triggered_at >= last_week,
            Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.HIGH])
        )
    )
    incidents_last_7d = incidents_7d_result.scalar()
    
    # Calculate health score (simple formula)
    if total_sensors > 0:
        overall_health_score = (online_sensors / total_sensors) * 100
    else:
        overall_health_score = 100.0
    
    # Calculate risk score
    if active_alerts > 0:
        risk_factors = (critical_alerts * 10 + high_alerts * 5 + (active_alerts - critical_alerts - high_alerts))
        overall_risk_score = min(100, risk_factors)
    else:
        overall_risk_score = 0.0
    
    stats = DashboardStats(
        total_sites=total_sites,
        active_sites=active_sites,
        total_sensors=total_sensors,
        online_sensors=online_sensors,
        offline_sensors=offline_sensors,
        active_alerts=active_alerts,
        critical_alerts=critical_alerts,
        high_alerts=high_alerts,
        overall_health_score=round(overall_health_score, 1),
        overall_risk_score=round(overall_risk_score, 1),
        alerts_last_24h=alerts_last_24h,
        incidents_last_7d=incidents_last_7d
    )
    
    # Cache for 30 seconds
    await cache.set("dashboard:stats", stats.model_dump(), expire_seconds=30)
    
    return stats


@router.get("/sites/health", response_model=List[SiteHealthSummary])
async def get_sites_health(
    limit: int = Query(20, ge=1, le=100),
    domain: Optional[DomainType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get health summary for all sites
    """
    query = select(Site).where(Site.is_active == True)
    
    if domain:
        query = query.where(Site.domain == domain)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    sites = result.scalars().all()
    
    summaries = []
    for site in sites:
        # Get sensor counts
        total_sensors_result = await db.execute(
            select(func.count(Sensor.id)).where(Sensor.site_id == site.id)
        )
        total_sensors = total_sensors_result.scalar()
        
        online_sensors_result = await db.execute(
            select(func.count(Sensor.id)).where(
                Sensor.site_id == site.id,
                Sensor.status == SensorStatus.ONLINE
            )
        )
        online_sensors = online_sensors_result.scalar()
        
        # Get alert counts
        active_alerts_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site.id,
                Alert.status == AlertStatus.ACTIVE
            )
        )
        active_alerts = active_alerts_result.scalar()
        
        critical_alerts_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site.id,
                Alert.status == AlertStatus.ACTIVE,
                Alert.severity == AlertSeverity.CRITICAL
            )
        )
        critical_alerts = critical_alerts_result.scalar()
        
        # Last incident
        last_incident_result = await db.execute(
            select(Alert.triggered_at)
            .where(
                Alert.site_id == site.id,
                Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.HIGH])
            )
            .order_by(Alert.triggered_at.desc())
            .limit(1)
        )
        last_incident = last_incident_result.scalar()
        
        # Calculate scores
        health_score = (online_sensors / total_sensors * 100) if total_sensors > 0 else 100.0
        risk_score = min(100, critical_alerts * 20 + active_alerts * 5)
        
        summaries.append(SiteHealthSummary(
            site_id=site.id,
            site_name=site.name,
            site_code=site.code,
            domain=site.domain,
            health_score=round(health_score, 1),
            risk_score=round(risk_score, 1),
            total_sensors=total_sensors,
            online_sensors=online_sensors,
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            last_incident=last_incident
        ))
    
    # Sort by risk score (highest first)
    summaries.sort(key=lambda x: x.risk_score, reverse=True)
    
    return summaries


@router.get("/alerts/trend")
async def get_alert_trend(
    period: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$"),
    site_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get alert trend data for charts
    """
    # Determine time range and interval
    now = datetime.utcnow()
    
    if period == "1h":
        start_time = now - timedelta(hours=1)
        interval_minutes = 5
    elif period == "6h":
        start_time = now - timedelta(hours=6)
        interval_minutes = 30
    elif period == "24h":
        start_time = now - timedelta(hours=24)
        interval_minutes = 60
    elif period == "7d":
        start_time = now - timedelta(days=7)
        interval_minutes = 360  # 6 hours
    else:  # 30d
        start_time = now - timedelta(days=30)
        interval_minutes = 1440  # 1 day
    
    # Build query
    query = select(Alert).where(Alert.triggered_at >= start_time)
    
    if site_id:
        query = query.where(Alert.site_id == site_id)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Group by time intervals
    intervals = {}
    current = start_time
    while current < now:
        key = current.strftime("%Y-%m-%d %H:%M")
        intervals[key] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        current += timedelta(minutes=interval_minutes)
    
    for alert in alerts:
        # Find the interval this alert belongs to
        alert_time = alert.triggered_at
        interval_start = start_time + timedelta(
            minutes=((alert_time - start_time).total_seconds() // 60 // interval_minutes) * interval_minutes
        )
        key = interval_start.strftime("%Y-%m-%d %H:%M")
        
        if key in intervals:
            intervals[key][alert.severity.value] += 1
    
    # Format for chart
    labels = list(intervals.keys())
    datasets = [
        {
            "label": "Critical",
            "data": [intervals[k]["critical"] for k in labels],
            "borderColor": "#ef4444",
            "backgroundColor": "rgba(239, 68, 68, 0.1)"
        },
        {
            "label": "High",
            "data": [intervals[k]["high"] for k in labels],
            "borderColor": "#f97316",
            "backgroundColor": "rgba(249, 115, 22, 0.1)"
        },
        {
            "label": "Medium",
            "data": [intervals[k]["medium"] for k in labels],
            "borderColor": "#eab308",
            "backgroundColor": "rgba(234, 179, 8, 0.1)"
        },
        {
            "label": "Low",
            "data": [intervals[k]["low"] for k in labels],
            "borderColor": "#22c55e",
            "backgroundColor": "rgba(34, 197, 94, 0.1)"
        }
    ]
    
    return ChartData(labels=labels, datasets=datasets)


@router.get("/sensors/status")
async def get_sensor_status_distribution(
    site_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sensor status distribution for pie chart
    """
    statuses = [SensorStatus.ONLINE, SensorStatus.OFFLINE, SensorStatus.DEGRADED, 
                SensorStatus.MAINTENANCE, SensorStatus.FAULT]
    
    data = []
    for status in statuses:
        query = select(func.count(Sensor.id)).where(Sensor.status == status)
        if site_id:
            query = query.where(Sensor.site_id == site_id)
        
        result = await db.execute(query)
        count = result.scalar()
        data.append(count)
    
    return {
        "labels": [s.value for s in statuses],
        "data": data,
        "colors": ["#22c55e", "#ef4444", "#f97316", "#3b82f6", "#8b5cf6"]
    }


@router.get("/domain/overview")
async def get_domain_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overview by domain type
    """
    domains = list(DomainType)
    overview = []
    
    for domain in domains:
        # Count sites
        sites_result = await db.execute(
            select(func.count(Site.id)).where(
                Site.domain == domain,
                Site.is_active == True
            )
        )
        site_count = sites_result.scalar()
        
        if site_count == 0:
            continue
        
        # Get site IDs
        site_ids_result = await db.execute(
            select(Site.id).where(Site.domain == domain)
        )
        site_ids = [r[0] for r in site_ids_result.fetchall()]
        
        # Count sensors
        sensors_result = await db.execute(
            select(func.count(Sensor.id)).where(Sensor.site_id.in_(site_ids))
        )
        sensor_count = sensors_result.scalar()
        
        # Count active alerts
        alerts_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id.in_(site_ids),
                Alert.status == AlertStatus.ACTIVE
            )
        )
        alert_count = alerts_result.scalar()
        
        overview.append({
            "domain": domain.value,
            "display_name": domain.value.replace("_", " ").title(),
            "sites": site_count,
            "sensors": sensor_count,
            "active_alerts": alert_count
        })
    
    return overview


@router.get("/realtime/summary")
async def get_realtime_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time summary for live dashboard updates
    """
    # Recent alerts (last 5 minutes)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    
    recent_alerts_result = await db.execute(
        select(Alert)
        .where(Alert.triggered_at >= five_minutes_ago)
        .order_by(Alert.triggered_at.desc())
        .limit(10)
    )
    recent_alerts = recent_alerts_result.scalars().all()
    
    # Sensors that went offline recently
    offline_sensors_result = await db.execute(
        select(Sensor)
        .where(
            Sensor.status == SensorStatus.OFFLINE,
            Sensor.last_heartbeat >= five_minutes_ago
        )
        .limit(10)
    )
    recently_offline = offline_sensors_result.scalars().all()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "recent_alerts": [
            {
                "id": str(a.id),
                "title": a.title,
                "severity": a.severity.value,
                "triggered_at": a.triggered_at.isoformat()
            } for a in recent_alerts
        ],
        "recently_offline_sensors": [
            {
                "id": str(s.id),
                "name": s.name,
                "sensor_uid": s.sensor_uid,
                "last_heartbeat": s.last_heartbeat.isoformat() if s.last_heartbeat else None
            } for s in recently_offline
        ],
        "alert_count": len(recent_alerts),
        "offline_count": len(recently_offline)
    }
