"""
Pydantic schemas for Schedule-related API requests/responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScheduleRunRequest(BaseModel):
    """Request to start a scheduling run."""
    use_ml: bool = True
    initial_machine_avail: Optional[Dict[str, int]] = None
    initial_machine_last_job: Optional[Dict[str, Optional[str]]] = None
    overtime_config: Optional[Dict[str, Any]] = None  # e.g. {"enabled": True, "end_time_mins": 1110}


class ScheduleSelectRequest(BaseModel):
    """Request to select a specific schedule option."""
    option_index: int = Field(..., ge=0, le=2, description="Index 0-2 of the chosen option")


class ManualAdjustRequest(BaseModel):
    """Request to manually adjust an operation (e.g. Gantt drag)."""
    operation_id: int
    new_start: Optional[int] = None
    new_finish: Optional[int] = None
    new_machine: Optional[str] = None


class RescheduleRequest(BaseModel):
    """Request to reschedule due to maintenance."""
    machine_id: str
    new_status: str  # "On", "Off", "Maintenance"
    repair_time: int = 40  # minutes
    breakdown_minute: int = 0  # minutes from 07:00


# ─── Response schemas ────────────────────────────────────────────────

class OperationResponse(BaseModel):
    id: Optional[int] = None
    job_id: str
    op_idx: int
    machine: str
    start: int
    finish: int
    setup: int
    note: Optional[str] = None
    worker_status: str = "pending"

    class Config:
        from_attributes = True


class ScheduleMetrics(BaseModel):
    fitness: float
    makespan: int
    setup: int
    tardiness: float


class ScheduleOption(BaseModel):
    name: str
    schedule: List[OperationResponse]
    metrics: ScheduleMetrics


class TaskStatusResponse(BaseModel):
    """Generic async task status."""
    task_token: str
    status: str  # "pending" | "running" | "completed" | "failed"
    progress: Optional[float] = None  # 0.0 - 1.0
    result: Optional[Any] = None
    error: Optional[str] = None


class ScheduleRunResponse(BaseModel):
    """Response after selecting a schedule — the final active schedule."""
    schedule: List[OperationResponse]
    version: int
    total_operations: int
    overtime_config: Optional[Dict[str, Any]] = None
