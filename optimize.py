import math
from typing import List, Dict, Any
from ortools.linear_solver import pywraplp

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the distance between two geographical points using the Haversine formula."""
    R = 6371.0  # Earth radius in kilometers
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def optimize_allocation(resources: List[Dict[str, Any]], needs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Hackathon-optimized resource allocation engine using Mixed Integer Programming.
    Returns the exact allocation plan and summary statistics.
    """
    # Edge case: If there's nothing to process, return immediately
    if not resources or not needs:
        return {"plan": [], "stats": {"message": "No resources or needs provided."}}

    # Upgrade: Use SCIP (Integer Solver) so we don't allocate fractions of items
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return {"plan": [], "stats": {"error": "Solver initialization failed"}}

    # Upgrade: Set a strict time limit (2000 milliseconds) so the API NEVER hangs during a live demo
    solver.SetTimeLimit(2000)

    x = {}
    
    # 1. Define Decision Variables (x[i][j])
    for i, res in enumerate(resources):
        for j, need in enumerate(needs):
            if res['type'] == need['type']:
                max_possible = min(res['quantity'], need['demand'])
                # Upgrade: IntVar ensures we only send whole numbers (integers)
                x[i, j] = solver.IntVar(0, max_possible, f'x_{i}_{j}')

    # 2. Define Constraints
    # Constraint A: Cannot exceed available resource quantity
    for i, res in enumerate(resources):
        constraint = solver.RowConstraint(0, res['quantity'], f'res_limit_{i}')
        for j in range(len(needs)):
            if (i, j) in x:
                constraint.SetCoefficient(x[i, j], 1)

    # Constraint B: Cannot exceed requested demand
    for j, need in enumerate(needs):
        constraint = solver.RowConstraint(0, need['demand'], f'need_limit_{j}')
        for i in range(len(resources)):
            if (i, j) in x:
                constraint.SetCoefficient(x[i, j], 1)

    # 3. Define the Objective Function
    objective = solver.Objective()
    
    for i, res in enumerate(resources):
        for j, need in enumerate(needs):
            if (i, j) in x:
                distance = calculate_distance(res['latitude'], res['longitude'], need['latitude'], need['longitude'])
                urgency = need.get('urgency', 1) 
                
                # Formula: Prioritize urgency heavily, use distance to break ties efficiently
                weight = (urgency * 1000) - distance
                objective.SetCoefficient(x[i, j], weight)

    objective.SetMaximization()

    # 4. Solve the Optimization Problem
    status = solver.Solve()

    # 5. Extract Data and Build Analytics
    allocation_plan = []
    total_allocated = 0
    total_distance = 0.0

    if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
        for i, res in enumerate(resources):
            for j, need in enumerate(needs):
                if (i, j) in x and x[i, j].solution_value() > 0:
                    allocated_amount = int(x[i, j].solution_value())
                    dist = calculate_distance(res['latitude'], res['longitude'], need['latitude'], need['longitude'])
                    
                    allocation_plan.append({
                        "resource_id": i,
                        "need_id": j,
                        "resource_type": res['type'],
                        "from_location": {"lat": res['latitude'], "lon": res['longitude']},
                        "to_location": {"lat": need['latitude'], "lon": need['longitude']},
                        "description": need.get('description', 'Unknown Location'),
                        "urgency_score": need.get('urgency', 1),
                        "quantity_allocated": allocated_amount,
                        "distance_km": round(dist, 2)
                    })
                    
                    total_allocated += allocated_amount
                    total_distance += dist * allocated_amount

    # Upgrade: Return a structured dict with both the plan and cool stats for your UI
    return {
        "plan": allocation_plan,
        "stats": {
            "solver_status": "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE" if status == pywraplp.Solver.FEASIBLE else "FAILED",
            "total_items_allocated": total_allocated,
            "total_delivery_distance_km": round(total_distance, 2),
            "total_matches_made": len(allocation_plan)
        }
    }