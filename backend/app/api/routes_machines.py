"""
Machine management endpoints.
GET    /api/machines               → List all machines with status
PUT    /api/machines/{id}/status   → Update machine status
GET    /api/machines/{id}/jobs     → Get jobs assigned to a machine
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..database.models import Machine, ScheduledOperation
from ..models.machine_schemas import MachineStatusUpdate, MachineResponse, MachineListResponse

router = APIRouter(prefix="/api/machines", tags=["Machines"])


@router.get("", response_model=MachineListResponse)
def list_machines(db: Session = Depends(get_db)):
    """List all machines with their current status and job count."""
    machines = db.query(Machine).order_by(Machine.id).all()
    result = []

    for m in machines:
        # Count active scheduled operations for this machine
        job_count = (
            db.query(ScheduledOperation)
            .filter(
                ScheduledOperation.machine == m.id,
                ScheduledOperation.worker_status.notin_(["completed"]),
            )
            .count()
        )

        caps = [c.capability_name for c in m.capabilities]

        result.append(MachineResponse(
            id=m.id,
            name=m.name,
            machine_type=m.machine_type,
            status=m.status,
            max_size_mm=m.max_size_mm,
            notes=m.notes,
            capabilities=caps,
            job_count=job_count,
        ))

    return MachineListResponse(machines=result, total=len(result))


@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    """Get a single machine's details."""
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")

    job_count = (
        db.query(ScheduledOperation)
        .filter(
            ScheduledOperation.machine == m.id,
            ScheduledOperation.worker_status.notin_(["completed"]),
        )
        .count()
    )
    caps = [c.capability_name for c in m.capabilities]

    return MachineResponse(
        id=m.id,
        name=m.name,
        machine_type=m.machine_type,
        status=m.status,
        max_size_mm=m.max_size_mm,
        notes=m.notes,
        capabilities=caps,
        job_count=job_count,
    )


@router.put("/{machine_id}/status", response_model=MachineResponse)
def update_machine_status(machine_id: str, data: MachineStatusUpdate, db: Session = Depends(get_db)):
    """Update the operational status of a machine."""
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")

    if data.status not in ("On", "Off", "Maintenance"):
        raise HTTPException(status_code=400, detail="Status must be 'On', 'Off', or 'Maintenance'")

    m.status = data.status
    db.commit()
    db.refresh(m)

    caps = [c.capability_name for c in m.capabilities]

    return MachineResponse(
        id=m.id,
        name=m.name,
        machine_type=m.machine_type,
        status=m.status,
        max_size_mm=m.max_size_mm,
        notes=m.notes,
        capabilities=caps,
        job_count=0,
    )


@router.get("/{machine_id}/jobs")
def get_machine_jobs(machine_id: str, db: Session = Depends(get_db)):
    """Get all scheduled operations for a specific machine, sorted by start time."""
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_id}' not found")

    ops = (
        db.query(ScheduledOperation)
        .filter(ScheduledOperation.machine == machine_id)
        .order_by(ScheduledOperation.start)
        .all()
    )

    return {
        "machine_id": machine_id,
        "machine_name": m.name,
        "jobs": [
            {
                "id": op.id,
                "job_id": op.job_id,
                "op_idx": op.op_idx,
                "start": op.start,
                "finish": op.finish,
                "setup": op.setup,
                "note": op.note,
                "worker_status": op.worker_status,
            }
            for op in ops
        ],
        "total": len(ops),
    }
