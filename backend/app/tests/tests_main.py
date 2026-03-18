from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import os

load_dotenv()
client = TestClient(app)
API_KEY = os.getenv("API_KEY")

HEADERS = {"X-API-Key": API_KEY}

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"



def test_missing_api_key():
    response = client.post("/api/reconcile/medication", json={
        "sources": [
            {"system": "Hospital", "medication": "Aspirin 81mg"},
            {"system": "Clinic", "medication": "Aspirin 325mg"}
        ]
    })
    assert response.status_code == 403



def test_invalid_api_key():
    response = client.post(
        "/api/reconcile/medication",
        json={
            "sources": [
                {"system": "Hospital", "medication": "Aspirin 81mg"},
                {"system": "Clinic", "medication": "Aspirin 325mg"}
            ]
        },
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401


def test_reconcile_medication():
    mock_response = MagicMock()
    mock_response.message.content = '''{
        "reconciled_medication": "Aspirin 81mg daily",
        "confidence_score": 0.88,
        "reasoning": "81mg is standard cardioprotective dose",
        "recommended_actions": ["Update clinic records"],
        "clinical_safety_check": "PASSED"
    }'''

    with patch("app.main.ollama_client.chat", return_value=mock_response):
        response = client.post(
            "/api/reconcile/medication",
            json={
                "patient_context": {
                    "age": 65,
                    "conditions": ["Hypertension"],
                    "recent_labs": {}
                },
                "sources": [
                    {
                        "system": "Hospital EHR",
                        "medication": "Aspirin 81mg daily",
                        "last_updated": "2025-01-01",
                        "source_reliability": "high"
                    },
                    {
                        "system": "Clinic",
                        "medication": "Aspirin 325mg daily",
                        "last_updated": "2024-06-01",
                        "source_reliability": "medium"
                    }
                ]
            },
            headers=HEADERS
        )

    assert response.status_code == 200
    data = response.json()
    assert "reconciled_medication" in data
    assert "confidence_score" in data
    assert "reasoning" in data
    assert "clinical_safety_check" in data
    assert 0.0 <= data["confidence_score"] <= 1.0



def test_validate_data_quality():
    mock_response = MagicMock()
    mock_response.message.content = '''{
        "overall_score": 45,
        "breakdown": {
            "completeness": 60,
            "accuracy": 30,
            "timeliness": 50,
            "clinical_plausibility": 20
        },
        "issues_detected": [
            {
                "field": "vital_signs.blood_pressure",
                "issue": "Blood pressure 340/180 is physiologically implausible",
                "severity": "critical"
            }
        ]
    }'''

    with patch("app.main.ollama_client.chat", return_value=mock_response):
        response = client.post(
            "/api/validate/data-quality",
            json={
                "demographics": {"name": "John Doe", "dob": "1955-03-15", "gender": "M"},
                "medications": ["Metformin 500mg"],
                "allergies": [],
                "conditions": ["Type 2 Diabetes"],
                "vital_signs": {"blood_pressure": "340/180", "heart_rate": 72},
                "last_updated": "2024-06-15"
            },
            headers=HEADERS
        )

    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "breakdown" in data
    assert "issues_detected" in data
    assert data["overall_score"] <= 100



def test_reconcile_invalid_ollama_response():
    mock_response = MagicMock()
    mock_response.message.content = "This is not JSON"

    with patch("app.main.ollama_client.chat", return_value=mock_response):
        response = client.post(
            "/api/reconcile/medication",
            json={
                "sources": [
                    {"system": "Hospital", "medication": "Aspirin 81mg"},
                    {"system": "Clinic", "medication": "Aspirin 325mg"}
                ]
            },
            headers=HEADERS
        )

    assert response.status_code == 500
    assert "invalid JSON" in response.json()["detail"]