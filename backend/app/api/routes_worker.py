"""
Worker action endpoints (Tablet / touch interface).
POST /api/worker/accept/{job_id}   → Accept a job assignment
POST /api/worker/pause/{job_id}    → Pause work
POST /api/worker/complete/{job_id} → Mark job as completed
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..database.models import ScheduledOperation, JobQueue
from ..services.telemetry_service import log_job_start, log_job_end, log_job_pause

router = APIRouter(prefix="/api/worker", tags=["Worker Actions"])


@router.post("/accept/{job_id}")
def accept_job(job_id: str, machine_id: str = None, db: Session = Depends(get_db)):
    """
    Worker accepts a job on their machine.
    Updates the worker_status of all operations for this job (on the specified machine)
    from 'pending' to 'accepted'.
    """
    query = db.query(ScheduledOperation).filter(ScheduledOperation.job_id == job_id)
    if machine_id:
        query = query.filter(ScheduledOperation.machine == machine_id)

    ops = query.all()
    if not ops:
        raise HTTPException(status_code=404, detail=f"No operations found for job '{job_id}'")

    for op in ops:
        op.worker_status = "accepted"
    
    # Hidden Telemetry: Log job start
    log_job_start(db, job_id, machine_id)

    db.commit()
    return {"job_id": job_id, "status": "accepted", "operations_updated": len(ops)}


@router.post("/pause/{job_id}")
def pause_job(job_id: str, machine_id: str = None, db: Session = Depends(get_db)):
    """
    Worker pauses a job.
    """
    query = db.query(ScheduledOperation).filter(ScheduledOperation.job_id == job_id)
    if machine_id:
        query = query.filter(ScheduledOperation.machine == machine_id)

    ops = query.all()
    if not ops:
        raise HTTPException(status_code=404, detail=f"No operations found for job '{job_id}'")

    for op in ops:
        op.worker_status = "paused"
    
    # Hidden Telemetry: Flag pause
    log_job_pause(db, job_id, machine_id)

    db.commit()
    return {"job_id": job_id, "status": "paused", "operations_updated": len(ops)}


@router.post("/complete/{job_id}")
def complete_job(job_id: str, machine_id: str = None, db: Session = Depends(get_db)):
    """
    Worker marks a job as completed.
    Also updates the job queue status.
    """
    query = db.query(ScheduledOperation).filter(ScheduledOperation.job_id == job_id)
    if machine_id:
        query = query.filter(ScheduledOperation.machine == machine_id)

    ops = query.all()
    if not ops:
        raise HTTPException(status_code=404, detail=f"No operations found for job '{job_id}'")

    for op in ops:
        op.worker_status = "completed"

    # Check if ALL operations for this job are completed
    all_ops_for_job = db.query(ScheduledOperation).filter(
        ScheduledOperation.job_id == job_id
    ).all()

    all_done = all(op.worker_status == "completed" for op in all_ops_for_job)

    if all_done:
        # Update job queue status
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if job:
            job.status = "completed"
    
    # Hidden Telemetry: Log job end
    log_job_end(db, job_id, machine_id)

    db.commit()

    return {
        "job_id": job_id,
        "status": "completed",
        "operations_updated": len(ops),
        "job_fully_completed": all_done,
    }
