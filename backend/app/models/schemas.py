"""
KAVACH-INFINITY Pydantic Schemas
Request/Response models for API validation
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ==================== ENUMS ====================

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class SensorType(str, Enum):
    RADAR = "radar"
    THERMAL = "thermal"
    VIBRATION = "vibration"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    GAS = "gas"
    MOTION = "motion"
    PROXIMITY = "proximity"
    POWER = "power"
    NETWORK = "network"


class SensorStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAULT = "fault"


class DomainType(str, Enum):
    RAILWAY = "railway"
    METRO = "metro"
    TRANSPORTATION = "transportation"
    INDUSTRIAL = "industrial"
    POWER = "power"
    UTILITIES = "utilities"
    SMART_CITY = "smart_city"
    IT_OT = "it_ot"


# ==================== BASE SCHEMAS ====================

class BaseSchema(BaseModel):
    """Base schema with common config"""
    
    class Config:
        from_attributes = True
        populate_by_name = True


class TimestampMixin(BaseModel):
    """Timestamp fields mixin"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==================== AUTH SCHEMAS ====================

class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)


class LoginResponse(BaseModel):
    """Login response with tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    """Create user request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """Update user request"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseSchema, TimestampMixin):
    """User response"""
    id: UUID
    email: str
    username: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Paginated user list"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ==================== SITE SCHEMAS ====================

class SiteCreate(BaseModel):
    """Create site request"""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    domain: DomainType
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    timezone: str = "Asia/Kolkata"
    config: Dict[str, Any] = {}
    safety_config: Dict[str, Any] = {}


class SiteUpdate(BaseModel):
    """Update site request"""
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    safety_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SiteResponse(BaseSchema, TimestampMixin):
    """Site response"""
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    domain: DomainType
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str
    is_active: bool
    commissioned_at: Optional[datetime] = None
    
    # Stats
    sensor_count: Optional[int] = None
    active_alerts: Optional[int] = None


class SiteListResponse(BaseModel):
    """Paginated site list"""
    items: List[SiteResponse]
    total: int
    page: int
    page_size: int


# ==================== SENSOR SCHEMAS ====================

class SensorCreate(BaseModel):
    """Create sensor request"""
    site_id: UUID
    zone_id: Optional[UUID] = None
    sensor_uid: str = Field(..., min_length=3, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    sensor_type: SensorType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    config: Dict[str, Any] = {}
    thresholds: Dict[str, Any] = {}


class SensorUpdate(BaseModel):
    """Update sensor request"""
    name: Optional[str] = None
    zone_id: Optional[UUID] = None
    firmware_version: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None
    calibration_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SensorResponse(BaseSchema, TimestampMixin):
    """Sensor response"""
    id: UUID
    site_id: UUID
    zone_id: Optional[UUID] = None
    sensor_uid: str
    name: str
    sensor_type: SensorType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: SensorStatus
    last_heartbeat: Optional[datetime] = None
    last_data_received: Optional[datetime] = None
    data_quality_score: float
    uptime_percentage: float
    is_active: bool


class SensorDataIngest(BaseModel):
    """Sensor data ingestion payload"""
    sensor_uid: str
    timestamp: datetime
    values: Dict[str, float]
    metadata: Optional[Dict[str, Any]] = None
    quality_flags: Optional[Dict[str, bool]] = None


class SensorDataBatch(BaseModel):
    """Batch sensor data ingestion"""
    data: List[SensorDataIngest]


# ==================== ALERT SCHEMAS ====================

class AlertCreate(BaseModel):
    """Create alert request (manual)"""
    site_id: UUID
    sensor_id: Optional[UUID] = None
    alert_code: str
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    source_type: str = "manual"
    trigger_data: Dict[str, Any] = {}


class AlertUpdate(BaseModel):
    """Update alert request"""
    status: Optional[AlertStatus] = None
    resolution_notes: Optional[str] = None
    root_cause: Optional[str] = None


class AlertAcknowledge(BaseModel):
    """Acknowledge alert request"""
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    """Resolve alert request"""
    resolution_notes: str
    root_cause: Optional[str] = None
    was_false_positive: bool = False


class AlertResponse(BaseSchema, TimestampMixin):
    """Alert response"""
    id: UUID
    site_id: UUID
    sensor_id: Optional[UUID] = None
    alert_code: str
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    status: AlertStatus
    source_type: str
    source_model: Optional[str] = None
    confidence_score: Optional[float] = None
    risk_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    recommended_actions: List[str] = []
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    # Nested
    site_name: Optional[str] = None
    sensor_name: Optional[str] = None


class AlertListResponse(BaseModel):
    """Paginated alert list"""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    
    # Summary stats
    critical_count: int = 0
    high_count: int = 0
    active_count: int = 0


class AlertCommentCreate(BaseModel):
    """Create alert comment"""
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class AlertCommentResponse(BaseSchema):
    """Alert comment response"""
    id: UUID
    alert_id: UUID
    user_id: Optional[UUID] = None
    content: str
    is_internal: bool
    created_at: datetime
    user_name: Optional[str] = None


# ==================== AI/ML SCHEMAS ====================

class AnomalyDetectionRequest(BaseModel):
    """Anomaly detection request"""
    sensor_uid: str
    values: Dict[str, float]
    timestamp: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None


class AnomalyDetectionResponse(BaseModel):
    """Anomaly detection response"""
    is_anomaly: bool
    anomaly_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    anomaly_type: Optional[str] = None
    contributing_features: List[Dict[str, Any]] = []
    explanation: str
    recommended_action: Optional[str] = None


class RiskScoreRequest(BaseModel):
    """Risk scoring request"""
    site_id: UUID
    context: Dict[str, Any] = {}


class RiskScoreResponse(BaseModel):
    """Risk scoring response"""
    overall_risk: float = Field(..., ge=0, le=1)
    risk_level: str  # low, medium, high, critical
    risk_factors: List[Dict[str, Any]] = []
    trend: str  # increasing, stable, decreasing
    recommendations: List[str] = []


class PredictionRequest(BaseModel):
    """Prediction request"""
    site_id: UUID
    sensor_id: Optional[UUID] = None
    prediction_type: str  # failure, maintenance, anomaly
    horizon_hours: int = Field(default=24, ge=1, le=720)


class PredictionResponse(BaseModel):
    """Prediction response"""
    prediction_type: str
    probability: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    predicted_time: Optional[datetime] = None
    horizon_hours: int
    factors: List[Dict[str, Any]] = []
    explanation: str


# ==================== DASHBOARD SCHEMAS ====================

class DashboardStats(BaseModel):
    """Main dashboard statistics"""
    total_sites: int
    active_sites: int
    total_sensors: int
    online_sensors: int
    offline_sensors: int
    
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    
    overall_health_score: float
    overall_risk_score: float
    
    alerts_last_24h: int
    incidents_last_7d: int


class SiteHealthSummary(BaseModel):
    """Site health summary for dashboard"""
    site_id: UUID
    site_name: str
    site_code: str
    domain: DomainType
    
    health_score: float
    risk_score: float
    
    total_sensors: int
    online_sensors: int
    
    active_alerts: int
    critical_alerts: int
    
    last_incident: Optional[datetime] = None


class TimeSeriesData(BaseModel):
    """Time series data point"""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class ChartData(BaseModel):
    """Chart data for frontend"""
    labels: List[str]
    datasets: List[Dict[str, Any]]


class AlertTrend(BaseModel):
    """Alert trend data"""
    period: str
    data: List[Dict[str, Any]]
    total: int
    change_percentage: float


# ==================== SAFETY SCHEMAS ====================

class SafetyOverrideRequest(BaseModel):
    """Safety override request"""
    event_id: UUID
    reason: str = Field(..., min_length=10)
    confirmation_code: str = Field(..., min_length=6)


class SafetyOverrideResponse(BaseModel):
    """Safety override response"""
    approved: bool
    override_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    message: str


class EmergencyStopRequest(BaseModel):
    """Emergency stop request"""
    site_id: UUID
    reason: str
    scope: str = "site"  # site, zone, sensor


class EmergencyStopResponse(BaseModel):
    """Emergency stop response"""
    success: bool
    stop_id: UUID
    affected_systems: List[str]
    message: str


# ==================== WEBSOCKET SCHEMAS ====================

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # alert, sensor_data, status_update, heartbeat
    payload: Dict[str, Any]
    timestamp: datetime
    source: str


class RealtimeAlert(BaseModel):
    """Real-time alert for WebSocket"""
    alert_id: UUID
    site_id: UUID
    site_name: str
    severity: AlertSeverity
    title: str
    description: str
    triggered_at: datetime
    requires_action: bool


class RealtimeSensorUpdate(BaseModel):
    """Real-time sensor update for WebSocket"""
    sensor_uid: str
    sensor_name: str
    site_id: UUID
    values: Dict[str, float]
    status: SensorStatus
    timestamp: datetime


# Fix forward reference
LoginResponse.model_rebuild()
