"""
ReliefLink AI Optimization Module
Allocates emergency resources to victims based on distance and demand
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import math
import json

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data Models
class Resource(BaseModel):
    type: str  # "food", "medicine", "clothes"
    quantity: int
    latitude: float
    longitude: float


class Need(BaseModel):
    type: str
    demand: int
    description: str
    latitude: float
    longitude: float


class OptimizationRequest(BaseModel):
    resources: List[Resource]
    needs: List[Need]


class AllocationPlan(BaseModel):
    quantity_allocated: int
    description: str
    distance_km: float
    resource_type: str
    status: str = "Pending Dispatch"


class OptimizationResponse(BaseModel):
    plan: List[AllocationPlan]
    total_allocated: int
    efficiency: float


# Utility Functions
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates in kilometers
    """
    R = 6371  # Earth radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def match_resource_type(resource_type: str, need_type: str) -> bool:
    """
    Check if resource type matches need type (exact match)
    """
    return resource_type.lower() == need_type.lower()


def calculate_priority_score(distance_km: float, demand: int, available_quantity: int) -> float:
    """
    Priority score for allocation (lower is better)
    Considers: distance, unmet demand, available supply
    """
    distance_weight = 0.4
    urgency_weight = 0.4
    efficiency_weight = 0.2
    
    distance_score = distance_km / 100
    urgency_score = demand / max(available_quantity, 1)
    efficiency_score = available_quantity / (demand + 1)
    
    return (distance_weight * distance_score + 
            urgency_weight * urgency_score - 
            efficiency_weight * efficiency_score)


# Main Optimization Endpoint
@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_allocation(request: OptimizationRequest):
    """
    Greedy algorithm to allocate resources to needs:
    1. Match resource types with needs
    2. Prioritize by distance and urgency
    3. Allocate greedily until resources or needs exhausted
    """
    
    plan = []
    resource_inventory = {r.type: list() for r in request.resources}
    
    # Organize resources by type
    for idx, resource in enumerate(request.resources):
        resource_inventory[resource.type].append({
            "id": idx,
            "quantity": resource.quantity,
            "available": resource.quantity,
            "latitude": resource.latitude,
            "longitude": resource.longitude,
        })
    
    # Sort needs by urgency (demand) - highest demand first
    sorted_needs = sorted(request.needs, key=lambda x: x.demand, reverse=True)
    
    total_allocated = 0
    total_demand = sum(n.demand for n in request.needs)
    
    # For each need, find best matching resources
    for need in sorted_needs:
        if need.demand <= 0:
            continue
        
        # Find matching resources by type
        matching_resources = resource_inventory.get(need.type, [])
        
        if not matching_resources:
            continue
        
        # Calculate distances and priority scores
        candidates = []
        for res in matching_resources:
            if res["available"] <= 0:
                continue
            
            distance = haversine_distance(
                need.latitude, need.longitude,
                res["latitude"], res["longitude"]
            )
            
            score = calculate_priority_score(distance, need.demand, res["available"])
            
            candidates.append({
                "resource": res,
                "distance": distance,
                "score": score
            })
        
        # Sort by priority score (lower is better)
        candidates = sorted(candidates, key=lambda x: x["score"])
        
        # Allocate from best candidates until need is met
        remaining_demand = need.demand
        
        for candidate in candidates:
            if remaining_demand <= 0:
                break
            
            res = candidate["resource"]
            allocate_qty = min(remaining_demand, res["available"])
            
            if allocate_qty > 0:
                plan.append(AllocationPlan(
                    quantity_allocated=allocate_qty,
                    description=need.description,
                    distance_km=round(candidate["distance"], 2),
                    resource_type=need.type,
                    status="Pending Dispatch"
                ))
                
                res["available"] -= allocate_qty
                remaining_demand -= allocate_qty
                total_allocated += allocate_qty
    
    # Calculate efficiency
    efficiency = (total_allocated / total_demand * 100) if total_demand > 0 else 0
    
    return OptimizationResponse(
        plan=plan,
        total_allocated=total_allocated,
        efficiency=round(efficiency, 2)
    )


# Health Check Endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "AI Module Running", "version": "1.0"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "ReliefLink AI Optimization Engine",
        "endpoints": {
            "POST /optimize": "Optimize resource allocation",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ReliefLink AI Module on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)