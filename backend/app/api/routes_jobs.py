"""
Job queue CRUD endpoints.
GET    /api/jobs           → List all jobs
POST   /api/jobs           → Add a single job
POST   /api/jobs/batch     → Add multiple jobs
PUT    /api/jobs/{job_id}  → Update a job
DELETE /api/jobs/{job_id}  → Delete a job
DELETE /api/jobs           → Clear all jobs
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..database.models import JobQueue
from ..models.job_schemas import (
    JobCreate, JobUpdate, JobBatchCreate,
    JobResponse, JobListResponse,
)

router = APIRouter(prefix="/api/jobs", tags=["Job Queue"])


@router.get("", response_model=JobListResponse)
def list_jobs(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all jobs in the queue, optionally filtered by status."""
    query = db.query(JobQueue)
    if status:
        query = query.filter(JobQueue.status == status)
    jobs = query.order_by(JobQueue.created_at.desc()).all()

    return JobListResponse(
        jobs=[_to_response(j) for j in jobs],
        total=len(jobs),
    )


@router.post("", response_model=JobResponse, status_code=201)
def create_job(data: JobCreate, db: Session = Depends(get_db)):
    """Add a single job to the queue."""
    existing = db.query(JobQueue).filter(JobQueue.id == data.id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Job '{data.id}' already exists")

    job = JobQueue(
        id=data.id,
        project_name=data.project_name,
        project_code=data.project_code,
        hexcode=data.hexcode,
        material_group=data.material_group,
        process_steps=data.process_steps,
        size_mm=data.size_mm,
        detail_len_mm=data.detail_len_mm,
        complexity=data.complexity,
        quantity=data.quantity,
        manual_setup_time=data.manual_setup_time,
        operations=data.operations,
        process=data.process,
        process_machine=data.process_machine,
        start_time=data.start_time,
        due_date=data.due_date,
        priority=data.priority,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _to_response(job)


@router.post("/batch", response_model=JobListResponse, status_code=201)
def create_jobs_batch(data: JobBatchCreate, db: Session = Depends(get_db)):
    """Add multiple jobs at once."""
    created = []
    for jd in data.jobs:
        existing = db.query(JobQueue).filter(JobQueue.id == jd.id).first()
        if existing:
            continue  # skip duplicates silently

        job = JobQueue(
            id=jd.id,
            project_name=jd.project_name,
            project_code=jd.project_code,
            hexcode=jd.hexcode,
            material_group=jd.material_group,
            process_steps=jd.process_steps,
            size_mm=jd.size_mm,
            detail_len_mm=jd.detail_len_mm,
            complexity=jd.complexity,
            quantity=jd.quantity,
            manual_setup_time=jd.manual_setup_time,
            operations=jd.operations,
            process=jd.process,
            process_machine=jd.process_machine,
            start_time=jd.start_time,
            due_date=jd.due_date,
            priority=jd.priority,
        )
        db.add(job)
        created.append(job)

    db.commit()
    for j in created:
        db.refresh(j)

    return JobListResponse(
        jobs=[_to_response(j) for j in created],
        total=len(created),
    )


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: str, data: JobUpdate, db: Session = Depends(get_db)):
    """Update an existing job."""
    job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return _to_response(job)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a specific job from the queue."""
    job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    db.delete(job)
    db.commit()


@router.delete("", status_code=204)
def clear_all_jobs(db: Session = Depends(get_db)):
    """Clear all jobs from the queue."""
    db.query(JobQueue).delete()
    db.commit()


# ─── Helpers ─────────────────────────────────────────────────────────

def _to_response(job: JobQueue) -> JobResponse:
    return JobResponse(
        id=job.id,
        project_name=job.project_name,
        project_code=job.project_code,
        hexcode=job.hexcode,
        material_group=job.material_group,
        process_steps=job.process_steps,
        size_mm=job.size_mm,
        detail_len_mm=job.detail_len_mm,
        complexity=job.complexity,
        quantity=job.quantity,
        manual_setup_time=job.manual_setup_time,
        operations=job.operations,
        process=job.process,
        process_machine=job.process_machine,
        start_time=job.start_time,
        due_date=job.due_date,
        priority=job.priority,
        status=job.status,
        created_at=job.created_at,
    )
