import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="LooFinder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reviews.db")

# Connection pool for better performance
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=DATABASE_URL
    )
except:
    # Fallback for local development
    db_pool = None

def get_db_connection():
    """Get database connection from pool or create new one"""
    if db_pool:
        return db_pool.getconn()
    else:
        return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                facility_name TEXT,
                rating INTEGER,
                review_text TEXT
            )
        ''')
        conn.commit()
        cursor.close()
        if not db_pool:
            conn.close()
    except Exception as e:
        print(f"Database setup skipped or failed: {e}")

init_db()

class Review(BaseModel):
    facility_name: str
    rating: int
    review_text: str

@app.get("/")
async def keep_alive():
    return {"status": "Awake and ready!"}
    
@app.post("/api/reviews")
async def submit_review(review: Review):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (facility_name, rating, review_text) VALUES (%s, %s, %s)",
            (review.facility_name, review.rating, review.review_text)
        )
        conn.commit()
        
        return {"status": "success", "message": f"Saved {review.rating}-star review for {review.facility_name}"}
    finally:
        # Always return connection to pool
        if db_pool:
            db_pool.putconn(conn)
        else:
            conn.close()

@app.get("/api/reviews/{facility_name}")
async def get_reviews(facility_name: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT rating, review_text FROM reviews WHERE facility_name = %s", (facility_name,))
        rows = cursor.fetchall()
        
        return {"facility_name": facility_name, "reviews": rows}
    finally:
        # Always return connection to pool
        if db_pool:
            db_pool.putconn(conn)
        else:
            conn.close()