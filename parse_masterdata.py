
import pandas as pd
import json
import shutil
import os

def parse_master_data():
    print("--- 1. CHUẨN BỊ FILE DỮ LIỆU ---")
    src = "data/MASTERDATA.csv"
    dst = "data/temp_master.xlsx"
    
    # Sao chép sang xlsx để đáp ứng yêu cầu engine nếu cần
    shutil.copy(src, dst)
    print(f"Đọc từ {dst}...")

    try:
        # Tải các Sheet
        df_mat = pd.read_excel(dst, sheet_name='MATERIALS')
        df_mac = pd.read_excel(dst, sheet_name='MACHINES')
        df_cap = pd.read_excel(dst, sheet_name='MACHINE_CAPABILITIES')
        df_spd = pd.read_excel(dst, sheet_name='PROCESSING_SPEEDS')
        
        # 1. Xây dựng Bản đồ Vật liệu
        # 1000... -> A
        print("--- 2. XÂY DỰNG BẢN ĐỒ VẬT LIỆU ---")
        materials_map = dict(zip(df_mat['material_code'].astype(str), df_mat['material_group']))
        print(f"Đã ánh xạ {len(materials_map)} vật liệu.")
        
        # 2. Xây dựng Dict Máy
        print("--- 3. XÂY DỰNG DỮ LIỆU MÁY ---")
        machines = {}
        
        # Khởi tạo
        for _, row in df_mac.iterrows():
            m_id = row['machine_id']
            status = 'On'
            if 'status' in df_mac.columns:
                val = row['status']
                if pd.notna(val):
                    status = str(val).strip()
            
            machines[m_id] = {
                "name": row['machine_name'],
                "type": row['machine_type'],
                "status": status,
                "capabilities": [],
                "speed_matrix": {}
            }
            
        # Thêm Khả năng
        for _, row in df_cap.iterrows():
            m_id = row['machine_id']
            if m_id in machines:
                machines[m_id]['capabilities'].append(row['op_type'])
                
        # Thêm Tốc độ
        # Cấu trúc: speed_matrix[Group][SizeCode] = Speed
        for _, row in df_spd.iterrows():
            m_id = row['machine_id']
            grp = row['material_group']
            size = row['size_code']
            speed = row['speed_mm_per_min']
            
            if m_id in machines:
                if grp not in machines[m_id]['speed_matrix']:
                    machines[m_id]['speed_matrix'][grp] = {}
                
                machines[m_id]['speed_matrix'][grp][size] = float(speed)
        
        # 4. Xây dựng Dữ liệu Process Templates
        print("--- 4. XÂY DỰNG PROCESS TEMPLATES ---")
        df_tmpl = pd.read_excel(dst, sheet_name='PROCESS_TEMPLATES')
        process_map = {}
        for _, row in df_tmpl.iterrows():
            # Combine process name and product type for display
            key = f"{row['process_name']} ({row['product_type']})"
            # Extract list of operations
            if pd.notna(row['op_sequence']):
                steps = [op.strip() for op in str(row['op_sequence']).split('→')]
            else:
                steps = ["Cut_straight"] # Default fallback
            process_map[key] = steps
            
        print(f"Đã ánh xạ {len(process_map)} quy trình.")

        # 5. Lưu thành JSON
        final_data = {
            "materials_map": materials_map,
            "machines": machines,
            "process_map": process_map
        }
        
        output_path = 'cleaned_master_data.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
            
        print(f"--- THÀNH CÔNG: Đã lưu vào {output_path} ---")
        print(f"Máy: {list(machines.keys())}")
        
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: {e}")
    finally:
        if os.path.exists(dst):
            os.remove(dst)

if __name__ == "__main__":
    parse_master_data()
