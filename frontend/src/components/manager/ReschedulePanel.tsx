import { useState, useEffect } from 'react';
import { listMachines, updateMachineStatus, reschedule, getScheduleStatus, selectSchedule } from '../../api/httpClient';

interface MachineInfo {
  id: string;
  name: string;
  machine_type: string;
  status: string;
}

export default function ReschedulePanel() {
  const [machines, setMachines] = useState<MachineInfo[]>([]);
  const [selectedMachine, setSelectedMachine] = useState('');
  const [newStatus, setNewStatus] = useState('Maintenance');
  const [repairTime, setRepairTime] = useState(40);
  const [breakdownTime, setBreakdownTime] = useState('09:30');
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [options, setOptions] = useState<any[]>([]);
  const [taskToken, setTaskToken] = useState('');
  const [selected, setSelected] = useState<number | null>(null);
  const [toast, setToast] = useState('');

  useEffect(() => {
    listMachines().then(d => setMachines(d.machines || [])).catch(() => { });
  }, []);

  const timeToMinutes = (t: string) => {
    const [h, m] = t.split(':').map(Number);
    return (h - 7) * 60 + m;
  };

  const handleReschedule = async () => {
    if (!selectedMachine) return;
    setRunning(true);
    setProgress(0);
    setOptions([]);
    setSelected(null);

    try {
      // Update machine status
      await updateMachineStatus(selectedMachine, newStatus);

      // Start rescheduling
      const breakdownMinute = timeToMinutes(breakdownTime);
      const result = await reschedule({
        machine_id: selectedMachine,
        new_status: newStatus,
        repair_time: repairTime,
        breakdown_minute: breakdownMinute,
      });

      if (result.task_token === 'none') {
        setToast(`${result.message}`);
        setRunning(false);
        setTimeout(() => setToast(''), 3000);
        return;
      }

      setTaskToken(result.task_token);

      // Poll
      let status = 'pending';
      while (status === 'pending' || status === 'running') {
        await new Promise(r => setTimeout(r, 1500));
        const data = await getScheduleStatus(result.task_token);
        status = data.status;
        setProgress(data.progress || 0);
        if (status === 'completed' && data.result) {
          setOptions(data.result);
        }
        if (status === 'failed') {
          setToast(`Lỗi: ${data.error}`);
        }
      }
    } catch (e: any) {
      setToast(`${e.message}`);
    }
    setRunning(false);
  };

  const handleSelect = async (idx: number) => {
    try {
      await selectSchedule(taskToken, idx);
      setSelected(idx);
      setToast('Đã áp dụng lịch trình bù');
      setTimeout(() => setToast(''), 3000);
    } catch (e: any) {
      setToast(`${e.message}`);
    }
  };

  const activeMachines = machines.filter(m => m.status === 'On');
  const machineName = machines.find(m => m.id === selectedMachine)?.name || '';

  return (
    <div className="card" style={{ marginTop: 'var(--spacing-xl)' }}>
      <div className="card-header">
        <span className="card-title">Xử Lý Sự Cố & Bảo Trì</span>
      </div>

      <div className="grid-4" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div className="form-group">
          <label className="form-label">Máy gặp sự cố</label>
          <select className="form-select" value={selectedMachine} onChange={e => setSelectedMachine(e.target.value)}>
            <option value="">-- Chọn máy --</option>
            {activeMachines.map(m => (
              <option key={m.id} value={m.id}>{m.id} — {m.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Trạng thái mới</label>
          <select className="form-select" value={newStatus} onChange={e => setNewStatus(e.target.value)}>
            <option value="Maintenance">🔴 Bảo trì (Maintenance)</option>
            <option value="Off">⚪ Tắt máy (Off)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Thời điểm sự cố</label>
          <input className="form-input" type="time" value={breakdownTime} min="07:00" max="17:00"
            onChange={e => setBreakdownTime(e.target.value)} />
        </div>

        <div className="form-group">
          <label className="form-label">Thời gian sửa (phút)</label>
          <input className="form-input" type="number" min={10} max={480} value={repairTime}
            onChange={e => setRepairTime(parseInt(e.target.value) || 40)} />
        </div>
      </div>

      {selectedMachine && (
        <div style={{ marginBottom: 'var(--spacing-md)' }}>
          <div className="badge badge-warning" style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
            Máy <b>{selectedMachine}</b> ({machineName}) sẽ chuyển sang <b>{newStatus}</b> lúc <b>{breakdownTime}</b>.
            {repairTime > 30
              ? ` Hệ thống sẽ tự động tái lập lịch cho các đơn bị ảnh hưởng.`
              : ` Thời gian sửa ngắn, không cần tái lập lịch.`
            }
          </div>
        </div>
      )}

      <button className="btn btn-danger btn-lg" onClick={handleReschedule} disabled={!selectedMachine || running}>
        {running ? <><span className="spinner" /> Đang tái lập lịch...</> : ' XỬ LÝ SỰ CỐ'}
      </button>

      {running && (
        <div style={{ marginTop: 'var(--spacing-md)' }}>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress * 100}%` }} />
          </div>
        </div>
      )}

      {/* Rescheduled Options */}
      {options.length > 0 && (
        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          <h4 style={{ marginBottom: 'var(--spacing-md)' }}>Phương Án Tái Lập Lịch</h4>
          <div className="grid-3">
            {options.map((opt: any, idx: number) => (
              <div
                key={idx}
                className={`option-card ${selected === idx ? 'selected' : ''}`}
                onClick={() => handleSelect(idx)}
              >
                <h4>{idx === 0 ? '' : idx === 1 ? '' : ''} Phương Án {idx + 1}</h4>
                <div className="grid-2" style={{ gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MAKESPAN</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                      {opt.metrics?.makespan}p
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SETUP</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-orange)' }}>
                      {opt.metrics?.setup}p
                    </div>
                  </div>
                </div>
                {selected === idx && (
                  <div style={{ marginTop: 'var(--spacing-sm)', textAlign: 'center' }}>
                    <span className="badge badge-success">✓ Đã chọn</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {toast && <div className={`toast ${toast.startsWith('') ? 'success' : 'error'}`}>{toast}</div>}
    </div>
  );
}
