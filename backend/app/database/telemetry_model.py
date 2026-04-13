from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime
from .models import Base

class MLProductionLog(Base):
    """
    Hidden table for Machine Learning data collection.
    Captured silently when workers perform actions.
    """
    __tablename__ = 'ml_production_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, nullable=False)
    machine_id = Column(String, nullable=False)
    
    # Feature set (Copied from JobQueue at capture time)
    material_group = Column(String)
    size_mm = Column(Float)
    complexity = Column(Float)
    process_name = Column(String)
    
    # Timing Predictions (from Schedule)
    predicted_duration_min = Column(Float)
    predicted_setup_min = Column(Float)
    
    # Actual Timing (Ground Truth)
    actual_start_time = Column(DateTime, default=datetime.utcnow)
    actual_finish_time = Column(DateTime, nullable=True)
    actual_duration_min = Column(Float, nullable=True)
    
    # Metadata
    is_paused = Column(Integer, default=0) # Flag if job was ever paused (per user request: just flag it)
    status = Column(String, default="started") # started | completed
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MLProductionLog job={self.job_id} dur={self.actual_duration_min}>"
