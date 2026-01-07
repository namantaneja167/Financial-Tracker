import sys
import os
from pathlib import Path

# Add project root to python path to allow imports from financial_tracker
# This allows running from within backend/ or root without issues
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from backend.api import endpoints

app = FastAPI(
    title="Financial Tracker Pro Max API",
    description="Backend API for Financial Tracker Pro Max",
    version="2.0.0"
)

# Configure CORS for local Next.js dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(endpoints.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
