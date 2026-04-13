import { useState, useEffect, useCallback } from 'react';
import { runSchedule, getScheduleStatus, selectSchedule, listJobs, updateJob } from '../../api/httpClient';

interface ScheduleOption {
  name: string;
  metrics: { fitness: number; makespan: number; setup: number; tardiness: number };
  schedule: any[];
}

interface JobSetupRow {
  id: string;
  process: string | null;
  setupTime: string; // '' = Auto
}

export default function SchedulePanel() {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [options, setOptions] = useState<ScheduleOption[]>([]);
  const [taskToken, setTaskToken] = useState('');
  const [useMl, setUseMl] = useState(false);
  const [toast, setToast] = useState('');

  // Overtime state
  const [enableOvertime, setEnableOvertime] = useState(false);
  const [overtimeEndHour, setOvertimeEndHour] = useState('18:00');
  const [selected, setSelected] = useState<number | null>(null);

  // Setup time config
  const [jobRows, setJobRows] = useState<JobSetupRow[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [showSetupConfig, setShowSetupConfig] = useState(false);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  const fetchQueuedJobs = useCallback(async () => {
    setLoadingJobs(true);
    try {
      const data = await listJobs(); // Lấy tất cả, filter client-side
      const rows: JobSetupRow[] = (data.jobs || [])
        .filter((j: any) => ['queued', 'scheduled'].includes(j.status)) // Chỉ job còn hoạt động
        .map((j: any) => ({
          id: j.id,
          process: j.process || null,
          setupTime: j.manual_setup_time != null ? String(j.manual_setup_time) : '',
        }));
      setJobRows(rows);
    } catch { /* ignore */ }
    setLoadingJobs(false);
  }, []);

  useEffect(() => { fetchQueuedJobs(); }, [fetchQueuedJobs]);

  // Sync với bảng hàng đợi phía trên khi có job bị xóa / lưu
  useEffect(() => {
    const handler = () => fetchQueuedJobs();
    window.addEventListener('jobs-updated', handler);
    return () => window.removeEventListener('jobs-updated', handler);
  }, [fetchQueuedJobs]);

  const handleSetupChange = (jobId: string, value: string) => {
    setJobRows(prev => prev.map(r => r.id === jobId ? { ...r, setupTime: value } : r));
  };

  const handleRun = async () => {
    setRunning(true);
    setProgress(0);
    setOptions([]);
    setSelected(null);
    try {
      // 1. Save any manually set setup times before scheduling
      const rowsWithSetup = jobRows.filter(r => r.setupTime !== '');
      if (rowsWithSetup.length > 0) {
        await Promise.all(
          rowsWithSetup.map(r =>
            updateJob(r.id, { manual_setup_time: parseInt(r.setupTime) })
          )
        );
      }

      // 2. Run scheduler
      let overtimeConfig = undefined;
      if (enableOvertime) {
        const [hh, mm] = overtimeEndHour.split(':').map(Number);
        const minsFrom7AM = (hh * 60 + mm) - (7 * 60);
        overtimeConfig = { enabled: true, end_time_mins: minsFrom7AM };
      }
      const { task_token } = await runSchedule(useMl, overtimeConfig);
      setTaskToken(task_token);

      let status = 'pending';
      while (status === 'pending' || status === 'running') {
        await new Promise(r => setTimeout(r, 1500));
        const data = await getScheduleStatus(task_token);
        status = data.status;
        setProgress(data.progress || 0);
        if (status === 'completed' && data.result) {
          // data.result is now {"options": [...], "overtime_config": {...}}
          const resOptions = Array.isArray(data.result) ? data.result : data.result.options;
          setOptions(resOptions);
        }
        if (status === 'failed') {
          showToast(` Lỗi: ${data.error}`);
        }
      }
    } catch (e: any) {
      showToast(` ${e.message}`);
    }
    setRunning(false);
  };

  const handleSelect = async (idx: number) => {
    try {
      await selectSchedule(taskToken, idx);
      setSelected(idx);
      showToast(' Đã áp dụng lịch trình!');
      window.dispatchEvent(new Event('schedule-updated'));
    } catch (e: any) {
      showToast(` ${e.message}`);
    }
  };

  const parseName = (name: string) => {
    if (name.includes('(')) {
      const main = name.split('(')[0].trim();
      const desc = name.split('(')[1]?.replace(')', '').trim();
      return { main, desc };
    }
    return { main: name, desc: '' };
  };

  const filledCount = jobRows.filter(r => r.setupTime !== '').length;

  return (
    <>
      {/* ── Setup Time Config Panel ─────────────────────────────── */}
      <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        {/* Header – always visible */}
        <div className="flex-between" style={{ cursor: 'pointer' }} onClick={() => setShowSetupConfig(v => !v)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.1rem' }}></span>
            <div>
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Cấu hình Setup Time (tùy chọn)</span>
              <span style={{ marginLeft: 10, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {filledCount > 0
                  ? `${filledCount}/${jobRows.length} job đã điền thủ công`
                  : jobRows.length > 0
                    ? `${jobRows.length} job – tất cả đang dùng Auto`
                    : 'Không có job trong hàng đợi'}
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {filledCount > 0 && (
              <span className="badge badge-warning">{filledCount} override</span>
            )}
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {showSetupConfig ? '▲ Thu gọn' : '▼ Mở rộng'}
            </span>
          </div>
        </div>

        {/* Collapsible body */}
        {showSetupConfig && (
          <div style={{ marginTop: 'var(--spacing-md)' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 'var(--spacing-sm)' }}>
              Để trống → hệ thống mặc định. Điền số phút → ghi đè giá trị tính toán của thuật toán.
            </p>

            {loadingJobs ? (
              <div className="flex-center" style={{ padding: 'var(--spacing-lg)' }}>
                <div className="spinner spinner-lg" />
              </div>
            ) : jobRows.length === 0 ? (
              <div className="empty-state" style={{ padding: 'var(--spacing-md)' }}>
                <p style={{ fontSize: '0.85rem' }}>Chưa có job nào trong hàng đợi.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Job ID</th>
                      <th>Quy trình</th>
                      <th style={{ width: 160 }}>Setup Time (phút)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobRows.map(row => (
                      <tr key={row.id} className={row.setupTime !== '' ? 'row-edited' : ''}>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.78rem', fontWeight: 600 }}>
                          {row.id}
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          {row.process || '—'}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <input
                              className="cell-input"
                              type="number"
                              min={0}
                              placeholder="Auto"
                              value={row.setupTime}
                              onChange={e => handleSetupChange(row.id, e.target.value)}
                              style={{ width: 90 }}
                            />
                            {row.setupTime !== '' && (
                              <button
                                title="Xóa – quay về Auto"
                                onClick={() => handleSetupChange(row.id, '')}
                                style={{
                                  background: 'none', border: 'none', cursor: 'pointer',
                                  color: 'var(--text-muted)', fontSize: '0.85rem', padding: '2px 4px',
                                  lineHeight: 1
                                }}
                              >✕</button>
                            )}
                            {row.setupTime !== '' && (
                              <span className="badge badge-warning" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>Manual</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{ marginTop: 'var(--spacing-sm)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary btn-sm" onClick={fetchQueuedJobs}>
                Làm mới danh sách
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Run Section ─────────────────────────────────────────── */}
      <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="flex-between">
          <div>
            <h3>Chạy Lập Lịch </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 4 }}>
              Thuật toán sẽ chạy nền, giao diện vẫn phản hồi mượt mà
            </p>
            {filledCount > 0 && !running && (
              <p style={{ color: 'var(--accent-orange)', fontSize: '0.8rem', marginTop: 4 }}>
                {filledCount} job sẽ dùng setup time thủ công trước khi chạy
              </p>
            )}
          </div>
          <div className="flex-gap" style={{ alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginRight: 16 }}>
              {/* 
                Tạm ẩn checkbox AI hỗ trợ để thu thập dữ liệu sản xuất thực tế trước.
                Khi nào đủ dữ liệu (2-4 tuần), có thể uncomment đoạn này để bật lại.
              */}
              {/* <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <input type="checkbox" checked={useMl} onChange={e => setUseMl(e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: 'var(--accent-blue)' }} />
                AI hỗ trợ
              </label> */}

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <input type="checkbox" checked={enableOvertime} onChange={e => setEnableOvertime(e.target.checked)}
                    style={{ width: 16, height: 16, accentColor: 'var(--accent-orange)' }} />
                  Tăng ca đến:
                </label>
                {enableOvertime && (
                  <input
                    type="time"
                    value={overtimeEndHour}
                    onChange={e => setOvertimeEndHour(e.target.value)}
                    style={{ padding: '2px 4px', fontSize: '0.8rem', borderRadius: 4, border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
                  />
                )}
              </div>
            </div>
            <button className="btn btn-primary btn-lg" onClick={handleRun} disabled={running}>
              {running ? <><span className="spinner" /> Đang tính toán...</> : 'CHẠY LẬP LỊCH'}
            </button>
          </div>
        </div>

        {running && (
          <div style={{ marginTop: 'var(--spacing-md)' }}>
            <div className="flex-between" style={{ marginBottom: 4 }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {progress < 0.15 ? 'Đang lưu cấu hình setup time...' : progress < 0.3 ? 'Đang tải dữ liệu máy...' : progress < 0.5 ? 'Đang phân tích ràng buộc kỹ thuật...' : 'Đang tối ưu GA-VNS...'}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-blue-light)' }}>{(progress * 100).toFixed(0)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress * 100}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* ── Schedule Options ─────────────────────────────────────── */}
      {options.length > 0 && (
        <>
          <h3 style={{ marginBottom: 'var(--spacing-md)' }}> Lựa Chọn Phương Án Lịch Trình</h3>
          <div className="grid-3">
            {options.map((opt, idx) => {
              const { main, desc } = parseName(opt.name);
              return (
                <div
                  key={idx}
                  className={`option-card ${selected === idx ? 'selected' : ''}`}
                  onClick={() => handleSelect(idx)}
                >
                  <h4>
                    {idx === 0 ? '' : idx === 1 ? '' : ''} {main}
                  </h4>
                  {desc && <p className="option-desc">{desc}</p>}

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Makespan</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                        {opt.metrics.makespan}<span style={{ fontSize: '0.65rem', fontWeight: 400 }}> phút</span>
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Setup</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-orange)' }}>
                        {opt.metrics.setup}<span style={{ fontSize: '0.65rem', fontWeight: 400 }}> phút</span>
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tardiness</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: opt.metrics.tardiness > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                        {opt.metrics.tardiness}<span style={{ fontSize: '0.65rem', fontWeight: 400 }}> phút</span>
                      </div>
                    </div>
                  </div>

                  {selected === idx && (
                    <div style={{ marginTop: 'var(--spacing-md)', textAlign: 'center' }}>
                      <span className="badge badge-success">✓ Đã chọn</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {toast && <div className={`toast ${toast.startsWith('') ? 'success' : 'error'}`}>{toast}</div>}
    </>
  );
}
