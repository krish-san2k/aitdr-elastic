"""
Test suite for ML Scorer service
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))


def test_health_check():
    """Test health check endpoint"""
    from services.ml_scorer.serve import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_score_event():
    """Test event scoring endpoint"""
    from services.ml_scorer.serve import app
    
    client = TestClient(app)
    response = client.post(
        "/score",
        json={
            "features": [1.0, 2.0, 3.0, 4.0, 5.0],
            "event_id": "test-123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "test-123"
    assert "anomaly_score" in data
    assert "is_anomaly" in data


def test_score_with_empty_features():
    """Test scoring with empty features"""
    from services.ml_scorer.serve import app
    
    client = TestClient(app)
    response = client.post(
        "/score",
        json={"features": []}
    )
    
    assert response.status_code == 400


def test_batch_score():
    """Test batch scoring endpoint"""
    from services.ml_scorer.serve import app
    
    client = TestClient(app)
    response = client.post(
        "/batch_score",
        json=[
            {"features": [1.0, 2.0, 3.0, 4.0, 5.0], "event_id": "evt-1"},
            {"features": [2.0, 3.0, 4.0, 5.0, 6.0], "event_id": "evt-2"}
        ]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2


def test_model_info():
    """Test model info endpoint"""
    from services.ml_scorer.serve import app
    
    client = TestClient(app)
    response = client.get("/model/info")
    
    assert response.status_code == 200
    assert "model_type" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
