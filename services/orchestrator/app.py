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
        
        # Count by severity
        severity_agg = es.search(
            index="alerts",
            body={
                "size": 0,
                "aggs": {
                    "by_severity": {
                        "range": {
                            "field": "severity",
                            "ranges": [
                                {"to": 3.5},
                                {"from": 3.5, "to": 6.5},
                                {"from": 6.5, "to": 8.5},
                                {"from": 8.5}
                            ]
                        }
                    }
                }
            }
        )
        
        return {
            "total_alerts": total_alerts,
            "processed_alerts": processed["count"],
            "pending_alerts": total_alerts - processed["count"],
            "es_connected": True,
            "severity_distribution": severity_agg["aggregations"]["by_severity"]["buckets"]
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e), "es_connected": False}


class CopilotQuestion(BaseModel):
    """Copilot question model"""
    query: str
    use_llm: bool = True


class CopilotTriageRequest(BaseModel):
    """Copilot triage request"""
    alert_id: str


@app.post("/copilot/ask")
async def copilot_ask(req: CopilotQuestion):
    """
    Ask Copilot to answer a security question using Elasticsearch context
    """
    try:
        if not es:
            raise Exception("Elasticsearch not connected")
        
        # Search for relevant alerts
        alert_query = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"description": {"query": req.query, "boost": 2}}},
                        {"match": {"detector": req.query}},
                        {"match": {"alert_signature": req.query}},
                    ]
                }
            },
            "size": 10
        }
        
        alert_results = es.search(index="alerts*", body=alert_query)
        alerts = [
            {
                "description": hit["_source"].get("description"),
                "severity": hit["_source"].get("severity"),
                "detector": hit["_source"].get("detector"),
                "timestamp": hit["_source"].get("timestamp")
            }
            for hit in alert_results["hits"]["hits"]
        ]
        
        # Search for relevant intelligence
        intel_query = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"value": req.query}},
                        {"match": {"description": req.query}},
                        {"match": {"tags": req.query}}
                    ]
                }
            },
            "size": 5
        }
        
        intel_results = es.search(index="intel*", body=intel_query)
        intel = [
            {
                "value": hit["_source"].get("value"),
                "type": hit["_source"].get("type"),
                "description": hit["_source"].get("description")
            }
            for hit in intel_results["hits"]["hits"]
        ]
        
        # Generate response
        response = f"Query: {req.query}\n\n"
        if alerts:
            response += f"Found {len(alerts)} relevant alerts:\n"
            for i, alert in enumerate(alerts[:5], 1):
                response += f"  {i}. [{alert['severity']}] {alert['description']}\n"
        else:
            response += "No relevant alerts found in the system.\n"
        
        if intel:
            response += f"\nFound {len(intel)} relevant intelligence items:\n"
            for i, item in enumerate(intel[:5], 1):
                response += f"  {i}. [{item['type']}] {item['value']}\n"
        
        logger.info(f"Copilot answered query: {req.query}")
        
        return {
            "query": req.query,
            "response": response,
            "alerts_found": len(alerts),
            "intel_found": len(intel),
            "context": {
                "alerts": alerts[:5],
                "intel": intel[:5]
            }
        }
    except Exception as e:
        logger.error(f"Error in copilot ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/copilot/triage")
async def copilot_triage(req: CopilotTriageRequest):
    """
    Get Copilot triage suggestion for an alert
    """
    try:
        if not es:
            raise Exception("Elasticsearch not connected")
        
        # Fetch alert
        alert = es.get(index="alerts", id=req.alert_id)
        alert_source = alert["_source"]
        
        # Search for similar alerts
        similar_query = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"detector": alert_source.get("detector")}},
                        {"match": {"description": alert_source.get("description")}},
                    ]
                }
            },
            "size": 5
        }
        
        similar_results = es.search(index="alerts*", body=similar_query)
        similar_alerts = similar_results["hits"]["hits"]
        
        # Build triage suggestion
        severity = alert_source.get("severity", 0)
        detector = alert_source.get("detector", "unknown")
        
        suggestion = f"Alert Analysis:\n"
        suggestion += f"- Severity: {severity}/10\n"
        suggestion += f"- Detector: {detector}\n"
        suggestion += f"- Similar alerts in system: {len(similar_alerts)}\n\n"
        
        if severity >= 8:
            suggestion += "RECOMMENDED ACTION: High-priority alert. Immediate investigation required.\n"
            suggestion += "1. Isolate affected host/account\n"
            suggestion += "2. Review detailed logs\n"
            suggestion += "3. Escalate to IR team\n"
        elif severity >= 6:
            suggestion += "RECOMMENDED ACTION: Medium-priority alert. Investigate within 1 hour.\n"
            suggestion += "1. Gather additional context\n"
            suggestion += "2. Check for similar incidents\n"
            suggestion += "3. Determine if false positive\n"
        else:
            suggestion += "RECOMMENDED ACTION: Low-priority alert. Review and monitor.\n"
            suggestion += "1. Log for trend analysis\n"
            suggestion += "2. Correlate with other events\n"
        
        logger.info(f"Copilot triaged alert: {req.alert_id}")
        
        return {
            "alert_id": req.alert_id,
            "description": alert_source.get("description"),
            "severity": severity,
            "triage_suggestion": suggestion,
            "related_alerts": len(similar_alerts),
            "ml_score": alert_source.get("ml_score", "N/A"),
            "is_anomaly": alert_source.get("is_anomaly", False)
        }
    except Exception as e:
        logger.error(f"Error in copilot triage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
