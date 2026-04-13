/**
 * HTTP client for backend API communication.
 */

const isFileProtocol = window.location.protocol === 'file:';
// When running in browser/Ngrok, use relative path so Vite proxy routes it.
// When bundled in Electron (file://), talk directly to the backend on port 8000.
const BASE_URL = isFileProtocol ? 'http://127.0.0.1:8000' : '';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
    ...options,
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── DXF ─────────────────────────────────────────────────────────────
export async function uploadDXF(files: File[]) {
  const fd = new FormData();
  files.forEach(f => fd.append('files', f));
  const res = await fetch(`${BASE_URL}/api/dxf/upload`, { method: 'POST', body: fd });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}
export const getDXFStatus = (token: string) => request<any>(`/api/dxf/status/${token}`);

// ── Jobs ────────────────────────────────────────────────────────────
export const listJobs = (status?: string) =>
  request<any>(`/api/jobs${status ? `?status=${status}` : ''}`);
export const createJob = (data: any) =>
  request<any>('/api/jobs', { method: 'POST', body: JSON.stringify(data) });
export const createJobsBatch = (jobs: any[]) =>
  request<any>('/api/jobs/batch', { method: 'POST', body: JSON.stringify({ jobs }) });
export const updateJob = (id: string, data: any) =>
  request<any>(`/api/jobs/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteJob = (id: string) =>
  request<void>(`/api/jobs/${id}`, { method: 'DELETE' });
export const clearAllJobs = () =>
  request<void>('/api/jobs', { method: 'DELETE' });

// ── Machines ────────────────────────────────────────────────────────
export const listMachines = () => request<any>('/api/machines');
export const getMachine = (id: string) => request<any>(`/api/machines/${id}`);
export const updateMachineStatus = (id: string, status: string) =>
  request<any>(`/api/machines/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) });
export const getMachineJobs = (id: string) => request<any>(`/api/machines/${id}/jobs`);

// ── Schedule ────────────────────────────────────────────────────────
export const runSchedule = (useMl = true, overtimeConfig?: any) =>
  request<any>('/api/schedule/run', { method: 'POST', body: JSON.stringify({ use_ml: useMl, overtime_config: overtimeConfig }) });
export const getScheduleStatus = (token: string) =>
  request<any>(`/api/schedule/status/${token}`);
export const selectSchedule = (token: string, optionIndex: number) =>
  request<any>(`/api/schedule/select?token=${token}`, {
    method: 'POST', body: JSON.stringify({ option_index: optionIndex }),
  });
export const getCurrentSchedule = () => request<any>('/api/schedule/current');
export const manualAdjust = (data: any) =>
  request<any>('/api/schedule/manual-adjust', { method: 'POST', body: JSON.stringify(data) });
export const reschedule = (data: any) =>
  request<any>('/api/schedule/reschedule', { method: 'POST', body: JSON.stringify(data) });
export const clearSchedule = () =>
  request<void>('/api/schedule/current', { method: 'DELETE' });

// ── Worker ──────────────────────────────────────────────────────────
export const acceptJob = (jobId: string, machineId?: string) =>
  request<any>(`/api/worker/accept/${jobId}${machineId ? `?machine_id=${machineId}` : ''}`, { method: 'POST' });
export const pauseJob = (jobId: string, machineId?: string) =>
  request<any>(`/api/worker/pause/${jobId}${machineId ? `?machine_id=${machineId}` : ''}`, { method: 'POST' });
export const completeJob = (jobId: string, machineId?: string) =>
  request<any>(`/api/worker/complete/${jobId}${machineId ? `?machine_id=${machineId}` : ''}`, { method: 'POST' });

// ── Master Data ─────────────────────────────────────────────────────
export const listMasterData = (table: string) => request<any>(`/api/masterdata/${table}`);
export const createMasterRecord = (table: string, data: any) =>
  request<any>(`/api/masterdata/${table}`, { method: 'POST', body: JSON.stringify(data) });
export const updateMasterRecord = (table: string, id: string | number, data: any) =>
  request<any>(`/api/masterdata/${table}/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteMasterRecord = (table: string, id: string | number) =>
  request<void>(`/api/masterdata/${table}/${id}`, { method: 'DELETE' });
