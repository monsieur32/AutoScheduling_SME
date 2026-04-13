import { useState, useEffect, useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { getCurrentSchedule, listMachines, listJobs, manualAdjust, clearSchedule, clearAllJobs } from '../../api/httpClient';

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
  const day = Math.floor(m / 1440);
  const minInDay = Math.floor(m % 1440);
  const h = Math.floor(minInDay / 60) + 7;
  const hFmt = (h >= 24 ? h - 24 : h).toString().padStart(2, '0');
  const min = minInDay % 60;
  const timeStr = `${hFmt}:${min.toString().padStart(2, '0')}`;
  return day > 0 ? `Ngày ${day + 1} ${timeStr}` : timeStr;
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
  const [overtimeConfig, setOvertimeConfig] = useState<any>(null);

  const handleClearData = async () => {
    if (!window.confirm("Bạn có chắc chắn muốn xoá TOÀN BỘ Lịch trình và Dữ liệu công việc để làm lại từ đầu không?")) return;
    try {
      await clearSchedule();
      await clearAllJobs();
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert("Lỗi khi xoá dữ liệu");
    }
  };
  const [detailData, setDetailData] = useState<any[]>([]);
  const [jobsQueue, setJobsQueue] = useState<any[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [schedData, machData, jobsData] = await Promise.all([
        getCurrentSchedule(), listMachines(), listJobs(),
      ]);
      setOvertimeConfig(schedData.overtime_config || null);
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

    // Diagonal hatch pattern
    const defs = svg.append('defs');

    // Lunch break pattern — red tint + dense diagonal
    const lunchPattern = defs.append('pattern')
      .attr('id', 'lunchHatch')
      .attr('patternUnits', 'userSpaceOnUse')
      .attr('width', 8)
      .attr('height', 8);
    lunchPattern.append('rect')
      .attr('width', 8).attr('height', 8)
      .attr('fill', 'rgba(220, 38, 38, 0.18)'); // red tint background
    lunchPattern.append('path')
      .attr('d', 'M-1,1 l2,-2 M0,8 l8,-8 M7,9 l2,-2')
      .attr('stroke', 'rgba(220, 38, 38, 0.55)')
      .attr('stroke-width', 1.8);

    // Off-hours pattern — dark gray + wide diagonal
    const offPattern = defs.append('pattern')
      .attr('id', 'offHatch')
      .attr('patternUnits', 'userSpaceOnUse')
      .attr('width', 12)
      .attr('height', 12);
    offPattern.append('rect')
      .attr('width', 12).attr('height', 12)
      .attr('fill', 'rgba(15, 23, 42, 0.4)'); // Giảm opacity nền một chút
    offPattern.append('path')
      .attr('d', 'M-1,1 l2,-2 M0,12 l12,-12 M11,13 l2,-2')
      .attr('stroke', 'rgba(100, 116, 139, 0.4)')
      .attr('stroke-width', 1.0);

    // Overtime pattern — orange tint + thin diagonal
    const overtimePattern = defs.append('pattern')
      .attr('id', 'overtimeHatch')
      .attr('patternUnits', 'userSpaceOnUse')
      .attr('width', 10)
      .attr('height', 10);
    overtimePattern.append('rect')
      .attr('width', 10).attr('height', 10)
      .attr('fill', 'rgba(245, 158, 11, 0.08)'); // orange tilt
    overtimePattern.append('path')
      .attr('d', 'M-1,1 l2,-2 M0,10 l10,-10 M9,11 l2,-2')
      .attr('stroke', 'rgba(245, 158, 11, 0.35)')
      .attr('stroke-width', 1.2);

    // Break block data — will be rendered AFTER bars so they stay on top
    const breakBlocks: { start: number; end: number; type: string }[] = [];
    const maxDays = Math.ceil(maxFinish / 1440) + 1;
    for (let day = 0; day <= maxDays; day++) {
      const lunchStart = day * 1440 + 265;
      const lunchEnd = day * 1440 + 310;
      if (lunchStart < maxFinish && lunchEnd > minStart) {
        breakBlocks.push({ start: Math.max(minStart, lunchStart), end: Math.min(maxFinish, lunchEnd), type: 'lunch' });
      }

      const adminEnd = day * 1440 + 510; // 15:30
      let overtimeEnd = adminEnd;
      if (overtimeConfig?.enabled) {
        overtimeEnd = day * 1440 + overtimeConfig.end_time_mins;
      }

      // Overtime region (15:30 -> actual end)
      if (overtimeEnd > adminEnd && adminEnd < maxFinish && overtimeEnd > minStart) {
        breakBlocks.push({ start: Math.max(minStart, adminEnd), end: Math.min(maxFinish, overtimeEnd), type: 'overtime' });
      }

      const offStart = overtimeEnd;
      const offEnd = (day + 1) * 1440 + 30;
      if (offStart < maxFinish && offEnd > minStart) {
        breakBlocks.push({ start: Math.max(minStart, offStart), end: Math.min(maxFinish, offEnd), type: 'offhours' });
      }
    }

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
        .attr('y1', -15).attr('y2', chartHeight + 10)
        .attr('stroke', 'var(--accent-cyan)').attr('stroke-width', 2).attr('stroke-dasharray', '4 2');
      g.append('text')
        .attr('x', xScale(currentMinute)).attr('y', -20)
        .attr('text-anchor', 'middle').attr('fill', 'var(--accent-cyan)').attr('font-size', 9).attr('font-weight', 800)
        .text('HIỆN TẠI');
    }

    // Shift boundary lines (15:30 and Dynamic End)
    for (let day = 0; day <= maxDays; day++) {
      const adminEnd = day * 1440 + 510;
      const isOt = overtimeConfig?.enabled && overtimeConfig.end_time_mins > 510;
      const shiftEnd = isOt ? (day * 1440 + overtimeConfig.end_time_mins) : adminEnd;

      // Always show 15:30 if it's not the final end line
      if (isOt && adminEnd >= minStart && adminEnd <= maxFinish) {
        g.append('line')
          .attr('x1', xScale(adminEnd)).attr('x2', xScale(adminEnd))
          .attr('y1', 0).attr('y2', chartHeight)
          .attr('stroke', 'rgba(255,255,255,0.1)').attr('stroke-width', 1).attr('stroke-dasharray', '2 2');

        g.append('text')
          .attr('x', xScale(adminEnd)).attr('y', chartHeight + 12)
          .attr('text-anchor', 'middle').attr('fill', 'var(--text-muted)').attr('font-size', 8)
          .text('HẾT GIỜ HC');
      }

      if (shiftEnd >= minStart && shiftEnd <= maxFinish) {
        g.append('line')
          .attr('x1', xScale(shiftEnd)).attr('x2', xScale(shiftEnd))
          .attr('y1', -10).attr('y2', chartHeight + 5)
          .attr('stroke', 'var(--accent-red)').attr('stroke-width', 1.5).attr('stroke-dasharray', '10 5');

        g.append('text')
          .attr('x', xScale(shiftEnd)).attr('y', -15)
          .attr('text-anchor', 'middle').attr('fill', 'var(--accent-red)').attr('font-size', 10).attr('font-weight', 700)
          .text(isOt ? 'HẾT GIỜ TĂNG CA' : 'HẾT CA 15:30');
      }

      const nextShiftStart = day * 1440 + 30;
      if (nextShiftStart >= minStart && nextShiftStart <= maxFinish && day > 0) {
        g.append('line')
          .attr('x1', xScale(nextShiftStart)).attr('x2', xScale(nextShiftStart))
          .attr('y1', -10).attr('y2', chartHeight + 5)
          .attr('stroke', 'var(--accent-green)').attr('stroke-width', 1).attr('stroke-dasharray', '5 5');
      }
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
      const workerStatus = op.worker_status || 'pending';
      const machStatus = machineStatusMap[op.machine] || 'On';
      let color = STATUS_COLORS[machStatus] || STATUS_COLORS['On'];
      let baseOpacity = 0.85;

      if (workerStatus === 'completed') {
        color = 'rgba(176, 190, 197, 0.4)'; // Xám tắt
        baseOpacity = 0.5;
      } else if (workerStatus === 'accepted') {
        color = '#1976D2'; // Xanh đang chạy
        baseOpacity = 0.95;
      }

      // Setup block
      if (op.setup > 0) {
        const setupStart = Math.max(op.start - op.setup, minStart);
        barG.append('rect')
          .attr('x', xScale(setupStart)).attr('y', y)
          .attr('width', Math.max(xScale(op.start) - xScale(setupStart), 0))
          .attr('height', h).attr('fill', color).attr('opacity', Math.min(baseOpacity, 0.2)).attr('rx', 4);
      }

      // Main bar
      const mainBar = barG.append('rect')
        .attr('x', x).attr('y', y).attr('width', w).attr('height', h)
        .attr('fill', color).attr('opacity', baseOpacity).attr('rx', 6)
        .attr('cursor', 'grab').attr('stroke', 'transparent').attr('stroke-width', 2);

      // Label
      if (w > 50) {
        let labelText = op.job_id.length > 14 ? op.job_id.slice(-12) : op.job_id;
        if (workerStatus === 'completed') labelText = `[Xong] ${labelText}`;
        else if (workerStatus === 'accepted') labelText = `[Đang chạy] ${labelText}`;

        barG.append('text')
          .attr('x', x + w / 2).attr('y', y + h / 2 + 1)
          .attr('text-anchor', 'middle').attr('dominant-baseline', 'middle')
          .attr('fill', 'white').attr('font-size', 10).attr('font-weight', 600)
          .attr('pointer-events', 'none')
          .text(labelText);
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
              ${op.note ? `<div style="color:#f59e0b;margin-top:4px"> ${op.note}</div>` : ''}
              <div style="color:#64748b;margin-top:6px;font-size:10px">Kéo để di chuyển</div>
            `);
        })
        .on('mousemove', (event: MouseEvent) => {
          tooltip.style('left', `${event.clientX + 12}px`).style('top', `${event.clientY - 10}px`);
        })
        .on('mouseleave', () => {
          mainBar.attr('opacity', baseOpacity).attr('stroke', 'transparent');
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

    // ── Break blocks — drawn AFTER bars to always show on top ─────
    const breaksG = g.append('g').attr('class', 'breaks-overlay');
    breaksG.selectAll('rect.break-overlay').data(breakBlocks).join('rect')
      .attr('class', 'break-overlay')
      .attr('x', (d: { start: number; end: number; type: string }) => xScale(d.start))
      .attr('y', 0)
      .attr('width', (d: { start: number; end: number; type: string }) => Math.max(0, xScale(d.end) - xScale(d.start)))
      .attr('height', chartHeight)
      .attr('fill', (d: { start: number; end: number; type: string }) => {
        if (d.type === 'lunch') return 'url(#lunchHatch)';
        if (d.type === 'overtime') return 'url(#overtimeHatch)';
        return 'url(#offHatch)';
      })
      .attr('opacity', 1)
      .attr('pointer-events', 'none');

    // Break labels
    breakBlocks.forEach((b: { start: number; end: number; type: string }) => {
      const bw = xScale(b.end) - xScale(b.start);
      if (bw > 28) {
        breaksG.append('text')
          .attr('x', xScale(b.start) + bw / 2)
          .attr('y', chartHeight / 2)
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'middle')
          .attr('fill', b.type === 'lunch' ? 'rgba(224, 0, 0, 0.88)' : b.type === 'overtime' ? 'rgba(245, 158, 11, 0.9)' : 'rgba(100, 116, 139, 0.8)')
          .attr('font-size', b.type === 'lunch' ? 15 : 12)
          .attr('font-weight', 800)
          .attr('pointer-events', 'none')
          .attr('transform', `rotate(-90, ${xScale(b.start) + bw / 2}, ${chartHeight / 2})`)
          .text(b.type === 'lunch' ? 'Nghỉ trưa' : b.type === 'overtime' ? 'Tăng ca' : 'Ngoài giờ');
      }
    });

    // X-axis label
    svg.append('text')
      .attr('x', MARGIN.left + chartWidth / 2).attr('y', totalH - 5)
      .attr('text-anchor', 'middle').attr('fill', '#64748b').attr('font-size', 11)
      .text('Thời gian (07:30 = phút 0)');

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
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}> Kéo thả để điều chỉnh thời gian xử lí</span>
            <button className="btn btn-secondary btn-sm" onClick={fetchData}>ResetChart</button>
          </div>
        </div>

        <div style={{ overflowX: 'auto', marginTop: 'var(--spacing-md)' }}>
          <svg ref={svgRef} />
        </div>

        {/* Legend — by machine status matching Streamlit color_discrete_map */}
        <div style={{ display: 'flex', gap: 'var(--spacing-lg)', marginTop: 'var(--spacing-md)', paddingTop: 'var(--spacing-md)', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#1B5E20' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Máy On</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#757575' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Off</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#B71C1C' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Bảo trì</span>
          </div>
          <div style={{ paddingLeft: 8, borderLeft: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: '#1976D2' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Đang chạy</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: 'rgba(176, 190, 197, 0.4)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Đã xong</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: 'rgba(245, 158, 11, 0.2)', border: '1px solid rgba(245, 158, 11, 0.5)' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Giờ tăng ca</span>
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
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
              <button className="btn btn-secondary btn-sm" onClick={e => { e.stopPropagation(); handleDownloadCSV(); }}>
                Tải xuống CSV
              </button>
              <button
                className="btn btn-primary btn-sm"
                style={{ backgroundColor: 'var(--accent-red)', borderColor: 'var(--accent-red)' }}
                onClick={e => { e.stopPropagation(); handleClearData(); }}
              >
                Xóa CSDL (Test)
              </button>
            </div>
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
