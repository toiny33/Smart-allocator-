import math
from typing import List, Dict, Any
from ortools.linear_solver import pywraplp


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


class AllocationOptimizer:
    def __init__(self, api_key=None):
        self.api_key = api_key  # not used yet but future ready

    def solve_matching(self, resources: List[Dict], needs: List[Dict]):

        if not resources or not needs:
            return []

        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return []

        solver.SetTimeLimit(2000)

        x = {}

        # Decision variables
        for i, res in enumerate(resources):
            for j, need in enumerate(needs):
                if res['type'] == need['type']:
                    max_possible = min(res['quantity'], need['demand'])
                    x[i, j] = solver.IntVar(0, max_possible, f'x_{i}_{j}')

        # Constraints: resource limits
        for i, res in enumerate(resources):
            constraint = solver.RowConstraint(0, res['quantity'], '')
            for j in range(len(needs)):
                if (i, j) in x:
                    constraint.SetCoefficient(x[i, j], 1)

        # Constraints: demand limits
        for j, need in enumerate(needs):
            constraint = solver.RowConstraint(0, need['demand'], '')
            for i in range(len(resources)):
                if (i, j) in x:
                    constraint.SetCoefficient(x[i, j], 1)

        # Objective
        objective = solver.Objective()

        for i, res in enumerate(resources):
            for j, need in enumerate(needs):
                if (i, j) in x:
                    distance = calculate_distance(
                        res['latitude'], res['longitude'],
                        need['latitude'], need['longitude']
                    )
                    urgency = need.get('urgency', 1)

                    weight = (urgency * 1000) - distance
                    objective.SetCoefficient(x[i, j], weight)

        objective.SetMaximization()

        status = solver.Solve()

        allocation_list = []

        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            for i, res in enumerate(resources):
                for j, need in enumerate(needs):
                    if (i, j) in x and x[i, j].solution_value() > 0:
                        allocation_list.append({
                            "to": f"Need {j}",
                            "quantity": int(x[i, j].solution_value())
                        })

        return allocation_list
    

    