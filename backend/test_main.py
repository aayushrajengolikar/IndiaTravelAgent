from fastapi.testclient import TestClient
from main import app
import os
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "indiatravelagent-backend"

def test_get_destinations():
    response = client.get("/api/destinations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_destinations_with_query():
    response = client.get("/api/destinations?query=Taj")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Taj Mahal" in data[0]["name"]

def test_get_destinations_with_state_filter():
    response = client.get("/api/destinations?state=Goa")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["state_ut"] == "Goa"

def test_get_destinations_with_category_filter():
    response = client.get("/api/destinations?category=Beach")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["category"] == "Beach"

def test_get_destinations_pagination():
    response = client.get("/api/destinations?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

def test_get_destination_by_id_valid():
    # First get list to get a valid ID
    list_res = client.get("/api/destinations")
    dest_id = list_res.json()[0]["id"]

    response = client.get(f"/api/destinations/{dest_id}")
    assert response.status_code == 200
    assert response.json()["id"] == dest_id

def test_get_destination_by_id_not_found():
    response = client.get("/api/destinations/nonexistentid12345")
    assert response.status_code == 404

def test_trip_search_valid():
    payload = {
        "origin": "Mumbai",
        "destination": "Goa",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "travelers": 2,
        "interests": ["Beaches", "Nightlife"],
        "budget_inr": 45000.0
    }
    response = client.post("/api/trip/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_trip_search_invalid_dates():
    payload = {
        "origin": "Mumbai",
        "destination": "Goa",
        "start_date": "2026-11-05",
        "end_date": "2026-11-01",
        "travelers": 2,
        "interests": ["Beaches"],
        "budget_inr": 45000.0
    }
    response = client.post("/api/trip/search", json=payload)
    assert response.status_code == 422

def test_coverage_report_exists():
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "coverage_report.json")
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert report["total_processed_records"] > 0
    assert "state_breakdown" in report
