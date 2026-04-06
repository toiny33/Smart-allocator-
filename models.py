from pydantic import BaseModel, Field
from typing import Optional, Literal


# -----------------------------
# Resource Model
# -----------------------------
class Resource(BaseModel):
    type: Literal["food", "medicine", "clothes"] = Field(
        ..., description="Type of resource"
    )
    quantity: int = Field(
        ..., gt=0, description="Available quantity of the resource"
    )
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude of the resource location"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude of the resource location"
    )


# -----------------------------
# Need Model
# -----------------------------
class Need(BaseModel):
    name: Optional[str] = Field(
        None, description="Name of the area/location (e.g., Area A)"
    )
    type: Literal["food", "medicine", "clothes"] = Field(
        ..., description="Type of need"
    )
    demand: int = Field(
        ..., gt=0, description="Required quantity"
    )
    description: str = Field(
        ..., min_length=5, description="Description of the situation"
    )
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitude of the need location"
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude of the need location"
    )
    urgency: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Urgency level (1–5), assigned by AI"
    )


# -----------------------------
# Request Model (API input)
# -----------------------------
class OptimizationRequest(BaseModel):
    resources: list[Resource]
    needs: list[Need]


# -----------------------------
# Allocation Model (single result)
# -----------------------------
class Allocation(BaseModel):
    to: str = Field(..., description="Destination area name")
    quantity: int = Field(..., ge=0, description="Allocated quantity")


# -----------------------------
# Response Model (API output)
# -----------------------------
class OptimizationResponse(BaseModel):
    allocations: list[Allocation]