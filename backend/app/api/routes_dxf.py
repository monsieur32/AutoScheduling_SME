"""
DXF upload and parsing endpoints.
POST /api/dxf/upload   → Upload DXF files, returns task_token
GET  /api/dxf/status/{token} → Poll parse result
"""

import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..config import UPLOAD_DIR
from ..tasks.task_manager import task_manager
from ..tasks.background_tasks import parse_dxf_task
from ..models.task_schemas import TaskToken
from ..models.schedule_schemas import TaskStatusResponse

router = APIRouter(prefix="/api/dxf", tags=["DXF Parsing"])


@router.post("/upload", response_model=TaskToken, status_code=202)
async def upload_dxf(files: List[UploadFile] = File(...)):
    """
    Upload one or more DXF files for analysis.
    Files are saved to disk, then parsed in a background thread.
    Returns a task_token for polling results.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved_paths = []
    for f in files:
        if not f.filename.lower().endswith('.dxf'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {f.filename}")

        save_path = os.path.join(str(UPLOAD_DIR), f.filename)
        with open(save_path, "wb") as fp:
            content = await f.read()
            fp.write(content)
        saved_paths.append(save_path)

    # Enqueue background parsing task
    token = task_manager.submit(parse_dxf_task, saved_paths)

    return TaskToken(task_token=token, message=f"Parsing {len(saved_paths)} file(s) in background")


@router.get("/status/{token}", response_model=TaskStatusResponse)
async def get_parse_status(token: str):
    """
    Poll the status of a DXF parsing task.
    Returns results when completed.
    """
    info = task_manager.get_status(token)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_token=token,
        status=info.status,
        progress=info.progress,
        result=info.result,
        error=info.error,
    )
