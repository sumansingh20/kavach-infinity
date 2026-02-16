"""
KAVACH-INFINITY Failure Prediction Service
Predictive analytics for equipment and system failures
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from app.models import Sensor, Alert, SensorStatus, AlertSeverity

logger = structlog.get_logger()


class FailurePredictor:
    """
    Predictive failure analysis engine
    
    Predicts:
    1. Sensor failures based on degradation patterns
    2. System failures based on alert patterns
    3. Maintenance needs based on usage and age
    """
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Prediction horizons
        self.horizons = {
            "short": 24,   # 24 hours
            "medium": 72,  # 3 days
            "long": 168    # 1 week
        }
        
        logger.info("Failure predictor initialized")
    
    async def predict(
        self,
        site_id: UUID,
        sensor_id: Optional[UUID],
        prediction_type: str,
        horizon_hours: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate failure prediction
        
        prediction_type: 'failure', 'maintenance', 'anomaly'
        """
        if sensor_id:
            return await self._predict_sensor_failure(sensor_id, horizon_hours, db)
        else:
            return await self._predict_site_failure(site_id, prediction_type, horizon_hours, db)
    
    async def _predict_sensor_failure(
        self,
        sensor_id: UUID,
        horizon_hours: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Predict failure probability for specific sensor"""
        # Get sensor info
        result = await db.execute(
            select(Sensor).where(Sensor.id == sensor_id)
        )
        sensor = result.scalar_one_or_none()
        
        if not sensor:
            return {
                "probability": 0.0,
                "confidence": 0.0,
                "factors": [],
                "explanation": "Sensor not found"
            }
        
        # Calculate features for prediction
        features = await self._extract_sensor_features(sensor, db)
        
        # Apply prediction model (rule-based + heuristic for demo)
        # In production, this would use trained ML models
        probability, factors = self._calculate_failure_probability(features)
        
        # Adjust for horizon
        horizon_factor = min(1.0, horizon_hours / 168)  # Longer horizon = higher probability
        adjusted_probability = min(1.0, probability * (0.5 + 0.5 * horizon_factor))
        
        # Predict likely failure time
        if adjusted_probability > 0.5:
            predicted_time = datetime.utcnow() + timedelta(hours=horizon_hours * (1 - adjusted_probability))
        else:
            predicted_time = None
        
        # Generate explanation
        explanation = self._generate_prediction_explanation(factors, adjusted_probability, horizon_hours)
        
        return {
            "probability": round(adjusted_probability, 4),
            "confidence": round(0.7 + 0.2 * len(factors) / 5, 4),  # More factors = higher confidence
            "predicted_time": predicted_time,
            "factors": factors,
            "explanation": explanation
        }
    
    async def _predict_site_failure(
        self,
        site_id: UUID,
        prediction_type: str,
        horizon_hours: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Predict failures at site level"""
        # Get all sensors for site
        result = await db.execute(
            select(Sensor).where(Sensor.site_id == site_id)
        )
        sensors = result.scalars().all()
        
        if not sensors:
            return {
                "probability": 0.0,
                "confidence": 0.0,
                "factors": [],
                "explanation": "No sensors at site"
            }
        
        # Calculate site-level risk factors
        site_factors = []
        
        # Sensor health distribution
        status_counts = {}
        for sensor in sensors:
            status = sensor.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_sensors = len(sensors)
        offline_ratio = status_counts.get("offline", 0) / total_sensors
        degraded_ratio = status_counts.get("degraded", 0) / total_sensors
        
        if offline_ratio > 0.1:
            site_factors.append({
                "factor": "high_offline_rate",
                "value": f"{offline_ratio:.1%}",
                "impact": "high",
                "contribution": offline_ratio * 0.4
            })
        
        if degraded_ratio > 0.2:
            site_factors.append({
                "factor": "sensor_degradation",
                "value": f"{degraded_ratio:.1%}",
                "impact": "medium",
                "contribution": degraded_ratio * 0.3
            })
        
        # Recent alert frequency
        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        alert_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site_id,
                Alert.triggered_at >= one_day_ago
            )
        )
        recent_alerts = alert_result.scalar() or 0
        
        if recent_alerts > 10:
            site_factors.append({
                "factor": "high_alert_frequency",
                "value": f"{recent_alerts} in 24h",
                "impact": "high",
                "contribution": min(0.5, recent_alerts / 20)
            })
        
        # Calculate overall probability
        base_probability = sum(f["contribution"] for f in site_factors)
        probability = min(1.0, base_probability)
        
        # Confidence based on data quality
        data_quality = sum(s.data_quality_score for s in sensors) / total_sensors
        confidence = min(0.95, 0.5 + data_quality * 0.4)
        
        explanation = self._generate_site_explanation(site_factors, prediction_type, horizon_hours)
        
        return {
            "probability": round(probability, 4),
            "confidence": round(confidence, 4),
            "predicted_time": None,
            "factors": site_factors,
            "explanation": explanation
        }
    
    async def _extract_sensor_features(
        self,
        sensor: Sensor,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Extract features for sensor failure prediction"""
        features = {
            "status": sensor.status.value,
            "uptime": sensor.uptime_percentage,
            "data_quality": sensor.data_quality_score,
            "age_days": (datetime.utcnow() - sensor.created_at).days if sensor.created_at else 0,
            "last_heartbeat_hours": 0
        }
        
        if sensor.last_heartbeat:
            features["last_heartbeat_hours"] = (
                datetime.utcnow() - sensor.last_heartbeat
            ).total_seconds() / 3600
        
        # Get recent alerts for this sensor
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        alert_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.sensor_id == sensor.id,
                Alert.triggered_at >= one_week_ago
            )
        )
        features["alerts_last_week"] = alert_result.scalar() or 0
        
        return features
    
    def _calculate_failure_probability(
        self,
        features: Dict[str, Any]
    ) -> tuple[float, List[Dict]]:
        """Calculate failure probability from features"""
        probability = 0.0
        factors = []
        
        # Status-based risk
        if features["status"] == "offline":
            probability += 0.8
            factors.append({
                "factor": "sensor_offline",
                "value": "true",
                "impact": "critical",
                "contribution": 0.8
            })
        elif features["status"] == "fault":
            probability += 0.9
            factors.append({
                "factor": "sensor_fault",
                "value": "true",
                "impact": "critical",
                "contribution": 0.9
            })
        elif features["status"] == "degraded":
            probability += 0.4
            factors.append({
                "factor": "sensor_degraded",
                "value": "true",
                "impact": "medium",
                "contribution": 0.4
            })
        
        # Uptime-based risk
        if features["uptime"] < 90:
            contribution = (90 - features["uptime"]) / 100 * 0.3
            probability += contribution
            factors.append({
                "factor": "low_uptime",
                "value": f"{features['uptime']:.1f}%",
                "impact": "medium",
                "contribution": contribution
            })
        
        # Data quality risk
        if features["data_quality"] < 0.8:
            contribution = (0.8 - features["data_quality"]) * 0.2
            probability += contribution
            factors.append({
                "factor": "poor_data_quality",
                "value": f"{features['data_quality']:.2f}",
                "impact": "low",
                "contribution": contribution
            })
        
        # Heartbeat staleness
        if features["last_heartbeat_hours"] > 1:
            contribution = min(0.5, features["last_heartbeat_hours"] / 24 * 0.5)
            probability += contribution
            factors.append({
                "factor": "stale_heartbeat",
                "value": f"{features['last_heartbeat_hours']:.1f}h ago",
                "impact": "high" if features["last_heartbeat_hours"] > 6 else "medium",
                "contribution": contribution
            })
        
        # Alert frequency risk
        if features["alerts_last_week"] > 5:
            contribution = min(0.3, features["alerts_last_week"] / 20 * 0.3)
            probability += contribution
            factors.append({
                "factor": "high_alert_frequency",
                "value": f"{features['alerts_last_week']} alerts",
                "impact": "medium",
                "contribution": contribution
            })
        
        return min(1.0, probability), factors
    
    def _generate_prediction_explanation(
        self,
        factors: List[Dict],
        probability: float,
        horizon_hours: int
    ) -> str:
        """Generate human-readable prediction explanation"""
        if probability < 0.2:
            risk_level = "low"
        elif probability < 0.5:
            risk_level = "moderate"
        elif probability < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        explanation = f"{risk_level.capitalize()} failure risk ({probability:.1%}) within {horizon_hours} hours. "
        
        if factors:
            top_factor = max(factors, key=lambda x: x["contribution"])
            explanation += f"Primary concern: {top_factor['factor'].replace('_', ' ')} ({top_factor['value']}). "
        
        if probability > 0.5:
            explanation += "Recommend immediate inspection and preventive maintenance."
        elif probability > 0.2:
            explanation += "Schedule maintenance at next opportunity."
        else:
            explanation += "Continue normal monitoring."
        
        return explanation
    
    def _generate_site_explanation(
        self,
        factors: List[Dict],
        prediction_type: str,
        horizon_hours: int
    ) -> str:
        """Generate site-level prediction explanation"""
        if not factors:
            return f"Low {prediction_type} risk for the next {horizon_hours} hours. All systems normal."
        
        total_risk = sum(f["contribution"] for f in factors)
        
        explanation = f"Site {prediction_type} analysis for next {horizon_hours}h: "
        
        if total_risk > 0.5:
            explanation += "ELEVATED RISK detected. "
        else:
            explanation += "Normal risk levels. "
        
        factor_names = [f["factor"].replace("_", " ") for f in factors]
        explanation += f"Key factors: {', '.join(factor_names)}."
        
        return explanation


# Singleton instance
failure_predictor = FailurePredictor()
