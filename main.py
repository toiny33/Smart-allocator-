import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv  # For managing your API Keys securely
from datamodel import CommunityNeed, Volunteer
from optimizer import AllocationOptimizer

# 1. SECURITY & CONFIGURATION
# Load secret keys from your local .env file (invisible to GitHub)
load_dotenv()
GOOGLE_AI_KEY = os.getenv("GEMINI_API_KEY") 
MAPS_API_KEY = os.getenv("MAPS_API_KEY")

# Initialize the FastAPI app - this is the "Intermediary" 
app = FastAPI(title="Smart Resource Allocator - Solution Challenge 2026")

@app.get("/")
def home():
    return {"status": "Online", "mission": "Solving real-world glitches with AI"}

# 2. THE CORE API ENDPOINT (Your main responsibility)
@app.post("/allocate")
def run_allocation(raw_data: dict):
    """
    Acts as the Manager: 
    1. Collects scattered data.
    2. Uses Datamodels to structure it.
    3. Calls Optimizer to solve.
    """
    try:
        # A. Organize Data using Datamodels
        # Turning messy JSON into structured Python objects
        needs = [CommunityNeed(**n) for n in raw_data.get("needs", [])]
        volunteers = [Volunteer(**v) for v in raw_data.get("volunteers", [])]

        if not needs or not volunteers:
            raise HTTPException(status_code=400, detail="Incomplete field data")

        # B. Delegate to Optimizer (The Specialist)
        # We pass the API keys so the optimizer can use Google Maps/Gemini
        engine = AllocationOptimizer(api_key=MAPS_API_KEY)
        results = engine.solve_matching(needs, volunteers)

        # C. Return Result to the Social Toolkit/UI
        return {
            "success": True,
            "impact_summary": f"Matched {len(results)} urgent community needs.",
            "assignments": results
        }

    except Exception as e:
        # Technical error handling for the backend
        return {"success": False, "error": str(e)}

# 3. TECHNICAL WORKFLOW (Run via: uvicorn main:app --reload)