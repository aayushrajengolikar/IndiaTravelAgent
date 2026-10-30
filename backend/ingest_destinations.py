import json
import os
import hashlib
from typing import Dict, Any, List, Optional, Tuple

RAW_SOURCED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "osm_attractions_raw.json")
RAW_FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "attractions_sample.json")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
PROCESSED_DATA_PATH = os.path.join(PROCESSED_DIR, "destinations_processed.json")
COVERAGE_REPORT_PATH = os.path.join(PROCESSED_DIR, "coverage_report.json")

# India Geographic Bounding Box
INDIA_LAT_MIN = 6.5
INDIA_LAT_MAX = 35.5
INDIA_LON_MIN = 68.0
INDIA_LON_MAX = 97.5

def validate_and_process_record(record: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    required = ["source", "source_id", "name", "category", "latitude", "longitude", "state_ut", "district_city", "license", "version_date"]
    for field in required:
        if field not in record or record[field] is None:
            return None, f"Missing required field: {field}"

    name = str(record["name"]).strip()
    if not name:
        return None, "Empty attraction name"

    category = str(record["category"]).strip()
    if not category:
        return None, "Empty category"

    try:
        lat = float(record["latitude"])
        lon = float(record["longitude"])
    except (ValueError, TypeError):
        return None, f"Invalid coordinate types: lat={record.get('latitude')}, lon={record.get('longitude')}"

    if not (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX and INDIA_LON_MIN <= lon <= INDIA_LON_MAX):
        return None, f"Coordinates out of India bounding box: lat={lat}, lon={lon}"

    source = str(record["source"])
    source_id = str(record["source_id"])
    raw_id_string = f"{source}:{source_id}"
    internal_id = hashlib.sha256(raw_id_string.encode("utf-8")).hexdigest()[:16]

    processed_record = {
        "id": internal_id,
        "source": source,
        "source_id": source_id,
        "source_url": str(record.get("source_url", "https://www.openstreetmap.org")),
        "name": name,
        "category": category,
        "latitude": lat,
        "longitude": lon,
        "state_ut": str(record["state_ut"]),
        "district_city": str(record["district_city"]),
        "description": str(record.get("description", "")),
        "license": str(record["license"]),
        "version_date": str(record["version_date"])
    }

    return processed_record, None

def run_ingestion(raw_path: Optional[str] = None) -> Dict[str, Any]:
    if not raw_path:
        if os.path.exists(RAW_SOURCED_PATH):
            raw_path = RAW_SOURCED_PATH
            dataset_mode = "Sourced OpenStreetMap Dataset"
        else:
            raw_path = RAW_FIXTURE_PATH
            dataset_mode = "Manually Curated Development Fixture (Fallback)"
    else:
        dataset_mode = "Custom Sourced Dataset"

    print(f"Reading raw data from {raw_path} (Mode: {dataset_mode})...")
    if not os.path.exists(raw_path):
        print(f"Error: Raw data file not found at {raw_path}")
        return {"error": "Raw data file not found"}

    try:
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_records = json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {raw_path}: {e}")
        return {"error": str(e)}

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    processed_records: List[Dict[str, Any]] = []
    seen_source_ids = set()
    rejected_records = []

    for idx, record in enumerate(raw_records):
        if not isinstance(record, dict):
            rejected_records.append({"index": idx, "record": str(record), "reason": "Record is not a dictionary object"})
            continue

        processed, error_msg = validate_and_process_record(record)
        if error_msg:
            rejected_records.append({"index": idx, "record": record, "reason": error_msg})
            continue

        source_key = f"{processed['source']}:{processed['source_id']}"
        if source_key in seen_source_ids:
            rejected_records.append({"index": idx, "record": record, "reason": f"Duplicate source identifier: {source_key}"})
            continue

        seen_source_ids.add(source_key)
        processed_records.append(processed)

    # Atomic write for processed data
    temp_processed_path = PROCESSED_DATA_PATH + ".tmp"
    with open(temp_processed_path, "w", encoding="utf-8") as f:
        json.dump(processed_records, f, indent=2, ensure_ascii=False)
    os.replace(temp_processed_path, PROCESSED_DATA_PATH)

    # Generate coverage report
    state_breakdown = {}
    category_breakdown = {}
    for rec in processed_records:
        st = rec["state_ut"]
        cat = rec["category"]
        state_breakdown[st] = state_breakdown.get(st, 0) + 1
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    coverage_report = {
        "dataset_mode": dataset_mode,
        "source_file": os.path.basename(raw_path),
        "total_raw_records": len(raw_records),
        "total_processed_records": len(processed_records),
        "total_rejected_records": len(rejected_records),
        "states_covered_count": len(state_breakdown),
        "state_breakdown": state_breakdown,
        "category_breakdown": category_breakdown,
        "rejection_log": rejected_records,
        "license": "Open Database License (ODbL) v1.0 © OpenStreetMap contributors" if "OpenStreetMap" in dataset_mode else "Public Domain / Development Fixture",
        "dataset_status": f"Successfully ingested {len(processed_records)} records from {dataset_mode}"
    }

    temp_report_path = COVERAGE_REPORT_PATH + ".tmp"
    with open(temp_report_path, "w", encoding="utf-8") as f:
        json.dump(coverage_report, f, indent=2, ensure_ascii=False)
    os.replace(temp_report_path, COVERAGE_REPORT_PATH)

    print(f"\nIngestion Complete!")
    print(f"Mode: {dataset_mode}")
    print(f"Processed: {len(processed_records)} valid records.")
    print(f"Rejected: {len(rejected_records)} invalid/duplicate records.")
    print(f"Saved processed data to: {PROCESSED_DATA_PATH}")
    print(f"Saved coverage report to: {COVERAGE_REPORT_PATH}")

    return coverage_report

if __name__ == "__main__":
    run_ingestion()
