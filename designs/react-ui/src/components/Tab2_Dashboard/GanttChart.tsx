import React from 'react';
import type { ScheduledJob } from '../../types';
import { machines } from '../../data/mockData';

interface GanttChartProps {
  scheduledJobs: ScheduledJob[];
}

/**
 * Gantt Chart component
 * Tương đương plotly.px.timeline() trong main.py lines 475-500
 * Render bằng div/CSS thuần thay vì plotly.js để tránh dependency nặng.
 * Nếu cần plotly thật, cộng sự có thể thêm react-plotly.js sau.
 */
const GanttChart: React.FC<GanttChartProps> = ({ scheduledJobs }) => {
  if (scheduledJobs.length === 0) return null;

  // Lấy trạng thái máy từ machines data (main.py line 451-465)
  const machineStatusMap: Record<string, string> = {};
  for (const m of machines) {
    machineStatusMap[m.id] = m.status;
  }

  // Color map (main.py line 469-473)
  const colorMap: Record<string, string> = {
    'On': '#1B5E20',
    'Off': '#757575',
    'Maintenance': '#B71C1C'
  };

  // Tính max finish time để scale chart
  const maxFinish = Math.max(...scheduledJobs.map(j => j.finish));
  const chartWidth = Math.max(maxFinish * 8, 600);

  // Nhóm jobs theo machine
  const machineIds = [...new Set(scheduledJobs.map(j => j.machine))].sort();

  // Base time 07:00 (main.py line 446-448)
  const formatTime = (minutes: number): string => {
    const h = Math.floor(minutes / 60) + 7;
    const m = minutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
      <div style={{ minWidth: chartWidth + 200 }}>
        {/* Y-axis labels + bars */}
        {machineIds.map(machineId => {
          const status = machineStatusMap[machineId] || 'On';
          const barColor = colorMap[status] || colorMap['On'];
          const jobsOnMachine = scheduledJobs.filter(j => j.machine === machineId);

          return (
            <div key={machineId} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
              {/* Machine label */}
              <div style={{
                width: '160px',
                flexShrink: 0,
                fontSize: '12px',
                fontWeight: 600,
                textAlign: 'right',
                paddingRight: '12px',
                color: 'var(--color-text)'
              }}>
                {machineId}
              </div>

              {/* Timeline bar area */}
              <div style={{
                position: 'relative',
                flex: 1,
                height: '36px',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px'
              }}>
                {jobsOnMachine.map((job, i) => {
                  const left = (job.start / maxFinish) * 100;
                  const width = ((job.finish - job.start) / maxFinish) * 100;
                  return (
                    <div
                      key={i}
                      title={`${job.job_id}\n${formatTime(job.start)} - ${formatTime(job.finish)}\nSetup: ${job.setup} phút\n${job.note}`}
                      style={{
                        position: 'absolute',
                        left: `${left}%`,
                        width: `${Math.max(width, 2)}%`,
                        height: '100%',
                        backgroundColor: barColor,
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '10px',
                        fontWeight: 600,
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        textOverflow: 'ellipsis',
                        padding: '0 4px',
                        cursor: 'pointer'
                      }}
                    >
                      {job.job_id}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Time axis */}
        <div style={{ display: 'flex', marginLeft: '160px', marginTop: '4px' }}>
          {Array.from({ length: Math.ceil(maxFinish / 30) + 1 }, (_, i) => i * 30).map(min => (
            <div key={min} style={{
              flex: 1,
              fontSize: '10px',
              color: 'var(--color-text-secondary)',
              textAlign: 'left'
            }}>
              {formatTime(min)}
            </div>
          ))}
        </div>

        {/* Legend (main.py line 469-473) */}
        <div style={{ display: 'flex', gap: '16px', marginTop: '12px', marginLeft: '160px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: 12, height: 12, backgroundColor: '#1B5E20', borderRadius: 2 }} />
            <span>Đang hoạt động (On)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: 12, height: 12, backgroundColor: '#757575', borderRadius: 2 }} />
            <span>Ngoại tuyến (Off)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: 12, height: 12, backgroundColor: '#B71C1C', borderRadius: 2 }} />
            <span>Bảo trì (Maintenance)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GanttChart;
