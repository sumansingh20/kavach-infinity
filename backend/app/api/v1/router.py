"""
KAVACH-INFINITY API Routes
Main API Router with all endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    sites,
    sensors,
    alerts,
    dashboard,
    ai,
    safety,
    websocket
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    sites.router,
    prefix="/sites",
    tags=["Sites"]
)

api_router.include_router(
    sensors.router,
    prefix="/sensors",
    tags=["Sensors"]
)

api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["AI/ML"]
)

api_router.include_router(
    safety.router,
    prefix="/safety",
    tags=["Safety"]
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)
