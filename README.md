# IndiaTravelAgent

`IndiaTravelAgent` is an India-only AI travel agent platform inspired by MakeMyTrip, offering coverage across Indian states and union territories. It generates practical, detailed day-by-day travel guides based on origin, destination, dates, traveler count, interests, and budget in INR.

---

## Architecture & Tech Stack
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS.
- **Backend**: Python FastAPI.
- **Data Ingestion Pipeline**: Robust validator supporting OpenStreetMap (OSM) sourced extracts (ODbL v1.0) and offline development fixtures with full provenance tracking.
- **Recommendation Engine**: Content-based recommendation module utilizing `scikit-learn` TF-IDF vectorization and cosine similarity combined with destination and user interest matching.

---

## Data Pipeline & Provenance (Task 004)
The backend ingestion pipeline (`backend/ingest_destinations.py`) supports:
- **Sourced OpenStreetMap Data** (ODbL v1.0 © OpenStreetMap contributors) or curated development fixtures.
- Strict geographic bounding box validation for India (`Lat: 6.5°N–35.5°N`, `Lon: 68.0°E–97.5°E`).
- Provenance traceability (`source`, `source_id`, `source_url`, `license`, `version_date`).
- Duplicate detection, rejection logging, stable SHA-256 ID generation, and automatic coverage reporting (`data/processed/coverage_report.json`).

---

## Attraction Recommendation Engine (Task 003 & 004)
The recommendation engine (`backend/recommender.py`) accepts a destination context, user interests, origin (for exclusion), and limit, returning ranked tourist attractions with relevance scores (0.0 to 1.0) and understandable reasoning.

### API Endpoints
- `GET /health` — Service health check.
- `GET /api/destinations` — Search and filter destinations.
- `GET /api/destinations/{id}` — Destination detail by ID.
- `POST /api/trip/search` — Validate trip parameters.
- `POST /api/recommendations` / `GET /api/recommendations` — Content-based attraction recommendations.

---

## Windows PowerShell Run & Test Commands

### Backend Setup & Run
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Backend Tests (pytest)
```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest
```

### Ingestion Script Run
```powershell
cd backend
.venv\Scripts\Activate.ps1
python ingest_destinations.py
```

### Frontend Setup & Production Build
```powershell
cd frontend
npm install
npm run build
npm run dev
```
