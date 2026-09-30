import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database initialization safely
from app.database import Base, engine

# Create SQLite database tables
Base.metadata.create_all(bind=engine)

# Import routes
from app.routes import router

# Initialize FastAPI Application
app = FastAPI(
    title="FitBuddy - AI Fitness Plan Generator",
    description="A web-based application using Google Gemini AI to generate personalized 7-day workout plans and nutrition tips.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve and mount static directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
STATIC_DIR = os.path.join(PROJECT_DIR, "static")

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include Core Router
app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "ok", "service": "FitBuddy AI Fitness Generator"}
from fastapi.responses import Response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    svg_favicon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🏋️</text></svg>"""
    return Response(content=svg_favicon, media_type="image/svg+xml")