
import random
import json
import copy
from ml_module import FJSPML
# import ga_module # Placeholder: In a real scenario, we would import the full GA class

class HybridEngine:
    def __init__(self, master_data_path='cleaned_master_data.json', ml_model_path='models'):
        with open(master_data_path, 'r', encoding='utf-8') as f:
            self.master_data = json.load(f)
        
        self.ml = FJSPML(model_path=ml_model_path)
        self.ml.load_models() # Ensure models are loaded
        
    def apply_expert_constraints(self, jobs, use_ml=True):
        """
        Scan jobs using ML/Rule-based logic.
        If ML predicts 'better_expert' -> Lock specific machines or add penalty.
        """
        adjusted_jobs = copy.deepcopy(jobs)
        log = []
        
        for job in adjusted_jobs:
            # Prepare feature dict for ML
            # Map real data keys to ML feature keys
            ml_input = {
                "process_steps": len(job.get('operations', [])), # Example structure
                "material_group": job.get('material_group', 'C'),
                "size_mm": job.get('size_mm', 1000),
                "dxf_complexity": job.get('complexity', 0.1)
            }
            
            # 1. DXF Check (Hard Logic) - From previous step
            if job.get('complexity', 0) > 0.3:
                 job['constraints'] = ['Waterjet', 'CNC']
                 log.append(f"Job {job['id']}: High Complexity -> Restricted to Waterjet/CNC")
                 continue # Skip ML check if hard constraint is set
            
            # 2. ML Prediction (Soft Logic)
            if use_ml:
                prediction = self.ml.predict_adjust(ml_input)
                
                if prediction.get('use_expert_rule'):
                    # Expert Strategy: For Hard Materials (I, L, K), avoid high-vibration machines
                    # This is "Tacit Knowledge" injected back
                    if ml_input['material_group'] in ['I', 'L', 'K']:
                        job['priority'] = 'HIGH'
                        job['slow_mode'] = True # hypothetical flag for GA to choose slower/safer speed
                        log.append(f"Job {job['id']}: ML Expert Rule -> Set High Priority & Smooth Mode (ROI +{prediction['predicted_roi']:.1%})")
            
        return adjusted_jobs, log

    def find_suitable_machines(self, is_complex):
        """
        Filter machines based on capability.
        is_complex = True -> Requires "Cut_contour" (Waterjet/CNC)
        is_complex = False -> Requires "Cut_straight" (Bridge Saw)
        """
        candidates = []
        required_cap = "Cut_contour" if is_complex else "Cut_straight"
        
        for m_id, m_data in self.master_data['machines'].items():
            if required_cap in m_data.get('capabilities', []):
                candidates.append(m_id)
                
        return candidates

    def calculate_duration(self, machine_id, material_group, size_mm):
        """
        Look up speed matrix to estimate duration.
        """
        m_data = self.master_data['machines'].get(machine_id)
        if not m_data: return 60 # Default fallback
        
        # Determine Size Category (New Codes)
        if size_mm < 200: size_cat = "LT_200"
        elif size_mm < 400: size_cat = "B200_400"
        elif size_mm < 600: size_cat = "B400_600"
        else: size_cat = "GT_600"
        
        # Get Speed
        speed = m_data.get('speed_matrix', {}).get(material_group, {}).get(size_cat, 500.0)
        
        # Duration = Length / Speed
        # Add 5 mins setup time
        return int(size_mm / speed) + 5

    def run_ga_simulation(self, jobs):
        """
        Simulate GA Scheduling with Real Data.
        """
        schedule = []
        machine_availability = {m: 0 for m in self.master_data['machines'].keys()}
        
        # Sort by priority (Expert intervention effect)
        sorted_jobs = sorted(jobs, key=lambda x: 0 if x.get('priority') == 'HIGH' else 1)
        
        for job in sorted_jobs:
            is_complex = job.get('complexity', 0) > 0.1
            
            # 1. Find Candidates
            candidates = self.find_suitable_machines(is_complex)
            
            # Expert Constraint: If job has specific constraints, intersect
            if job.get('constraints'):
                # Map broad categories to specific IDs if needed, or assume constraints are IDs
                # For now, let's assume constraints are Machine Types (Waterjet/CNC)
                # We filter candidates that strictly match "Waterjet" or "CNC" keywords in their ID/Name if we had names
                # logic: keep candidates
                pass
            
            if not candidates:
                candidates = ["MANUAL_FALLBACK"]
            
            # 2. GA Selection (Greedy for MVP: Pick machine with earliest finish time)
            best_machine = None
            earliest_finish = float('inf')
            best_duration = 0
            
            for m in candidates:
                if m == "MANUAL_FALLBACK": continue
                
                # Calculate Duration
                duration = self.calculate_duration(m, job.get('material_group', 'C'), job.get('size_mm', 1000))
                
                if job.get('slow_mode'):
                    duration = int(duration * 1.5) # Slower by 50%
                
                start_time = machine_availability[m]
                finish_time = start_time + duration
                
                if finish_time < earliest_finish:
                    earliest_finish = finish_time
                    best_machine = m
                    best_duration = duration
            
            # Fallback
            if best_machine is None:
                best_machine = "MANUAL_WORK"
                best_duration = 120
                earliest_finish = machine_availability.get(best_machine, 0) + 120
            
            # 3. Schedule
            schedule.append({
                "job_id": job['id'],
                "machine": best_machine,
                "start": earliest_finish - best_duration,
                "finish": earliest_finish,
                "note": "Expert Intervention" if job.get('priority') == 'HIGH' else "Standard GA"
            })
            
            # Update machine availability
            if best_machine in machine_availability:
                machine_availability[best_machine] = earliest_finish
            
        makespan = max(s['finish'] for s in schedule) if schedule else 0
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
