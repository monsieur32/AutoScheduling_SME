"""
Pydantic schemas for background task status tracking.
"""

from pydantic import BaseModel
from typing import Optional, Any


class TaskToken(BaseModel):
    task_token: str
    message: str = "Task enqueued"


class DXFUploadResult(BaseModel):
    filename: str
    status: str  # "success" | "error"
    total_len_mm: Optional[float] = None
    straight_len_mm: Optional[float] = None
    curved_len_mm: Optional[float] = None
    complexity_ratio: Optional[float] = None
    entity_counts: Optional[dict] = None
    texts: Optional[list] = None
    files_processed: Optional[int] = None
    warnings: Optional[list] = None
    message: Optional[str] = None
