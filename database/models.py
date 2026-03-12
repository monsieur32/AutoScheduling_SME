from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Material(Base):
    __tablename__ = 'materials'
    id = Column(String, primary_key=True)  # material_code
    material_name = Column(String, nullable=True)
    material_type = Column(String, nullable=True)
    group_code = Column(String, nullable=False) # material_group
    notes = Column(String, nullable=True)

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(String, primary_key=True) # machine_id
    name = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
    status = Column(String, default="On")
    max_size_mm = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    # Quan hệ 1-Nhiều với Capabilities và Speeds
    capabilities = relationship("MachineCapability", back_populates="machine", cascade="all, delete-orphan")
    speeds = relationship("MachineSpeed", back_populates="machine", cascade="all, delete-orphan")

class MachineCapability(Base):
    __tablename__ = 'machine_capabilities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey('machines.id'), nullable=False)
    capability_name = Column(String, nullable=False) # op_type
    priority = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    
    machine = relationship("Machine", back_populates="capabilities")

class MachineSpeed(Base):
    __tablename__ = 'machine_speeds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, ForeignKey('machines.id'), nullable=False)
    material_group_code = Column(String, nullable=False)
    size_category = Column(String, nullable=False) # LT_200, B200_400...
    speed_value = Column(Float, nullable=False)
    
    machine = relationship("Machine", back_populates="speeds")

class ProcessDefinition(Base):
    __tablename__ = 'process_definitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_id = Column(String, nullable=True)
    process_name = Column(String, nullable=False) 
    product_type = Column(String, nullable=True)
    step_order = Column(Integer, nullable=False)
    capability_required = Column(String, nullable=False) # op_type
    notes = Column(String, nullable=True)

# Helper function để lấy engine
def get_engine(db_path='sqlite:///master_data_v2.db'):
    return create_engine(db_path)

def init_db(engine):
    Base.metadata.create_all(engine)
