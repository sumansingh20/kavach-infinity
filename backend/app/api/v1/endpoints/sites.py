"""
KAVACH-INFINITY Sites Endpoints
Site management and configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
import structlog

from app.core import get_db, rbac
from app.models import Site, Sensor, Alert, DomainType, AlertStatus
from app.models.schemas import (
    SiteCreate, SiteUpdate, SiteResponse, SiteListResponse
)
from app.api.v1.deps import get_current_user
from app.models import User

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=SiteListResponse)
async def list_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[DomainType] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all sites with pagination
    """
    if not rbac.has_permission(current_user.role, "sites", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    query = select(Site)
    count_query = select(func.count(Site.id))
    
    if domain:
        query = query.where(Site.domain == domain)
        count_query = count_query.where(Site.domain == domain)
    
    if is_active is not None:
        query = query.where(Site.is_active == is_active)
        count_query = count_query.where(Site.is_active == is_active)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Site.name.ilike(search_filter)) |
            (Site.code.ilike(search_filter)) |
            (Site.city.ilike(search_filter))
        )
        count_query = count_query.where(
            (Site.name.ilike(search_filter)) |
            (Site.code.ilike(search_filter)) |
            (Site.city.ilike(search_filter))
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(Site.name)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    sites = result.scalars().all()
    
    # Get sensor and alert counts for each site
    site_responses = []
    for site in sites:
        # Count sensors
        sensor_count_result = await db.execute(
            select(func.count(Sensor.id)).where(Sensor.site_id == site.id)
        )
        sensor_count = sensor_count_result.scalar()
        
        # Count active alerts
        alert_count_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site.id,
                Alert.status == AlertStatus.ACTIVE
            )
        )
        active_alerts = alert_count_result.scalar()
        
        site_responses.append(SiteResponse(
            id=site.id,
            code=site.code,
            name=site.name,
            description=site.description,
            domain=site.domain,
            address=site.address,
            city=site.city,
            state=site.state,
            country=site.country,
            latitude=site.latitude,
            longitude=site.longitude,
            timezone=site.timezone,
            is_active=site.is_active,
            commissioned_at=site.commissioned_at,
            created_at=site.created_at,
            updated_at=site.updated_at,
            sensor_count=sensor_count,
            active_alerts=active_alerts
        ))
    
    return SiteListResponse(
        items=site_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: SiteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new site
    """
    if not rbac.has_permission(current_user.role, "sites", "create"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    # Check if code already exists
    result = await db.execute(
        select(Site).where(Site.code == site_data.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Site code already exists"
        )
    
    site = Site(**site_data.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    
    logger.info("Site created", site_id=str(site.id), code=site.code, created_by=str(current_user.id))
    
    return SiteResponse(
        id=site.id,
        code=site.code,
        name=site.name,
        description=site.description,
        domain=site.domain,
        address=site.address,
        city=site.city,
        state=site.state,
        country=site.country,
        latitude=site.latitude,
        longitude=site.longitude,
        timezone=site.timezone,
        is_active=site.is_active,
        commissioned_at=site.commissioned_at,
        created_at=site.created_at,
        updated_at=site.updated_at,
        sensor_count=0,
        active_alerts=0
    )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get site by ID
    """
    if not rbac.has_permission(current_user.role, "sites", "read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Site).where(Site.id == site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    
    # Get counts
    sensor_count_result = await db.execute(
        select(func.count(Sensor.id)).where(Sensor.site_id == site.id)
    )
    sensor_count = sensor_count_result.scalar()
    
    alert_count_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.site_id == site.id,
            Alert.status == AlertStatus.ACTIVE
        )
    )
    active_alerts = alert_count_result.scalar()
    
    return SiteResponse(
        id=site.id,
        code=site.code,
        name=site.name,
        description=site.description,
        domain=site.domain,
        address=site.address,
        city=site.city,
        state=site.state,
        country=site.country,
        latitude=site.latitude,
        longitude=site.longitude,
        timezone=site.timezone,
        is_active=site.is_active,
        commissioned_at=site.commissioned_at,
        created_at=site.created_at,
        updated_at=site.updated_at,
        sensor_count=sensor_count,
        active_alerts=active_alerts
    )


@router.patch("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: UUID,
    site_data: SiteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update site
    """
    if not rbac.has_permission(current_user.role, "sites", "update"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Site).where(Site.id == site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    
    update_data = site_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)
    
    await db.commit()
    await db.refresh(site)
    
    logger.info("Site updated", site_id=str(site_id), updated_by=str(current_user.id))
    
    return SiteResponse(
        id=site.id,
        code=site.code,
        name=site.name,
        description=site.description,
        domain=site.domain,
        address=site.address,
        city=site.city,
        state=site.state,
        country=site.country,
        latitude=site.latitude,
        longitude=site.longitude,
        timezone=site.timezone,
        is_active=site.is_active,
        commissioned_at=site.commissioned_at,
        created_at=site.created_at,
        updated_at=site.updated_at
    )


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete site (soft delete)
    """
    if not rbac.has_permission(current_user.role, "sites", "delete"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    result = await db.execute(
        select(Site).where(Site.id == site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    
    site.is_active = False
    await db.commit()
    
    logger.info("Site deleted", site_id=str(site_id), deleted_by=str(current_user.id))
