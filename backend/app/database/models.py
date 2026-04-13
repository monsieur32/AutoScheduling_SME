"""
SQLAlchemy ORM models — extended from the original database/models.py.
Adds JobQueue and ScheduledOperation tables for persistent state management
that was previously stored in Streamlit session_state.
"""

from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()

# Import Telemetry model here to ensure it's registered with Base for create_all()
from .telemetry_model import MLProductionLog 

# ─── Original Models (ported from database/models.py) ───────────────

class Material(Base):
    __tablename__ = 'materials'
    id = Column(String, primary_key=True)
    material_name = Column(String, nullable=True)
    material_type = Column(String, nullable=True)
    group_code = Column(String, nullable=False)
    notes = Column(String, nullable=True)


class Machine(Base):
    __tablename__ = 'machines'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
    status = Column(String, default="On")
    max_size_mm = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    capabilities = relationship("MachineCapability", back_populates="machine", cascade="all, delete-orphan")
    speeds = relationship("MachineSpeed", back_populates="machine", cascade="all, delete-orphan")


class MachineCapability(Base):
    __tablename__ = 'machine_capabilities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey('machines.id'), nullable=False)
    capability_name = Column(String, nullable=False)
    priority = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    machine = relationship("Machine", back_populates="capabilities")


class MachineSpeed(Base):
    __tablename__ = 'machine_speeds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey('machines.id'), nullable=False)
    material_group_code = Column(String, nullable=False)
    size_category = Column(String, nullable=False)
    speed_value = Column(Float, nullable=False)

    machine = relationship("Machine", back_populates="speeds")


class ProcessDefinition(Base):
    __tablename__ = 'process_definitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_id = Column(String, nullable=True)
    process_name = Column(String, nullable=False)
    product_type = Column(String, nullable=True)
    step_order = Column(Integer, nullable=False)
    capability_required = Column(String, nullable=False)
    notes = Column(String, nullable=True)


class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String, nullable=False)
    project_code = Column(String, nullable=False, unique=True)
    hexcode = Column(String, nullable=True)
    notes = Column(String, nullable=True)


# ─── NEW Models (replacing Streamlit session_state) ──────────────────

class JobQueue(Base):
    """Replaces st.session_state.jobs_queue — persistent job queue."""
    __tablename__ = 'job_queue'
    id = Column(String, primary_key=True)  # e.g. "PRJ001.1_abc_1234"
    project_name = Column(String, nullable=True)
    project_code = Column(String, nullable=True)
    hexcode = Column(String, nullable=True)
    material_group = Column(String, nullable=False, default="C")
    process_steps = Column(Integer, default=1)
    size_mm = Column(Float, default=1000.0)
    detail_len_mm = Column(Float, nullable=True)
    complexity = Column(Float, default=0.0)
    quantity = Column(Integer, default=1)
    manual_setup_time = Column(Integer, nullable=True)
    operations = Column(JSON, nullable=True)  # list of capability strings
    process = Column(String, nullable=True)
    process_machine = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String, default="Bình thường")
    status = Column(String, default="queued")  # queued | scheduled | completed
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledOperation(Base):
    """Replaces st.session_state.scheduled_jobs — persistent schedule results."""
    __tablename__ = 'scheduled_operations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_version = Column(Integer, default=1)  # track which schedule batch
    job_id = Column(String, nullable=False)
    op_idx = Column(Integer, default=0)
    machine = Column(String, nullable=False)
    start = Column(Integer, nullable=False)  # minutes from 07:00
    finish = Column(Integer, nullable=False)
    setup = Column(Integer, default=0)
    note = Column(String, nullable=True)
    worker_status = Column(String, default="pending")  # pending | accepted | paused | completed
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduleConfig(Base):
    """Stores metadata/settings for the active schedule (e.g. overtime)."""
    __tablename__ = 'schedule_config'
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_version = Column(Integer, ForeignKey('scheduled_operations.schedule_version'))
    overtime_enabled = Column(Integer, default=0) # 0 or 1
    overtime_end_mins = Column(Integer, default=510) # minutes from 07:00
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Helpers ─────────────────────────────────────────────────────────

def get_engine(db_url: str = 'sqlite:///master_data_v2.db'):
    return create_engine(db_url, echo=False)


def init_db(engine):
    """Create all tables (safe to call multiple times)."""
    Base.metadata.create_all(engine)
