"""
KAVACH-INFINITY Configuration Settings
Production-grade configuration with environment variable support
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "KAVACH-INFINITY"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="development|staging|production")
    DEBUG: bool = Field(default=True)
    SECRET_KEY: str = Field(default="kavach-secret-key-change-in-production-2024")
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    
    # Database - PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://kavach:kavach123@localhost:5432/kavach_infinity"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    
    # TimescaleDB (for time-series sensor data)
    TIMESCALE_URL: str = Field(
        default="postgresql://kavach:kavach123@localhost:5433/kavach_timeseries"
    )
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default="jwt-super-secret-key-change-this")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )
    
    # MQTT Broker
    MQTT_BROKER: str = Field(default="localhost")
    MQTT_PORT: int = Field(default=1883)
    MQTT_USERNAME: Optional[str] = Field(default=None)
    MQTT_PASSWORD: Optional[str] = Field(default=None)
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    KAFKA_CONSUMER_GROUP: str = Field(default="kavach-consumer-group")
    
    # AI/ML Models
    MODEL_PATH: str = Field(default="./models")
    ANOMALY_MODEL_VERSION: str = Field(default="v1.0.0")
    PREDICTION_MODEL_VERSION: str = Field(default="v1.0.0")
    
    # Safety Settings
    EMERGENCY_STOP_ENABLED: bool = Field(default=True)
    SAFETY_OVERRIDE_TIMEOUT_SECONDS: int = Field(default=30)
    MAX_ALERT_QUEUE_SIZE: int = Field(default=1000)
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True)
    PROMETHEUS_PORT: int = Field(default=9090)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
