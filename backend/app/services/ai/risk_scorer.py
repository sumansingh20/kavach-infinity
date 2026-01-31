"""
KAVACH-INFINITY Risk Scoring Service
Aggregate risk assessment for sites and systems
"""

import numpy as np
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import structlog

from app.models import Site, Sensor, Alert, SafetyEvent
from app.models import SensorStatus, AlertStatus, AlertSeverity

logger = structlog.get_logger()


class RiskScorer:
    """
    Multi-factor risk scoring engine
    
    Calculates risk based on:
    1. Sensor health status
    2. Active alerts (weighted by severity)
    3. Historical incident frequency
    4. Anomaly detection trends
    5. Environmental factors
    6. Time-based patterns
    """
    
    def __init__(self):
        # Risk weights for different factors
        self.weights = {
            "sensor_health": 0.20,
            "active_alerts": 0.30,
            "historical_incidents": 0.20,
            "anomaly_trend": 0.15,
            "environmental": 0.10,
            "time_pattern": 0.05
        }
        
        # Alert severity scores
        self.alert_severity_scores = {
            AlertSeverity.CRITICAL: 1.0,
            AlertSeverity.HIGH: 0.7,
            AlertSeverity.MEDIUM: 0.4,
            AlertSeverity.LOW: 0.2,
            AlertSeverity.INFO: 0.05
        }
        
        logger.info("Risk scorer initialized")
    
    async def calculate(
        self,
        site_id: UUID,
        db: AsyncSession,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a site
        
        Returns:
            dict with overall_risk, risk_level, risk_factors, trend, recommendations
        """
        risk_factors = []
        
        # 1. Sensor Health Risk
        sensor_risk = await self._calculate_sensor_health_risk(site_id, db)
        risk_factors.append({
            "factor": "sensor_health",
            "score": sensor_risk["score"],
            "weight": self.weights["sensor_health"],
            "details": sensor_risk["details"]
        })
        
        # 2. Active Alerts Risk
        alert_risk = await self._calculate_alert_risk(site_id, db)
        risk_factors.append({
            "factor": "active_alerts",
            "score": alert_risk["score"],
            "weight": self.weights["active_alerts"],
            "details": alert_risk["details"]
        })
        
        # 3. Historical Incidents Risk
        historical_risk = await self._calculate_historical_risk(site_id, db)
        risk_factors.append({
            "factor": "historical_incidents",
            "score": historical_risk["score"],
            "weight": self.weights["historical_incidents"],
            "details": historical_risk["details"]
        })
        
        # 4. Anomaly Trend Risk
        anomaly_risk = self._calculate_anomaly_trend_risk(context)
        risk_factors.append({
            "factor": "anomaly_trend",
            "score": anomaly_risk["score"],
            "weight": self.weights["anomaly_trend"],
            "details": anomaly_risk["details"]
        })
        
        # 5. Environmental Risk
        env_risk = self._calculate_environmental_risk(context)
        risk_factors.append({
            "factor": "environmental",
            "score": env_risk["score"],
            "weight": self.weights["environmental"],
            "details": env_risk["details"]
        })
        
        # 6. Time Pattern Risk
        time_risk = self._calculate_time_pattern_risk()
        risk_factors.append({
            "factor": "time_pattern",
            "score": time_risk["score"],
            "weight": self.weights["time_pattern"],
            "details": time_risk["details"]
        })
        
        # Calculate weighted overall risk
        overall_risk = sum(
            f["score"] * f["weight"] for f in risk_factors
        )
        overall_risk = round(min(1.0, max(0.0, overall_risk)), 4)
        
        # Determine risk level
        if overall_risk >= 0.8:
            risk_level = "critical"
        elif overall_risk >= 0.6:
            risk_level = "high"
        elif overall_risk >= 0.4:
            risk_level = "medium"
        elif overall_risk >= 0.2:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        # Calculate trend
        trend = await self._calculate_trend(site_id, db, overall_risk)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, risk_level)
        
        return {
            "overall_risk": overall_risk,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "trend": trend,
            "recommendations": recommendations
        }
    
    async def _calculate_sensor_health_risk(
        self,
        site_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate risk based on sensor health status"""
        # Count sensors by status
        total_result = await db.execute(
            select(func.count(Sensor.id)).where(Sensor.site_id == site_id)
        )
        total_sensors = total_result.scalar() or 0
        
        if total_sensors == 0:
            return {"score": 0.5, "details": "No sensors configured"}
        
        # Count unhealthy sensors
        unhealthy_result = await db.execute(
            select(func.count(Sensor.id)).where(
                Sensor.site_id == site_id,
                Sensor.status.in_([SensorStatus.OFFLINE, SensorStatus.FAULT, SensorStatus.DEGRADED])
            )
        )
        unhealthy_count = unhealthy_result.scalar() or 0
        
        # Calculate score
        unhealthy_ratio = unhealthy_count / total_sensors
        score = min(1.0, unhealthy_ratio * 2)  # 50% unhealthy = max risk
        
        return {
            "score": round(score, 4),
            "details": f"{unhealthy_count}/{total_sensors} sensors unhealthy"
        }
    
    async def _calculate_alert_risk(
        self,
        site_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate risk based on active alerts"""
        # Get active alerts by severity
        result = await db.execute(
            select(Alert.severity, func.count(Alert.id))
            .where(
                Alert.site_id == site_id,
                Alert.status == AlertStatus.ACTIVE
            )
            .group_by(Alert.severity)
        )
        
        alert_counts = {row[0]: row[1] for row in result.fetchall()}
        
        if not alert_counts:
            return {"score": 0.0, "details": "No active alerts"}
        
        # Calculate weighted score
        total_alerts = sum(alert_counts.values())
        weighted_score = sum(
            count * self.alert_severity_scores.get(sev, 0.1)
            for sev, count in alert_counts.items()
        )
        
        # Normalize (max 10 critical alerts = 1.0)
        score = min(1.0, weighted_score / 10)
        
        details = ", ".join(f"{sev.value}: {count}" for sev, count in alert_counts.items())
        
        return {
            "score": round(score, 4),
            "details": f"Active alerts - {details}"
        }
    
    async def _calculate_historical_risk(
        self,
        site_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate risk based on historical incident frequency"""
        # Count incidents in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site_id,
                Alert.triggered_at >= thirty_days_ago,
                Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.HIGH])
            )
        )
        incident_count = result.scalar() or 0
        
        # Count in last 7 days for comparison
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        result_recent = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site_id,
                Alert.triggered_at >= seven_days_ago,
                Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.HIGH])
            )
        )
        recent_count = result_recent.scalar() or 0
        
        # Calculate score (10+ incidents in 30 days = high risk)
        base_score = min(1.0, incident_count / 10)
        
        # Add recency factor (more recent = higher risk)
        recency_multiplier = 1 + (recent_count / 5) * 0.5
        score = min(1.0, base_score * recency_multiplier)
        
        return {
            "score": round(score, 4),
            "details": f"{incident_count} incidents in 30 days, {recent_count} in last 7 days"
        }
    
    def _calculate_anomaly_trend_risk(
        self,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Calculate risk based on anomaly detection trends"""
        if not context:
            return {"score": 0.0, "details": "No anomaly context available"}
        
        anomaly_rate = context.get("anomaly_rate", 0.0)
        increasing = context.get("anomaly_trend_increasing", False)
        
        score = min(1.0, anomaly_rate * 2)
        if increasing:
            score = min(1.0, score * 1.3)
        
        return {
            "score": round(score, 4),
            "details": f"Anomaly rate: {anomaly_rate:.2%}, trending {'up' if increasing else 'stable'}"
        }
    
    def _calculate_environmental_risk(
        self,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Calculate risk based on environmental factors"""
        if not context:
            return {"score": 0.1, "details": "Default environmental risk"}
        
        # Environmental factors from external APIs
        weather_risk = context.get("weather_risk", 0.0)  # Bad weather
        time_of_day_risk = context.get("time_risk", 0.0)  # Night operations
        load_risk = context.get("load_factor", 0.0)  # System load
        
        score = (weather_risk * 0.4 + time_of_day_risk * 0.3 + load_risk * 0.3)
        
        return {
            "score": round(min(1.0, score), 4),
            "details": f"Weather: {weather_risk:.2f}, Time: {time_of_day_risk:.2f}, Load: {load_risk:.2f}"
        }
    
    def _calculate_time_pattern_risk(self) -> Dict[str, Any]:
        """Calculate risk based on time patterns"""
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()
        
        # Higher risk during night shifts and weekends
        if 22 <= hour or hour <= 6:
            time_factor = 0.6  # Night
        elif weekday >= 5:
            time_factor = 0.4  # Weekend
        else:
            time_factor = 0.1  # Normal hours
        
        return {
            "score": time_factor,
            "details": f"Hour: {hour}, Day: {weekday} ({'weekend' if weekday >= 5 else 'weekday'})"
        }
    
    async def _calculate_trend(
        self,
        site_id: UUID,
        db: AsyncSession,
        current_risk: float
    ) -> str:
        """Determine if risk is increasing, stable, or decreasing"""
        # Compare with historical risk (simplified - check alert trends)
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Recent alerts
        recent_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site_id,
                Alert.triggered_at >= one_week_ago
            )
        )
        recent = recent_result.scalar() or 0
        
        # Previous week alerts
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        prev_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.site_id == site_id,
                Alert.triggered_at >= two_weeks_ago,
                Alert.triggered_at < one_week_ago
            )
        )
        previous = prev_result.scalar() or 0
        
        if recent > previous * 1.2:
            return "increasing"
        elif recent < previous * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_recommendations(
        self,
        risk_factors: List[Dict],
        risk_level: str
    ) -> List[str]:
        """Generate actionable recommendations based on risk factors"""
        recommendations = []
        
        # Sort factors by score
        sorted_factors = sorted(risk_factors, key=lambda x: -x["score"])
        
        for factor in sorted_factors[:3]:  # Top 3 risks
            if factor["factor"] == "sensor_health" and factor["score"] > 0.3:
                recommendations.append(
                    "Check sensor connectivity and perform maintenance on offline devices"
                )
            elif factor["factor"] == "active_alerts" and factor["score"] > 0.3:
                recommendations.append(
                    "Review and address active alerts, prioritizing critical severity"
                )
            elif factor["factor"] == "historical_incidents" and factor["score"] > 0.3:
                recommendations.append(
                    "Conduct root cause analysis on recent incidents to prevent recurrence"
                )
            elif factor["factor"] == "anomaly_trend" and factor["score"] > 0.3:
                recommendations.append(
                    "Investigate increasing anomaly patterns for potential system issues"
                )
            elif factor["factor"] == "environmental" and factor["score"] > 0.3:
                recommendations.append(
                    "Adjust operations for current environmental conditions"
                )
        
        if risk_level in ["critical", "high"]:
            recommendations.insert(0, "IMMEDIATE: Review safety protocols and increase monitoring")
        
        return recommendations[:5]  # Max 5 recommendations


# Singleton instance
risk_scorer = RiskScorer()
