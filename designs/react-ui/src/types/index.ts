// =============================================
// TypeScript Interfaces — mapping 1:1 với database/models.py
// =============================================

export interface Project {
  id: number;
  project_name: string;
  project_code: string;
  hexcode: string | null;
  notes: string | null;
}

export interface Material {
  id: string;
  material_name: string;
  material_type: string;
  group_code: string;
  notes: string | null;
}

export interface Machine {
  id: string;
  name: string;
  machine_type: string;
  status: 'On' | 'Off' | 'Maintenance';
  max_size_mm: string | null;
  notes: string | null;
}

export interface MachineCapability {
  id: number;
  machine_id: string;
  capability_name: string;
  priority: number | null;
  notes: string | null;
}

export interface MachineSpeed {
  id: number;
  machine_id: string;
  material_group_code: string;
  size_category: string;
  speed_value: number;
}

export interface ProcessDefinition {
  id: number;
  process_id: string | null;
  process_name: string;
  product_type: string | null;
  step_order: number;
  capability_required: string;
  notes: string | null;
}

// =============================================
// UI State Interfaces — mapping với session_state trong main.py
// =============================================

export interface DxfInfo {
  status: 'success' | 'error';
  straight_len_mm: number;
  curved_len_mm: number;
  total_len_mm: number;
  complexity_ratio: number;
  texts: string[];
  warnings: string[];
  message?: string;
}

export interface JobData {
  id: string;
  project_name: string;
  project_code: string;
  hexcode: string | null;
  material_group: string;
  process_steps: number;
  size_mm: number;
  detail_len_mm: number;
  complexity: number;
  quantity: number;
  operations: string[];
  start_time: string;
  due_date: string;
  priority: string;
  process: string;
  process_machine: string;
}

export interface ScheduledJob {
  job_id: string;
  machine: string;
  start: number;
  finish: number;
  setup: number;
  op_idx: number;
  note: string;
  machine_status?: string;
}

export interface ScheduleOption {
  name: string;
  metrics: {
    makespan: number;
    setup: number;
  };
  schedule: ScheduledJob[];
}

// Process map: process_name -> capability_required list
export type ProcessMap = Record<string, string[]>;

// Capability -> machine list mapping
export type CapabilityMachineMap = Record<string, string[]>;
