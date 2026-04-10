"""
Pydantic schemas for Job-related API requests/responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Request schemas ─────────────────────────────────────────────────

class JobCreate(BaseModel):
    """Schema for adding a single job to the queue."""
    id: str = Field(..., description="Unique job identifier e.g. 'PRJ001.1_abc_1234'")
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    hexcode: Optional[str] = None
    material_group: str = "C"
    process_steps: int = 1
    size_mm: float = 1000.0
    detail_len_mm: Optional[float] = None
    complexity: float = 0.0
    quantity: int = 1
    operations: Optional[List[str]] = None
    process: Optional[str] = None
    process_machine: Optional[str] = None
    start_time: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: str = "Bình thường"


class JobUpdate(BaseModel):
    """Schema for updating an existing job."""
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    hexcode: Optional[str] = None
    material_group: Optional[str] = None
    size_mm: Optional[float] = None
    detail_len_mm: Optional[float] = None
    complexity: Optional[float] = None
    quantity: Optional[int] = None
    process: Optional[str] = None
    process_machine: Optional[str] = None
    start_time: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None


class JobBatchCreate(BaseModel):
    """Schema for adding multiple jobs at once."""
    jobs: List[JobCreate]


# ─── Response schemas ────────────────────────────────────────────────

class JobResponse(BaseModel):
    id: str
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    hexcode: Optional[str] = None
    material_group: str
    process_steps: int
    size_mm: float
    detail_len_mm: Optional[float] = None
    complexity: float
    quantity: int
    operations: Optional[List[str]] = None
    process: Optional[str] = None
    process_machine: Optional[str] = None
    start_time: Optional[datetime] = None
    due_date: Optional[datetime] = None
    priority: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
