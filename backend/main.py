from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional
import json
import os

app = FastAPI(
    title="IndiaTravelAgent API",
    description="Backend API for IndiaTravelAgent - AI Travel Planner for India",
    version="0.2.0"
)

# Configure CORS for local frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load processed destinations dataset
PROCESSED_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "destinations_processed.json")

def load_destinations() -> List[dict]:
    if os.path.exists(PROCESSED_DATA_PATH):
        try:
            with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

class HealthResponse(BaseModel):
    status: str
    service: str

class DestinationResponse(BaseModel):
    id: str
    source: str
    source_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    state_ut: str
    district_city: str
    description: str
    license: str
    version_date: str

class TripSearchRequest(BaseModel):
    origin: str = Field(..., min_length=2, description="Origin city or state in India")
    destination: str = Field(..., min_length=2, description="Destination city or state in India")
    start_date: date = Field(..., description="Journey start date")
    end_date: date = Field(..., description="Journey end date")
    travelers: int = Field(..., gt=0, description="Number of travelers")
    interests: List[str] = Field(default=[], description="List of user interests")
    budget_inr: float = Field(..., gt=0, description="Budget in Indian Rupees (INR)")

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, end_date: date, info) -> date:
        values = info.data
        if 'start_date' in values and end_date < values['start_date']:
            raise ValueError('End date must be greater than or equal to start date')
        return end_date

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "healthy", "service": "indiatravelagent-backend"}

@app.get("/api/destinations", response_model=List[DestinationResponse])
def get_destinations(
    query: Optional[str] = Query(None, description="Search term for name, description, or city"),
    state: Optional[str] = Query(None, description="Filter by state or union territory"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    destinations = load_destinations()
    filtered = destinations

    if query:
        q = query.lower()
        filtered = [
            d for d in filtered
            if q in d["name"].lower() or q in d["district_city"].lower() or q in d["description"].lower()
        ]

    if state:
        s = state.lower()
        filtered = [d for d in filtered if s in d["state_ut"].lower()]

    if category:
        c = category.lower()
        filtered = [d for d in filtered if c in d["category"].lower()]

    paginated = filtered[offset : offset + limit]
    return paginated

@app.get("/api/destinations/{destination_id}", response_model=DestinationResponse)
def get_destination_by_id(destination_id: str):
    destinations = load_destinations()
    for d in destinations:
        if d["id"] == destination_id:
            return d
    raise HTTPException(status_code=404, detail="Destination not found")

@app.post("/api/trip/search")
def search_trip(request: TripSearchRequest):
    return {
        "message": "Trip parameters validated successfully",
        "search_parameters": request.model_dump(mode='json')
    }
