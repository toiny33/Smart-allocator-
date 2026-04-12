import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

try:
    from ai_module import get_urgency_score 
except ImportError:
    # Fallback if ai_module isn't finished
    def get_urgency_score(text): 
        high_priority = ["life", "severe", "trapped", "bleeding", "insulin", "baby"]
        if any(word in text.lower() for word in high_priority):
            return 10
        return 3

from models import OptimizationRequest
from optimize import AllocationOptimizer

app = FastAPI(title="ReliefLink API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/optimize")
async def optimize_endpoint(request: OptimizationRequest):
    try:
        resources_data = [res.dict() for res in request.resources]
        needs_data = [need.dict() for need in request.needs]

        for need in needs_data:
            # Enhanced urgency scoring
            need['urgency'] = get_urgency_score(need['description'])

        engine = AllocationOptimizer()
        result = engine.solve_matching(resources_data, needs_data)
        return result

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Optimization failed on backend.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)