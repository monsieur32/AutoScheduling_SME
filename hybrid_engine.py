
import random
import json
import copy
from ml_module import FJSPML
from ga_vns import GAVNSSolver
from database.models import get_engine, Machine
from sqlalchemy.orm import sessionmaker

class HybridEngine:
    def __init__(self, db_path='sqlite:///master_data_v2.db', ml_model_path='models'):
        engine = get_engine(db_path)
        Session = sessionmaker(bind=engine)
        session = Session()

        self.master_data = {'machines': {}}
        
        # Pull all machines and relationships into dictionary to maintain compatibility with GA_VNS
        machines_db = session.query(Machine).all()
        for m in machines_db:
            caps = [c.capability_name for c in m.capabilities]
            speed_matrix = {}
            for s in m.speeds:
                if s.material_group_code not in speed_matrix:
                    speed_matrix[s.material_group_code] = {}
                speed_matrix[s.material_group_code][s.size_category] = s.speed_value
                
            self.master_data['machines'][m.id] = {
                'name': m.name,
                'type': m.machine_type,
                'status': m.status,
                'capabilities': caps,
                'speed_matrix': speed_matrix
            }
            
        session.close()
        
        self.ml = FJSPML(model_path=ml_model_path)
        self.ml.load_models()
        
    def apply_expert_constraints(self, jobs, use_ml=True):
        adjusted_jobs = copy.deepcopy(jobs)
        log = []
        
        for job in adjusted_jobs:

            ml_input = {
                "process_steps": len(job.get('operations', [])),
                "material_group": job.get('material_group', 'C'),
                "size_mm": job.get('size_mm', 1000),
                "dxf_complexity": job.get('complexity', 0.1)
            }
            
            # 1. Kiểm tra DXF
            if job.get('complexity', 0) > 0.3:
                 job['constraints'] = ['Waterjet', 'CNC']
                 log.append(f"Job {job['id']}: Dị hình phức tạp -> Giới hạn máy Waterjet/CNC")
                 continue
            
            # 2. Dự đoán ML
            if use_ml:
                prediction = self.ml.predict_adjust(ml_input)
                
                if prediction.get('use_expert_rule'):

                    if ml_input['material_group'] in ['I', 'L', 'K']:
                        job['priority'] = 'HIGH'
                        job['slow_mode'] = True
                        log.append(f"Job {job['id']}: Luật chuyên gia ML -> Ưu tiên Cao & Chế độ An toàn (ROI +{prediction['predicted_roi']:.1%})")
            
        return adjusted_jobs, log

    def find_suitable_machines(self, is_complex):
        """
        Lọc máy dựa trên năng lực.
        is_complex = True -> Yêu cầu "Cut_contour" (Waterjet/CNC)
        is_complex = False -> Yêu cầu "Cut_straight" (Cắt Cầu)
        """
        candidates = []
        required_cap = "Cut_contour" if is_complex else "Cut_straight"
        
        for m_id, m_data in self.master_data['machines'].items():
            if required_cap in m_data.get('capabilities', []):
                candidates.append(m_id)
                
        return candidates

    def calculate_duration(self, machine_id, material_group, size_mm):
        m_data = self.master_data['machines'].get(machine_id)
        if not m_data: return 60
        # Xác định nhóm kích thước (Mã mới)
        if size_mm < 200: size_cat = "LT_200"
        elif size_mm < 400: size_cat = "B200_400"
        elif size_mm < 600: size_cat = "B400_600"
        else: size_cat = "GT_600"
        
        # Lấy tốc độ
        speed = m_data.get('speed_matrix', {}).get(material_group, {}).get(size_cat, 500.0)
        
        # Thời gian = Chiều dài / Tốc độ
        # Thêm 5 phút thời gian gá đặt
        return int(size_mm / speed) + 5

    def run_ga_simulation(self, jobs, initial_machine_avail=None, initial_machine_last_job=None):
        """
        Sử dụng thuật toán GA-VNS để thay thế cho mô phỏng Greedy cũ.
        """
        print("Starting GA-VNS Optimizer...")
        solver = GAVNSSolver(
            jobs=jobs,
            machines_data=self.master_data['machines'],
            calculate_duration_fn=self.calculate_duration,
            pop_size=50,  # Giảm xuống 50 để chạy nhanh trên UI
            max_gen=50,   # Giảm xuống 50 thế hệ
            tightness_factor=1.5,
            initial_machine_avail=initial_machine_avail,
            initial_machine_last_job=initial_machine_last_job
        )
        options = solver.solve()
        
        # Định dạng lại note cho schedule nếu priority cao
        for opt in options:
            for s in opt['schedule']:
                job_info = next((j for j in jobs if j['id'] == s['job_id']), {})
                s['note'] = "Expert Intervention" if job_info.get('priority') == 'HIGH' else "Standard GA-VNS"

        return options

    def solve(self, input_jobs, use_ml=True, initial_machine_avail=None, initial_machine_last_job=None):
        print("--- PHASE 1: HYBRID PRE-PROCESSING ---")
        itemized_jobs, logs = self.apply_expert_constraints(input_jobs, use_ml=use_ml)
        for l in logs:
            print(l)
            
        print("\n--- PHASE 2: GENETIC ALGORITHM OPTIMIZATION ---")
        options = self.run_ga_simulation(
            itemized_jobs, 
            initial_machine_avail=initial_machine_avail, 
            initial_machine_last_job=initial_machine_last_job
        )
        print(f"Optimization Complete. Generated {len(options)} options.")
        
        return options

if __name__ == "__main__":
    # Test Data simulating real input from App/Excel
    test_jobs = [
        {"id": "J001", "material_group": "A", "size_mm": 500, "complexity": 0.0, "operations": [1,2,3]}, # Easy
        {"id": "J002", "material_group": "I", "size_mm": 2500, "complexity": 0.1, "operations": [1]*14}, # Hard Material
        {"id": "J003", "material_group": "C", "size_mm": 1200, "complexity": 0.5, "operations": [1,2]}, # Complex Shape
    ]
    
    engine = HybridEngine()
    final_schedule = engine.solve(test_jobs)
    
    print("\n--- FINAL SCHEDULE ---")
    import pandas as pd
    print(pd.DataFrame(final_schedule))
