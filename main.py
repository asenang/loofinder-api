import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# Initialize FastAPI app
app = FastAPI()

# Configure CORS (Allows your GitHub Pages frontend to talk to this backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client using Environment Variables from Render
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define the Data Model for a Review (Using the unique OSM ID)
class Review(BaseModel):
    facility_id: str
    rating: int
    review_text: str

# --- API Endpoints ---

# 1. Enhanced Keep-Alive Ping (Stops Render AND Supabase from going to sleep)
@app.get("/")
async def keep_alive():
    try:
        # Quick Supabase database tap to reset the 7-day sleep timer
        supabase.table("reviews").select("facility_id").limit(1).execute()
        db_status = "✅ Supabase DB awake"
    except Exception as e:
        db_status = f"❌ Supabase DB tap failed: {str(e)}"
    
    return {
        "status": "LooFinder API is awake and ready!",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "API and database keep-alive active"
    }

# 2. Dedicated database health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check for monitoring services"""
    try:
        # Test Supabase connection
        db_test = supabase.table("reviews").select("facility_id").limit(1).execute()
        db_status = "healthy"
        db_count = len(db_test.data) if db_test.data else 0
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_count = 0
    
    return {
        "api": "healthy",
        "database": db_status,
        "sample_records": db_count,
        "timestamp": datetime.utcnow().isoformat()
    }

# 3. Submit a new review
@app.post("/api/reviews")
async def add_review(review: Review):
    try:
        data = supabase.table("reviews").insert({
            "facility_id": review.facility_id,
            "rating": review.rating,
            "review_text": review.review_text
        }).execute()
        return {"message": "Review added successfully", "data": data.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Fetch reviews for a specific facility
@app.get("/api/reviews/{facility_id}")
async def get_reviews(facility_id: str):
    try:
        response = supabase.table("reviews").select("*").eq("facility_id", facility_id).execute()
        return {"reviews": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))