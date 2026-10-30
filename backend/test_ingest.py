import os
import json
import tempfile
import pytest
from ingest_destinations import run_ingestion, validate_and_process_record

def test_validate_and_process_record_valid():
    record = {
        "source": "OpenStreetMap",
        "source_id": "node_12345",
        "source_url": "https://www.openstreetmap.org/node/12345",
        "name": "Test Monument",
        "category": "Monument",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "state_ut": "Delhi",
        "district_city": "New Delhi",
        "description": "A historic test monument.",
        "license": "ODbL 1.0",
        "version_date": "2026-10-23"
    }
    processed, error = validate_and_process_record(record)
    assert error is None
    assert processed is not None
    assert processed["name"] == "Test Monument"
    assert processed["id"] is not None
    assert processed["source"] == "OpenStreetMap"
    assert processed["source_url"] == "https://www.openstreetmap.org/node/12345"

def test_validate_and_process_record_invalid_coords():
    record = {
        "source": "OpenStreetMap",
        "source_id": "node_99999",
        "name": "Out of Bounds",
        "category": "Monument",
        "latitude": 51.5074,  # London latitude (out of India bounding box)
        "longitude": -0.1278,
        "state_ut": "Unknown",
        "district_city": "London",
        "license": "ODbL 1.0",
        "version_date": "2026-10-23"
    }
    processed, error = validate_and_process_record(record)
    assert processed is None
    assert "bounding box" in error

def test_validate_and_process_record_missing_field():
    record = {
        "source": "OpenStreetMap",
        # missing source_id and name
        "category": "Monument",
        "latitude": 28.6,
        "longitude": 77.2,
        "state_ut": "Delhi",
        "district_city": "Delhi",
        "license": "ODbL 1.0",
        "version_date": "2026-10-23"
    }
    processed, error = validate_and_process_record(record)
    assert processed is None
    assert "Missing required field" in error

def test_ingestion_with_temp_raw_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_file = os.path.join(tmpdir, "raw_test.json")
        test_data = [
            {
                "source": "TestOSM",
                "source_id": "1",
                "name": "Attraction A",
                "category": "Beach",
                "latitude": 15.2993,
                "longitude": 74.1240,
                "state_ut": "Goa",
                "district_city": "Panaji",
                "license": "ODbL",
                "version_date": "2026-10-23"
            },
            {
                "source": "TestOSM",
                "source_id": "1",  # Duplicate source_id
                "name": "Attraction A Duplicate",
                "category": "Beach",
                "latitude": 15.2993,
                "longitude": 74.1240,
                "state_ut": "Goa",
                "district_city": "Panaji",
                "license": "ODbL",
                "version_date": "2026-10-23"
            },
            {
                "source": "TestOSM",
                "source_id": "2",
                "name": "Invalid Lat",
                "category": "Beach",
                "latitude": 99.0,  # Invalid
                "longitude": 74.1240,
                "state_ut": "Goa",
                "district_city": "Panaji",
                "license": "ODbL",
                "version_date": "2026-10-23"
            },
            "malformed_non_dict_record"
        ]
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        report = run_ingestion(raw_path=raw_file)
        assert report["total_raw_records"] == 4
        assert report["total_processed_records"] == 1
        assert report["total_rejected_records"] == 3
        assert "Goa" in report["state_breakdown"]
        assert report["dataset_mode"] == "Custom Sourced Dataset"

def test_ingest_fixture_fallback_mode(monkeypatch):
    # Test fallback behavior when raw sourced file does not exist
    import ingest_destinations
    monkeypatch.setattr(ingest_destinations, "RAW_SOURCED_PATH", "nonexistent_sourced_file_123.json")
    report = ingest_destinations.run_ingestion()
    assert "Fallback" in report["dataset_mode"]
    assert report["total_processed_records"] > 0

def test_restore_default_ingestion():
    # Restore default sourced ingestion if available, or fixture
    run_ingestion()
