"""
Scheduling endpoints — the core of the system.
POST /api/schedule/run            → Start GA-VNS (async), returns task_token
GET  /api/schedule/status/{token} → Poll schedule results
POST /api/schedule/select         → Choose one of 3 options → persist to DB
GET  /api/schedule/current        → Get the active schedule
POST /api/schedule/manual-adjust  → Manually adjust an operation (Gantt DnD)
POST /api/schedule/reschedule     → Reschedule after maintenance event
DELETE /api/schedule/current      → Clear the active schedule
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database.session import get_db
from ..database.models import JobQueue, ScheduledOperation, Machine
from ..tasks.task_manager import task_manager
from ..tasks.background_tasks import schedule_run_task, _load_machines_data_from_db
from ..models.schedule_schemas import (
    ScheduleRunRequest, ScheduleSelectRequest,
    ManualAdjustRequest, RescheduleRequest,
    TaskStatusResponse, ScheduleRunResponse, OperationResponse,
)
from ..models.task_schemas import TaskToken

router = APIRouter(prefix="/api/schedule", tags=["Scheduling"])

# In-memory store for schedule options pending selection
# Key: task_token → Value: list of options dicts
_pending_options: dict = {}


@router.post("/run", response_model=TaskToken, status_code=202)
def run_schedule(req: ScheduleRunRequest, db: Session = Depends(get_db)):
    """
    Start a scheduling computation in the background.
    Reads all 'queued' jobs from DB, runs HybridEngine + GA-VNS.
    Returns a task_token for polling.
    """
    # Load jobs from DB
    jobs_db = db.query(JobQueue).filter(JobQueue.status.in_(["queued", "scheduled"])).all()
    if not jobs_db:
        raise HTTPException(status_code=400, detail="No jobs in queue to schedule")

    # Convert ORM objects to dicts (same format the old main.py used)
    jobs_list = []
    for j in jobs_db:
        jobs_list.append({
            "id": j.id,
            "material_group": j.material_group,
            "process_steps": j.process_steps,
            "size_mm": j.size_mm,
            "detail_len_mm": j.detail_len_mm or j.size_mm,
            "complexity": j.complexity,
            "quantity": j.quantity,
            "operations": j.operations or [],
            "start_time": j.start_time or datetime.now().replace(hour=7, minute=0, second=0),
            "due_date": j.due_date or datetime.now().replace(hour=17, minute=0, second=0),
            "priority": j.priority,
        })

    # Submit to background thread
    token = task_manager.submit(
        schedule_run_task,
        jobs_list,
        req.use_ml,
        req.initial_machine_avail,
        req.initial_machine_last_job,
    )

    return TaskToken(task_token=token, message=f"Scheduling {len(jobs_list)} jobs in background")


@router.get("/status/{token}", response_model=TaskStatusResponse)
def get_schedule_status(token: str):
    """
    Poll the status of a scheduling task.
    When completed, result contains 3 schedule options.
    """
    info = task_manager.get_status(token)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found")

    # Cache options for later selection
    if info.status == "completed" and info.result:
        _pending_options[token] = info.result

    return TaskStatusResponse(
        task_token=token,
        status=info.status,
        progress=info.progress,
        result=info.result,
        error=info.error,
    )


@router.post("/select", response_model=ScheduleRunResponse)
def select_schedule(req: ScheduleSelectRequest, token: str, db: Session = Depends(get_db)):
    """
    Select one of the 3 schedule options returned by a completed scheduling task.
    Persists the chosen schedule to the database.

    Query param `token` is the task_token from the scheduling run.
    """
    options = _pending_options.get(token)
    if not options:
        # Try to get from task manager
        info = task_manager.get_status(token)
        if not info or info.status != "completed" or not info.result:
            raise HTTPException(status_code=404, detail="No schedule options found for this token")
        options = info.result

    if req.option_index >= len(options):
        raise HTTPException(status_code=400, detail=f"Option index {req.option_index} out of range")

    chosen = options[req.option_index]
    schedule = chosen["schedule"]

    # Determine new schedule version
    max_version = db.query(ScheduledOperation.schedule_version).order_by(
        ScheduledOperation.schedule_version.desc()
    ).first()
    new_version = (max_version[0] + 1) if max_version else 1

    # Clear existing active schedule
    db.query(ScheduledOperation).delete()

    # Persist selected schedule
    for op in schedule:
        db_op = ScheduledOperation(
            schedule_version=new_version,
            job_id=op["job_id"],
            op_idx=op.get("op_idx", 0),
            machine=op["machine"],
            start=op["start"],
            finish=op["finish"],
            setup=op.get("setup", 0),
            note=op.get("note", ""),
        )
        db.add(db_op)

    # Update job statuses to 'scheduled'
    job_ids = list(set(op["job_id"] for op in schedule))
    db.query(JobQueue).filter(JobQueue.id.in_(job_ids)).update(
        {"status": "scheduled"}, synchronize_session=False
    )

    db.commit()

    # Clean up pending options
    _pending_options.pop(token, None)

    # Return the persisted schedule
    ops = db.query(ScheduledOperation).filter(
        ScheduledOperation.schedule_version == new_version
    ).order_by(ScheduledOperation.start).all()

    return ScheduleRunResponse(
        schedule=[OperationResponse(
            id=op.id, job_id=op.job_id, op_idx=op.op_idx, machine=op.machine,
            start=op.start, finish=op.finish, setup=op.setup,
            note=op.note, worker_status=op.worker_status,
        ) for op in ops],
        version=new_version,
        total_operations=len(ops),
    )


@router.get("/current", response_model=ScheduleRunResponse)
def get_current_schedule(db: Session = Depends(get_db)):
    """Get the currently active schedule."""
    max_version = db.query(ScheduledOperation.schedule_version).order_by(
        ScheduledOperation.schedule_version.desc()
    ).first()

    if not max_version:
        return ScheduleRunResponse(schedule=[], version=0, total_operations=0)

    version = max_version[0]
    ops = db.query(ScheduledOperation).filter(
        ScheduledOperation.schedule_version == version
    ).order_by(ScheduledOperation.start).all()

    return ScheduleRunResponse(
        schedule=[OperationResponse(
            id=op.id, job_id=op.job_id, op_idx=op.op_idx, machine=op.machine,
            start=op.start, finish=op.finish, setup=op.setup,
            note=op.note, worker_status=op.worker_status,
        ) for op in ops],
        version=version,
        total_operations=len(ops),
    )


@router.post("/manual-adjust", response_model=OperationResponse)
def manual_adjust(req: ManualAdjustRequest, db: Session = Depends(get_db)):
    """
    Manually adjust a scheduled operation (e.g. drag on Gantt chart).
    Validates no conflicts before applying.
    """
    op = db.query(ScheduledOperation).filter(ScheduledOperation.id == req.operation_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    if req.new_start is not None:
        duration = op.finish - op.start
        op.start = req.new_start
        if req.new_finish is not None:
            op.finish = req.new_finish
        else:
            op.finish = req.new_start + duration

    if req.new_machine is not None:
        # Validate machine exists
        machine = db.query(Machine).filter(Machine.id == req.new_machine).first()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine '{req.new_machine}' not found")
        op.machine = req.new_machine

    op.note = "Manual Adjustment"
    db.commit()
    db.refresh(op)

    return OperationResponse(
        id=op.id, job_id=op.job_id, op_idx=op.op_idx, machine=op.machine,
        start=op.start, finish=op.finish, setup=op.setup,
        note=op.note, worker_status=op.worker_status,
    )


@router.post("/reschedule", response_model=TaskToken, status_code=202)
def reschedule(req: RescheduleRequest, db: Session = Depends(get_db)):
    """
    Reschedule after a machine status change (e.g. maintenance).
    Mirrors the rescheduling logic from the original main.py Tab 3.
    """
    # Update machine status
    machine = db.query(Machine).filter(Machine.id == req.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine '{req.machine_id}' not found")

    machine.status = req.new_status
    db.commit()

    if req.new_status != "Maintenance" or req.repair_time <= 30:
        return TaskToken(task_token="none", message="Status updated, no reschedule needed")

    # Identify affected operations
    all_ops = db.query(ScheduledOperation).all()
    all_machines = {m.id: m for m in db.query(Machine).all()}
    job_status = {}

    for op in all_ops:
        j_id = op.job_id
        if j_id not in job_status:
            job_status[j_id] = "unaffected"

        if op.machine == req.machine_id and op.start <= req.breakdown_minute < op.finish:
            job_status[j_id] = "affected"

    # Jobs that haven't started yet are also affected
    for j_id in job_status.keys():
        ops_for_job = [o for o in all_ops if o.job_id == j_id]
        if ops_for_job:
            first_start = min(o.start for o in ops_for_job)
            if first_start > req.breakdown_minute:
                job_status[j_id] = "affected"

    affected_job_ids = {j for j, s in job_status.items() if s == "affected"}

    if not affected_job_ids:
        return TaskToken(task_token="none", message="No jobs affected")

    # Calculate machine availability
    unaffected_ops = [op for op in all_ops if op.job_id not in affected_job_ids]
    mac_avail = {}
    mac_last = {}

    for m_id in all_machines.keys():
        if m_id == req.machine_id:
            mac_avail[m_id] = req.breakdown_minute + req.repair_time
            mac_last[m_id] = None
        else:
            ops_on_m = [op for op in unaffected_ops if op.machine == m_id]
            if ops_on_m:
                mac_avail[m_id] = max(
                    max(op.finish for op in ops_on_m),
                    req.breakdown_minute,
                )
                mac_last[m_id] = max(ops_on_m, key=lambda x: x.finish).job_id
            else:
                mac_avail[m_id] = req.breakdown_minute
                mac_last[m_id] = None

    # Build affected jobs list from DB
    affected_jobs = db.query(JobQueue).filter(JobQueue.id.in_(affected_job_ids)).all()
    jobs_list = []
    for j in affected_jobs:
        jobs_list.append({
            "id": j.id,
            "material_group": j.material_group,
            "process_steps": j.process_steps,
            "size_mm": j.size_mm,
            "detail_len_mm": j.detail_len_mm or j.size_mm,
            "complexity": j.complexity,
            "quantity": j.quantity,
            "operations": j.operations or [],
            "start_time": j.start_time or datetime.now().replace(hour=7, minute=0),
            "due_date": j.due_date or datetime.now().replace(hour=17, minute=0),
            "priority": j.priority,
        })

    # Submit rescheduling task
    token = task_manager.submit(
        schedule_run_task,
        jobs_list,
        True,  # use_ml
        mac_avail,
        mac_last,
    )

    return TaskToken(task_token=token, message=f"Rescheduling {len(jobs_list)} affected jobs")


@router.delete("/current", status_code=204)
def clear_schedule(db: Session = Depends(get_db)):
    """Clear the current schedule."""
    db.query(ScheduledOperation).delete()
    db.query(JobQueue).update({"status": "queued"}, synchronize_session=False)
    db.commit()
