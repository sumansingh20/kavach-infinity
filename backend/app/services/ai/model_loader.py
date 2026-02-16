"""
KAVACH-INFINITY Model Loader
Load and manage ML models at startup
"""

import os
import structlog
from pathlib import Path

from app.config import settings
from app.services.ai.anomaly_detector import anomaly_detector
from app.services.ai.risk_scorer import risk_scorer
from app.services.ai.predictor import failure_predictor

logger = structlog.get_logger()


async def load_all_models() -> None:
    """
    Load all ML models at application startup
    """
    model_path = Path(settings.MODEL_PATH)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Load anomaly detection models
    anomaly_model_path = model_path / "anomaly_detector.joblib"
    if anomaly_model_path.exists():
        await anomaly_detector.load_model(str(anomaly_model_path))
        logger.info("Loaded anomaly detection models")
    else:
        logger.info("No pre-trained anomaly models found, will train online")
    
    # Risk scorer and predictor use rule-based + online learning
    # No pre-trained models needed
    
    logger.info("All AI/ML models initialized",
               anomaly_detector_id=str(anomaly_detector.model_id))


async def save_all_models() -> None:
    """
    Save all trained models before shutdown
    """
    model_path = Path(settings.MODEL_PATH)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Save anomaly detection models
    anomaly_model_path = model_path / "anomaly_detector.joblib"
    await anomaly_detector.save_model(str(anomaly_model_path))
    
    logger.info("All AI/ML models saved")
