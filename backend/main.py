from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional
import json
import os
from recommender import recommend_attractions

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
    source_url: Optional[str] = "https://www.openstreetmap.org"
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

class RecommendationRequest(BaseModel):
    destination: str = Field(..., min_length=2, description="Target destination city, state, or region")
    interests: List[str] = Field(default=[], description="List of user interests")
    origin: Optional[str] = Field(None, description="Optional origin location to exclude")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of recommendations (1-50)")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold (0.0-1.0)")

class RecommendedAttractionItem(BaseModel):
    attraction: DestinationResponse
    relevance_score: float = Field(..., description="Content and interest relevance score (0.0 to 1.0)")
    reason: str = Field(..., description="Understandable reason for the recommendation")

class RecommendationListResponse(BaseModel):
    destination: str
    total_recommendations: int
    recommendations: List[RecommendedAttractionItem]

@app.post("/api/recommendations", response_model=RecommendationListResponse)
def get_recommendations(request: RecommendationRequest):
    try:
        recs = recommend_attractions(
            destination=request.destination,
            interests=request.interests,
            origin=request.origin,
            limit=request.limit,
            min_score=request.min_score
        )
        return {
            "destination": request.destination,
            "total_recommendations": len(recs),
            "recommendations": recs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")

@app.get("/api/recommendations", response_model=RecommendationListResponse)
def get_recommendations_get(
    destination: str = Query(..., min_length=2, description="Target destination city, state, or region"),
    interests: Optional[str] = Query(None, description="Comma-separated list of user interests"),
    origin: Optional[str] = Query(None, description="Optional origin location to exclude"),
    limit: int = Query(5, ge=1, le=50, description="Maximum number of recommendations"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold")
):
    interest_list = [i.strip() for i in interests.split(",")] if interests else []
    try:
        recs = recommend_attractions(
            destination=destination,
            interests=interest_list,
            origin=origin,
            limit=limit,
            min_score=min_score
        )
        return {
            "destination": destination,
            "total_recommendations": len(recs),
            "recommendations": recs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")

@app.get("/api/dataset-status")
def get_dataset_status():
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "coverage_report.json")
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "dataset_mode": "Manually Curated Development Fixture",
        "source_file": "attractions_sample.json",
        "total_processed_records": len(load_destinations()),
        "license": "Public Domain / Development Fixture"
    }
