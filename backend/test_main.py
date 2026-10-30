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
    response = client.get("/api/destinations?query=Fort")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Fort" in data[0]["name"] or "Fort" in data[0]["description"]

def test_get_destinations_with_state_filter():
    response = client.get("/api/destinations?state=Goa")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["state_ut"] == "Goa"

def test_get_destinations_with_category_filter():
    response = client.get("/api/destinations?category=Heritage")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Heritage" in data[0]["category"]

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

def test_recommendations_successful_post():
    payload = {
        "destination": "Jaipur",
        "interests": ["Heritage & History"],
        "limit": 3
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Jaipur"
    assert "recommendations" in data
    recs = data["recommendations"]
    assert isinstance(recs, list)
    if len(recs) > 0:
        rec = recs[0]
        assert "attraction" in rec
        assert "relevance_score" in rec
        assert "reason" in rec
        assert 0.0 <= rec["relevance_score"] <= 1.0
        assert len(rec["reason"]) > 0

def test_recommendations_successful_get():
    response = client.get("/api/recommendations?destination=Goa&interests=Beaches&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Goa"
    assert len(data["recommendations"]) <= 2

def test_recommendations_empty_interests():
    payload = {
        "destination": "Agra",
        "interests": [],
        "limit": 2
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) >= 0

def test_recommendations_unknown_interests():
    payload = {
        "destination": "Delhi",
        "interests": ["Quantum Physics", "Underwater Basket Weaving"],
        "limit": 3
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data

def test_recommendations_no_matches():
    payload = {
        "destination": "NonExistentCityXYZ123",
        "interests": ["Beaches"],
        "limit": 3
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_recommendations"] == 0

def test_recommendations_invalid_limit():
    payload = {
        "destination": "Jaipur",
        "limit": 999  # Exceeds max 50
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 422

def test_recommendations_origin_exclusion():
    payload = {
        "destination": "Jaipur",
        "origin": "Amer Fort",
        "interests": ["History"],
        "limit": 5
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    for rec in data["recommendations"]:
        assert "Amer Fort" not in rec["attraction"]["name"]

def test_recommender_module_directly():
    from recommender import recommend_attractions
    recs = recommend_attractions(destination="Kerala", interests=["Nature"], limit=2)
    assert isinstance(recs, list)
    if len(recs) > 0:
        assert 0.0 <= recs[0]["relevance_score"] <= 1.0