"""
KAVACH-INFINITY Database Models
SQLAlchemy ORM models for PostgreSQL
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime

Base = declarative_base()


# Enums
class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class SensorType(str, enum.Enum):
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


class SensorStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAULT = "fault"


class DomainType(str, enum.Enum):
    RAILWAY = "railway"
    METRO = "metro"
    TRANSPORTATION = "transportation"
    INDUSTRIAL = "industrial"
    POWER = "power"
    UTILITIES = "utilities"
    SMART_CITY = "smart_city"
    IT_OT = "it_ot"


# ==================== USER & AUTH MODELS ====================

class User(Base):
    """User account model with RBAC support"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    alert_assignments = relationship("AlertAssignment", back_populates="user")
    
    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
    )


class UserSession(Base):
    """Active user sessions for JWT tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    access_token_hash = Column(String(255), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=False, index=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("ix_sessions_user_active", "user_id", "revoked_at"),
    )


# ==================== SITE & LOCATION MODELS ====================

class Site(Base):
    """Physical site/location being monitored"""
    __tablename__ = "sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    domain = Column(Enum(DomainType), nullable=False)
    
    # Location
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), default="India")
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata")
    
    # Configuration
    config = Column(JSONB, default={})
    safety_config = Column(JSONB, default={})
    
    is_active = Column(Boolean, default=True)
    commissioned_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    zones = relationship("Zone", back_populates="site", cascade="all, delete-orphan")
    sensors = relationship("Sensor", back_populates="site")
    alerts = relationship("Alert", back_populates="site")
    
    __table_args__ = (
        Index("ix_sites_domain_active", "domain", "is_active"),
        Index("ix_sites_location", "latitude", "longitude"),
    )


class Zone(Base):
    """Sub-areas within a site"""
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    zone_type = Column(String(50), nullable=True)  # e.g., "platform", "crossing", "substation"
    risk_level = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Boundary polygon (GeoJSON)
    boundary = Column(JSONB, nullable=True)
    
    config = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="zones")
    sensors = relationship("Sensor", back_populates="zone")
    
    __table_args__ = (
        UniqueConstraint("site_id", "code", name="uq_zone_site_code"),
    )


# ==================== SENSOR MODELS ====================

class Sensor(Base):
    """Physical sensor devices"""
    __tablename__ = "sensors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    
    sensor_uid = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sensor_type = Column(Enum(SensorType), nullable=False)
    
    # Hardware info
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    
    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    installation_notes = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(SensorStatus), default=SensorStatus.OFFLINE)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    last_data_received = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    config = Column(JSONB, default={})
    calibration_data = Column(JSONB, default={})
    thresholds = Column(JSONB, default={})
    
    # Data quality
    data_quality_score = Column(Float, default=1.0)
    uptime_percentage = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    commissioned_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="sensors")
    zone = relationship("Zone", back_populates="sensors")
    
    __table_args__ = (
        Index("ix_sensors_site_type", "site_id", "sensor_type"),
        Index("ix_sensors_status", "status", "is_active"),
    )


# ==================== ALERT MODELS ====================

class Alert(Base):
    """Real-time alerts generated by the system"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id", ondelete="SET NULL"), nullable=True)
    
    alert_code = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, index=True)
    
    # Source information
    source_type = Column(String(50), nullable=False)  # ai, rule, manual, system
    source_model = Column(String(100), nullable=True)  # ML model name if AI-generated
    
    # AI/ML metadata
    confidence_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    prediction_data = Column(JSONB, default={})
    
    # Raw data that triggered alert
    trigger_data = Column(JSONB, default={})
    context_data = Column(JSONB, default={})
    
    # Actions
    recommended_actions = Column(ARRAY(Text), default=[])
    automated_actions_taken = Column(JSONB, default={})
    
    # Timestamps
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    site = relationship("Site", back_populates="alerts")
    assignments = relationship("AlertAssignment", back_populates="alert", cascade="all, delete-orphan")
    comments = relationship("AlertComment", back_populates="alert", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_alerts_severity_status", "severity", "status"),
        Index("ix_alerts_triggered", "triggered_at"),
        Index("ix_alerts_site_active", "site_id", "status"),
    )


class AlertAssignment(Base):
    """Alert assignment to operators"""
    __tablename__ = "alert_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    alert = relationship("Alert", back_populates="assignments")
    user = relationship("User", back_populates="alert_assignments", foreign_keys=[user_id])


class AlertComment(Base):
    """Comments on alerts"""
    __tablename__ = "alert_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    alert = relationship("Alert", back_populates="comments")


# ==================== AI/ML MODELS ====================

class MLModel(Base):
    """Registered ML models"""
    __tablename__ = "ml_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # anomaly, prediction, classification
    
    # Model metadata
    description = Column(Text, nullable=True)
    algorithm = Column(String(100), nullable=True)  # xgboost, random_forest, isolation_forest
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)
    
    # Configuration
    input_features = Column(ARRAY(String), default=[])
    output_format = Column(JSONB, default={})
    hyperparameters = Column(JSONB, default={})
    
    # Training info
    training_data_info = Column(JSONB, default={})
    trained_at = Column(DateTime(timezone=True), nullable=True)
    training_duration_seconds = Column(Integer, nullable=True)
    
    # Deployment
    artifact_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=False)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
        Index("ix_models_active", "is_active", "model_type"),
    )


class ModelPrediction(Base):
    """Logged model predictions for audit"""
    __tablename__ = "model_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=False)
    confidence = Column(Float, nullable=True)
    
    inference_time_ms = Column(Float, nullable=True)
    
    # For explainability
    feature_importance = Column(JSONB, default={})
    explanation = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("ix_predictions_model_time", "model_id", "created_at"),
    )


# ==================== AUDIT & COMPLIANCE ====================

class AuditLog(Base):
    """Immutable audit log for all actions"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True)
    
    # Request details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    
    # Change details
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("ix_audit_action_time", "action", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )


class SafetyEvent(Base):
    """Safety-critical events log"""
    __tablename__ = "safety_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False)
    
    description = Column(Text, nullable=False)
    
    # What triggered it
    trigger_source = Column(String(100), nullable=False)
    trigger_data = Column(JSONB, default={})
    
    # Actions taken
    automated_response = Column(JSONB, default={})
    human_response = Column(JSONB, default={})
    
    # Safety override info
    override_requested = Column(Boolean, default=False)
    override_approved = Column(Boolean, default=False)
    override_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    override_reason = Column(Text, nullable=True)
    
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("ix_safety_type_time", "event_type", "occurred_at"),
    )
