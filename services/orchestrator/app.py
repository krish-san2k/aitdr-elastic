"""
Orchestrator Service - Coordinates alert triage and incident response
"""
from fastapi import FastAPI, Request, HTTPException
from elasticsearch import Elasticsearch
import requests
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Orchestrator", version="1.0.0")

# Configuration
ES_URL = os.getenv("ES_URL", "http://elasticsearch:9200")
JIRA_URL = os.getenv("JIRA_URL", "http://example-jira.local")
EDR_API = os.getenv("EDR_API", "http://mock-edr.local")
COPILOT_URL = os.getenv("COPILOT_URL", "http://copilot:8002")
ML_SCORER_URL = os.getenv("ML_SCORER_URL", "http://ml_scorer:8001")

# Initialize Elasticsearch
try:
    es = Elasticsearch([ES_URL])
    es.ping()
    logger.info(f"Connected to Elasticsearch: {ES_URL}")
except Exception as e:
    logger.error(f"Failed to connect to Elasticsearch: {e}")
    es = None


class Alert(BaseModel):
    """Alert data model"""
    detector: str
    description: str
    severity: float
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    timestamp: Optional[str] = None
    references: Optional[list] = None


class TriageRequest(BaseModel):
    """Triage request model"""
    alert_id: str
    action: str  # "approve", "reject", "investigate"
    comment: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "orchestrator"}


@app.post("/webhook/alerts")
async def webhook_alerts(request: Request):
    """
    Receive alerts from external sources and process them
    """
    try:
        payload = await request.json()
        
        # Add metadata
        payload["ingestion_time"] = datetime.utcnow().isoformat()
        payload["processed"] = False
        
        # Index alert into Elasticsearch
        if es:
            result = es.index(index="alerts", document=payload)
            logger.info(f"Indexed alert: {result['_id']}")
            payload["_id"] = result["_id"]
        
        # Send for ML scoring
        try:
            if payload.get("source_ip") and payload.get("dest_ip"):
                features = [
                    float(payload.get("severity", 0)),
                    hash(payload.get("detector", "")) % 100,
                    1.0 if payload.get("source_ip") else 0
                ]
                
                score_response = requests.post(
                    f"{ML_SCORER_URL}/score",
                    json={"features": features, "event_id": payload.get("_id", "unknown")},
                    timeout=5
                )
                
                if score_response.status_code == 200:
                    ml_result = score_response.json()
                    payload["ml_score"] = ml_result.get("anomaly_score", 0)
                    payload["is_anomaly"] = ml_result.get("is_anomaly", False)
                    logger.info(f"ML Score: {ml_result.get('anomaly_score', 'N/A')}")
        except Exception as e:
            logger.warning(f"ML scoring failed: {e}")
        
        return {
            "status": "accepted",
            "alert_id": payload.get("_id", "unknown"),
            "severity": payload.get("severity", "unknown")
        }
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts", response_model=Dict[str, Any])
async def create_alert(alert: Alert):
    """
    Create a new alert
    """
    try:
        alert_doc = {
            **alert.dict(),
            "timestamp": alert.timestamp or datetime.utcnow().isoformat(),
            "ingestion_time": datetime.utcnow().isoformat(),
            "processed": False
        }
        
        if es:
            result = es.index(index="alerts", document=alert_doc)
            logger.info(f"Created alert: {result['_id']}")
            return {
                "status": "created",
                "alert_id": result["_id"],
                "severity": alert.severity
            }
        else:
            raise Exception("Elasticsearch not connected")
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/triage")
async def triage_alert(triage_req: TriageRequest):
    """
    Record triage action for an alert
    """
    try:
        # Fetch alert from ES
        if not es:
            raise Exception("Elasticsearch not connected")
        
        alert = es.get(index="alerts", id=triage_req.alert_id)
        alert_source = alert["_source"]
        
        # Add triage info
        alert_source["triage_action"] = triage_req.action
        alert_source["triage_comment"] = triage_req.comment
        alert_source["triage_timestamp"] = datetime.utcnow().isoformat()
        alert_source["processed"] = True
        
        # Update in ES
        es.index(index="alerts", id=triage_req.alert_id, document=alert_source)
        
        logger.info(f"Triaged alert {triage_req.alert_id}: {triage_req.action}")
        
        return {
            "status": "triaged",
            "alert_id": triage_req.alert_id,
            "action": triage_req.action,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triaging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """
    Get alert details by ID
    """
    try:
        if not es:
            raise Exception("Elasticsearch not connected")
        
        result = es.get(index="alerts", id=alert_id)
        return result["_source"]
    except Exception as e:
        logger.error(f"Error fetching alert: {e}")
        raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/alerts")
async def list_alerts(severity: Optional[str] = None, limit: int = 10):
    """
    List alerts with optional filtering
    """
    try:
        if not es:
            raise Exception("Elasticsearch not connected")
        
        query = {"match_all": {}}
        if severity:
            query = {"term": {"severity": severity}}
        
        result = es.search(index="alerts", body={"query": query, "size": limit})
        alerts = [hit["_source"] for hit in result["hits"]["hits"]]
        
        return {
            "total": result["hits"]["total"]["value"],
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get orchestrator statistics
    """
    try:
        if not es:
            return {"error": "Elasticsearch not connected"}
        
        # Count alerts
        result = es.count(index="alerts")
        total_alerts = result["count"]
        
        # Count processed
        processed = es.count(
            index="alerts",
            body={"query": {"term": {"processed": True}}}
        )
        
        return {
            "total_alerts": total_alerts,
            "processed_alerts": processed["count"],
            "pending_alerts": total_alerts - processed["count"],
            "es_connected": True
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e), "es_connected": False}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
