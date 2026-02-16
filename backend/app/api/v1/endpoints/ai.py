"""
KAVACH-INFINITY AI/ML Endpoints
Anomaly detection, predictions, risk scoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import structlog

from app.core import get_db, rbac
from app.models import Site, Sensor, MLModel, ModelPrediction, User
from app.models.schemas import (
    AnomalyDetectionRequest, AnomalyDetectionResponse,
    RiskScoreRequest, RiskScoreResponse,
    PredictionRequest, PredictionResponse
)
from app.api.v1.deps import get_current_user
from app.services.ai.anomaly_detector import anomaly_detector
from app.services.ai.risk_scorer import risk_scorer
from app.services.ai.predictor import failure_predictor

logger = structlog.get_logger()
router = APIRouter()


@router.post("/anomaly/detect", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run anomaly detection on sensor data
    
    This endpoint analyzes sensor readings and determines if they represent
    anomalous behavior that may require attention.
    """
    # Get sensor for context
    result = await db.execute(
        select(Sensor).where(Sensor.sensor_uid == request.sensor_uid)
    )
    sensor = result.scalar_one_or_none()
    
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor {request.sensor_uid} not found"
        )
    
    # Run detection
    detection_result = await anomaly_detector.detect(
        sensor_uid=request.sensor_uid,
        values=request.values,
        sensor_type=sensor.sensor_type.value,
        thresholds=sensor.thresholds,
        context=request.context
    )
    
    # Log prediction
    prediction_log = ModelPrediction(
        model_id=anomaly_detector.model_id,
        site_id=sensor.site_id,
        input_data={"sensor_uid": request.sensor_uid, "values": request.values},
        output_data=detection_result,
        confidence=detection_result.get("confidence", 0.0),
        feature_importance=detection_result.get("contributing_features", {}),
        explanation=detection_result.get("explanation", "")
    )
    db.add(prediction_log)
    await db.commit()
    
    return AnomalyDetectionResponse(
        is_anomaly=detection_result["is_anomaly"],
        anomaly_score=detection_result["score"],
        confidence=detection_result["confidence"],
        anomaly_type=detection_result.get("anomaly_type"),
        contributing_features=detection_result.get("contributing_features", []),
        explanation=detection_result["explanation"],
        recommended_action=detection_result.get("recommended_action")
    )


@router.post("/risk/score", response_model=RiskScoreResponse)
async def calculate_risk_score(
    request: RiskScoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate risk score for a site
    
    Aggregates multiple risk factors including:
    - Sensor health status
    - Recent anomalies
    - Active alerts
    - Historical incidents
    - Environmental factors
    """
    # Verify site exists
    result = await db.execute(
        select(Site).where(Site.id == request.site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Calculate risk
    risk_result = await risk_scorer.calculate(
        site_id=request.site_id,
        db=db,
        context=request.context
    )
    
    return RiskScoreResponse(
        overall_risk=risk_result["overall_risk"],
        risk_level=risk_result["risk_level"],
        risk_factors=risk_result["risk_factors"],
        trend=risk_result["trend"],
        recommendations=risk_result["recommendations"]
    )


@router.post("/predict/failure", response_model=PredictionResponse)
async def predict_failure(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict potential failures for a site or sensor
    
    Uses historical data and current trends to predict:
    - Sensor failures
    - System degradation
    - Maintenance needs
    """
    # Verify site exists
    result = await db.execute(
        select(Site).where(Site.id == request.site_id)
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Run prediction
    prediction = await failure_predictor.predict(
        site_id=request.site_id,
        sensor_id=request.sensor_id,
        prediction_type=request.prediction_type,
        horizon_hours=request.horizon_hours,
        db=db
    )
    
    return PredictionResponse(
        prediction_type=request.prediction_type,
        probability=prediction["probability"],
        confidence=prediction["confidence"],
        predicted_time=prediction.get("predicted_time"),
        horizon_hours=request.horizon_hours,
        factors=prediction["factors"],
        explanation=prediction["explanation"]
    )


@router.get("/models")
async def list_models(
    model_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List registered ML models
    """
    query = select(MLModel)
    
    if model_type:
        query = query.where(MLModel.model_type == model_type)
    
    if is_active is not None:
        query = query.where(MLModel.is_active == is_active)
    
    result = await db.execute(query.order_by(MLModel.name, MLModel.version.desc()))
    models = result.scalars().all()
    
    return {
        "models": [
            {
                "id": str(m.id),
                "name": m.name,
                "version": m.version,
                "model_type": m.model_type,
                "algorithm": m.algorithm,
                "accuracy": m.accuracy,
                "precision": m.precision,
                "recall": m.recall,
                "f1_score": m.f1_score,
                "is_active": m.is_active,
                "deployed_at": m.deployed_at.isoformat() if m.deployed_at else None,
                "trained_at": m.trained_at.isoformat() if m.trained_at else None
            } for m in models
        ],
        "total": len(models)
    }


@router.get("/models/{model_id}/performance")
async def get_model_performance(
    model_id: UUID,
    period: str = Query("7d", regex="^(1d|7d|30d)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get model performance metrics over time
    """
    # Verify model exists
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    
    # Get predictions for period
    if period == "1d":
        start_time = datetime.utcnow() - timedelta(days=1)
    elif period == "7d":
        start_time = datetime.utcnow() - timedelta(days=7)
    else:
        start_time = datetime.utcnow() - timedelta(days=30)
    
    # Count predictions
    from sqlalchemy import func
    
    total_predictions = await db.execute(
        select(func.count(ModelPrediction.id)).where(
            ModelPrediction.model_id == model_id,
            ModelPrediction.created_at >= start_time
        )
    )
    total = total_predictions.scalar()
    
    # Average confidence
    avg_confidence = await db.execute(
        select(func.avg(ModelPrediction.confidence)).where(
            ModelPrediction.model_id == model_id,
            ModelPrediction.created_at >= start_time
        )
    )
    avg_conf = avg_confidence.scalar() or 0.0
    
    # Average inference time
    avg_time = await db.execute(
        select(func.avg(ModelPrediction.inference_time_ms)).where(
            ModelPrediction.model_id == model_id,
            ModelPrediction.created_at >= start_time
        )
    )
    avg_inference = avg_time.scalar() or 0.0
    
    return {
        "model_id": str(model_id),
        "model_name": model.name,
        "model_version": model.version,
        "period": period,
        "metrics": {
            "total_predictions": total,
            "average_confidence": round(avg_conf, 4),
            "average_inference_time_ms": round(avg_inference, 2),
            "registered_accuracy": model.accuracy,
            "registered_precision": model.precision,
            "registered_recall": model.recall,
            "registered_f1": model.f1_score
        }
    }


@router.get("/explainability/{prediction_id}")
async def get_prediction_explanation(
    prediction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed explanation for a specific prediction
    
    Provides feature importance and human-readable explanation
    for AI decisions (XAI - Explainable AI)
    """
    result = await db.execute(
        select(ModelPrediction).where(ModelPrediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    
    # Get model info
    model_result = await db.execute(
        select(MLModel).where(MLModel.id == prediction.model_id)
    )
    model = model_result.scalar_one_or_none()
    
    return {
        "prediction_id": str(prediction_id),
        "model": {
            "name": model.name if model else "Unknown",
            "version": model.version if model else "Unknown",
            "type": model.model_type if model else "Unknown"
        },
        "input_data": prediction.input_data,
        "output": prediction.output_data,
        "confidence": prediction.confidence,
        "feature_importance": prediction.feature_importance,
        "explanation": prediction.explanation,
        "created_at": prediction.created_at.isoformat()
    }
