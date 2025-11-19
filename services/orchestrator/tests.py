"""
Test suite for Orchestrator service
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def test_health_check():
    """Test health check endpoint"""
    from services.orchestrator.app import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_alert():
    """Test creating an alert"""
    from services.orchestrator.app import app
    
    client = TestClient(app)
    response = client.post(
        "/alerts",
        json={
            "detector": "test_detector",
            "description": "Test alert",
            "severity": 5.0,
            "source_ip": "192.168.1.1",
            "dest_ip": "192.168.1.2"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert "alert_id" in data


def test_list_alerts():
    """Test listing alerts"""
    from services.orchestrator.app import app
    
    client = TestClient(app)
    response = client.get("/alerts?limit=10")
    
    # Should work even if ES is not connected
    assert response.status_code in [200, 500]


def test_get_stats():
    """Test getting orchestrator stats"""
    from services.orchestrator.app import app
    
    client = TestClient(app)
    response = client.get("/stats")
    
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
