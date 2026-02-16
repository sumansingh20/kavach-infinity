"""
KAVACH-INFINITY Sensors Endpoints
Sensor management and data ingestion
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import structlog

from app.core import get_db, rbac, cache, pubsub
from app.models import Sensor, Site, SensorType, SensorStatus
from app.models.schemas import (
    SensorCreate, SensorUpdate, SensorResponse, 
    SensorDataIngest, SensorDataBatch
)
from app.api.v1.deps import get_current_user
from app.models import User
from app.services.ai.anomaly_detector import anomaly_detector

logger = structlog.get_logger()
router = APIRouter()


@router.get("")
async def list_sensors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    site_id: Optional[UUID] = None,
    sensor_type: Optional[SensorType] = None,
    status_filter: Optional[SensorStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all sensors with filtering
    """
    if not rbac.has_permission(current_user.role, "sensors", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    query = select(Sensor)
    count_query = select(func.count(Sensor.id))
    
    if site_id:
        query = query.where(Sensor.site_id == site_id)
        count_query = count_query.where(Sensor.site_id == site_id)
    
    if sensor_type:
        query = query.where(Sensor.sensor_type == sensor_type)
        count_query = count_query.where(Sensor.sensor_type == sensor_type)
    
    if status_filter:
        query = query.where(Sensor.status == status_filter)
        count_query = count_query.where(Sensor.status == status_filter)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(Sensor.name)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    sensors = result.scalars().all()
    
    return {
        "items": [
            SensorResponse(
                id=s.id,
                site_id=s.site_id,
                zone_id=s.zone_id,
                sensor_uid=s.sensor_uid,
                name=s.name,
                sensor_type=s.sensor_type,
                manufacturer=s.manufacturer,
                model=s.model,
                status=s.status,
                last_heartbeat=s.last_heartbeat,
                last_data_received=s.last_data_received,
                data_quality_score=s.data_quality_score,
                uptime_percentage=s.uptime_percentage,
                is_active=s.is_active,
                created_at=s.created_at,
                updated_at=s.updated_at
            ) for s in sensors
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor(
    sensor_data: SensorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register new sensor
    """
    if not rbac.has_permission(current_user.role, "sensors", "create"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    # Verify site exists
    result = await db.execute(
        select(Site).where(Site.id == sensor_data.site_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    
    # Check if sensor_uid already exists
    result = await db.execute(
        select(Sensor).where(Sensor.sensor_uid == sensor_data.sensor_uid)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensor UID already exists"
        )
    
    sensor = Sensor(**sensor_data.model_dump())
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)
    
    logger.info("Sensor created", 
               sensor_id=str(sensor.id), 
               sensor_uid=sensor.sensor_uid,
               created_by=str(current_user.id))
    
    return SensorResponse(
        id=sensor.id,
        site_id=sensor.site_id,
        zone_id=sensor.zone_id,
        sensor_uid=sensor.sensor_uid,
        name=sensor.name,
        sensor_type=sensor.sensor_type,
        manufacturer=sensor.manufacturer,
        model=sensor.model,
        status=sensor.status,
        last_heartbeat=sensor.last_heartbeat,
        last_data_received=sensor.last_data_received,
        data_quality_score=sensor.data_quality_score,
        uptime_percentage=sensor.uptime_percentage,
        is_active=sensor.is_active,
        created_at=sensor.created_at,
        updated_at=sensor.updated_at
    )


@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sensor by ID
    """
    if not rbac.has_permission(current_user.role, "sensors", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Sensor).where(Sensor.id == sensor_id)
    )
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    return SensorResponse(
        id=sensor.id,
        site_id=sensor.site_id,
        zone_id=sensor.zone_id,
        sensor_uid=sensor.sensor_uid,
        name=sensor.name,
        sensor_type=sensor.sensor_type,
        manufacturer=sensor.manufacturer,
        model=sensor.model,
        status=sensor.status,
        last_heartbeat=sensor.last_heartbeat,
        last_data_received=sensor.last_data_received,
        data_quality_score=sensor.data_quality_score,
        uptime_percentage=sensor.uptime_percentage,
        is_active=sensor.is_active,
        created_at=sensor.created_at,
        updated_at=sensor.updated_at
    )


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_sensor_data(
    data: SensorDataIngest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest real-time sensor data
    
    This endpoint accepts sensor readings and:
    1. Validates the data
    2. Updates sensor status
    3. Runs anomaly detection
    4. Stores in time-series database
    5. Publishes to real-time subscribers
    """
    # Find sensor by UID
    result = await db.execute(
        select(Sensor).where(Sensor.sensor_uid == data.sensor_uid)
    )
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor {data.sensor_uid} not found"
        )
    
    if not sensor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensor is not active"
        )
    
    # Update sensor status
    sensor.last_data_received = datetime.utcnow()
    sensor.last_heartbeat = datetime.utcnow()
    sensor.status = SensorStatus.ONLINE
    
    # Run anomaly detection
    anomaly_result = await anomaly_detector.detect(
        sensor_uid=data.sensor_uid,
        values=data.values,
        sensor_type=sensor.sensor_type.value,
        thresholds=sensor.thresholds
    )
    
    await db.commit()
    
    # Publish to real-time channel
    await pubsub.publish(
        f"sensor:{data.sensor_uid}",
        {
            "sensor_uid": data.sensor_uid,
            "site_id": str(sensor.site_id),
            "values": data.values,
            "timestamp": data.timestamp.isoformat(),
            "anomaly": anomaly_result
        }
    )
    
    # Cache latest reading
    await cache.set(
        f"sensor:latest:{data.sensor_uid}",
        {
            "values": data.values,
            "timestamp": data.timestamp.isoformat(),
            "status": sensor.status.value
        },
        expire_seconds=300
    )
    
    logger.debug("Sensor data ingested", 
                sensor_uid=data.sensor_uid,
                values=data.values,
                is_anomaly=anomaly_result.get("is_anomaly", False))
    
    return {
        "status": "accepted",
        "sensor_uid": data.sensor_uid,
        "timestamp": data.timestamp,
        "anomaly_detected": anomaly_result.get("is_anomaly", False),
        "anomaly_score": anomaly_result.get("score", 0.0)
    }


@router.post("/ingest/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_sensor_data_batch(
    batch: SensorDataBatch,
    db: AsyncSession = Depends(get_db)
):
    """
    Batch ingest sensor data
    """
    results = []
    for data in batch.data:
        try:
            result = await db.execute(
                select(Sensor).where(Sensor.sensor_uid == data.sensor_uid)
            )
            sensor = result.scalar_one_or_none()
            
            if sensor and sensor.is_active:
                sensor.last_data_received = datetime.utcnow()
                sensor.status = SensorStatus.ONLINE
                
                results.append({
                    "sensor_uid": data.sensor_uid,
                    "status": "accepted"
                })
            else:
                results.append({
                    "sensor_uid": data.sensor_uid,
                    "status": "skipped",
                    "reason": "not found or inactive"
                })
        except Exception as e:
            results.append({
                "sensor_uid": data.sensor_uid,
                "status": "error",
                "reason": str(e)
            })
    
    await db.commit()
    
    return {
        "total": len(batch.data),
        "accepted": sum(1 for r in results if r["status"] == "accepted"),
        "results": results
    }


@router.post("/{sensor_id}/heartbeat")
async def sensor_heartbeat(
    sensor_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Sensor heartbeat endpoint
    """
    result = await db.execute(
        select(Sensor).where(Sensor.id == sensor_id)
    )
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    sensor.last_heartbeat = datetime.utcnow()
    if sensor.status == SensorStatus.OFFLINE:
        sensor.status = SensorStatus.ONLINE
    
    await db.commit()
    
    return {"status": "ok", "timestamp": datetime.utcnow()}


@router.patch("/{sensor_id}", response_model=SensorResponse)
async def update_sensor(
    sensor_id: UUID,
    sensor_data: SensorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update sensor configuration
    """
    if not rbac.has_permission(current_user.role, "sensors", "update"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Sensor).where(Sensor.id == sensor_id)
    )
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    update_data = sensor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sensor, field, value)
    
    await db.commit()
    await db.refresh(sensor)
    
    logger.info("Sensor updated", sensor_id=str(sensor_id), updated_by=str(current_user.id))
    
    return SensorResponse(
        id=sensor.id,
        site_id=sensor.site_id,
        zone_id=sensor.zone_id,
        sensor_uid=sensor.sensor_uid,
        name=sensor.name,
        sensor_type=sensor.sensor_type,
        manufacturer=sensor.manufacturer,
        model=sensor.model,
        status=sensor.status,
        last_heartbeat=sensor.last_heartbeat,
        last_data_received=sensor.last_data_received,
        data_quality_score=sensor.data_quality_score,
        uptime_percentage=sensor.uptime_percentage,
        is_active=sensor.is_active,
        created_at=sensor.created_at,
        updated_at=sensor.updated_at
    )
