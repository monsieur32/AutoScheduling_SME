import React, { useState } from 'react';
import Expander from '../shared/Expander';
import AlertBanner from '../shared/AlertBanner';
import { machines, mockScheduledJobs } from '../../data/mockData';
import './WorkerTab.css';

/**
 * TAB 3: GIAO DIỆN MÁY (CÔNG NHÂN)
 * Tương đương main.py lines 587–821
 */
const WorkerTab: React.FC = () => {
  const [selectedMachine, setSelectedMachine] = useState<string | null>(null);
  const [machineStatuses, setMachineStatuses] = useState<Record<string, string>>(
    Object.fromEntries(machines.map(m => [m.id, m.status]))
  );

  // State cho maintenance form (main.py line 682-694)
  const [repairTime, setRepairTime] = useState(40);
  const now = new Date();
  const [breakdownTime, setBreakdownTime] = useState(
    `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
  );

  // Sắp xếp máy (main.py line 620)
  const machineIds = machines.map(m => m.id).sort();

  // Grid layout 4 cột (main.py line 625)
  const colsPerRow = 4;

  // Format time từ phút kể từ 07:00 (main.py line 797-798)
  const formatMinToTime = (minutes: number): string => {
    const h = Math.floor(minutes / 60) + 7;
    const m = minutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  // Lấy icon trạng thái + text (main.py line 638-653)
  const getStatusDisplay = (machineId: string) => {
    const status = machineStatuses[machineId] || 'On';
    const machineJobs = mockScheduledJobs.filter(j => j.machine === machineId);
    const jobCount = machineJobs.length;

    if (status === 'Maintenance') {
      return { icon: '🔴', text: 'Bảo trì' };
    } else if (status === 'Off') {
      return { icon: '⚪', text: 'Ngoại tuyến' };
    } else {
      if (jobCount > 100) {
        return { icon: '🔴', text: 'Quá tải' };
      } else if (jobCount > 0) {
        return { icon: '🟡', text: `Đang chờ: ${jobCount} đơn` };
      } else {
        return { icon: '🟢', text: 'Rảnh' };
      }
    }
  };

  // Jobs cho selected machine (main.py line 780-781)
  const selectedMachineJobs = selectedMachine
    ? mockScheduledJobs.filter(j => j.machine === selectedMachine).sort((a, b) => a.start - b.start)
    : [];

  const selectedMachineData = selectedMachine
    ? machines.find(m => m.id === selectedMachine)
    : null;

  return (
    <div>
      <h3>GIAO DIỆN VẬN HÀNH MÁY (SƠ ĐỒ XƯỞNG)</h3>

      {/* ===== Sơ đồ các máy — Grid layout (main.py line 622-659) ===== */}
      <h4>Sơ đồ các máy</h4>
      <div className="machine-grid">
        {machineIds.map(machineId => {
          const { icon, text } = getStatusDisplay(machineId);
          const isSelected = selectedMachine === machineId;

          return (
            <button
              key={machineId}
              className={`machine-card ${isSelected ? 'selected' : ''}`}
              onClick={() => setSelectedMachine(machineId)}
            >
              <span className="machine-card-icon">{icon}</span>
              <span className="machine-card-id">{machineId}</span>
              <span className="machine-card-status">{text}</span>
            </button>
          );
        })}
      </div>

      <hr />

      {/* ===== Chi tiết công việc máy được chọn (main.py line 665-821) ===== */}
      {selectedMachine && selectedMachineData ? (
        <>
          <h3>Chi tiết công việc: {selectedMachine} ({selectedMachineData.name})</h3>

          {/* Cài đặt Trạng thái Máy (main.py line 670-778) */}
          <Expander title="Cài đặt Trạng thái Máy" defaultExpanded={false}>
            <div className="columns flex-3-1">
              <div>
                <div className="field-group">
                  <label>Cập nhật trạng thái mới cho máy:</label>
                  <select
                    value={machineStatuses[selectedMachine] || 'On'}
                    onChange={e => {
                      setMachineStatuses(prev => ({ ...prev, [selectedMachine]: e.target.value }));
                    }}
                  >
                    <option value="On">On</option>
                    <option value="Off">Off</option>
                    <option value="Maintenance">Maintenance</option>
                  </select>
                </div>

                {/* Conditional maintenance fields (main.py line 681-694) */}
                {machineStatuses[selectedMachine] === 'Maintenance' && (
                  <div className="columns" style={{ marginTop: '0.5rem' }}>
                    <div className="field-group">
                      <label>Thời gian dự kiến sửa (phút)</label>
                      <input
                        type="number"
                        min={1}
                        value={repairTime}
                        onChange={e => setRepairTime(parseInt(e.target.value) || 1)}
                      />
                    </div>
                    <div className="field-group">
                      <label>Thời điểm sự cố</label>
                      <input
                        type="time"
                        value={breakdownTime}
                        onChange={e => setBreakdownTime(e.target.value)}
                      />
                    </div>
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                <br />
                {machineStatuses[selectedMachine] === 'Maintenance' && <br />}
                <button className="primary full-width">
                  Lưu Trạng Thái
                </button>
              </div>
            </div>
          </Expander>

          {/* Danh sách jobs (main.py line 780-819) */}
          {selectedMachineJobs.length === 0 ? (
            <AlertBanner type="success">
              {selectedMachine} hiện không có công việc nào!
            </AlertBanner>
          ) : (
            selectedMachineJobs.map((job, idx) => {
              const startStr = formatMinToTime(job.start);
              const endStr = formatMinToTime(job.finish);
              const duration = job.finish - job.start;

              return (
                <div className="container-bordered" key={`${job.job_id}_${idx}`}>
                  <div className="columns columns-4-1-2-2-1" style={{ alignItems: 'center' }}>
                    {/* Col 1: Job ID & trạng thái (main.py line 791-794) */}
                    <div>
                      <strong>{job.job_id}</strong>
                      <br />
                      <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                        {idx === 0 ? '(Đang thực thi)' : '(Đang chờ)'}
                      </span>
                    </div>

                    {/* Col 2: Thời gian + progress bar (main.py line 797-803) */}
                    <div>
                      <span> {startStr} - {endStr} ({duration} phút)</span>
                      {idx === 0 && (
                        <div className="progress-bar">
                          <div className="progress-bar-fill" style={{ width: '40%' }} />
                        </div>
                      )}
                    </div>

                    {/* Col 3: Chế độ (main.py line 806-809) */}
                    <div>
                      {job.note === 'Expert Intervention' ? (
                        <AlertBanner type="warning">Chạy chế độ an toàn</AlertBanner>
                      ) : (
                        <AlertBanner type="info">Chế độ tiêu chuẩn</AlertBanner>
                      )}
                    </div>

                    {/* Col 4: Nút Hoàn Thành (main.py line 812-819) */}
                    <div>
                      <button className={idx === 0 ? 'primary full-width' : 'secondary full-width'}>
                        ✅ Hoàn Thành
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </>
      ) : selectedMachine ? (
        <AlertBanner type="success">Chọn máy khác phía trên!</AlertBanner>
      ) : null}
    </div>
  );
};

export default WorkerTab;
