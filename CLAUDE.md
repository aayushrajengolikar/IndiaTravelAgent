# CLAUDE.md — IndiaTravelAgent

## Project Goals
`IndiaTravelAgent` is an India-only AI travel agent platform inspired by MakeMyTrip, offering nationwide coverage across all Indian states and union territories. It generates practical, detailed day-by-day travel guides based on origin, destination, dates, traveler count, interests, and budget in INR.

## Architecture Boundaries (Phase 1)
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS.
- **Backend**: Python FastAPI.
- **Deferred in Phase 1**: PostgreSQL/PostGIS, Docker, LangGraph, ML model training, and external travel APIs (OSRM, Open-Meteo, etc.) are deferred to subsequent phases as per project instructions.
- **Modularity**: Frontend and backend are strictly separated.

## Coding Conventions
- Write clean, readable code with descriptive comments matching surrounding code.
- Validate inputs rigorously (required fields, positive numbers, date order).
- Handle errors gracefully with clear user feedback on the frontend and descriptive HTTP status codes on the backend.

## Windows PowerShell Run Commands
- **Backend Setup & Run**:
  ```powershell
  cd backend
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000
  ```
- **Backend Tests**:
  ```powershell
  cd backend
  .venv\Scripts\Activate.ps1
  pytest
  ```
- **Frontend Setup & Run**:
  ```powershell
  cd frontend
  npm install
  npm run dev
  ```
