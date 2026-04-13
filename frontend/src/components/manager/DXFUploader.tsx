import { useState, useEffect, useRef, useCallback } from 'react';
import { uploadDXF, getDXFStatus, createJobsBatch, listMasterData, createMasterRecord } from '../../api/httpClient';

/* ── Types ─────────────────────────────────────────────────── */
interface DXFInfo {
  filename: string;
  status: string;
  message?: string;
  total_len_mm: number;
  straight_len_mm: number;
  curved_len_mm: number;
  complexity_ratio: number;
  texts?: string[];
  warnings?: string[];
}

interface ProcessDef {
  process_name: string;
  capability_required: string;
  step_order: number;
}

interface ProjectOption {
  id: number;
  project_name: string;
  project_code: string;
  hexcode: string | null;
}

interface FileConfig {
  file: File;
  dxfInfo: DXFInfo;
  material: string;
  quantity: number;
  processType: string;
  detailLenMm: number;
}

const MATERIALS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];

/* ── Component ─────────────────────────────────────────────── */
export default function DXFUploader() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState<Record<string, DXFInfo>>({});
  const [fileConfigs, setFileConfigs] = useState<FileConfig[]>([]);
  const [toast, setToast] = useState('');
  const [dragOver, setDragOver] = useState(false);

  // Project
  const [projects, setProjects] = useState<ProjectOption[]>([]);
  const [selectedProjectIdx, setSelectedProjectIdx] = useState(-1);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newPName, setNewPName] = useState('');
  const [newPCode, setNewPCode] = useState('');
  const [newPHex, setNewPHex] = useState('');

  // Priority & Dates
  const [priority, setPriority] = useState('Bình thường');
  const today = new Date();
  const tomorrow = new Date(today.getTime() + 86400000);
  const [startDate, setStartDate] = useState(today.toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState('07:30');
  const [dueDate, setDueDate] = useState(tomorrow.toISOString().slice(0, 10));
  const [dueTime, setDueTime] = useState('17:00');

  // Process definitions from DB
  const [processMap, setProcessMap] = useState<Record<string, string[]>>({});

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 4000); };

  // Load projects and process definitions on mount
  useEffect(() => {
    listMasterData('projects').then(d => {
      setProjects((d.records || []).map((r: any) => ({
        id: r.id, project_name: r.project_name, project_code: r.project_code, hexcode: r.hexcode
      })));
    }).catch(() => { });

    listMasterData('processes').then(d => {
      const map: Record<string, string[]> = {};
      for (const r of (d.records || []) as ProcessDef[]) {
        if (!map[r.process_name]) map[r.process_name] = [];
        if (!map[r.process_name].includes(r.capability_required)) {
          map[r.process_name].push(r.capability_required);
        }
      }
      setProcessMap(map);
    }).catch(() => { });
  }, []);

  /* ── File Handling ──────────────────────────────────────── */
  const addFiles = (newFiles: FileList | File[]) => {
    const dxfFiles = Array.from(newFiles).filter(f => f.name.toLowerCase().endsWith('.dxf'));
    if (dxfFiles.length === 0) return;
    setFiles(prev => [...prev, ...dxfFiles]);
  };

  const handleAnalyze = async () => {
    if (!files.length) return;
    setAnalyzing(true);
    try {
      const { task_token } = await uploadDXF(files);
      let status = 'pending';
      let result: any = null;
      while (status === 'pending' || status === 'running') {
        await new Promise(r => setTimeout(r, 1000));
        const data = await getDXFStatus(task_token);
        status = data.status;
        if (status === 'completed') result = data.result;
        if (status === 'failed') { showToast(` ${data.error}`); break; }
      }
      if (result) {
        const map: Record<string, DXFInfo> = {};
        for (const r of result) {
          map[r.filename] = r;
        }
        setAnalyzed(map);

        // Initialize file configs
        const configs: FileConfig[] = [];
        files.forEach(f => {
          const info = map[f.name];
          if (info && info.status === 'success') {
            configs.push({
              file: f, dxfInfo: info,
              material: 'C', quantity: 1,
              processType: Object.keys(processMap)[0] || '',
              detailLenMm: info.total_len_mm,
            });
          }
        });
        setFileConfigs(configs);
      }
    } catch (e: any) { showToast(` ${e.message}`); }
    setAnalyzing(false);
  };

  /* ── Process filtering ─────────────────────────────────── */
  const getValidProcesses = useCallback((dxfInfo: DXFInfo): string[] => {
    const hasCurve = (dxfInfo.curved_len_mm || 0) > 0;
    const valid: string[] = [];
    for (const [pName, caps] of Object.entries(processMap)) {
      const isStraightOnly = caps.includes('Cut_straight') && !caps.includes('Cut_contour');
      if (hasCurve && isStraightOnly) continue;
      valid.push(pName);
    }
    return valid.length ? valid : Object.keys(processMap);
  }, [processMap]);

  const needsDetailLen = (processType: string): boolean => {
    const lower = processType.toLowerCase();
    return ['vát', 'rãnh', 'biên dạng', 'chỉ', 'hoa văn', 'tất cả'].some(k => lower.includes(k));
  };

  const updateConfig = (idx: number, patch: Partial<FileConfig>) => {
    setFileConfigs(prev => prev.map((c, i) => i === idx ? { ...c, ...patch } : c));
  };

  /* ── Create new project ────────────────────────────────── */
  const handleCreateProject = async () => {
    if (!newPName.trim() || !newPCode.trim()) { showToast(' Tên và Mã công trình bắt buộc!'); return; }
    const existing = projects.find(p => p.project_code === newPCode.trim());
    if (existing) { showToast(` Mã '${newPCode}' đã tồn tại!`); return; }
    try {
      const created = await createMasterRecord('projects', {
        project_name: newPName.trim(), project_code: newPCode.trim(), hexcode: newPHex.trim() || null,
      });
      setProjects(prev => [...prev, { id: created.id, project_name: created.project_name, project_code: created.project_code, hexcode: created.hexcode }]);
      setSelectedProjectIdx(projects.length);
      setShowNewProject(false);
      setNewPName(''); setNewPCode(''); setNewPHex('');
      showToast(` Tạo dự án '${newPName}' thành công!`);
    } catch (e: any) { showToast(` ${e.message}`); }
  };

  /* ── Add to queue ──────────────────────────────────────── */
  const handleAddToQueue = async () => {
    if (selectedProjectIdx < 0 || !projects[selectedProjectIdx]) {
      showToast(' Vui lòng chọn hoặc tạo Dự án trước!'); return;
    }
    if (!fileConfigs.length) { showToast(' Chưa có bản vẽ nào được phân tích!'); return; }

    const proj = projects[selectedProjectIdx];
    const ts = Date.now() % 10000;
    const startDT = `${startDate}T${startTime}:00`;
    const dueDT = `${dueDate}T${dueTime}:00`;

    const jobs = fileConfigs.map((cfg, idx) => {
      const shortName = cfg.file.name.slice(0, 6).replace(/\s/g, '_').replace('.dxf', '');
      const prefix = proj.project_code.trim() || `JOB-${ts}`;
      const jobId = `${prefix}.${idx + 1}_${shortName}_${ts}`;
      const ops = processMap[cfg.processType] || [];

      return {
        id: jobId,
        project_name: proj.project_name,
        project_code: proj.project_code,
        hexcode: proj.hexcode,
        material_group: cfg.material,
        process_steps: ops.length,
        size_mm: cfg.dxfInfo.total_len_mm,
        detail_len_mm: cfg.detailLenMm,
        complexity: cfg.dxfInfo.complexity_ratio,
        quantity: cfg.quantity,
        operations: ops,
        process: cfg.processType,
        process_machine: JSON.stringify(ops),
        start_time: startDT,
        due_date: dueDT,
        priority: priority,
      };
    });

    try {
      const result = await createJobsBatch(jobs);
      showToast(` Đã thêm ${result.total} bản vẽ vào hàng đợi!`);
      setFiles([]); setAnalyzed({}); setFileConfigs([]);
    } catch (e: any) { showToast(` ${e.message}`); }
  };

  /* ── Render ────────────────────────────────────────────── */
  return (
    <>
      {/* ═══ Section 1: Thiết lập Đơn hàng ═══ */}
      <div className="card">
        <h3 className="card-title">Thiết lập chung cho Đơn hàng</h3>

        {/* Row 1: Project selector + Priority */}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-md)' }}>
          <div className="form-group">
            <label className="form-label">Chọn Dự án / Công trình hiện có</label>
            <select className="form-select" value={selectedProjectIdx} onChange={e => setSelectedProjectIdx(Number(e.target.value))}>
              <option value={-1}>-- Chọn dự án --</option>
              {projects.map((p, i) => (
                <option key={p.id} value={i}>
                  [{p.project_code}] {p.project_name} (Hex: {p.hexcode || 'N/A'})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Mức độ ưu tiên</label>
            <select className="form-select" value={priority} onChange={e => setPriority(e.target.value)}>
              <option value="Bình thường">Bình thường</option>
              <option value="Cao">Cao</option>
              <option value="Gấp">Gấp</option>
            </select>
          </div>
        </div>

        {/* Create new project (expandable) */}
        <div style={{ marginTop: 'var(--spacing-sm)' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => setShowNewProject(!showNewProject)}>
            {showNewProject ? '▼' : '▶'} Tạo mới Dự án nhanh tại đây
          </button>
          {showNewProject && (
            <div style={{ marginTop: 'var(--spacing-sm)', padding: 'var(--spacing-md)', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--spacing-md)' }}>
                <div className="form-group">
                  <label className="form-label">Tên Công trình *</label>
                  <input className="form-input" value={newPName} onChange={e => setNewPName(e.target.value)} placeholder="VD: Tòa nhà ABC" />
                </div>
                <div className="form-group">
                  <label className="form-label">Mã Công trình *</label>
                  <input className="form-input" value={newPCode} onChange={e => setNewPCode(e.target.value)} placeholder="VD: PRJ001" />
                </div>
                <div className="form-group">
                  <label className="form-label">Hexcode</label>
                  <input className="form-input" value={newPHex} onChange={e => setNewPHex(e.target.value)} placeholder="VD: #FF5733" />
                </div>
              </div>
              <button className="btn btn-primary btn-sm" onClick={handleCreateProject} style={{ marginTop: 'var(--spacing-sm)' }}>
                Lưu & Thêm Dự án mới
              </button>
            </div>
          )}
        </div>

        {/* Row 2: Date/Time inputs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-lg)' }}>
          <div className="form-group">
            <label className="form-label">Ngày bắt đầu làm</label>
            <input className="form-input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Giờ bắt đầu làm</label>
            <input className="form-input" type="time" value={startTime} onChange={e => setStartTime(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Hạn chót (Due Date)</label>
            <input className="form-input" type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Giờ giao</label>
            <input className="form-input" type="time" value={dueTime} onChange={e => setDueTime(e.target.value)} />
          </div>
        </div>
      </div>

      {/* ═══ Section 2: Upload DXF ═══ */}
      <div className="card" style={{ marginTop: 'var(--spacing-lg)' }}>
        <h3 className="card-title"> Tải lên Bản vẽ & Phân tích</h3>

        {/* Drop zone */}
        <div
          className={`upload-area ${dragOver ? 'drag-over' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input ref={fileInputRef} type="file" accept=".dxf" multiple hidden onChange={e => e.target.files && addFiles(e.target.files)} />
          <div className="upload-icon"></div>
          <div className="upload-text">Kéo thả hoặc nhấp để chọn file DXF</div>
          <div className="upload-hint">Hỗ trợ nhiều file .dxf cùng lúc</div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div style={{ marginTop: 'var(--spacing-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-sm)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>{files.length} file đã chọn</span>
              <button className="btn btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                {analyzing ? <><span className="spinner" /> Đang phân tích...</> : ' Phân tích bản vẽ'}
              </button>
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)', flexWrap: 'wrap' }}>
              {files.map((f, i) => (
                <span key={i} className="badge badge-info">{f.name}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ═══ Section 3: Config per file ═══ */}
      {fileConfigs.length > 0 && (
        <div className="card" style={{ marginTop: 'var(--spacing-lg)' }}>
          <h3 className="card-title"> Cấu hình cho từng Bản vẽ</h3>

          {fileConfigs.map((cfg, idx) => {
            const info = cfg.dxfInfo;
            const validProcesses = getValidProcesses(info);

            return (
              <div key={idx} style={{
                marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)',
                border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)',
                background: 'rgba(255,255,255,0.02)',
              }}>
                <h4 style={{ marginBottom: 'var(--spacing-sm)' }}>
                  Bản vẽ {idx + 1}: {cfg.file.name}
                </h4>

                {/* DXF Analysis results */}
                <div className="badge badge-success" style={{ padding: '6px 12px', fontSize: '0.8rem', marginBottom: 'var(--spacing-sm)' }}>
                  Dài thẳng: {info.straight_len_mm}mm | Cong/Tròn: {info.curved_len_mm}mm | Tổng: {info.total_len_mm}mm
                </div>

                {/* DXF Texts */}
                {info.texts && info.texts.length > 0 && (
                  <div className="badge badge-info" style={{ display: 'block', padding: '6px 12px', fontSize: '0.8rem', marginBottom: 'var(--spacing-sm)' }}>
                    Ghi chú trong bản vẽ: {info.texts.slice(0, 10).join(', ')}{info.texts.length > 10 ? '...' : ''}
                  </div>
                )}

                {/* DXF Warnings */}
                {info.warnings && info.warnings.length > 0 && (
                  <div className="badge badge-warning" style={{ display: 'block', padding: '6px 12px', fontSize: '0.8rem', marginBottom: 'var(--spacing-sm)' }}>
                    Cảnh báo: {info.warnings.join('; ')}
                  </div>
                )}

                {/* Config inputs */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: 'var(--spacing-md)' }}>
                  <div className="form-group">
                    <label className="form-label">Nhóm Vật Liệu</label>
                    <select className="form-select" value={cfg.material} onChange={e => updateConfig(idx, { material: e.target.value })}>
                      {MATERIALS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Số lượng (tấm)</label>
                    <input className="form-input" type="number" min={1} value={cfg.quantity}
                      onChange={e => updateConfig(idx, { quantity: parseInt(e.target.value) || 1 })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Quy trình Gia công phù hợp</label>
                    <select className="form-select" value={cfg.processType}
                      onChange={e => updateConfig(idx, { processType: e.target.value })}>
                      {validProcesses.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                </div>

                {/* Detail length for special processes */}
                {needsDetailLen(cfg.processType) && (
                  <div className="form-group" style={{ marginTop: 'var(--spacing-sm)' }}>
                    <label className="form-label">
                      Chiều dài chi tiết cần gia công (mm) — Dành cho Vát/Rãnh/Biên dạng
                    </label>
                    <input className="form-input" type="number" min={0} step={50} value={cfg.detailLenMm}
                      onChange={e => updateConfig(idx, { detailLenMm: parseFloat(e.target.value) || 0 })} />
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                      Hệ thống sẽ dùng chiều dài này để tính toán thời gian thay vì dùng toàn bộ chiều dài phôi.
                    </span>
                  </div>
                )}
              </div>
            );
          })}

          <button className="btn btn-primary btn-lg" onClick={handleAddToQueue}
            style={{ marginTop: 'var(--spacing-lg)', width: '100%' }}>
            Thêm tất cả vào hàng đợi
          </button>
        </div>
      )}

      {toast && <div className={`toast ${toast.startsWith('') ? 'success' : 'error'}`}>{toast}</div>}
    </>
  );
}
