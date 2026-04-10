import { useState } from 'react';
import { runSchedule, getScheduleStatus, selectSchedule } from '../../api/httpClient';

interface ScheduleOption {
  name: string;
  metrics: { fitness: number; makespan: number; setup: number; tardiness: number };
  schedule: any[];
}

export default function SchedulePanel() {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [options, setOptions] = useState<ScheduleOption[]>([]);
  const [taskToken, setTaskToken] = useState('');
  const [selected, setSelected] = useState<number | null>(null);
  const [useMl, setUseMl] = useState(true);
  const [toast, setToast] = useState('');

  const handleRun = async () => {
    setRunning(true);
    setProgress(0);
    setOptions([]);
    setSelected(null);
    try {
      const { task_token } = await runSchedule(useMl);
      setTaskToken(task_token);

      let status = 'pending';
      while (status === 'pending' || status === 'running') {
        await new Promise(r => setTimeout(r, 1500));
        const data = await getScheduleStatus(task_token);
        status = data.status;
        setProgress(data.progress || 0);
        if (status === 'completed' && data.result) {
          setOptions(data.result);
        }
        if (status === 'failed') {
          setToast(` Lỗi: ${data.error}`);
        }
      }
    } catch (e: any) {
      setToast(` ${e.message}`);
    }
    setRunning(false);
  };

  const handleSelect = async (idx: number) => {
    try {
      await selectSchedule(taskToken, idx);
      setSelected(idx);
      setToast(' Đã áp dụng lịch trình!');
      setTimeout(() => setToast(''), 3000);
      // Trigger reload in GanttChart via parent or window event
      window.dispatchEvent(new Event('schedule-updated'));
    } catch (e: any) {
      setToast(` ${e.message}`);
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

  return (
    <>
      {/* Run Section */}
      <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="flex-between">
          <div>
            <h3>Chạy Lập Lịch </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 4 }}>
              Thuật toán sẽ chạy nền, giao diện vẫn phản hồi mượt mà
            </p>
          </div>
          <div className="flex-gap" style={{ alignItems: 'center' }}>
            {/* AI Checkbox — matching original Streamlit */}
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <input type="checkbox" checked={useMl} onChange={e => setUseMl(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--accent-blue)' }} />
              AI hỗ trợ
            </label>
            <button className="btn btn-primary btn-lg" onClick={handleRun} disabled={running}>
              {running ? <><span className="spinner" /> Đang tính toán...</> : 'CHẠY LẬP LỊCH'}
            </button>
          </div>
        </div>

        {running && (
          <div style={{ marginTop: 'var(--spacing-md)' }}>
            <div className="flex-between" style={{ marginBottom: 4 }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {progress < 0.3 ? 'Đang tải dữ liệu máy...' : progress < 0.5 ? 'Đang phân tích ràng buộc kỹ thuật...' : 'Đang tối ưu GA-VNS...'}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-blue-light)' }}>{(progress * 100).toFixed(0)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress * 100}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Schedule Options */}
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

                  {/* 3 metrics matching original: Makespan + Setup + Tardiness */}
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
