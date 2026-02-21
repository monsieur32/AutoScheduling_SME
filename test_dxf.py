
import os
import glob
from dxf_parser import extract_cutting_info

# Initial directory
dxf_dir = r"c:\Users\32ngu\Desktop\AutoScheduling_SME-main\AutoScheduling_SME-main\designs"

# Find DXF files
dxf_files = glob.glob(os.path.join(dxf_dir, "*.dxf"))

print(f"Found {len(dxf_files)} DXF files.")

results = []
for f in dxf_files[:5]: # Test first 5 files
    print(f"Processing: {os.path.basename(f)}...")
    info = extract_cutting_info(f)
    results.append(info)
    
    if info['status'] == 'success':
        print(f" -> Total: {info['total_len_mm']} mm")
        print(f" -> Straight: {info['straight_len_mm']} mm | Curved: {info['curved_len_mm']} mm")
        print(f" -> Complexity Ratio: {info['complexity_ratio']}")
        
        # Simple Machine Suggestion Logic
        machine_type = "MAY CAT CAU (Bridge Saw)"
        if info['complexity_ratio'] > 0.1: # If >10% is curved
            machine_type = "MAY TIA NUOC (Waterjet) / CNC"
        
        print(f" -> GOI Y: {machine_type}")
    else:
        print(f" -> Error: {info['message']}")
        
    print("-" * 30)

# Simulate Processing Time Calculation
# Assume Bridge Saw = 500 mm/min (Fast), Waterjet = 150 mm/min (Slow)
SPEED_BRIDGE_SAW = 500
SPEED_WATERJET = 150

print("\n--- ESTIMATED TIME & MACHINE ---")
for r in results:
    if r['status'] == 'success':
        ratio = r['complexity_ratio']
        total = r['total_len_mm']
        
        if ratio > 0.1:
            mech = "WATERJET"
            speed = SPEED_WATERJET
        else:
            mech = "BRIDGE SAW"
            speed = SPEED_BRIDGE_SAW
            
        est_time = total / speed
        print(f"File: {os.path.basename(r['filename'])}")
        print(f"  Machine: {mech} (Speed: {speed} mm/min)")
        print(f"  Est. Time: {round(est_time, 1)} min")