import { useState, useEffect, useCallback } from 'react';
import { listJobs, updateJob, deleteJob, listMasterData } from '../../api/httpClient';

interface Job {
  id: string;
  project_name: string | null;
  project_code: string | null;
  hexcode: string | null;
  material_group: string;
  size_mm: number;
  detail_len_mm: number | null;
  complexity: number;
  quantity: number;
  operations: string | string[] | null;
  process: string | null;
  process_machine: string | null;
  start_time: string | null;
  due_date: string | null;
  priority: string;
  status: string;
}

export default function JobQueueTable() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [editedJobs, setEditedJobs] = useState<Record<string, Partial<Job>>>({});
  const [capMapping, setCapMapping] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000); };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [jobsData, capsData] = await Promise.all([
        listJobs(), listMasterData('capabilities'),
      ]);

      // Build capability → machine_ids mapping
      const mapping: Record<string, string[]> = {};
      for (const cap of (capsData.records || [])) {
        if (!mapping[cap.capability_name]) mapping[cap.capability_name] = [];
        if (!mapping[cap.capability_name].includes(cap.machine_id)) {
          mapping[cap.capability_name].push(cap.machine_id);
        }
      }
      setCapMapping(mapping);
      setJobs(jobsData.jobs || []);
    } catch { /* ignore */ }
    setLoading(false);
    setEditedJobs({});
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Map operations list to machine IDs string (matching original Streamlit)
  const mapOpsToMachines = (ops: any): string => {
    if (!ops) return '';
    let opsList: string[] = [];
    if (typeof ops === 'string') {
      try { opsList = JSON.parse(ops); } catch { opsList = ops.split(' '); }
    } else if (Array.isArray(ops)) {
      opsList = ops;
    }
    return opsList.map(cap => {
      const machines = capMapping[cap];
      return machines ? machines.join(' / ') : cap;
    }).join(' -> ');
  };

  // Edit a cell
  const handleEdit = (jobId: string, field: string, value: any) => {
    setEditedJobs(prev => ({
      ...prev,
      [jobId]: { ...prev[jobId], [field]: value }
    }));
  };

  // Get display value (edited or original)
  const getValue = (job: Job, field: keyof Job) => {
    if (editedJobs[job.id] && field in editedJobs[job.id]) {
      return editedJobs[job.id][field];
    }
    return job[field];
  };

  // Save edits
  const handleSave = async (jobId: string) => {
    const edits = editedJobs[jobId];
    if (!edits) return;
    try {
      await updateJob(jobId, edits);
      showToast(`Đã lưu ${jobId}`);
      fetchData();
    } catch (e: any) { showToast(` ${e.message}`); }
  };

  // Delete
  const handleDelete = async (jobId: string) => {
    if (!confirm(`Xóa job "${jobId}"?`)) return;
    try {
      await deleteJob(jobId);
      showToast(`Đã xóa ${jobId}`);
      fetchData();
    } catch (e: any) { showToast(` ${e.message}`); }
  };

  const hasEdits = Object.keys(editedJobs).length > 0;

  /* ── Render ────────────────────────────────────────────── */
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Hàng Đợi Công Việc ({jobs.length})</span>
        <div className="flex-gap">
          {hasEdits && <span className="badge badge-warning">Có thay đổi chưa lưu</span>}
          <button className="btn btn-secondary btn-sm" onClick={fetchData}>Refresh</button>
        </div>
      </div>

      {loading ? (
        <div className="flex-center" style={{ padding: 'var(--spacing-xl)' }}><div className="spinner spinner-lg" /></div>
      ) : jobs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"></div>
          <p>Chưa có đơn hàng nào. Hãy upload bản vẽ DXF ở phía trên.</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto', marginTop: 'var(--spacing-md)' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Dự án</th>
                <th>Mã CT</th>
                <th>Hex</th>
                <th>Vật liệu</th>
                <th>Kích thước (mm)</th>
                <th>Chi tiết (mm)</th>
                <th>Complexity</th>
                <th>Quy trình</th>
                <th>Máy gia công</th>
                <th style={{ width: 90 }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(job => {
                const edited = editedJobs[job.id];
                return (
                  <tr key={job.id} className={edited ? 'row-edited' : ''}>
                    <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', fontWeight: 600 }}>
                      {job.id}
                    </td>
                    <td>
                      <input className="cell-input" value={String(getValue(job, 'project_name') || '')}
                        onChange={e => handleEdit(job.id, 'project_name', e.target.value)} />
                    </td>
                    <td>
                      <input className="cell-input" value={String(getValue(job, 'project_code') || '')}
                        onChange={e => handleEdit(job.id, 'project_code', e.target.value)} />
                    </td>
                    <td>
                      <input className="cell-input" value={String(getValue(job, 'hexcode') || '')}
                        onChange={e => handleEdit(job.id, 'hexcode', e.target.value)} style={{ width: 70 }} />
                    </td>
                    <td>
                      <select className="cell-input" value={String(getValue(job, 'material_group'))}
                        onChange={e => handleEdit(job.id, 'material_group', e.target.value)}>
                        {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'].map(m => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input className="cell-input" type="number" style={{ width: 80 }}
                        value={Number(getValue(job, 'size_mm') || 0)}
                        onChange={e => handleEdit(job.id, 'size_mm', parseFloat(e.target.value))} />
                    </td>
                    <td>
                      <input className="cell-input" type="number" style={{ width: 80 }}
                        value={Number(getValue(job, 'detail_len_mm') || 0)}
                        onChange={e => handleEdit(job.id, 'detail_len_mm', parseFloat(e.target.value))} />
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {(job.complexity || 0).toFixed(2)}
                    </td>
                    <td style={{ fontSize: '0.75rem' }}>
                      {job.process || '-'}
                    </td>
                    <td style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                      {mapOpsToMachines(job.operations)}
                    </td>
                    <td>
                      <div className="flex-gap" style={{ gap: 4 }}>
                        {edited && (
                          <button className="btn btn-primary btn-sm" onClick={() => handleSave(job.id)} title="Lưu">Save</button>
                        )}
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(job.id)} title="Xóa">Delete</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {toast && <div className={`toast ${toast.startsWith('') ? 'success' : 'error'}`}>{toast}</div>}
    </div>
  );
}
