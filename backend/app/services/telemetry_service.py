from datetime import datetime
from sqlalchemy.orm import Session
from ..database.models import ScheduledOperation, JobQueue
from ..database.telemetry_model import MLProductionLog

def log_job_start(db: Session, job_id: str, machine_id: str):
    """
    Called when a worker accepts a job. 
    Captures features and start time.
    """
    try:
        # 1. Get Job Features
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return # Job not in queue, maybe manual entry? Skip.

        # 2. Get Scheduled info (for predicted duration)
        op = db.query(ScheduledOperation).filter(
            ScheduledOperation.job_id == job_id,
            ScheduledOperation.machine == machine_id
        ).first()
        
        predicted_dur = 0
        predicted_setup = 0
        if op:
            predicted_dur = op.finish - op.start
            predicted_setup = op.setup

        # 3. Create Telemetry Entry
        new_log = MLProductionLog(
            job_id=job_id,
            machine_id=machine_id,
            material_group=job.material_group,
            size_mm=job.size_mm,
            complexity=job.complexity,
            process_name=job.process,
            predicted_duration_min=predicted_dur,
            predicted_setup_min=predicted_setup,
            actual_start_time=datetime.utcnow(),
            status="started"
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Telemetry Error (Start): {e}")
        db.rollback()

def log_job_end(db: Session, job_id: str, machine_id: str):
    """
    Called when a worker completes a job. 
    Calculates final duration.
    """
    try:
        # Find the latest started record for this job/machine
        log_entry = db.query(MLProductionLog).filter(
            MLProductionLog.job_id == job_id,
            MLProductionLog.machine_id == machine_id,
            MLProductionLog.status == "started"
        ).order_by(MLProductionLog.actual_start_time.desc()).first()

        if not log_entry:
            return

        end_time = datetime.utcnow()
        duration_delta = end_time - log_entry.actual_start_time
        duration_min = duration_delta.total_seconds() / 60.0

        log_entry.actual_finish_time = end_time
        log_entry.actual_duration_min = round(duration_min, 2)
        log_entry.status = "completed"
        
        db.commit()
    except Exception as e:
        print(f"Telemetry Error (End): {e}")
        db.rollback()

def log_job_pause(db: Session, job_id: str, machine_id: str):
    """
    Optionally flag if a job was paused.
    """
    try:
        log_entry = db.query(MLProductionLog).filter(
            MLProductionLog.job_id == job_id,
            MLProductionLog.machine_id == machine_id,
            MLProductionLog.status == "started"
        ).order_by(MLProductionLog.actual_start_time.desc()).first()

        if log_entry:
            log_entry.is_paused = 1
            db.commit()
    except Exception:
        db.rollback()
