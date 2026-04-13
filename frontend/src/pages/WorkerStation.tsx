import { useState, useEffect, useCallback } from 'react';
import { listMachines, getMachineJobs, updateMachineStatus, completeJob, reschedule, getScheduleStatus, acceptJob, pauseJob } from '../api/httpClient';
import ThemeToggle from '../components/ThemeToggle';

interface MachineInfo { id: string; name: string; machine_type: string; status: string; }
interface MachineJob {
  id: number; job_id: string; op_idx: number; machine: string;
  start: number; finish: number; setup: number;
  note: string | null; worker_status: string;
}

function minuteToTime(m: number): string {
  const h = Math.floor(m / 60) + 7;
  const min = m % 60;
  return `${h.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`;
}

export default function WorkerStation() {
  const [machines, setMachines] = useState<MachineInfo[]>([]);
  const [selectedMachine, setSelectedMachine] = useState<string | null>(null);
  const [machineJobs, setMachineJobs] = useState<MachineJob[]>([]);
  const [toast, setToast] = useState('');

  // Machine status changer state
  const [showStatusSettings, setShowStatusSettings] = useState(false);
  const [newStatus, setNewStatus] = useState('On');
  const [repairTime, setRepairTime] = useState(40);
  const [breakdownTime, setBreakdownTime] = useState(() => {
    const now = new Date();
    return `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;
  });
  const [statusSaving, setStatusSaving] = useState(false);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 4000); };

  // Load machines
  const fetchMachines = useCallback(async () => {
    try {
      const data = await listMachines();
      setMachines((data.machines || []).sort((a: MachineInfo, b: MachineInfo) => a.id.localeCompare(b.id)));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchMachines(); }, [fetchMachines]);

  // Load jobs for selected machine
  const fetchMachineJobs = useCallback(async () => {
    if (!selectedMachine) return;
    try {
      const data = await getMachineJobs(selectedMachine);
      const sorted = (data.jobs || []).sort((a: MachineJob, b: MachineJob) => a.start - b.start);
      setMachineJobs(sorted);
    } catch { /* ignore */ }
  }, [selectedMachine]);

  useEffect(() => { fetchMachineJobs(); }, [fetchMachineJobs]);

  // Count jobs per machine (from all scheduled operations)
  const getJobCountDisplay = (machine: MachineInfo) => {
    // Simple: we show status from DB directly
    if (machine.status === 'Maintenance') return { icon: '🔴', text: 'Bảo trì' };
    if (machine.status === 'Off') return { icon: '⚪', text: 'Ngoại tuyến' };
    return { icon: '🟢', text: 'Rảnh' }; // Will be updated when we know job counts
  };

  // Handle machine select
  const handleSelectMachine = (id: string) => {
    setSelectedMachine(id);
    setShowStatusSettings(false);
    const m = machines.find(m => m.id === id);
    if (m) setNewStatus(m.status);
  };

  // Handle "Hoàn Thành"
  const handleComplete = async (job: MachineJob) => {
    try {
      await completeJob(job.job_id, selectedMachine || undefined);
      showToast(`Máy ${selectedMachine} đã hoàn thành ${job.job_id}!`);
      fetchMachineJobs();
    } catch (e: any) { showToast(`${e.message}`); }
  };

  const handleStart = async (job: MachineJob) => {
    try {
      await acceptJob(job.job_id, selectedMachine || undefined);
      showToast(`Máy ${selectedMachine} đang chạy ${job.job_id}`);
      fetchMachineJobs();
    } catch (e: any) { showToast(`${e.message}`); }
  };

  const handleUndo = async (job: MachineJob) => {
    try {
      await pauseJob(job.job_id, selectedMachine || undefined);
      // Backend sets to "paused", which treats as pending in our UI.
      showToast(`Đã hoàn tác ${job.job_id}`);
      fetchMachineJobs();
    } catch (e: any) { showToast(`${e.message}`); }
  };

  // Handle machine status save (with rescheduling if Maintenance + repair > 30)
  const handleSaveStatus = async () => {
    if (!selectedMachine) return;
    const currentMachine = machines.find(m => m.id === selectedMachine);
    if (!currentMachine || newStatus === currentMachine.status) return;

    setStatusSaving(true);
    try {
      await updateMachineStatus(selectedMachine, newStatus);

      if (newStatus === 'Maintenance' && repairTime > 30) {
        // Trigger rescheduling
        const [h, m] = breakdownTime.split(':').map(Number);
        const breakdownMinute = (h - 7) * 60 + m;

        showToast('Đang tái lập lịch ...');

        const result = await reschedule({
          machine_id: selectedMachine,
          new_status: newStatus,
          repair_time: repairTime,
          breakdown_minute: breakdownMinute,
        });

        if (result.task_token && result.task_token !== 'none') {
          // Poll for completion
          let status = 'pending';
          while (status === 'pending' || status === 'running') {
            await new Promise(r => setTimeout(r, 1500));
            const data = await getScheduleStatus(result.task_token);
            status = data.status;
            if (status === 'failed') { showToast(`${data.error}`); break; }
          }
          showToast('Tái lập lịch thành công. Đã tạo lịch mới thay thế.');
        } else {
          showToast(result.message || 'Cập nhật thành công, không có hoạt động bị ảnh hưởng!');
        }
      } else {
        showToast('Cập nhật trạng thái thành công!');
      }

      fetchMachines();
      fetchMachineJobs();
    } catch (e: any) { showToast(`${e.message}`); }
    setStatusSaving(false);
  };

  const selectedMachineInfo = machines.find(m => m.id === selectedMachine);

  /* ── Render ────────────────────────────────────────────── */
  return (
    <div className="worker-layout">
      <div className="worker-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Tab Công Nhân</h1>
          <p className="worker-subtitle">GIAO DIỆN VẬN HÀNH MÁY (SƠ ĐỒ XƯỞNG)</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
          <ThemeToggle />
          <a href="/manager" className="btn btn-secondary btn-sm">
            Tab Quản Đốc
          </a>
        </div>
      </div>

      {/* ═══ Machine Grid (4 columns matching original) ═══ */}
      <h3 style={{ margin: 'var(--spacing-lg) var(--spacing-lg) var(--spacing-md)' }}>Sơ đồ các máy</h3>
      <div className="worker-grid">
        {machines.map(machine => {
          const display = getJobCountDisplay(machine);
          const isSelected = selectedMachine === machine.id;
          return (
            <div
              key={machine.id}
              className={`machine-card ${isSelected ? 'selected' : ''}`}
              onClick={() => handleSelectMachine(machine.id)}
            >
              <div className="machine-id">{machine.id}</div>
              <div className="machine-name">{machine.name}</div>
              <div className="machine-status">
                <span>{display.icon}</span> {display.text}
              </div>
            </div>
          );
        })}
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: 'var(--spacing-lg)' }} />

      {/* ═══ Selected machine detail ═══ */}
      {selectedMachine && selectedMachineInfo && (
        <div style={{ padding: '0 var(--spacing-lg) var(--spacing-lg)' }}>
          <h2>Chi tiết công việc: {selectedMachine} ({selectedMachineInfo.name})</h2>

          {/* Machine Status Settings (Expandable — matching original st.expander) */}
          <div className="card" style={{ marginTop: 'var(--spacing-md)' }}>
            <div className="card-header" onClick={() => setShowStatusSettings(!showStatusSettings)} style={{ cursor: 'pointer' }}>
              <span className="card-title">{showStatusSettings ? '▼' : '▶'} Cài đặt Trạng thái Máy</span>
            </div>

            {showStatusSettings && (
              <div style={{ marginTop: 'var(--spacing-md)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: 'var(--spacing-md)' }}>
                  <div>
                    <div className="form-group">
                      <label className="form-label">Cập nhật trạng thái mới cho máy:</label>
                      <select className="form-select" value={newStatus} onChange={e => setNewStatus(e.target.value)}>
                        <option value="On">On</option>
                        <option value="Off">Off</option>
                        <option value="Maintenance">Maintenance</option>
                      </select>
                    </div>

                    {newStatus === 'Maintenance' && (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-sm)' }}>
                        <div className="form-group">
                          <label className="form-label">Thời gian dự kiến sửa (phút)</label>
                          <input className="form-input" type="number" min={1} value={repairTime}
                            onChange={e => setRepairTime(parseInt(e.target.value) || 40)} />
                        </div>
                        <div className="form-group">
                          <label className="form-label">Thời điểm sự cố</label>
                          <input className="form-input" type="time" value={breakdownTime}
                            onChange={e => setBreakdownTime(e.target.value)} />
                        </div>
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                    <button className="btn btn-primary" onClick={handleSaveStatus} disabled={statusSaving}
                      style={{ width: '100%' }}>
                      {statusSaving ? <><span className="spinner" /> Đang xử lý...</> : 'Lưu Trạng Thái'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ═══ Job Cards (matching original 4-column layout) ═══ */}
          {machineJobs.length === 0 ? (
            <div className="card" style={{ marginTop: 'var(--spacing-md)', textAlign: 'center', padding: 'var(--spacing-xl)' }}>
              <p style={{ color: 'var(--accent-green)', fontSize: '1.1rem' }}>
                {selectedMachine} hiện không có công việc nào!
              </p>
            </div>
          ) : (
            <div style={{ marginTop: 'var(--spacing-md)' }}>
              {(() => {
                const inProgressJobs = machineJobs.filter(j => j.worker_status === 'accepted');
                const pendingJobs = machineJobs.filter(j => j.worker_status !== 'accepted' && j.worker_status !== 'completed');
                const completedJobs = machineJobs.filter(j => j.worker_status === 'completed');

                const renderJobCard = (job: MachineJob, cardType: 'pending' | 'in_progress' | 'completed') => {
                  const startStr = minuteToTime(job.start);
                  const endStr = minuteToTime(job.finish);
                  const duration = job.finish - job.start;
                  
                  let lbl = "Đang chờ";
                  if (cardType === 'in_progress') lbl = "Đang thực thi";
                  else if (cardType === 'completed') lbl = "Đã hoàn thành";

                  return (
                    <div key={job.id} className="card" style={{
                      marginBottom: 'var(--spacing-sm)',
                      borderLeft: `4px solid ${cardType === 'in_progress' ? 'var(--accent-blue)' : 'var(--border-color)'}`,
                      opacity: cardType === 'completed' ? 0.6 : 1
                    }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 2fr 1fr', gap: 'var(--spacing-md)', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{job.job_id}</div>
                          <div style={{ fontSize: '0.75rem', color: cardType === 'in_progress' ? 'var(--accent-blue-light)' : 'var(--text-muted)', marginTop: 4 }}>
                            ({lbl})
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: '0.85rem' }}>
                            ⏱ {startStr} — {endStr} ({duration} phút)
                          </div>
                          {cardType === 'in_progress' && (
                            <div className="progress-bar" style={{ marginTop: 6, height: 6 }}>
                              <div className="progress-fill" style={{ width: '40%' }} />
                            </div>
                          )}
                        </div>

                        <div>
                          {job.note === 'Expert Intervention' ? (
                            <span className="badge badge-warning" style={{ padding: '4px 10px' }}>Chạy an toàn</span>
                          ) : (
                            <span className="badge badge-info" style={{ padding: '4px 10px' }}>Tiêu chuẩn</span>
                          )}
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          {cardType === 'pending' && (
                            <button className="btn btn-primary" onClick={() => handleStart(job)}>Bắt Đầu</button>
                          )}
                          {cardType === 'in_progress' && (
                            <button className="btn btn-primary" onClick={() => handleComplete(job)}>Hoàn Thành</button>
                          )}
                          {cardType === 'completed' && (
                            <button className="btn btn-secondary" onClick={() => handleUndo(job)}>Hoàn Tác</button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                };

                return (
                  <>
                    <h5 style={{ marginTop: 'var(--spacing-md)', marginBottom: 'var(--spacing-sm)', color: 'var(--accent-blue)' }}>[ĐANG THỰC THI]</h5>
                    {!inProgressJobs.length && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Không có công việc nào đang chạy.</p>}
                    {inProgressJobs.map(j => renderJobCard(j, 'in_progress'))}

                    <h5 style={{ marginTop: 'var(--spacing-lg)', marginBottom: 'var(--spacing-sm)' }}>[HÀNG ĐỢI]</h5>
                    {!pendingJobs.length && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Không có công việc trong hàng đợi.</p>}
                    {pendingJobs.map(j => renderJobCard(j, 'pending'))}

                    <h5 style={{ marginTop: 'var(--spacing-lg)', marginBottom: 'var(--spacing-sm)', color: 'var(--text-muted)' }}>[LỊCH SỬ - ĐÃ HOÀN THÀNH]</h5>
                    {!completedJobs.length && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Chưa có công việc nào hoàn thành.</p>}
                    {completedJobs.map(j => renderJobCard(j, 'completed'))}
                  </>
                );
              })()}
            </div>
          )}
        </div>
      )}

      {selectedMachine && !machines.find(m => m.id === selectedMachine) && (
        <div style={{ padding: 'var(--spacing-lg)', textAlign: 'center' }}>
          <p style={{ color: 'var(--accent-green)' }}>Chọn máy khác phía trên!</p>
        </div>
      )}

      {toast && <div className={`toast ${toast.startsWith('') || toast.startsWith('') ? 'success' : 'error'}`}>{toast}</div>}
    </div>
  );
}
