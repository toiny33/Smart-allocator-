from pydantic import BaseModel, Field
from typing import Optional, List

class Resource(BaseModel):
    ngo_name: str = Field("Relief NGO", description="Name of the supplying NGO")
    contact: str = Field("Unknown", description="NGO Contact Number")
    address: str = Field("Unknown Location", description="Address of the resources")
    type: str = Field(..., description="Type of resource")
    quantity: int = Field(..., gt=0)
    latitude: float
    longitude: float

class Need(BaseModel):
    victim_name: str = Field("Anonymous", description="Name of the person in need")
    address: str = Field("Unknown Location", description="Address of the victim")
    type: str = Field(..., description="Type of need")
    demand: int = Field(..., gt=0)
    description: str = Field(..., min_length=1)
    latitude: float
    longitude: float
    urgency: Optional[int] = 1

class OptimizationRequest(BaseModel):
    resources: List[Resource]
    needs: List[Need]

class AllocationPlan(BaseModel):
    resource_type: str
    quantity_allocated: int
    description: str
    urgency_score: int
    distance_km: float
    ngo_source: str
    ngo_contact: str
    victim_destination: str
    status: str = "Pending Dispatch"

class OptimizationResponse(BaseModel):
    plan: List[AllocationPlan]
    stats: dict