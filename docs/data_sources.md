# Data Sources & Ingestion Documentation — IndiaTravelAgent

## 1. Data Sourcing Architecture & Strategy
`IndiaTravelAgent` supports two distinct data ingestion modes:
1. **Sourced OpenStreetMap Data (Primary Production Target)**: Extracted from OpenStreetMap (OSM) via Overpass API or Geofabrik regional extracts (`https://download.geofabrik.de/asia/india-latest.osm.pbf`).
2. **Manually Curated Development Fixture (Offline Fallback)**: `data/raw/attractions_sample.json` is maintained specifically for reliable local development, deterministic unit testing, and offline execution without requiring live network calls.

## 2. License & Attribution Requirements
- **License**: Open Database License (ODbL) v1.0.
- **Attribution Requirement**: *"© OpenStreetMap contributors"* must be visibly displayed where map tiles, point-of-interest data, or search results derived from OSM are rendered to users.
- **Development Fixture**: Public Domain / Offline Development Fixture.

## 3. Geographic Scope & Bounding Box
All ingested records are strictly validated against India's geographic bounding box:
- **Latitude**: `6.5°N` to `35.5°N`
- **Longitude**: `68.0°E` to `97.5°E`
Records falling outside this bounding box are automatically rejected and logged.

## 4. Provenance Fields
Every processed record retains complete provenance traceability:
- **`source`**: Origin data provider (e.g., `"OpenStreetMap (Geofabrik Extract / Overpass API)"` or `"Manually Curated Development Fixture"`).
- **`source_id`**: Unique source object ID (OSM node/way/relation ID or fixture ID).
- **`source_url`**: Direct reference URL (e.g., `"https://www.openstreetmap.org/node/{id}"`).
- **`license`**: Explicit license statement.
- **`version_date`**: Retrieval or extract date.

## 5. Ingestion Pipeline & PowerShell Commands

To run the data ingestion pipeline, validate records, remove duplicates, generate stable SHA-256 identifiers, and output coverage reports:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python ingest_destinations.py
```

### Input & Output Paths
- **Raw Input (Sourced)**: `data/raw/osm_attractions_raw.json`
- **Raw Input (Fallback Fixture)**: `data/raw/attractions_sample.json`
- **Processed Output**: `data/processed/destinations_processed.json`
- **Coverage Report**: `data/processed/coverage_report.json`

## 6. Coverage Report & Rejection Logging
The ingestion script automatically generates `data/processed/coverage_report.json`, detailing:
- Dataset mode (`Sourced OpenStreetMap Dataset` vs `Manually Curated Development Fixture`).
- Total raw, processed, and rejected record counts.
- State/UT and category breakdowns.
- Rejection log with specific failure reasons (invalid coordinates, missing required fields, duplicate source identifiers).

## 7. Known Limitations
- The system currently focuses on core tourist circuits across major Indian states and union territories rather than complete exhaustive coverage of all 700+ districts.
- Live network data ingestion requires placing valid OSM JSON extracts in `data/raw/osm_attractions_raw.json` or running Overpass API queries.
