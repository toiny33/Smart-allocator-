import math
from typing import List, Dict
from ortools.linear_solver import pywraplp
from difflib import SequenceMatcher # Built-in, no install needed

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_similar(a, b):
    # Standardize and check for exact/plural matches
    a, b = a.lower().strip(), b.lower().strip()
    if a == b or a == b + 's' or b == a + 's':
        return True
    # Fuzzy matching ratio (0.8 = 80% similar)
    return SequenceMatcher(None, a, b).ratio() > 0.8

class AllocationOptimizer:
    def solve_matching(self, resources: List[Dict], needs: List[Dict]):
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver: return {"plan": [], "stats": {}}

        x = {}
        for i, res in enumerate(resources):
            for j, need in enumerate(needs):
                # FUZZY MATCHING REPLACES EXACT MATCHING HERE
                if is_similar(res['type'], need['type']):
                    upper_bound = min(res['quantity'], need['demand'])
                    x[i, j] = solver.IntVar(0, upper_bound, f'x_{i}_{j}')

        for i, res in enumerate(resources):
            solver.Add(sum(x[i, j] for j in range(len(needs)) if (i, j) in x) <= res['quantity'])

        for j, need in enumerate(needs):
            solver.Add(sum(x[i, j] for i in range(len(resources)) if (i, j) in x) <= need['demand'])

        objective = solver.Objective()
        for (i, j), var in x.items():
            dist = calculate_distance(
                resources[i]['latitude'], resources[i]['longitude'], 
                needs[j]['latitude'], needs[j]['longitude']
            )
            weight = (needs[j].get('urgency', 1) * 1000) - dist
            objective.SetCoefficient(var, weight)
        
        objective.SetMaximization()
        status = solver.Solve()
        
        plan = []
        total_items = 0
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            for (i, j), var in x.items():
                qty = int(var.solution_value())
                if qty > 0:
                    d = calculate_distance(
                        resources[i]['latitude'], resources[i]['longitude'], 
                        needs[j]['latitude'], needs[j]['longitude']
                    )
                    plan.append({
                        "resource_type": resources[i]['type'], # Keep NGO's naming
                        "quantity_allocated": qty,
                        "description": needs[j].get('description', 'Emergency Request'),
                        "urgency_score": needs[j].get('urgency', 1),
                        "distance_km": round(d, 2),
                        "ngo_source": resources[i].get('ngo_name', 'Relief NGO'),
                        "ngo_contact": resources[i].get('contact', 'Unknown'),
                        "victim_destination": needs[j].get('address', 'Unknown Destination'),
                        "status": "Pending Dispatch"
                    })
                    total_items += qty

        return {
            "plan": plan,
            "stats": {"total_items_allocated": total_items, "total_matches": len(plan)}
        }