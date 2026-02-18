
import pandas as pd
import json
import shutil
import os

def parse_master_data():
    print("--- 1. PREPARING DATA FILE ---")
    src = "data/MASTERDATA.csv"
    dst = "data/temp_master.xlsx"
    
    # Copy to xlsx to satisfy engine requirements if needed
    shutil.copy(src, dst)
    print(f"Read from {dst}...")

    try:
        # Load Sheets
        df_mat = pd.read_excel(dst, sheet_name='MATERIALS')
        df_mac = pd.read_excel(dst, sheet_name='MACHINES')
        df_cap = pd.read_excel(dst, sheet_name='MACHINE_CAPABILITIES')
        df_spd = pd.read_excel(dst, sheet_name='PROCESSING_SPEEDS')
        
        # 1. Build Materials Map
        # 1000... -> A
        print("--- 2. BUILDING MATERIALS MAP ---")
        materials_map = dict(zip(df_mat['material_code'].astype(str), df_mat['material_group']))
        print(f"Mapped {len(materials_map)} materials.")
        
        # 2. Build Machines Dict
        print("--- 3. BUILDING MACHINES DATA ---")
        machines = {}
        
        # Initialize
        for _, row in df_mac.iterrows():
            m_id = row['machine_id']
            machines[m_id] = {
                "name": row['machine_name'],
                "type": row['machine_type'],
                "capabilities": [],
                "speed_matrix": {}
            }
            
        # Add Capabilities
        for _, row in df_cap.iterrows():
            m_id = row['machine_id']
            if m_id in machines:
                machines[m_id]['capabilities'].append(row['op_type'])
                
        # Add Speeds
        # Structure: speed_matrix[Group][SizeCode] = Speed
        for _, row in df_spd.iterrows():
            m_id = row['machine_id']
            grp = row['material_group']
            size = row['size_code']
            speed = row['speed_mm_per_min']
            
            if m_id in machines:
                if grp not in machines[m_id]['speed_matrix']:
                    machines[m_id]['speed_matrix'][grp] = {}
                
                machines[m_id]['speed_matrix'][grp][size] = float(speed)
        
        # 3. Save to JSON
        final_data = {
            "materials_map": materials_map,
            "machines": machines
        }
        
        output_path = 'cleaned_master_data.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
            
        print(f"--- SUCCESS: Saved to {output_path} ---")
        print(f"Machines: {list(machines.keys())}")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    finally:
        if os.path.exists(dst):
            os.remove(dst)

if __name__ == "__main__":
    parse_master_data()
