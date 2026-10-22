# IndiaTravelAgent — Implementation Blueprint

**Project Name:** IndiaTravelAgent  
**Inspiration:** MakeMyTrip (Tailored specifically for Indian domestic and inbound travel intelligence)  
**Status:** Blueprint Phase (Awaiting Approval)  
---

## 1. Executive Summary & Student Team Feasibility

`IndiaTravelAgent` is an AI-driven, intelligent travel planning platform designed exclusively for India. It combines robust spatial data management (PostGIS), LLM agent orchestration (LangGraph), machine learning recommendation models (CatBoost/scikit-learn), and a modern web interface (Next.js & Tailwind CSS) to generate practical, optimized day-by-day itineraries.

To ensure feasibility for a student team within a standard academic/project timeline, the project adopts a **phased MVP strategy**:
- **Phase 1 (MVP Scope):** Focus on top tourist circuits across 10 major Indian states/UTs (e.g., Rajasthan, Kerala, Goa, Himachal Pradesh, Uttarakhand, Karnataka, Tamil Nadu, Maharashtra, Uttar Pradesh, Delhi) rather than all 700+ districts instantly.
- **Incremental Expansion:** Build reusable data ingestion pipelines and modular agent workflows that scale nationwide as data sources are verified.

---

## 2. Proposed Folder Structure

A monorepo structure separating frontend, backend, database migrations, data pipelines, and machine learning modules:

```text
IndiaTravelAgent/
├── frontend/                 # Next.js 14+ (App Router), TypeScript, Tailwind CSS
│   ├── src/
│   │   ├── app/              # Pages (Home, Itinerary Builder, Trip View, Profile)
│   │   ├── components/       # Reusable UI components (Map, Timeline, Cards)
│   │   ├── lib/              # API clients & utility functions
│   │   └── types/            # TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.ts
├── backend/                  # Python FastAPI application
│   ├── app/
│   │   ├── api/              # API routers (trips, users, destinations, weather)
│   │   ├── core/             # Config, security, database sessions
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Business logic (Routing, Weather, LLM orchestration)
│   │   └── agents/           # LangGraph state machine & prompt definitions
│   ├── requirements.txt
│   └── main.py
├── database/                 # Database migrations & seed scripts
│   ├── alembic/              # Alembic migration scripts
│   ├── init_postgis.sql      # Initial spatial extensions
│   └── seeds/                # Initial seed data (states, categories)
├── ml/                       # Machine learning modules
│   ├── data_prep/            # Pandas scripts for data cleaning
│   ├── models/               # CatBoost / collaborative filtering training code
│   ├── evaluation/           # Evaluation metric scripts (NDCG, RMSE)
│   └── notebooks/            # Exploratory Jupyter notebooks
├── data/                     # Raw & processed datasets (git-ignored large files)
│   ├── raw/
│   └── processed/
├── tests/                    # Automated test suite (pytest & Jest)
│   ├── backend/
│   └── frontend/
├── docs/                     # Architecture diagrams & API documentation
├── docker-compose.yml        # Local development environment (Postgres/PostGIS + FastAPI + Next.js)
├── CLAUDE.md                 # Development guidelines and commands
└── README.md
```

---

## 3. System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       Next.js Frontend                      │
│                (User Input: Origin, Dates, Budget, Interests)│
└──────────────┬──────────────────────────────┬───────────────┘
               │ HTTP / REST                  │ WebSockets / Streaming
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend API                     │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌────────────────────────────┐    ┌───────────────────────────┐
│     LangGraph Agent        │    │    PostgreSQL + PostGIS   │
│   (Orchestrator & LLM)     │◄──►│  (Attractions, Hotels,    │
│                            │    │   Spatial Indexing, Trips)│
└──────────────┬─────────────┘    └───────────────────────────┘
               │
               ├───► Open-Meteo API (Live Weather & Forecasts)
               ├───► OSRM / Nominatim (Routing & Geocoding)
               └───► CatBoost / Scikit-Learn (Personalized Scoring)
```

### Data Flow for Trip Generation:
1. **User Request:** User submits trip parameters via Next.js frontend.
2. **API Receipt:** FastAPI receives the request and initializes a `LangGraph` workflow state.
3. **Retrieval & Spatial Query:** The agent queries PostgreSQL/PostGIS for attractions and accommodations within the destination bounding box matching user interests and budget tier.
4. **Enrichment:** Real-time weather is fetched via Open-Meteo API, and transit times/distances are calculated via OSRM.
5. **ML Ranking:** CatBoost recommendation model scores POIs based on user historical preferences and demographic affinity.
6. **Itinerary Optimization:** LangGraph agent sequences activities into a feasible day-by-day schedule respecting opening hours, transit feasibility, and meal breaks.
7. **Response Delivery:** The structured itinerary is returned to the frontend for interactive visualization (timeline & map).

---

## 4. Database Schema (PostgreSQL + PostGIS)

Key tables and spatial entities:

- **`users`**: User profiles, preferences, authentication metadata.
- **`destinations`**: States, cities, regions with PostGIS `GEOMETRY(Polygon, 4326)` boundaries.
- **`attractions`**: POIs (monuments, museums, nature spots, restaurants) with `GEOMETRY(Point, 4326)`, category, opening hours, average duration, price tier, and tags.
- **`accommodations`**: Hotels, hostels, resorts with spatial points, pricing, amenities, and ratings.
- **`transport_routes`**: Major transit links (train/bus/flight routes between key hubs) with estimated durations and costs.
- **`trips`**: Saved user trips, origin, destination, start/end dates, traveller count, budget.
- **`itinerary_days`**: Day-by-day breakdown for a trip.
- **`itinerary_items`**: Ordered list of activities/stops per day with timing and transit notes.
- **`dataset_metadata`**: Traceability table storing source name, license, coverage region, last updated timestamp, and verification status.

---

## 5. Dataset Requirements & Acquisition Strategy

To maintain high fidelity and traceability, all datasets adhere to strict metadata logging:

1. **Geospatial & POI Data:**
   - *Source:* OpenStreetMap (via Overpass API / Geofabrik extracts) & GeoNames.
   - *License:* ODbL / Creative Commons.
   - *Coverage:* Nationwide (prioritizing top 10 circuits in MVP).
   - *Metadata:* Tracked in `dataset_metadata`.
2. **Administrative Boundaries:**
   - *Source:* Survey of India / GitHub open boundaries repository / Natural Earth.
   - *Coverage:* State and District boundaries across India.
3. **Tourism & Monument Metadata:**
   - *Source:* Ministry of Tourism (Incredible India open data portals) / curated Wikipedia dumps.
   - *Attributes:* Opening hours, ticket pricing, entry rules.
4. **Transport & Connectivity:**
   - *Source:* OSRM routing engine matrices + Indian Railways station master lists / GTFS feeds where available.

---

## 6. Machine Learning Tasks & Evaluation Metrics

1. **Personalized POI Recommendation Model:**
   - *Task:* Ranking potential attractions based on user interest vector, budget tier, travel style (solo, family, adventure, luxury), and seasonal appropriateness.
   - *Model:* CatBoost Classifier / Gradient Boosted Decision Trees trained on synthetic/historical preference interaction logs.
   - *Evaluation Metrics:* **NDCG@k** (Normalized Discounted Cumulative Gain), Precision@k, Recall@k.
2. **Itinerary Feasibility & Travel Time Estimation:**
   - *Task:* Estimating intra-city travel times during peak traffic vs. off-peak hours in major Indian cities.
   - *Model:* Gradient Boosting Regression / heuristic adjustment models.
   - *Evaluation Metrics:* **RMSE** (Root Mean Squared Error) and **MAE** against benchmark routing times.

---

## 7. API Integration Requirements

- **LLM Provider API:** Anthropic Claude / OpenAI API for LangGraph reasoning and itinerary narrative generation.
- **Open-Meteo API:** Free tier for historical and forecasted weather data for Indian cities (lat/lon lookup).
- **OpenStreetMap Nominatim & OSRM:** Self-hosted or public API endpoints for geocoding addresses and calculating route distance/duration matrix.

---

## 8. Development Phases & Testable Acceptance Criteria

| Phase | Milestone | Testable Acceptance Criteria |
| :--- | :--- | :--- |
| **Phase 1** | Foundation & DB Setup | PostgreSQL + PostGIS container runs successfully; Alembic migrations execute cleanly; base tables created with spatial indexes. |
| **Phase 2** | Data Ingestion & External APIs | Python ingestion scripts successfully load sample POIs and boundary geometries into PostGIS; Open-Meteo and routing APIs return valid responses. |
| **Phase 3** | Backend & Agent Orchestration | FastAPI endpoints accept trip parameters; LangGraph agent successfully coordinates retrieval, weather check, and generates a structured JSON itinerary. |
| **Phase 4** | Frontend Development | Next.js app renders responsive home page, trip input form, and interactive day-by-day itinerary view with map integration. |
| **Phase 5** | ML Integration & Scoring | CatBoost recommendation model scores and ranks POIs; evaluation script validates NDCG@k > threshold on test split. |
| **Phase 6** | End-to-End Testing & Polish | Automated pytest & Jest test suites pass successfully; security audit verifies API key handling; documentation complete. |

---

## 9. Estimated Development Complexity & Major Risks

- **Complexity:** Medium-High (due to multi-service orchestration across PostGIS, LangGraph agents, external APIs, and spatial routing).
- **Major Risks & Mitigation:**
  1. *Risk:* LLM hallucination in opening hours or travel sequences.  
     *Mitigation:* Strict Pydantic output validation schemas and deterministic rule-based post-filtering for operational hours.
  2. *Risk:* Incomplete regional POI data in remote areas.  
     *Mitigation:* Bounded MVP focusing on top tourist circuits with fallback default recommendations.
  3. *Risk:* API rate limits on free public routing and weather services.  
     *Mitigation:* Local caching of static POI and weather forecasts using Redis or PostgreSQL caching tables.

---

## 10. Data Sources Requiring Verification

The following sources require active verification during Phase 2 implementation:
- Real-time or schedule accuracy for Indian regional buses (State Road Transport Corporations like KSRTC, MSRTC, RSRTC). *Mitigation:* Focus MVP on private/general transit estimates and OSRM driving/transit matrix.
- Official precise holiday closure calendars for state-run museums and monuments. *Mitigation:* Include standard closure flags (e.g., Mondays for specific central museums) with user disclaimers.

---
*Awaiting user review and approval before proceeding to implementation.*
