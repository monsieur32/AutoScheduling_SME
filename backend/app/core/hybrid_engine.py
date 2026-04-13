"""
HybridEngine — adapted for Backend context.
Logic is identical to the original hybrid_engine.py,
only imports are changed to use the new package structure.
"""

import random
import json
import copy
import sys
import io
from .ml_module import FJSPML
from .ga_vns import GAVNSSolver

# Fix Windows console encoding for Vietnamese output
if sys.stdout and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


class HybridEngine:
    def __init__(self, machines_data: dict, ml_model_path: str = 'models'):
        """
        Khởi tạo HybridEngine.

        Parameters
        ----------
        machines_data : dict
            Dictionary of machine data pre-loaded from DB.
            Format: { machine_id: { name, type, status, capabilities, speed_matrix } }
        ml_model_path : str
            Path to directory containing trained ML model files.
        """
        self.master_data = {'machines': machines_data}
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
                        log.append(
                            f"Job {job['id']}: Luật chuyên gia ML -> Ưu tiên Cao & Chế độ An toàn "
                            f"(ROI +{prediction['predicted_roi']:.1%})"
                        )

        return adjusted_jobs, log

    def find_suitable_machines(self, is_complex):
        candidates = []
        required_cap = "Cut_contour" if is_complex else "Cut_straight"

        for m_id, m_data in self.master_data['machines'].items():
            if required_cap in m_data.get('capabilities', []):
                candidates.append(m_id)

        return candidates

    def calculate_duration(self, machine_id, material_group, size_mm):
        m_data = self.master_data['machines'].get(machine_id)
        if not m_data:
            return 60

        if size_mm < 200:
            size_cat = "LT_200"
        elif size_mm < 400:
            size_cat = "B200_400"
        elif size_mm < 600:
            size_cat = "B400_600"
        else:
            size_cat = "GT_600"

        speed = m_data.get('speed_matrix', {}).get(material_group, {}).get(size_cat, 500.0)
        return int(size_mm / speed) + 5

    def run_ga_simulation(self, jobs, initial_machine_avail=None, initial_machine_last_job=None, overtime_config=None):
        print("Starting GA-VNS Optimizer...")
        solver = GAVNSSolver(
            jobs=jobs,
            machines_data=self.master_data['machines'],
            calculate_duration_fn=self.calculate_duration,
            pop_size=50,
            max_gen=50,
            tightness_factor=1.5,
            initial_machine_avail=initial_machine_avail,
            initial_machine_last_job=initial_machine_last_job,
            overtime_config=overtime_config
        )
        options = solver.solve()

        # Định dạng note
        for opt in options:
            for s in opt['schedule']:
                job_info = next((j for j in jobs if j['id'] == s['job_id']), {})
                s['note'] = "Expert Intervention" if job_info.get('priority') == 'HIGH' else "Standard GA-VNS"

        return options

    def solve(self, input_jobs, use_ml=True, initial_machine_avail=None, initial_machine_last_job=None, overtime_config=None):
        print("--- PHASE 1: HYBRID PRE-PROCESSING ---")
        itemized_jobs, logs = self.apply_expert_constraints(input_jobs, use_ml=use_ml)
        for l in logs:
            print(l)

        print("\n--- PHASE 2: GENETIC ALGORITHM OPTIMIZATION ---")
        options = self.run_ga_simulation(
            itemized_jobs,
            initial_machine_avail=initial_machine_avail,
            initial_machine_last_job=initial_machine_last_job,
            overtime_config=overtime_config
        )
        print(f"Optimization Complete. Generated {len(options)} options.")

        return options
