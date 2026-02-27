
import random
import json
import copy
from ml_module import FJSPML
from ga_vns import GAVNSSolver

class HybridEngine:
    def __init__(self, master_data_path='cleaned_master_data.json', ml_model_path='models'):
        with open(master_data_path, 'r', encoding='utf-8') as f:
            self.master_data = json.load(f)
        
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

    def run_ga_simulation(self, jobs):
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
            tightness_factor=1.5
        )
        schedule = solver.solve()
        
        makespan = max((s['finish'] for s in schedule), default=0)
        
        # Định dạng lại note cho schedule nếu priority cao
        for s in schedule:
            job_info = next((j for j in jobs if j['id'] == s['job_id']), {})
            s['note'] = "Expert Intervention" if job_info.get('priority') == 'HIGH' else "Standard GA-VNS"

        return schedule, makespan

    def solve(self, input_jobs, use_ml=True):
        print("--- PHASE 1: HYBRID PRE-PROCESSING ---")
        itemized_jobs, logs = self.apply_expert_constraints(input_jobs, use_ml=use_ml)
        for l in logs:
            print(l)
            
        print("\n--- PHASE 2: GENETIC ALGORITHM OPTIMIZATION ---")
        schedule, makespan = self.run_ga_simulation(itemized_jobs)
        print(f"Optimization Complete. Makespan: {makespan} mins")
        
        return schedule

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
