import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import asyncio
import aiohttp
from datetime import datetime

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

# Optional: Self-ping to keep API warm (not needed for Supabase, but included)
async def self_ping():
    """Ping our own API every 10 minutes to keep it warm"""
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://loofinder-api.onrender.com/', timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ Self-ping successful: {datetime.now()}")
        except Exception as e:
            print(f"❌ Self-ping failed: {e}")
        
        await asyncio.sleep(600)  # 10 minutes

# Define the Data Model for a Review (Now using the unique OSM ID)
class Review(BaseModel):
    facility_id: str
    rating: int
    review_text: str

# --- API Endpoints ---

# 1. Keep-Alive Ping (Stops Render from going to sleep)
@app.get("/")
async def keep_alive():
    return {"status": "LooFinder is awake and ready!"}

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

# Optional: Start self-ping on startup (uncomment if needed)
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping())