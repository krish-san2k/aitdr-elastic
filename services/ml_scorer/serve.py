"""
ML Scorer Service - FastAPI service for anomaly detection using Isolation Forest
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import joblib
import os
import json
from confluent_kafka import Consumer, KafkaError
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Scorer", version="1.0.0")

# Load model or create dummy one
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/isoforest.pkl")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

# Initialize model (create dummy if not exists)
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        logger.info(f"Loaded model from {MODEL_PATH}")
    else:
        logger.warning(f"Model not found at {MODEL_PATH}, creating dummy model")
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(contamination=0.1, random_state=42)
        # Fit on dummy data
        X_dummy = np.random.randn(100, 5)
        model.fit(X_dummy)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model, MODEL_PATH)
except Exception as e:
    logger.error(f"Error loading/creating model: {e}")
    from sklearn.ensemble import IsolationForest
    model = IsolationForest(contamination=0.1, random_state=42)
    X_dummy = np.random.randn(100, 5)
    model.fit(X_dummy)


class ScoreRequest(BaseModel):
    features: List[float]
    event_id: Optional[str] = None
    timestamp: Optional[str] = None


class ScoreResponse(BaseModel):
    event_id: str
    anomaly_score: float
    is_anomaly: bool
    timestamp: str


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ml_scorer"}


@app.post("/score", response_model=ScoreResponse)
def score_event(request: ScoreRequest):
    """
    Score an event for anomaly detection
    
    Args:
        request: ScoreRequest with features and optional event_id
        
    Returns:
        ScoreResponse with anomaly score and classification
    """
    try:
        # Validate input
        if not request.features or len(request.features) == 0:
            raise HTTPException(status_code=400, detail="Features cannot be empty")
        
        # Convert to numpy array
        X = np.array(request.features).reshape(1, -1)
        
        # Get anomaly score (-1 for anomalies, 1 for normal)
        prediction = model.predict(X)[0]
        # Get raw anomaly score (lower = more anomalous)
        anomaly_score = float(-model.score_samples(X)[0])
        
        is_anomaly = prediction == -1
        
        return ScoreResponse(
            event_id=request.event_id or "unknown",
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            timestamp=request.timestamp or datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error scoring event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_score")
def batch_score_events(requests: List[ScoreRequest]):
    """
    Score multiple events in batch
    """
    results = []
    for req in requests:
        try:
            X = np.array(req.features).reshape(1, -1)
            prediction = model.predict(X)[0]
            anomaly_score = float(-model.score_samples(X)[0])
            is_anomaly = prediction == -1
            
            results.append({
                "event_id": req.event_id or "unknown",
                "anomaly_score": anomaly_score,
                "is_anomaly": is_anomaly,
                "timestamp": req.timestamp or datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error scoring event {req.event_id}: {e}")
            results.append({
                "event_id": req.event_id or "unknown",
                "error": str(e)
            })
    
    return {"results": results}


@app.get("/model/info")
def model_info():
    """Get information about the loaded model"""
    return {
        "model_type": type(model).__name__,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
