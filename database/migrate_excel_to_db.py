import pandas as pd
import os
import shutil
from sqlalchemy.orm import sessionmaker
from models import get_engine, init_db, Material, Machine, MachineCapability, MachineSpeed, ProcessDefinition

def migrate_from_excel():
    src_path = '../data/MASTERDATA.csv'
    temp_path = '../data/temp_master.xlsx'
    db_path = 'sqlite:///../master_data_v2.db'

    if not os.path.exists(src_path):
        print(f"Error: Could not find {src_path}")
        return

    # Use the same parse_masterdata tactic to copy to xlsx
    shutil.copy(src_path, temp_path)
    
    print("Initializing Database...")
    engine = get_engine(db_path)
    init_db(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing
        session.query(Material).delete()
        session.query(MachineCapability).delete()
        session.query(MachineSpeed).delete()
        session.query(Machine).delete()
        session.query(ProcessDefinition).delete()

        # Load sheets
        df_mat = pd.read_excel(temp_path, sheet_name='MATERIALS')
        df_mac = pd.read_excel(temp_path, sheet_name='MACHINES')
        df_cap = pd.read_excel(temp_path, sheet_name='MACHINE_CAPABILITIES')
        df_spd = pd.read_excel(temp_path, sheet_name='PROCESSING_SPEEDS')
        df_tmpl = pd.read_excel(temp_path, sheet_name='PROCESS_TEMPLATES')

        # 1. Materials
        print("Migrating Materials...")
        for _, row in df_mat.iterrows():
            mat = Material(
                id=str(row['material_code']).strip(),
                material_name=str(row['material_name']) if pd.notna(row['material_name']) else None,
                material_type=str(row['material_type']) if pd.notna(row['material_type']) else None,
                group_code=str(row['material_group']).strip(),
                notes=str(row['notes']) if pd.notna(row['notes']) else None
            )
            session.add(mat)

        # 2. Machines
        print("Migrating Machines...")
        machine_map = {} # to save objects for relationships
        for _, row in df_mac.iterrows():
            m_id = str(row['machine_id']).strip()
            status = 'On'
            if 'status' in df_mac.columns and pd.notna(row['status']):
                status = str(row['status']).strip()

            mac = Machine(
                id=m_id,
                name=str(row['machine_name']).strip() if pd.notna(row['machine_name']) else "Unknown",
                machine_type=str(row['machine_type']).strip() if pd.notna(row['machine_type']) else "Unknown",
                status=status,
                max_size_mm=str(row['max_size_mm']).strip() if pd.notna(row.get('max_size_mm')) else None,
                notes=str(row['notes']) if 'notes' in row and pd.notna(row['notes']) else None
            )
            session.add(mac)
            machine_map[m_id] = mac

        # 3. Machine Capabilities
        print("Migrating Machine Capabilities...")
        for _, row in df_cap.iterrows():
            m_id = str(row['machine_id']).strip()
            if m_id in machine_map:
                cap = MachineCapability(
                    machine=machine_map[m_id],
                    capability_name=str(row['op_type']).strip(),
                    priority=int(row['priority']) if 'priority' in row and pd.notna(row['priority']) else None,
                    notes=str(row['notes']) if 'notes' in row and pd.notna(row['notes']) else None
                )
                session.add(cap)

        # 4. Processing Speeds
        print("Migrating Processing Speeds...")
        for _, row in df_spd.iterrows():
            m_id = str(row['machine_id']).strip()
            if m_id in machine_map:
                spd = MachineSpeed(
                    machine=machine_map[m_id],
                    material_group_code=str(row['material_group']).strip(),
                    size_category=str(row['size_code']).strip(),
                    speed_value=float(row['speed_mm_per_min'])
                )
                session.add(spd)

        # 5. Process Templates
        print("Migrating Process Templates...")
        for _, row in df_tmpl.iterrows():
            proc_id = str(row['process_id']).strip() if pd.notna(row.get('process_id')) else None
            proc_name = str(row['process_name']).strip() if pd.notna(row.get('process_name')) else "Unknown"
            prod_type = str(row['product_type']).strip() if pd.notna(row.get('product_type')) else None
            notes = str(row['notes']).strip() if pd.notna(row.get('notes')) else None
            
            # process name used to combined with product_type in json:
            display_name = f"{proc_name} ({prod_type})" if prod_type else proc_name
            
            if pd.notna(row.get('op_sequence')):
                steps = [op.strip() for op in str(row['op_sequence']).split('→')]
            else:
                steps = ["Cut_straight"]
            
            for idx, capability in enumerate(steps):
                proc_def = ProcessDefinition(
                    process_id=proc_id,
                    process_name=display_name, # Giữ nguyên format tên gộp để UI chạy ổn
                    product_type=prod_type,
                    step_order=idx + 1,
                    capability_required=capability,
                    notes=notes
                )
                session.add(proc_def)

        session.commit()
        print("Successfully migrated all data directly from Excel to SQLite!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    migrate_from_excel()
