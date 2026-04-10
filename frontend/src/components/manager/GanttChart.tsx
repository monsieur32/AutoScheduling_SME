import { useState, useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { getCurrentSchedule, listMachines, listJobs, manualAdjust } from '../../api/httpClient';

/* ── Types ─────────────────────────────────────────────────── */
interface Operation {
  id: number;
  job_id: string;
  op_idx: number;
  machine: string;
  start: number;
  finish: number;
  setup: number;
  note: string | null;
  worker_status: string;
}

interface MachineInfo { id: string; name: string; status: string; }

/* ── Constants ─────────────────────────────────────────────── */
const STATUS_COLORS: Record<string, string> = {
  'On': '#1B5E20',
  'Off': '#757575',
  'Maintenance': '#B71C1C',
};

const MARGIN = { top: 50, right: 40, bottom: 40, left: 140 };
const ROW_HEIGHT = 48;
const BAR_PADDING = 6;

function minuteToTime(m: number): string {
  const h = Math.floor(m / 60) + 7;
  const min = m % 60;
  return `${h.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`;
}

/* ── Component ─────────────────────────────────────────────── */
export default function GanttChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [machineStatusMap, setMachineStatusMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');
  const [showDetail, setShowDetail] = useState(false);
  const [detailData, setDetailData] = useState<any[]>([]);
  const [jobsQueue, setJobsQueue] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [schedData, machData, jobsData] = await Promise.all([
        getCurrentSchedule(), listMachines(), listJobs(),
      ]);
      setOperations(schedData.schedule || []);
      const statusMap: Record<string, string> = {};
      (machData.machines || []).forEach((m: MachineInfo) => { statusMap[m.id] = m.status; });
      setMachineStatusMap(statusMap);
      setJobsQueue(jobsData.jobs || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Listen for schedule-updated events
  useEffect(() => {
    const handler = () => { setTimeout(fetchData, 500); };
    window.addEventListener('schedule-updated', handler);
    return () => window.removeEventListener('schedule-updated', handler);
  }, [fetchData]);

  /* ── Build detail table data ───────────────────────────── */
  useEffect(() => {
    if (!operations.length) { setDetailData([]); return; }
    const baseTime = new Date();
    baseTime.setHours(7, 0, 0, 0);

    const merged = operations.map(op => {
      const jobInfo = jobsQueue.find(j => j.id === op.job_id) || {};
      const startTime = new Date(baseTime.getTime() + op.start * 60000);
      const finishTime = new Date(baseTime.getTime() + op.finish * 60000);
      return {
        job_id: op.job_id,
        project_name: jobInfo.project_name || '',
        project_code: jobInfo.project_code || '',
        hexcode: jobInfo.hexcode || '',
        machine: op.machine,
        machine_status: machineStatusMap[op.machine] || 'On',
        Start_Time: startTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        Finish_Time: finishTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        setup: op.setup,
        material_group: jobInfo.material_group || '',
        size_mm: jobInfo.size_mm || '',
        quantity: jobInfo.quantity || '',
        worker_status: op.worker_status,
      };
    });
    setDetailData(merged);
  }, [operations, jobsQueue, machineStatusMap]);

  /* ── D3 Render ─────────────────────────────────────────── */
  useEffect(() => {
    if (!operations.length || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const machineIds = [...new Set<string>(operations.map(o => o.machine))].sort();
    const minStart = Math.min(...operations.map(o => Math.max(0, o.start - o.setup)));
    const maxFinish = Math.max(...operations.map(o => o.finish)) + 10;

    const containerWidth = containerRef.current?.clientWidth || 1000;
    const chartWidth = Math.max(containerWidth - MARGIN.left - MARGIN.right, 600);
    const chartHeight = machineIds.length * ROW_HEIGHT;
    const totalW = chartWidth + MARGIN.left + MARGIN.right;
    const totalH = chartHeight + MARGIN.top + MARGIN.bottom;

    svg.attr('width', totalW).attr('height', totalH);

    const xScale = d3.scaleLinear().domain([minStart, maxFinish]).range([0, chartWidth]);
    const yScale = d3.scaleBand<string>().domain(machineIds).range([0, chartHeight]).padding(0.1);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid lines
    const tickInterval = (maxFinish - minStart) <= 60 ? 10 : (maxFinish - minStart) <= 180 ? 30 : 60;
    const tickValues: number[] = [];
    for (let t = Math.ceil(minStart / tickInterval) * tickInterval; t <= maxFinish; t += tickInterval) tickValues.push(t);

    g.append('g').selectAll('line').data(tickValues).join('line')
      .attr('x1', (d: number) => xScale(d)).attr('x2', (d: number) => xScale(d))
      .attr('y1', 0).attr('y2', chartHeight)
      .attr('stroke', 'rgba(255,255,255,0.04)').attr('stroke-dasharray', '3 6');

    // Row backgrounds
    g.append('g').selectAll('rect').data(machineIds).join('rect')
      .attr('x', 0).attr('width', chartWidth)
      .attr('y', (d: string) => yScale(d) || 0).attr('height', yScale.bandwidth())
      .attr('fill', (_: string, i: number) => i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)')
      .attr('rx', 4);

    // X-axis
    g.append('g').attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale).tickValues(tickValues).tickFormat((d: any) => minuteToTime(d)))
      .selectAll('text').attr('fill', '#64748b').attr('font-size', 11);
    g.select('.domain').attr('stroke', 'rgba(255,255,255,0.1)');
    g.selectAll('.tick line').attr('stroke', 'rgba(255,255,255,0.06)');

    // Y-axis labels
    g.append('g').selectAll('text').data(machineIds).join('text')
      .attr('x', -10).attr('y', (d: string) => (yScale(d) || 0) + yScale.bandwidth() / 2)
      .attr('text-anchor', 'end').attr('dominant-baseline', 'middle')
      .attr('fill', '#94a3b8').attr('font-size', 11).attr('font-weight', 600)
      .attr('font-family', "'JetBrains Mono', monospace")
      .text((d: string) => d);

    // Now-time indicator
    const now = new Date();
    const currentMinute = (now.getHours() - 7) * 60 + now.getMinutes();
    if (currentMinute >= minStart && currentMinute <= maxFinish) {
      g.append('line')
        .attr('x1', xScale(currentMinute)).attr('x2', xScale(currentMinute))
        .attr('y1', -10).attr('y2', chartHeight + 5)
        .attr('stroke', '#ef4444').attr('stroke-width', 2).attr('stroke-dasharray', '6 3');
      g.append('text')
        .attr('x', xScale(currentMinute)).attr('y', -15)
        .attr('text-anchor', 'middle').attr('fill', '#ef4444').attr('font-size', 10).attr('font-weight', 700)
        .text('NOW');
    }

    const tooltip = d3.select(tooltipRef.current);
    const barsG = g.append('g');

    // Bars — COLOR BY MACHINE STATUS (matching original Streamlit)
    operations.forEach(op => {
      const barG = barsG.append('g');
      const y = (yScale(op.machine) || 0) + BAR_PADDING;
      const h = yScale.bandwidth() - BAR_PADDING * 2;
      const x = xScale(op.start);
      const w = Math.max(xScale(op.finish) - xScale(op.start), 4);
      const machStatus = machineStatusMap[op.machine] || 'On';
      const color = STATUS_COLORS[machStatus] || STATUS_COLORS['On'];

      // Setup block
      if (op.setup > 0) {
        const setupStart = Math.max(op.start - op.setup, minStart);
        barG.append('rect')
          .attr('x', xScale(setupStart)).attr('y', y)
          .attr('width', Math.max(xScale(op.start) - xScale(setupStart), 0))
          .attr('height', h).attr('fill', color).attr('opacity', 0.2).attr('rx', 4);
      }

      // Main bar
      const mainBar = barG.append('rect')
        .attr('x', x).attr('y', y).attr('width', w).attr('height', h)
        .attr('fill', color).attr('opacity', 0.85).attr('rx', 6)
        .attr('cursor', 'grab').attr('stroke', 'transparent').attr('stroke-width', 2);

      // Label
      if (w > 50) {
        barG.append('text')
          .attr('x', x + w / 2).attr('y', y + h / 2 + 1)
          .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
          .attr('fill', 'white').attr('font-size', 10).attr('font-weight', 600)
          .attr('pointer-events', 'none')
          .text(op.job_id.length > 14 ? op.job_id.slice(-12) : op.job_id);
      }

      // Hover
      barG
        .on('mouseenter', (event: MouseEvent) => {
          mainBar.attr('opacity', 1).attr('stroke', 'white');
          tooltip.style('display', 'block')
            .style('left', `${event.clientX + 12}px`).style('top', `${event.clientY - 10}px`)
            .html(`
              <div style="font-weight:700;margin-bottom:4px">${op.job_id}</div>
              <div>Máy: <b>${op.machine}</b> (${machStatus})</div>
              <div>Thời gian: <b>${minuteToTime(op.start)} → ${minuteToTime(op.finish)}</b></div>
              <div>Gia công: <b>${op.finish - op.start}p</b> | Setup: <b>${op.setup}p</b></div>
              <div>Worker: <b>${op.worker_status}</b></div>
              ${op.note ? `<div style="color:#f59e0b;margin-top:4px">⚠ ${op.note}</div>` : ''}
              <div style="color:#64748b;margin-top:6px;font-size:10px">🖱 Kéo để di chuyển</div>
            `);
        })
        .on('mousemove', (event: MouseEvent) => {
          tooltip.style('left', `${event.clientX + 12}px`).style('top', `${event.clientY - 10}px`);
        })
        .on('mouseleave', () => {
          mainBar.attr('opacity', 0.85).attr('stroke', 'transparent');
          tooltip.style('display', 'none');
        });

      // Drag & Drop
      let dragStartX = 0;
      let originalStart = op.start;
      const drag = d3.drag<SVGGElement, unknown>()
        .on('start', function (event) {
          dragStartX = event.x; originalStart = op.start;
          d3.select(this).raise();
          mainBar.attr('cursor', 'grabbing').attr('opacity', 1).attr('stroke', '#f59e0b');
        })
        .on('drag', function (event) {
          const dx = event.x - dragStartX;
          const minuteDelta = Math.round(dx / (chartWidth / (maxFinish - minStart)));
          const newStart = Math.max(0, originalStart + minuteDelta);
          const duration = op.finish - op.start;
          const newX = xScale(newStart);
          const newW = xScale(newStart + duration) - newX;
          mainBar.attr('x', newX).attr('width', newW);
          barG.selectAll('text').attr('x', newX + newW / 2);
        })
        .on('end', async function (event) {
          const dx = event.x - dragStartX;
          const minuteDelta = Math.round(dx / (chartWidth / (maxFinish - minStart)));
          const newStart = Math.max(0, originalStart + minuteDelta);
          const duration = op.finish - op.start;
          mainBar.attr('cursor', 'grab').attr('stroke', 'transparent');
          if (minuteDelta === 0) return;
          try {
            await manualAdjust({ operation_id: op.id, new_start: newStart, new_finish: newStart + duration });
            setToast(` Đã di chuyển ${op.job_id} → ${minuteToTime(newStart)}`);
            setTimeout(() => setToast(''), 3000);
            fetchData();
          } catch (e: any) { setToast(` ${e.message}`); fetchData(); }
        });
      drag(barG as any);
    });

    // X-axis label
    svg.append('text')
      .attr('x', MARGIN.left + chartWidth / 2).attr('y', totalH - 5)
      .attr('text-anchor', 'middle').attr('fill', '#64748b').attr('font-size', 11)
      .text('Thời gian (07:00 = phút 0)');

  }, [operations, machineStatusMap, fetchData]);

  /* ── CSV Download ──────────────────────────────────────── */
  const handleDownloadCSV = () => {
    if (!detailData.length) return;
    const headers = Object.keys(detailData[0]);
    const csv = [headers.join(','), ...detailData.map(row =>
      headers.map(h => `"${String((row as any)[h] ?? '').replace(/"/g, '""')}"`).join(',')
    )].join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'schedule.csv';
    a.click();
  };

  /* ── Render ────────────────────────────────────────────── */
  if (loading) {
    return <div className="gantt-container flex-center" style={{ minHeight: 300 }}><div className="spinner spinner-lg" /></div>;
  }

  if (!operations.length) {
    return (
      <div className="gantt-container">
        <div className="empty-state">
          <p>Chưa có dữ liệu lịch trình.</p>
        </div>
      </div>
    );
  }

  // Summary
  const totalJobs = new Set(operations.map(o => o.job_id)).size;
  const totalMachines = new Set(operations.map(o => o.machine)).size;
  const makespan = Math.max(...operations.map(o => o.finish));

  return (
    <div>
      {/* Gantt */}
      <div className="gantt-container" ref={containerRef}>
        <div className="card-header">
          <span className="card-title"> BIỂU ĐỒ KẾ HOẠCH SẢN XUẤT (GANTT)</span>
          <div className="flex-gap">
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>🖱 Kéo thả để điều chỉnh</span>
            <button className="btn btn-secondary btn-sm" onClick={fetchData}>🔄</button>
          </div>
        </div>

        <div style={{ overflowX: 'auto', marginTop: 'var(--spacing-md)' }}>
          <svg ref={svgRef} />
        </div>

        {/* Legend — by machine status matching Streamlit color_discrete_map */}
        <div style={{ display: 'flex', gap: 'var(--spacing-lg)', marginTop: 'var(--spacing-md)', paddingTop: 'var(--spacing-md)', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#1B5E20' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Bình thường (On)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#757575' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Tắt máy (Off)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#B71C1C' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Bảo trì (Maintenance)</span>
          </div>
          <div style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>
            {totalJobs} đơn | {totalMachines} máy | Makespan: {makespan}p
          </div>
        </div>
      </div>

      {/* Detail Table (Expandable) — matching original "Xem chi tiết dữ liệu" */}
      <div className="card" style={{ marginTop: 'var(--spacing-md)' }}>
        <div className="card-header" onClick={() => setShowDetail(!showDetail)} style={{ cursor: 'pointer' }}>
          <span className="card-title">{showDetail ? '▼' : '▶'} Xem chi tiết dữ liệu</span>
          {showDetail && (
            <button className="btn btn-secondary btn-sm" onClick={e => { e.stopPropagation(); handleDownloadCSV(); }}>
              Tải xuống CSV
            </button>
          )}
        </div>

        {showDetail && detailData.length > 0 && (
          <div style={{ overflowX: 'auto', marginTop: 'var(--spacing-md)' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Dự án</th>
                  <th>Mã CT</th>
                  <th>Hex</th>
                  <th>Máy</th>
                  <th>Trạng thái</th>
                  <th>Bắt đầu</th>
                  <th>Kết thúc</th>
                  <th>Setup</th>
                  <th>Vật liệu</th>
                  <th>Size</th>
                  <th>SL</th>
                </tr>
              </thead>
              <tbody>
                {detailData.map((row, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem' }}>{row.job_id}</td>
                    <td>{row.project_name}</td>
                    <td>{row.project_code}</td>
                    <td>{row.hexcode}</td>
                    <td>{row.machine}</td>
                    <td>
                      <span className={`badge ${row.machine_status === 'On' ? 'badge-success' : row.machine_status === 'Maintenance' ? 'badge-danger' : 'badge-secondary'}`}>
                        {row.machine_status}
                      </span>
                    </td>
                    <td>{row.Start_Time}</td>
                    <td>{row.Finish_Time}</td>
                    <td>{row.setup}p</td>
                    <td>{row.material_group}</td>
                    <td>{row.size_mm}</td>
                    <td>{row.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Tooltip */}
      <div ref={tooltipRef} style={{
        display: 'none', position: 'fixed', background: 'rgba(15, 23, 42, 0.95)',
        border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
        padding: '10px 14px', fontSize: '0.8rem', color: '#f1f5f9',
        pointerEvents: 'none', zIndex: 1000, backdropFilter: 'blur(8px)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)', maxWidth: 280, lineHeight: 1.5,
      }} />

      {toast && <div className={`toast ${toast.startsWith('✅') ? 'success' : 'error'}`}>{toast}</div>}
    </div>
  );
}
