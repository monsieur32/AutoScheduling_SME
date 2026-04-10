"""
Pydantic schemas for Machine-related API requests/responses.
"""

from pydantic import BaseModel
from typing import Optional, List


class MachineStatusUpdate(BaseModel):
    status: str  # "On", "Off", "Maintenance"


class MachineResponse(BaseModel):
    id: str
    name: str
    machine_type: str
    status: str
    max_size_mm: Optional[str] = None
    notes: Optional[str] = None
    capabilities: Optional[List[str]] = None
    job_count: int = 0

    class Config:
        from_attributes = True


class MachineListResponse(BaseModel):
    machines: List[MachineResponse]
    total: int
