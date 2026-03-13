import os
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

# 1. Keep-Alive Ping (Stops Render AND Supabase from going to sleep)
@app.get("/")
async def keep_alive():
    try:
        # Quickly tap the database to reset the 7-day sleep timer
        supabase.table("reviews").select("facility_id").limit(1).execute()
        return {"status": "LooFinder API and Database are both awake!"}
    except Exception as e:
        return {"status": f"API is awake, but DB tap failed: {str(e)}"}

# 2. Submit a new review
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