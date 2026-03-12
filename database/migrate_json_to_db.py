import json
import os
from sqlalchemy.orm import sessionmaker
from models import get_engine, init_db, Material, Machine, MachineCapability, MachineSpeed, ProcessDefinition

def migrate_data():
    json_path = '../cleaned_master_data.json'
    db_path = 'sqlite:///../master_data.db'

    if not os.path.exists(json_path):
        print(f"Error: Could not find {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Initializing Database...")
    engine = get_engine(db_path)
    init_db(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing data (optional, for idempotency)
        session.query(Material).delete()
        session.query(MachineCapability).delete()
        session.query(MachineSpeed).delete()
        session.query(Machine).delete()
        session.query(ProcessDefinition).delete()

        # 1. Migrate Materials
        print("Migrating Materials...")
        materials_map = data.get('materials_map', {})
        material_objects = [
            Material(id=mat_id, group_code=group)
            for mat_id, group in materials_map.items()
        ]
        session.bulk_save_objects(material_objects)

        # 2. Migrate Machines, Capabilities, Speeds
        print("Migrating Machines...")
        machines_data = data.get('machines', {})
        for m_id, m_info in machines_data.items():
            machine = Machine(
                id=m_id,
                name=m_info.get('name', 'Unknown'),
                machine_type=m_info.get('type', 'Unknown'),
                status=m_info.get('status', 'active')
            )
            session.add(machine)
            
            # Capabilities
            for cap in m_info.get('capabilities', []):
                capability = MachineCapability(machine=machine, capability_name=cap)
                session.add(capability)

            # Speeds
            speed_matrix = m_info.get('speed_matrix', {})
            for mat_group, sizes in speed_matrix.items():
                for size_cat, speed_val in sizes.items():
                    speed = MachineSpeed(
                        machine=machine,
                        material_group_code=mat_group,
                        size_category=size_cat,
                        speed_value=speed_val
                    )
                    session.add(speed)

        # 3. Migrate Process Definitions
        print("Migrating Process Definitions...")
        process_map = data.get('process_map', {})
        for proc_name, steps in process_map.items():
            for idx, capability in enumerate(steps):
                proc_def = ProcessDefinition(
                    process_name=proc_name,
                    step_order=idx + 1,  # 1-based indexing
                    capability_required=capability
                )
                session.add(proc_def)

        # Commit transaction
        session.commit()
        print("Successfully migrated all data to SQLite Database!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred during migration: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_data()
