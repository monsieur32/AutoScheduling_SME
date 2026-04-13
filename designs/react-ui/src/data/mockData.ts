import type {
  Project, Material, Machine, MachineCapability,
  MachineSpeed, ProcessDefinition, JobData, ScheduledJob,
  ScheduleOption, ProcessMap, CapabilityMachineMap, DxfInfo
} from '../types';

// =============================================
// DỮ LIỆU THỰC TỪ DATABASE master_data_v2.db
// =============================================

export const projects: Project[] = [
  { id: 1, project_name: "VIN", project_code: "VIN2408", hexcode: "V-0302", notes: null },
  { id: 2, project_name: "VIN2", project_code: "VIN24082004", hexcode: "V-1234", notes: null }
];

export const machines: Machine[] = [
  { id: "CNCTNC0001", name: "WJ-01 (HEAD3020BA)", machine_type: "Waterjet", status: "On", max_size_mm: "3000x2000", notes: null },
  { id: "CNCTNC0002", name: "WJ-02 (HEAD3020BA-F)", machine_type: "Waterjet", status: "On", max_size_mm: "3000x2000", notes: null },
  { id: "CNCTNC0003", name: "WJ-03 (HEAD3020BA-F)", machine_type: "Waterjet", status: "Maintenance", max_size_mm: "3000x2000", notes: null },
  { id: "CNCTNC0004", name: "WJ-04 (HEAD3020BA-F)", machine_type: "Waterjet", status: "On", max_size_mm: "3000x2000", notes: null },
  { id: "CNCTNC0007", name: "WJ 5 trục", machine_type: "Waterjet_5axis", status: "On", max_size_mm: "3000x2000", notes: null },
  { id: "CNCCCC0001", name: "Cắt cầu 1", machine_type: "BridgeSaw", status: "On", max_size_mm: "3600x2400", notes: null },
  { id: "CNCCCC0002", name: "Cắt cầu 5 trục YQ5H-3624", machine_type: "BridgeSaw_5axis", status: "On", max_size_mm: "3600x2400", notes: null },
  { id: "CNCCCC0003", name: "Cắt cầu 5 trục YQ5H-3624-2", machine_type: "BridgeSaw_5axis", status: "On", max_size_mm: "3600x2400", notes: null },
  { id: "CNCTRT0001", name: "CMS-01", machine_type: "CNC_Router", status: "On", max_size_mm: "2500x1800", notes: null },
  { id: "CNCTRT0002", name: "MÁY CMS - 02 (TN-C/TN-S 8517)", machine_type: "CNC_Router", status: "On", max_size_mm: "2500x1800", notes: null },
  { id: "CATVTC0001", name: "Máy líp 45", machine_type: "Chamfer", status: "On", max_size_mm: null, notes: null }
];

export const machineCapabilities: MachineCapability[] = [
  { id: 1, machine_id: "CNCTNC0001", capability_name: "Cut_straight", priority: 1, notes: null },
  { id: 2, machine_id: "CNCTNC0001", capability_name: "Cut_contour", priority: 1, notes: null },
  { id: 3, machine_id: "CNCTNC0002", capability_name: "Cut_straight", priority: 1, notes: null },
  { id: 4, machine_id: "CNCTNC0002", capability_name: "Cut_contour", priority: 1, notes: null },
  { id: 5, machine_id: "CNCTNC0003", capability_name: "Cut_straight", priority: 1, notes: null },
  { id: 6, machine_id: "CNCTNC0003", capability_name: "Cut_contour", priority: 1, notes: null },
  { id: 7, machine_id: "CNCTNC0004", capability_name: "Cut_straight", priority: 1, notes: null },
  { id: 8, machine_id: "CNCTNC0004", capability_name: "Cut_contour", priority: 1, notes: null },
  { id: 11, machine_id: "CNCTNC0007", capability_name: "Cut_straight", priority: 1, notes: "5 trục" },
  { id: 12, machine_id: "CNCTNC0007", capability_name: "Cut_contour", priority: 1, notes: null },
  { id: 13, machine_id: "CNCCCC0001", capability_name: "Cut_straight", priority: 2, notes: null },
  { id: 14, machine_id: "CNCCCC0001", capability_name: "Chamfer_45", priority: 2, notes: null },
  { id: 15, machine_id: "CNCCCC0002", capability_name: "Cut_straight", priority: 2, notes: null },
  { id: 16, machine_id: "CNCCCC0002", capability_name: "Chamfer_45", priority: 2, notes: null },
  { id: 17, machine_id: "CNCCCC0002", capability_name: "Edge_simple", priority: 2, notes: null },
  { id: 18, machine_id: "CNCCCC0003", capability_name: "Cut_straight", priority: 2, notes: null },
  { id: 19, machine_id: "CNCCCC0003", capability_name: "Chamfer_45", priority: 2, notes: null },
  { id: 20, machine_id: "CNCCCC0003", capability_name: "Edge_simple", priority: 2, notes: null },
  { id: 21, machine_id: "CNCTRT0001", capability_name: "Edge_simple", priority: 3, notes: null },
  { id: 22, machine_id: "CNCTRT0001", capability_name: "Edge_complex", priority: 3, notes: null },
  { id: 23, machine_id: "CNCTRT0002", capability_name: "Chamfer_45", priority: 3, notes: null },
  { id: 24, machine_id: "CNCTRT0002", capability_name: "Edge_simple", priority: 3, notes: null },
  { id: 25, machine_id: "CNCTRT0002", capability_name: "Edge_complex", priority: 3, notes: null },
  { id: 26, machine_id: "CATVTC0001", capability_name: "Chamfer_45", priority: 4, notes: null }
];

// Chỉ lấy mẫu đại diện machine_speeds (CNCTNC0001 group A-L + CNCCCC0001 group A)
export const machineSpeeds: MachineSpeed[] = [
  { id: 1, machine_id: "CNCTNC0001", material_group_code: "A", size_category: "LT_200", speed_value: 180 },
  { id: 2, machine_id: "CNCTNC0001", material_group_code: "A", size_category: "B200_400", speed_value: 180 },
  { id: 3, machine_id: "CNCTNC0001", material_group_code: "A", size_category: "B400_600", speed_value: 180 },
  { id: 4, machine_id: "CNCTNC0001", material_group_code: "A", size_category: "GT_600", speed_value: 180 },
  { id: 5, machine_id: "CNCTNC0001", material_group_code: "B", size_category: "LT_200", speed_value: 400 },
  { id: 9, machine_id: "CNCTNC0001", material_group_code: "C", size_category: "LT_200", speed_value: 200 },
  { id: 13, machine_id: "CNCTNC0001", material_group_code: "D", size_category: "LT_200", speed_value: 400 },
  { id: 17, machine_id: "CNCTNC0001", material_group_code: "E", size_category: "LT_200", speed_value: 100 },
  { id: 49, machine_id: "CNCCCC0001", material_group_code: "A", size_category: "LT_200", speed_value: 800 },
  { id: 50, machine_id: "CNCCCC0001", material_group_code: "A", size_category: "B200_400", speed_value: 950 },
  { id: 97, machine_id: "CNCTRT0001", material_group_code: "A", size_category: "LT_200", speed_value: 400 },
  { id: 98, machine_id: "CNCTRT0001", material_group_code: "A", size_category: "B200_400", speed_value: 500 }
];

export const processDefinitions: ProcessDefinition[] = [
  { id: 1, process_id: "1", process_name: "Quy trình 1 (Phôi thô)", product_type: "Phôi thô", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 2, process_id: "2", process_name: "Quy trình 2 (Phôi cong hoặc bo góc)", product_type: "Phôi cong hoặc bo góc", step_order: 1, capability_required: "Cut_contour", notes: null },
  { id: 3, process_id: "2", process_name: "Quy trình 2 (Phôi cong hoặc bo góc)", product_type: "Phôi cong hoặc bo góc", step_order: 2, capability_required: "Cut_contour", notes: null },
  { id: 4, process_id: "3", process_name: "Quy trình 3 (Tấm thẳng có vát cạnh)", product_type: "Tấm thẳng có vát cạnh", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 5, process_id: "3", process_name: "Quy trình 3 (Tấm thẳng có vát cạnh)", product_type: "Tấm thẳng có vát cạnh", step_order: 2, capability_required: "Chamfer_45", notes: null },
  { id: 6, process_id: "4", process_name: "Quy trình 4 (Tấm thẳng có chạy chỉ/rãnh)", product_type: "Tấm thẳng có chạy chỉ/rãnh", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 7, process_id: "4", process_name: "Quy trình 4 (Tấm thẳng có chạy chỉ/rãnh)", product_type: "Tấm thẳng có chạy chỉ/rãnh", step_order: 2, capability_required: "Edge_simple", notes: null },
  { id: 8, process_id: "5", process_name: "Quy trình 5 (Tấm thẳng có hoa văn phức tạp)", product_type: "Tấm thẳng có hoa văn phức tạp", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 9, process_id: "5", process_name: "Quy trình 5 (Tấm thẳng có hoa văn phức tạp)", product_type: "Tấm thẳng có hoa văn phức tạp", step_order: 2, capability_required: "Edge_complex", notes: null },
  { id: 10, process_id: "6", process_name: "Quy trình 6 (Sản phẩm cong có vát 45)", product_type: "Sản phẩm cong có vát 45", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 11, process_id: "6", process_name: "Quy trình 6 (Sản phẩm cong có vát 45)", product_type: "Sản phẩm cong có vát 45", step_order: 2, capability_required: "Cut_contour", notes: null },
  { id: 12, process_id: "6", process_name: "Quy trình 6 (Sản phẩm cong có vát 45)", product_type: "Sản phẩm cong có vát 45", step_order: 3, capability_required: "Chamfer_45", notes: null },
  { id: 13, process_id: "7", process_name: "Quy trình 7 (Sản phẩm cong có chạy chỉ)", product_type: "Sản phẩm cong có chạy chỉ", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 14, process_id: "7", process_name: "Quy trình 7 (Sản phẩm cong có chạy chỉ)", product_type: "Sản phẩm cong có chạy chỉ", step_order: 2, capability_required: "Cut_contour", notes: null },
  { id: 15, process_id: "7", process_name: "Quy trình 7 (Sản phẩm cong có chạy chỉ)", product_type: "Sản phẩm cong có chạy chỉ", step_order: 3, capability_required: "Edge_simple", notes: null },
  { id: 16, process_id: "8", process_name: "Quy trình 8 (Sản phẩm cong có hoa văn)", product_type: "Sản phẩm cong có hoa văn", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 17, process_id: "8", process_name: "Quy trình 8 (Sản phẩm cong có hoa văn)", product_type: "Sản phẩm cong có hoa văn", step_order: 2, capability_required: "Cut_contour", notes: null },
  { id: 18, process_id: "8", process_name: "Quy trình 8 (Sản phẩm cong có hoa văn)", product_type: "Sản phẩm cong có hoa văn", step_order: 3, capability_required: "Edge_complex", notes: null },
  { id: 19, process_id: "9", process_name: "Quy trình 9 (Tấm thẳng vát + soi rãnh)", product_type: "Tấm thẳng vát + soi rãnh", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 20, process_id: "9", process_name: "Quy trình 9 (Tấm thẳng vát + soi rãnh)", product_type: "Tấm thẳng vát + soi rãnh", step_order: 2, capability_required: "Chamfer_45", notes: null },
  { id: 21, process_id: "9", process_name: "Quy trình 9 (Tấm thẳng vát + soi rãnh)", product_type: "Tấm thẳng vát + soi rãnh", step_order: 3, capability_required: "Edge_simple", notes: null },
  { id: 22, process_id: "10", process_name: "Quy trình 10 (Tấm thẳng vát + hoa văn)", product_type: "Tấm thẳng vát + hoa văn", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 23, process_id: "10", process_name: "Quy trình 10 (Tấm thẳng vát + hoa văn)", product_type: "Tấm thẳng vát + hoa văn", step_order: 2, capability_required: "Chamfer_45", notes: null },
  { id: 24, process_id: "10", process_name: "Quy trình 10 (Tấm thẳng vát + hoa văn)", product_type: "Tấm thẳng vát + hoa văn", step_order: 3, capability_required: "Edge_complex", notes: null },
  { id: 44, process_id: "16", process_name: "Quy trình 16 (Đầy đủ tất cả công đoạn)", product_type: "Đầy đủ tất cả công đoạn", step_order: 1, capability_required: "Cut_straight", notes: null },
  { id: 45, process_id: "16", process_name: "Quy trình 16 (Đầy đủ tất cả công đoạn)", product_type: "Đầy đủ tất cả công đoạn", step_order: 2, capability_required: "Cut_contour", notes: null },
  { id: 46, process_id: "16", process_name: "Quy trình 16 (Đầy đủ tất cả công đoạn)", product_type: "Đầy đủ tất cả công đoạn", step_order: 3, capability_required: "Chamfer_45", notes: null },
  { id: 47, process_id: "16", process_name: "Quy trình 16 (Đầy đủ tất cả công đoạn)", product_type: "Đầy đủ tất cả công đoạn", step_order: 4, capability_required: "Edge_simple", notes: null },
  { id: 48, process_id: "16", process_name: "Quy trình 16 (Đầy đủ tất cả công đoạn)", product_type: "Đầy đủ tất cả công đoạn", step_order: 5, capability_required: "Edge_complex", notes: null }
];

export const materials: Material[] = [
  { id: "100000470839", material_name: "DARK GREY EMPERADOR", material_type: "MARBLE", group_code: "B", notes: null },
  { id: "100000447257", material_name: "LIGHT EMPERADOR", material_type: "MARBLE", group_code: "B", notes: null },
  { id: "100000474067", material_name: "TRẮNG BÌNH ĐỊNH", material_type: "GRANITE", group_code: "A", notes: null },
  { id: "100000446895", material_name: "ABSOLUTE BLACK", material_type: "GRANITE", group_code: "A", notes: null },
  { id: "100000451598", material_name: "ĐEN BAZAN", material_type: "BAZAN", group_code: "C", notes: null },
  { id: "100000474019", material_name: "CALACATTA VIOLA", material_type: "MARBLE", group_code: "D", notes: null },
  { id: "100000449013", material_name: "CARRARA WHITE", material_type: "MARBLE", group_code: "D", notes: null },
  { id: "100000473365", material_name: "NUNG KẾT EXAMPLE", material_type: "SINTERED", group_code: "E", notes: null },
  { id: "100000451698", material_name: "KIM SA TRUNG", material_type: "GRANITE", group_code: "F", notes: null },
  { id: "100000462811", material_name: "ATHEN GOLDEN FLOWER", material_type: "MARBLE", group_code: "G", notes: null },
  { id: "100000451699", material_name: "NERO MARQUINA", material_type: "MARBLE", group_code: "H", notes: null },
  { id: "100000466310", material_name: "QUARTZ SAMPLE 1", material_type: "QUARTZ", group_code: "I", notes: null },
  { id: "100000433186", material_name: "ORIENTAL WHITE", material_type: "MARBLE", group_code: "J", notes: "Onyx" },
  { id: "100001000610", material_name: "PLATTINUM GREY", material_type: "MARBLE", group_code: "K", notes: null },
  { id: "100000471919", material_name: "VOLAKAS BUTTERFLY", material_type: "MARBLE", group_code: "L", notes: null }
];

// =============================================
// COMPUTED DATA — tương đương logic trong main.py
// =============================================

// Xây dựng processMap: process_name -> [capability_required, ...] (giống main.py line 71-75)
export function buildProcessMap(): ProcessMap {
  const map: ProcessMap = {};
  for (const pd of processDefinitions) {
    if (!map[pd.process_name]) {
      map[pd.process_name] = [];
    }
    if (!map[pd.process_name].includes(pd.capability_required)) {
      map[pd.process_name].push(pd.capability_required);
    }
  }
  return map;
}

// Xây dựng capability -> machines mapping (giống main.py line 318-332)
export function buildCapabilityMachineMap(): CapabilityMachineMap {
  const map: CapabilityMachineMap = {};
  for (const cap of machineCapabilities) {
    if (!map[cap.capability_name]) {
      map[cap.capability_name] = [];
    }
    if (!map[cap.capability_name].includes(cap.machine_id)) {
      map[cap.capability_name].push(cap.machine_id);
    }
  }
  return map;
}

// Map operations list to machine names string (giống main.py line 338-347)
export function mapOpsToMachines(opsList: string[]): string {
  const capMap = buildCapabilityMachineMap();
  const mapping: Record<string, string> = {};
  for (const [capName, machineIds] of Object.entries(capMap)) {
    mapping[capName] = machineIds.join(" / ");
  }
  return opsList.map(cap => mapping[cap] || cap).join(" -> ");
}

// =============================================
// DEMO / MOCK DATA — dữ liệu mẫu cho UI demo
// =============================================

export const mockDxfFiles: { name: string; info: DxfInfo }[] = [
  {
    name: "VIN_BanDa_001.dxf",
    info: {
      status: "success",
      straight_len_mm: 2400,
      curved_len_mm: 350,
      total_len_mm: 2750,
      complexity_ratio: 0.127,
      texts: ["Bàn đá bếp", "2400x600x20"],
      warnings: []
    }
  },
  {
    name: "VIN_LavaBo_002.dxf",
    info: {
      status: "success",
      straight_len_mm: 1800,
      curved_len_mm: 0,
      total_len_mm: 1800,
      complexity_ratio: 0.0,
      texts: ["Tấm ốp lavabo"],
      warnings: []
    }
  },
  {
    name: "VIN_CauThang_003.dxf",
    info: {
      status: "success",
      straight_len_mm: 1200,
      curved_len_mm: 180,
      total_len_mm: 1380,
      complexity_ratio: 0.130,
      texts: ["Bậc cầu thang", "1200x300x30"],
      warnings: ["Layer 'Defpoints' chứa nét không chuẩn"]
    }
  }
];

// Mock jobs queue (giống st.session_state.jobs_queue)
export const mockJobsQueue: JobData[] = [
  {
    id: "VIN2408.1_VIN_Ba_7821",
    project_name: "VIN",
    project_code: "VIN2408",
    hexcode: "V-0302",
    material_group: "C",
    process_steps: 2,
    size_mm: 2750,
    detail_len_mm: 2750,
    complexity: 0.127,
    quantity: 1,
    operations: ["Cut_contour", "Cut_contour"],
    start_time: "2026-04-03T07:00:00",
    due_date: "2026-04-04T17:00:00",
    priority: "Cao",
    process: "Quy trình 2 (Phôi cong hoặc bo góc)",
    process_machine: "CNCTNC0001 / CNCTNC0002 / CNCTNC0003 / CNCTNC0004 / CNCTNC0007 -> CNCTNC0001 / CNCTNC0002 / CNCTNC0003 / CNCTNC0004 / CNCTNC0007"
  },
  {
    id: "VIN2408.2_VIN_La_7821",
    project_name: "VIN",
    project_code: "VIN2408",
    hexcode: "V-0302",
    material_group: "A",
    process_steps: 1,
    size_mm: 1800,
    detail_len_mm: 1800,
    complexity: 0.0,
    quantity: 1,
    operations: ["Cut_straight"],
    start_time: "2026-04-03T07:00:00",
    due_date: "2026-04-04T17:00:00",
    priority: "Bình thường",
    process: "Quy trình 1 (Phôi thô)",
    process_machine: "CNCTNC0001 / CNCTNC0002 / CNCTNC0003 / CNCTNC0004 / CNCTNC0007 / CNCCCC0001 / CNCCCC0002 / CNCCCC0003"
  },
  {
    id: "VIN2408.3_VIN_Ca_7821",
    project_name: "VIN",
    project_code: "VIN2408",
    hexcode: "V-0302",
    material_group: "D",
    process_steps: 2,
    size_mm: 1380,
    detail_len_mm: 1380,
    complexity: 0.130,
    quantity: 2,
    operations: ["Cut_straight", "Chamfer_45"],
    start_time: "2026-04-03T07:00:00",
    due_date: "2026-04-04T17:00:00",
    priority: "Gấp",
    process: "Quy trình 3 (Tấm thẳng có vát cạnh)",
    process_machine: "CNCTNC0001 / CNCCCC0001 / CNCCCC0002 / CNCCCC0003 -> CNCCCC0001 / CNCCCC0002 / CNCCCC0003 / CNCTRT0002 / CATVTC0001"
  },
  {
    id: "VIN2408.4_VIN_Op_9012",
    project_name: "VIN",
    project_code: "VIN2408",
    hexcode: "V-0302",
    material_group: "B",
    process_steps: 3,
    size_mm: 980,
    detail_len_mm: 500,
    complexity: 0.05,
    quantity: 1,
    operations: ["Cut_straight", "Cut_contour", "Edge_simple"],
    start_time: "2026-04-03T07:00:00",
    due_date: "2026-04-04T17:00:00",
    priority: "Bình thường",
    process: "Quy trình 7 (Sản phẩm cong có chạy chỉ)",
    process_machine: "CNCTNC0001 / CNCCCC0001 -> CNCTNC0001 / CNCTNC0002 -> CNCCCC0002 / CNCCCC0003 / CNCTRT0001 / CNCTRT0002"
  }
];

// Mock scheduled jobs (giống st.session_state.scheduled_jobs)
export const mockScheduledJobs: ScheduledJob[] = [
  { job_id: "VIN2408.1_VIN_Ba_7821", machine: "CNCTNC0001", start: 0, finish: 45, setup: 5, op_idx: 0, note: "GA Optimized" },
  { job_id: "VIN2408.1_VIN_Ba_7821", machine: "CNCTNC0002", start: 50, finish: 90, setup: 3, op_idx: 1, note: "GA Optimized" },
  { job_id: "VIN2408.2_VIN_La_7821", machine: "CNCCCC0001", start: 0, finish: 25, setup: 2, op_idx: 0, note: "GA Optimized" },
  { job_id: "VIN2408.3_VIN_Ca_7821", machine: "CNCCCC0002", start: 0, finish: 30, setup: 5, op_idx: 0, note: "GA Optimized" },
  { job_id: "VIN2408.3_VIN_Ca_7821", machine: "CATVTC0001", start: 35, finish: 55, setup: 3, op_idx: 1, note: "GA Optimized" },
  { job_id: "VIN2408.4_VIN_Op_9012", machine: "CNCTNC0004", start: 0, finish: 20, setup: 2, op_idx: 0, note: "Expert Intervention" },
  { job_id: "VIN2408.4_VIN_Op_9012", machine: "CNCTNC0001", start: 50, finish: 75, setup: 3, op_idx: 1, note: "Expert Intervention" },
  { job_id: "VIN2408.4_VIN_Op_9012", machine: "CNCTRT0001", start: 80, finish: 110, setup: 5, op_idx: 2, note: "GA Optimized" },
  // Thêm jobs cho CNCTNC0003 (Maintenance)
  { job_id: "VIN2408.3_VIN_Ca_7821", machine: "CNCTNC0003", start: 0, finish: 35, setup: 5, op_idx: 0, note: "GA Optimized" }
];

// Mock schedule options (kết quả từ HybridEngine)
export const mockScheduleOptions: ScheduleOption[] = [
  {
    name: "Phương án Cân Bằng (Balanced Load)",
    metrics: { makespan: 110, setup: 33 },
    schedule: mockScheduledJobs
  },
  {
    name: "Phương án Nhanh Nhất (Minimum Makespan)",
    metrics: { makespan: 95, setup: 42 },
    schedule: mockScheduledJobs
  },
  {
    name: "Phương án Tiết Kiệm (Minimum Setup)",
    metrics: { makespan: 130, setup: 18 },
    schedule: mockScheduledJobs
  }
];
