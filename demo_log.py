
import pandas as pd
import numpy as np
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_synthetic_log(num_jobs=50):
    data = []
    
    # Material Groups
    # Hard/Complex: I, L, K (Granite, Quartzite)
    # Easy/Standard: A, B, C, F (Marble, Soft Stone)
    materials_hard = ['I', 'L', 'K']
    materials_easy = ['A', 'B', 'C', 'F']
    
    for i in range(num_jobs):
        job_id = f'JOB_{i+1:03d}'
        
        # Randomly assign attributes
        # 40% Chance of being a "Hard" job (Complex case)
        is_hard_case = random.random() < 0.4
        
        if is_hard_case:
            # Case 1: Complex Job -> Expert likely better
            process_steps = random.randint(12, 16) # Long process
            material = random.choice(materials_hard)
            size_mm = random.randint(500, 3000)
            complexity_ratio = round(random.uniform(0.3, 0.8), 2) # High complexity (curved)
            
            # Simulation: GA standard makespan
            ga_makespan = random.randint(1000, 1500)
            
            # Expert uses "Tacit Knowledge" (e.g., knows machine X vibrates less for hard stone)
            # Expert improves by 10-15%
            improvement_factor = random.uniform(0.10, 0.15) 
            expert_makespan = int(ga_makespan * (1 - improvement_factor))
            
            better_expert = 1
            roi_improvement = round(improvement_factor, 3)
            note = f"Expert chose specific machine for {material} to avoid breakage"
            
        else:
            # Case 2: Simple Job -> GA likely better or Equal
            process_steps = random.randint(4, 10) # Short process
            material = random.choice(materials_easy)
            size_mm = random.randint(200, 1000)
            complexity_ratio = round(random.uniform(0.0, 0.2), 2) # Low complexity (straight)
            
            # Simulation
            ga_makespan = random.randint(400, 800)
            
            # Expert intervention might be unnecessary or slightly slower due to manual buffer
            # Expert worse by 0-5%
            worsen_factor = random.uniform(-0.05, 0.0)
            expert_makespan = int(ga_makespan * (1 - worsen_factor))
            
            better_expert = 0
            roi_improvement = round(worsen_factor, 3) # Negative means GA was better
            note = "GA Optimization sufficient for standard job"

        data.append({
            "job_id": job_id,
            "process_steps": process_steps,
            "material_group": material,
            "size_mm": size_mm,
            "dxf_complexity": complexity_ratio,
            "ga_makespan": ga_makespan,
            "expert_makespan": expert_makespan,
            "roi_improvement": roi_improvement,
            "better_expert": better_expert,
            "note": note
        })

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    print("Generating synthetic schedule logs...")
    df_log = generate_synthetic_log(100) # Generate 100 jobs
    
    output_path = "schedule_log.csv"
    df_log.to_csv(output_path, index=False)
    
    print(f"-> Saved {len(df_log)} records to {output_path}")
    print("\n--- SAMPLE DATA ---")
    print(df_log[["job_id", "material_group", "process_steps", "dxf_complexity", "roi_improvement", "better_expert"]].head(10))
    
    # Validation
    expert_wins = df_log[df_log['better_expert'] == 1].shape[0]
    print(f"\nStats: Expert Better in {expert_wins}/{len(df_log)} cases (Target ~40%)")
