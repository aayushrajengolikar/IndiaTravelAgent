# IndiaTravelAgent

An India-only AI travel agent platform inspired by MakeMyTrip, providing comprehensive nationwide coverage across all Indian states and union territories. Users can specify origin, destination, journey start/end dates, number of travelers, interests, and budget in INR to generate custom, practical day-by-day itineraries.

---

## Tech Stack (Phase 2)
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Backend**: Python FastAPI, Pydantic
- **Data & Ingestion**: OpenStreetMap (OSM) via ODbL v1.0, Python validation pipeline
- **Testing**: Pytest (Backend), Next.js build verification (Frontend)

---

## Prerequisites
- Python 3.10+
- Node.js 18+ & npm

---

## Getting Started & Ingestion (Windows PowerShell)

Follow these exact steps in **Windows PowerShell** to set up the data foundation, run ingestion, test the backend, and start both services.

### 1. Backend Setup & Data Ingestion
Open a PowerShell terminal and run:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ingest_destinations.py
```

This runs the repeatable data ingestion pipeline, validates records against India's geographic bounding box, removes duplicates, generates stable IDs, and writes processed records (`data/processed/destinations_processed.json`) and a coverage report (`data/processed/coverage_report.json`).

### 2. Run Backend Tests
```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest
```

### 3. Run Backend Server
```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```
The FastAPI server will start at `http://localhost:8000`. API docs are available at `http://localhost:8000/docs`.

### 4. Run Frontend Service
Open a separate PowerShell terminal and run:

```powershell
cd frontend
npm install
npm run dev
```
The Next.js development server will start at `http://localhost:3000`.

---

## Project Structure
- `backend/` — Python FastAPI application, ingestion pipeline (`ingest_destinations.py`), and test suite (`test_main.py`).
- `frontend/` — Next.js TypeScript application with Tailwind CSS and interactive destination autocomplete search.
- `data/` — Raw sample datasets (`data/raw/`) and processed datasets/coverage reports (`data/processed/`).
- `docs/` — Data sources, licensing, and provenance documentation (`docs/data_sources.md`).
- `blueprint.md` — Approved architectural blueprint.
- `memory/` — Project persistent memory records.
