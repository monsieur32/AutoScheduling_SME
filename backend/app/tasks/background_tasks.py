"""
Background task definitions for heavy computations.
Each task function receives (task_token, task_manager, ...) as first args.
"""

import os
import sys
import io
import copy
from typing import List, Dict, Optional, Any

from .task_manager import TaskManager
from ..core.hybrid_engine import HybridEngine
from ..core.dxf_parser import extract_cutting_info
from ..database.session import get_db_context
from ..database.models import Machine, MachineCapability, MachineSpeed, JobQueue, ScheduledOperation
from ..config import ML_MODEL_DIR

# Fix Windows console encoding for Vietnamese characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from ..database.session import get_db_context
from ..database.models import Machine, MachineCapability, MachineSpeed, JobQueue, ScheduledOperation
from ..config import ML_MODEL_DIR


def _load_machines_data_from_db() -> dict:
    """Helper: Load machine master-data dict from DB (same format as original HybridEngine)."""
    machines_data = {}
    with get_db_context() as db:
        machines = db.query(Machine).all()
        for m in machines:
            caps = [c.capability_name for c in m.capabilities]
            speed_matrix = {}
            for s in m.speeds:
                if s.material_group_code not in speed_matrix:
                    speed_matrix[s.material_group_code] = {}
                speed_matrix[s.material_group_code][s.size_category] = s.speed_value

            machines_data[m.id] = {
                'name': m.name,
                'type': m.machine_type,
                'status': m.status,
                'capabilities': caps,
                'speed_matrix': speed_matrix,
            }
    return machines_data


def parse_dxf_task(task_token: str, tm: TaskManager, file_paths: List[str]) -> list:
    """
    Background task: Parse one or more DXF files.
    Returns list of parse results (one per file).
    """
    results = []
    total = len(file_paths)

    for i, path in enumerate(file_paths):
        tm.update_progress(task_token, i / total)
        info = extract_cutting_info([path])
        results.append({
            "filename": os.path.basename(path),
            **info,
        })

    tm.update_progress(task_token, 1.0)
    return results


def schedule_run_task(
    task_token: str,
    tm: TaskManager,
    jobs: List[dict],
    use_ml: bool = True,
    initial_machine_avail: Optional[Dict[str, int]] = None,
    initial_machine_last_job: Optional[Dict[str, Optional[str]]] = None,
    overtime_config: Optional[Dict[str, Any]] = None,
) -> list:
    """
    Background task: Run HybridEngine + GA-VNS.
    Returns list of 3 schedule options.
    """

    tm.update_progress(task_token, 0.1)

    # Load machines data from DB
    machines_data = _load_machines_data_from_db()
    tm.update_progress(task_token, 0.2)

    # Create engine with pre-loaded data
    engine = HybridEngine(machines_data=machines_data, ml_model_path=ML_MODEL_DIR)
    tm.update_progress(task_token, 0.3)

    # Run solver
    options = engine.solve(
        jobs,
        use_ml=use_ml,
        initial_machine_avail=initial_machine_avail,
        initial_machine_last_job=initial_machine_last_job,
        overtime_config=overtime_config,
    )
    tm.update_progress(task_token, 1.0)

    return {
        "options": options,
        "overtime_config": overtime_config
    }
