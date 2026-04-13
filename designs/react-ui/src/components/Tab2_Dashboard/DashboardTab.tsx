import React, { useState } from 'react';
import Expander from '../shared/Expander';
import DataTable from '../shared/DataTable';
import MetricCard from '../shared/MetricCard';
import AlertBanner from '../shared/AlertBanner';
import GanttChart from './GanttChart';
import {
  mockJobsQueue, mockScheduledJobs, mockScheduleOptions,
  machines
} from '../../data/mockData';
import type { ScheduleOption } from '../../types';
import './DashboardTab.css';

/**
 * TAB 2: BẢNG ĐIỀU ĐỘ SẢN XUẤT
 * Tương đương main.py lines 307–582
 */
const DashboardTab: React.FC = () => {
  // State cho schedule options (main.py line 408-434)
  const [scheduleOptions, setScheduleOptions] = useState<ScheduleOption[] | null>(mockScheduleOptions);
  const [scheduledJobs, setScheduledJobs] = useState(mockScheduledJobs);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  // Hàng đợi data (main.py line 352-358)
  const queueColumns = [
    { key: 'id', label: 'ID', disabled: true },
    { key: 'project_name', label: 'Dự án' },
    { key: 'project_code', label: 'Mã CT' },
    { key: 'hexcode', label: 'Hexcode' },
    { key: 'material_group', label: 'Nhóm VL' },
    { key: 'size_mm', label: 'Kích thước (mm)' },
    { key: 'detail_len_mm', label: 'Chiều dài GC (mm)' },
    { key: 'complexity', label: 'Độ phức tạp' },
    { key: 'process', label: 'Quy trình' },
    { key: 'process_machine', label: 'Luồng máy' }
  ];

  // Tính Start_Time / Finish_Time từ start/finish minutes (main.py line 446-448)
  const formatMinToTime = (minutes: number): string => {
    const h = Math.floor(minutes / 60) + 7;
    const m = minutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  // Detailed schedule data (main.py line 524-533)
  const detailColumns = [
    { key: 'job_id', label: 'Job ID', disabled: true },
    { key: 'project_name', label: 'Dự án' },
    { key: 'project_code', label: 'Mã CT' },
    { key: 'hexcode', label: 'Hexcode' },
    { key: 'machine', label: 'Máy' },
    { key: 'Start_Time', label: 'Bắt đầu' },
    { key: 'Finish_Time', label: 'Kết thúc' },
    { key: 'setup', label: 'Setup (phút)' },
    { key: 'machine_status', label: 'Trạng thái máy' }
  ];

  // Merge schedule data with queue data (main.py line 504-527)
  const mergedDetailData = scheduledJobs.map(sj => {
    const queueJob = mockJobsQueue.find(jq => jq.id === sj.job_id);
    const machineData = machines.find(m => m.id === sj.machine);
    return {
      ...sj,
      project_name: queueJob?.project_name || '',
      project_code: queueJob?.project_code || '',
      hexcode: queueJob?.hexcode || '',
      Start_Time: formatMinToTime(sj.start),
      Finish_Time: formatMinToTime(sj.finish),
      machine_status: machineData?.status || 'On'
    };
  });

  return (
    <div>
      <h3>TRUNG TÂM ĐIỀU ĐỘ SẢN XUẤT</h3>

      {/* ===== Phần 1: Hàng đợi (main.py line 311-436) ===== */}
      <Expander title="DANH SÁCH HÀNG ĐỢI CÔNG VIỆC" defaultExpanded={true}>
        {mockJobsQueue.length > 0 ? (
          <>
            {/* Data editor (main.py line 352-358) */}
            <DataTable
              columns={queueColumns}
              data={mockJobsQueue as unknown as Record<string, unknown>[]}
              dynamicRows={true}
            />

            {/* AI checkbox + Run button (main.py line 387-405) */}
            <div className="columns flex-1-4" style={{ alignItems: 'center', marginTop: '1rem' }}>
              <div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                  <input type="checkbox" defaultChecked={true} />
                  Kích hoạt AI hỗ trợ
                </label>
              </div>
              <div>
                <button className="primary">
                  CHẠY LẬP LỊCH (HYBRID ENGINE)
                </button>
              </div>
            </div>

            {/* Schedule options (main.py line 408-434) */}
            {scheduleOptions && (
              <>
                <hr />
                <h4>LỰA CHỌN PHƯƠNG ÁN LỊCH TRÌNH</h4>
                <div className="columns">
                  {scheduleOptions.map((opt, idx) => {
                    // Parse name (main.py line 417-423)
                    let mainName = opt.name;
                    let desc = '';
                    if (opt.name.includes('(') && opt.name.includes(')')) {
                      mainName = opt.name.split('(')[0].trim();
                      desc = opt.name.split('(')[1].replace(')', '').trim();
                    }

                    return (
                      <div key={idx} className="container-bordered" style={{ textAlign: 'center' }}>
                        <strong>{mainName}</strong>
                        {desc && <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>{desc}</div>}

                        {/* Metrics (main.py line 426-427) */}
                        <MetricCard label="Tổng Thời Gian (Makespan)" value={`${opt.metrics.makespan} phút`} />
                        <MetricCard label="Thời gian Setup" value={`${opt.metrics.setup} phút`} />

                        {/* Select button (main.py line 430-434) */}
                        <button
                          className={selectedOption === opt.name ? 'primary' : 'secondary'}
                          style={{ marginTop: '0.5rem', width: '100%' }}
                          onClick={() => {
                            setSelectedOption(opt.name);
                            setScheduledJobs(opt.schedule);
                          }}
                        >
                          Chọn Phương án {idx + 1}
                        </button>
                      </div>
                    );
                  })}
                </div>

                {selectedOption && (
                  <AlertBanner type="success">Đã chọn {selectedOption}!</AlertBanner>
                )}
              </>
            )}
          </>
        ) : (
          <AlertBanner type="info">Chưa có đơn hàng nào trong hàng đợi.</AlertBanner>
        )}
      </Expander>

      <hr />

      {/* ===== Phần 2: Biểu đồ Gantt (main.py line 441-582) ===== */}
      <h4>BIỂU ĐỒ KẾ HOẠCH SẢN XUẤT (GANTT)</h4>
      {scheduledJobs.length > 0 ? (
        <>
          <GanttChart scheduledJobs={scheduledJobs} />

          {/* Detail expander (main.py line 503-579) */}
          <Expander title="Xem chi tiết dữ liệu">
            <DataTable
              columns={detailColumns}
              data={mergedDetailData as unknown as Record<string, unknown>[]}
              dynamicRows={true}
            />

            {/* Download CSV button (main.py line 578-579) */}
            <button style={{ marginTop: '0.5rem' }}>
              📥 Tải xuống CSV
            </button>
          </Expander>
        </>
      ) : (
        <p style={{ color: 'var(--color-text-secondary)' }}>Chưa có dữ liệu lịch trình.</p>
      )}
    </div>
  );
};

export default DashboardTab;
