# Data Sources & Ingestion Documentation — IndiaTravelAgent

## 1. Current Development Data (Manually Curated Fixture)
- **Current Data Source:** `data/raw/attractions_sample.json` is a **manually curated development and testing fixture** created specifically for local development and offline testing.
- **License / Provenance:** Public Domain / Development Fixture (not downloaded from OpenStreetMap).
- **Purpose:** Enables deterministic unit testing and frontend development without requiring external network calls or large datasets.

## 2. Planned Real-World Data Source (OpenStreetMap)
- **Future Source:** OpenStreetMap (OSM) via Overpass API / Geofabrik regional extracts.
- **License:** Open Database License (ODbL) v1.0.
- **Attribution Requirement:** "© OpenStreetMap contributors" (must be displayed where map or POI data is rendered).
- **Service Policy:** Automated scripts will use local extracts or cached files rather than repeatedly querying public Overpass demo servers.

## 3. Nationwide Coverage Strategy
`IndiaTravelAgent` is architected to support all **36 Indian states and union territories**. 
- In Phase 2, the localized development fixture provides initial test records.
- Production and expanded deployments will ingest regional GeoJSON/JSON extracts per state/UT into the processed data layer.
- **Dataset Coverage Report:** The ingestion pipeline automatically analyzes processed records and generates a coverage summary (`data/processed/coverage_report.json`) detailing state-wise breakdown, category distribution, and missing data indicators.

## 4. Data Schema & Validation Rules
Each attraction record is validated against strict constraints during ingestion:
- **`id`**: Unique internal stable hash/UUID.
- **`source` & `source_id`**: Origin provenance.
- **`name`**: Required non-empty string.
- **`category`**: Attraction classification (Monument, Heritage, Beach, Nature, Spiritual, Adventure, etc.).
- **`latitude` & `longitude`**: Must fall within India's strict geographic bounding box (Lat: `6.5°N` to `35.5°N`, Lon: `68.0°E` to `97.5°E`).
- **`state_ut` & `district_city`**: Standardized administrative region names.
- **`license`**: Explicitly logged license string.
- **`version_date`**: Retrieval date.

Records failing coordinate validation, lacking required fields, or identified as duplicate source IDs are filtered out and logged during ingestion.

## 5. Ingestion Pipeline Commands (Windows PowerShell)

To run the data ingestion script and generate processed outputs and coverage reports:

```powershell
python backend/ingest_destinations.py
```

This reads `data/raw/attractions_sample.json`, applies validation rules, cleans duplicates, generates internal IDs, and writes:
- `data/processed/destinations_processed.json`
- `data/processed/coverage_report.json`
