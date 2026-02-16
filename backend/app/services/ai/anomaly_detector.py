"""
KAVACH-INFINITY Anomaly Detection Service
Real AI-powered anomaly detection using Isolation Forest and statistical methods
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Optional
import joblib
import os
from datetime import datetime, timedelta
import structlog
from uuid import UUID, uuid4

from app.config import settings

logger = structlog.get_logger()


class AnomalyDetector:
    """
    Production anomaly detection engine
    
    Uses multiple detection strategies:
    1. Isolation Forest for multivariate anomalies
    2. Statistical thresholds for univariate anomalies
    3. Rate-of-change detection for sudden shifts
    4. Pattern-based detection for known failure modes
    """
    
    def __init__(self):
        self.model_id = uuid4()
        self.models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.history: Dict[str, List[Dict]] = {}
        self.history_window = 100  # Keep last 100 readings per sensor
        
        # Default thresholds by sensor type
        self.default_thresholds = {
            "temperature": {"min": -40, "max": 85, "rate": 5.0},
            "humidity": {"min": 0, "max": 100, "rate": 10.0},
            "pressure": {"min": 800, "max": 1200, "rate": 50.0},
            "vibration": {"min": 0, "max": 50, "rate": 10.0},
            "power": {"min": 0, "max": 500, "rate": 100.0},
            "radar": {"min": 0, "max": 1000, "rate": 200.0},
            "thermal": {"min": -20, "max": 200, "rate": 20.0},
            "gas": {"min": 0, "max": 1000, "rate": 50.0},
            "motion": {"min": 0, "max": 1, "rate": 1.0},
            "proximity": {"min": 0, "max": 1000, "rate": 500.0},
            "network": {"min": 0, "max": 100, "rate": 50.0}
        }
        
        # Contamination rate (expected proportion of anomalies)
        self.contamination = 0.05
        
        logger.info("Anomaly detector initialized", model_id=str(self.model_id))
    
    async def detect(
        self,
        sensor_uid: str,
        values: Dict[str, float],
        sensor_type: str,
        thresholds: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run anomaly detection on sensor values
        
        Returns:
            dict with is_anomaly, score, confidence, explanation, etc.
        """
        start_time = datetime.utcnow()
        
        # Use custom thresholds or defaults
        active_thresholds = thresholds or self.default_thresholds.get(sensor_type, {})
        
        anomalies = []
        scores = []
        contributing_features = []
        
        # 1. Threshold-based detection (fast, deterministic)
        threshold_result = self._check_thresholds(values, active_thresholds)
        if threshold_result["is_anomaly"]:
            anomalies.append("threshold")
            scores.append(threshold_result["score"])
            contributing_features.extend(threshold_result["features"])
        
        # 2. Rate-of-change detection
        roc_result = await self._check_rate_of_change(sensor_uid, values, active_thresholds)
        if roc_result["is_anomaly"]:
            anomalies.append("rate_of_change")
            scores.append(roc_result["score"])
            contributing_features.extend(roc_result["features"])
        
        # 3. Isolation Forest detection (ML-based)
        ml_result = await self._ml_detection(sensor_uid, values)
        if ml_result["is_anomaly"]:
            anomalies.append("ml_isolation_forest")
            scores.append(ml_result["score"])
            contributing_features.extend(ml_result["features"])
        
        # 4. Update history
        await self._update_history(sensor_uid, values)
        
        # Calculate overall result
        is_anomaly = len(anomalies) > 0
        
        if is_anomaly:
            # Average of all anomaly scores, weighted
            overall_score = np.mean(scores) if scores else 0.0
            confidence = min(0.95, 0.5 + 0.15 * len(anomalies))
            
            # Determine anomaly type
            if "threshold" in anomalies:
                anomaly_type = "threshold_violation"
            elif "rate_of_change" in anomalies:
                anomaly_type = "sudden_change"
            else:
                anomaly_type = "pattern_anomaly"
            
            # Generate explanation
            explanation = self._generate_explanation(
                anomaly_type, contributing_features, values, active_thresholds
            )
            
            # Recommend action based on severity
            if overall_score > 0.8:
                recommended_action = "IMMEDIATE: Investigate sensor readings. Possible equipment failure."
            elif overall_score > 0.6:
                recommended_action = "HIGH: Review sensor data and check for environmental factors."
            else:
                recommended_action = "MONITOR: Track readings for developing patterns."
        else:
            overall_score = 0.0
            confidence = 0.95
            anomaly_type = None
            explanation = "All readings within normal parameters."
            recommended_action = None
        
        inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "is_anomaly": is_anomaly,
            "score": round(overall_score, 4),
            "confidence": round(confidence, 4),
            "anomaly_type": anomaly_type,
            "detection_methods": anomalies,
            "contributing_features": contributing_features[:5],  # Top 5
            "explanation": explanation,
            "recommended_action": recommended_action,
            "inference_time_ms": round(inference_time, 2)
        }
    
    def _check_thresholds(
        self, 
        values: Dict[str, float], 
        thresholds: Dict
    ) -> Dict[str, Any]:
        """Check values against static thresholds"""
        violations = []
        max_score = 0.0
        
        for key, value in values.items():
            min_val = thresholds.get("min", thresholds.get(f"{key}_min"))
            max_val = thresholds.get("max", thresholds.get(f"{key}_max"))
            
            if min_val is not None and value < min_val:
                severity = (min_val - value) / abs(min_val) if min_val != 0 else 1.0
                violations.append({
                    "feature": key,
                    "value": value,
                    "violation": "below_minimum",
                    "threshold": min_val,
                    "severity": min(1.0, severity)
                })
                max_score = max(max_score, min(1.0, 0.5 + severity * 0.5))
            
            if max_val is not None and value > max_val:
                severity = (value - max_val) / abs(max_val) if max_val != 0 else 1.0
                violations.append({
                    "feature": key,
                    "value": value,
                    "violation": "above_maximum",
                    "threshold": max_val,
                    "severity": min(1.0, severity)
                })
                max_score = max(max_score, min(1.0, 0.5 + severity * 0.5))
        
        return {
            "is_anomaly": len(violations) > 0,
            "score": max_score,
            "features": violations
        }
    
    async def _check_rate_of_change(
        self,
        sensor_uid: str,
        values: Dict[str, float],
        thresholds: Dict
    ) -> Dict[str, Any]:
        """Check for sudden changes in values"""
        history = self.history.get(sensor_uid, [])
        
        if len(history) < 2:
            return {"is_anomaly": False, "score": 0.0, "features": []}
        
        violations = []
        max_score = 0.0
        
        # Get last reading
        last_reading = history[-1]["values"]
        
        for key, value in values.items():
            if key in last_reading:
                change = abs(value - last_reading[key])
                rate_threshold = thresholds.get("rate", thresholds.get(f"{key}_rate", float('inf')))
                
                if change > rate_threshold:
                    severity = (change - rate_threshold) / rate_threshold if rate_threshold > 0 else 1.0
                    violations.append({
                        "feature": key,
                        "value": value,
                        "previous_value": last_reading[key],
                        "change": change,
                        "violation": "rapid_change",
                        "threshold": rate_threshold,
                        "severity": min(1.0, severity)
                    })
                    max_score = max(max_score, min(1.0, 0.6 + severity * 0.4))
        
        return {
            "is_anomaly": len(violations) > 0,
            "score": max_score,
            "features": violations
        }
    
    async def _ml_detection(
        self,
        sensor_uid: str,
        values: Dict[str, float]
    ) -> Dict[str, Any]:
        """Run Isolation Forest anomaly detection"""
        history = self.history.get(sensor_uid, [])
        
        # Need enough history for training
        if len(history) < 20:
            return {"is_anomaly": False, "score": 0.0, "features": []}
        
        # Prepare data
        feature_names = sorted(values.keys())
        
        # Build training data from history
        X_train = []
        for h in history[-50:]:  # Use last 50 readings
            row = [h["values"].get(f, 0.0) for f in feature_names]
            X_train.append(row)
        
        X_train = np.array(X_train)
        
        # Current reading
        X_current = np.array([[values.get(f, 0.0) for f in feature_names]])
        
        # Get or create model for this sensor
        if sensor_uid not in self.models or len(history) % 20 == 0:
            # Train new model
            self.scalers[sensor_uid] = StandardScaler()
            X_scaled = self.scalers[sensor_uid].fit_transform(X_train)
            
            self.models[sensor_uid] = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto'
            )
            self.models[sensor_uid].fit(X_scaled)
        
        # Predict
        scaler = self.scalers[sensor_uid]
        model = self.models[sensor_uid]
        
        X_current_scaled = scaler.transform(X_current)
        
        # -1 for anomaly, 1 for normal
        prediction = model.predict(X_current_scaled)[0]
        
        # Get anomaly score (negative scores are more anomalous)
        score = -model.score_samples(X_current_scaled)[0]
        
        # Normalize score to 0-1
        normalized_score = min(1.0, max(0.0, (score + 0.5) / 1.0))
        
        if prediction == -1:
            # Calculate feature importance using deviation from mean
            mean_values = np.mean(X_train, axis=0)
            std_values = np.std(X_train, axis=0) + 1e-6
            
            deviations = np.abs(X_current[0] - mean_values) / std_values
            
            features = []
            for i, fname in enumerate(feature_names):
                if deviations[i] > 2:  # More than 2 std deviations
                    features.append({
                        "feature": fname,
                        "deviation_sigma": round(deviations[i], 2),
                        "value": values.get(fname),
                        "mean": round(mean_values[i], 2)
                    })
            
            return {
                "is_anomaly": True,
                "score": normalized_score,
                "features": sorted(features, key=lambda x: -x["deviation_sigma"])[:3]
            }
        
        return {"is_anomaly": False, "score": 0.0, "features": []}
    
    async def _update_history(
        self,
        sensor_uid: str,
        values: Dict[str, float]
    ) -> None:
        """Update sensor reading history"""
        if sensor_uid not in self.history:
            self.history[sensor_uid] = []
        
        self.history[sensor_uid].append({
            "values": values,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Trim history
        if len(self.history[sensor_uid]) > self.history_window:
            self.history[sensor_uid] = self.history[sensor_uid][-self.history_window:]
    
    def _generate_explanation(
        self,
        anomaly_type: str,
        features: List[Dict],
        values: Dict[str, float],
        thresholds: Dict
    ) -> str:
        """Generate human-readable explanation"""
        if not features:
            return "Anomaly detected based on pattern analysis."
        
        explanations = []
        
        for f in features[:3]:
            feature_name = f.get("feature", "unknown")
            value = f.get("value", 0)
            
            if f.get("violation") == "below_minimum":
                explanations.append(
                    f"{feature_name} ({value}) is below minimum threshold ({f.get('threshold')})"
                )
            elif f.get("violation") == "above_maximum":
                explanations.append(
                    f"{feature_name} ({value}) exceeds maximum threshold ({f.get('threshold')})"
                )
            elif f.get("violation") == "rapid_change":
                explanations.append(
                    f"{feature_name} changed by {f.get('change'):.2f} (threshold: {f.get('threshold')})"
                )
            elif f.get("deviation_sigma"):
                explanations.append(
                    f"{feature_name} is {f.get('deviation_sigma')}σ from normal (value: {value})"
                )
        
        return "; ".join(explanations) if explanations else "Anomaly detected in sensor readings."
    
    async def load_model(self, model_path: str) -> bool:
        """Load pre-trained model from disk"""
        try:
            if os.path.exists(model_path):
                data = joblib.load(model_path)
                self.models = data.get("models", {})
                self.scalers = data.get("scalers", {})
                logger.info("Loaded anomaly detection models", path=model_path)
                return True
        except Exception as e:
            logger.error("Failed to load models", error=str(e))
        return False
    
    async def save_model(self, model_path: str) -> bool:
        """Save trained models to disk"""
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            joblib.dump({
                "models": self.models,
                "scalers": self.scalers,
                "model_id": str(self.model_id)
            }, model_path)
            logger.info("Saved anomaly detection models", path=model_path)
            return True
        except Exception as e:
            logger.error("Failed to save models", error=str(e))
            return False


# Singleton instance
anomaly_detector = AnomalyDetector()
