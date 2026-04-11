import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import Need, Resource, OptimizationRequest, OptimizationResponse, Allocation
from optimize import AllocationOptimizer
#from ai_module import assign_urgency

# 1. SECURITY & CONFIGURATION
# Load secret keys from your local .env file (invisible to GitHub)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
MAPS_API_KEY = os.getenv("MAPS_API_KEY")

# Initialize the FastAPI app
app = FastAPI(title="AI-Powered NGO Resource Allocation System")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "status": "Online",
        "mission": "Optimal resource allocation for NGOs",
        "version": "1.0"
    }

# 2. THE CORE API ENDPOINT
@app.post("/optimize")
def optimize_allocation(request: OptimizationRequest):
    """
    Main optimization endpoint:
    1. Receive resources + needs
    2. Call AI module → assign urgency to each need
    3. Call optimizer → compute optimal allocation
    4. Return allocation plan with impact summary
    """
    try:
        needs = request.needs
        resources = request.resources

        if not needs or not resources:
            raise HTTPException(status_code=400, detail="Incomplete field data: needs and resources required")

        # Step 1: Call AI module to assign urgency to each need
        print(f"[LOG] Processing {len(needs)} needs for urgency assignment...")
        for need in needs:
            urgency = assign_urgency(need.description, GEMINI_API_KEY)
            need.urgency = urgency
            print(f"[LOG] Need '{need.name}': urgency = {urgency}")

        # Step 2: Call optimizer to compute allocation
        print(f"[LOG] Running optimization engine with {len(resources)} resources...")
        engine = AllocationOptimizer(api_key=MAPS_API_KEY)
        allocation_list = engine.solve_matching(resources, needs)

        # Step 3: Format response
        allocations = [
            Allocation(to=alloc["to"], quantity=alloc["quantity"]) 
            for alloc in allocation_list
        ]
        
        response = OptimizationResponse(allocations=allocations)

        print(f"[LOG] Optimization complete. Generated {len(allocations)} allocations.")

        return {
            "success": True,
            "impact_summary": f"Optimally allocated resources to {len(allocations)} areas based on urgency and distance",
            "data": response.dict()
        }

    except HTTPException as e:
        print(f"[ERROR] HTTP Exception: {e.detail}")
        return {"success": False, "error": e.detail}
    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        return {"success": False, "error": str(e)}

# 3. Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api_keys_configured": bool(GEMINI_API_KEY and MAPS_API_KEY)
    }

# 4. TECHNICAL WORKFLOW
# Run via: uvicorn main:app --reload