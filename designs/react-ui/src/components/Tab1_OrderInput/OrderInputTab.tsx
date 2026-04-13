import React, { useState } from 'react';
import AlertBanner from '../shared/AlertBanner';
import Expander from '../shared/Expander';
import FileUploader from '../shared/FileUploader';
import { projects, buildProcessMap, mockDxfFiles } from '../../data/mockData';
import type { DxfInfo } from '../../types';
import './OrderInputTab.css';

/**
 * TAB 1: NHẬP LIỆU ĐƠN HÀNG (PLANNER)
 * Tương đương main.py lines 59–303
 */
const OrderInputTab: React.FC = () => {
  const processMap = buildProcessMap();
  const processOptions = Object.keys(processMap);

  // State cho project selector
  const projectDisplayOptions = projects.map(
    p => `[${p.project_code}] ${p.project_name} (Hex: ${p.hexcode || 'N/A'})`
  );
  const [selectedProject, setSelectedProject] = useState(projectDisplayOptions[0] || '');
  const [priority, setPriority] = useState('Bình thường');

  // State cho new project form
  const [showNewProject, setShowNewProject] = useState(false);
  const [newPName, setNewPName] = useState('');
  const [newPCode, setNewPCode] = useState('');
  const [newPHex, setNewPHex] = useState('');

  // State cho date/time (giống main.py line 152-160)
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const formatDate = (d: Date) => d.toISOString().split('T')[0];

  const [startDate, setStartDate] = useState(formatDate(now));
  const [startTime, setStartTime] = useState('07:00');
  const [dueDate, setDueDate] = useState(formatDate(tomorrow));
  const [dueTime, setDueTime] = useState('17:00');

  // State cho DXF files (demo mode: hiển thị file mẫu đã phân tích)
  const [analyzed, setAnalyzed] = useState(false);
  const uploadedFileNames = mockDxfFiles.map(f => f.name);

  // State cho file configs
  const [fileConfigs, setFileConfigs] = useState<Array<{
    material: string;
    quantity: number;
    processType: string;
    detailLenMm: number;
  }>>(mockDxfFiles.map(f => ({
    material: 'C',
    quantity: 1,
    processType: processOptions[0] || '',
    detailLenMm: f.info.total_len_mm
  })));

  // Logic lọc quy trình (giống main.py lines 200-211)
  const getValidProcesses = (dxfInfo: DxfInfo): string[] => {
    const hasCurve = dxfInfo.curved_len_mm > 0;
    const valid: string[] = [];
    for (const [pName, caps] of Object.entries(processMap)) {
      const isStraightOnly = caps.includes('Cut_straight') && !caps.includes('Cut_contour');
      if (hasCurve && isStraightOnly) continue;
      valid.push(pName);
    }
    return valid.length > 0 ? valid : processOptions;
  };

  // Logic kiểm tra process có cần nhập chiều dài chi tiết hay không (main.py line 221-231)
  const needsDetailLength = (processType: string): boolean => {
    const lower = processType.toLowerCase();
    return ['vát', 'rãnh', 'biên dạng', 'chỉ', 'hoa văn'].some(k => lower.includes(k));
  };

  return (
    <div>
      <h3>NHẬP ĐƠN HÀNG MỚI</h3>

      {/* ===== Thiết lập chung cho Đơn hàng (main.py line 97-160) ===== */}
      <div className="container-bordered">
        <h4>Thiết lập chung cho Đơn hàng</h4>

        {/* Project selector + Priority (main.py line 105-114) */}
        <div className="columns flex-3-1">
          <div className="field-group">
            <label>Chọn Dự án / Công trình hiện có:</label>
            <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
              {projectDisplayOptions.length > 0 ? (
                projectDisplayOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))
              ) : (
                <option>Chưa có dự án nào</option>
              )}
            </select>
          </div>
          <div className="field-group">
            <label>Mức độ ưu tiên</label>
            <select value={priority} onChange={e => setPriority(e.target.value)}>
              <option>Bình thường</option>
              <option>Cao</option>
              <option>Gấp</option>
            </select>
          </div>
        </div>

        {/* Tạo mới Dự án nhanh (main.py line 116-148) */}
        <Expander title="Tạo mới Dự án nhanh tại đây" defaultExpanded={showNewProject}>
          <div className="columns">
            <div className="field-group">
              <label>Tên Công trình *</label>
              <input type="text" value={newPName} onChange={e => setNewPName(e.target.value)} placeholder="VD: Biệt thự Vinhomes" />
            </div>
            <div className="field-group">
              <label>Mã Công trình *</label>
              <input type="text" value={newPCode} onChange={e => setNewPCode(e.target.value)} placeholder="VD: VIN2408" />
            </div>
            <div className="field-group">
              <label>Hexcode</label>
              <input type="text" value={newPHex} onChange={e => setNewPHex(e.target.value)} placeholder="VD: V-0302" />
            </div>
          </div>
          <button className="primary" style={{ marginTop: '0.5rem' }}>
            Lưu & Thêm Dự án mới
          </button>
        </Expander>

        {/* Date/Time pickers (main.py line 150-160) */}
        <div className="columns">
          <div>
            <div className="field-group">
              <label>Ngày bắt đầu làm</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
            </div>
            <div className="field-group">
              <label>Giờ bắt đầu làm</label>
              <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} />
            </div>
          </div>
          <div>
            <div className="field-group">
              <label>Hạn chót (Due Date)</label>
              <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
            </div>
            <div className="field-group">
              <label>Giờ giao</label>
              <input type="time" value={dueTime} onChange={e => setDueTime(e.target.value)} />
            </div>
          </div>
        </div>

        {/* DXF File Uploader (main.py line 162-179) */}
        <h4>Tải lên Bản vẽ & Phân tích</h4>
        <FileUploader
          label="Tải lên nhiều bản vẽ (.dxf)"
          accept=".dxf"
          multiple={true}
          files={uploadedFileNames}
        />

        <button className="primary" onClick={() => setAnalyzed(true)}>
          Phân tích bản vẽ
        </button>

        {/* ===== Cấu hình cho từng Bản vẽ (main.py line 183-242) ===== */}
        {analyzed && (
          <>
            <div className="spacer" />
            <h4>Cấu hình cho từng Bản vẽ</h4>

            {mockDxfFiles.map((file, idx) => {
              const dxfInfo = file.info;
              const validProcesses = getValidProcesses(dxfInfo);
              const config = fileConfigs[idx];

              return (
                <Expander key={idx} title={`Bản vẽ ${idx + 1}: ${file.name}`} defaultExpanded={true}>
                  {/* Thông tin DXF (main.py line 192) */}
                  {dxfInfo.status === 'success' && (
                    <>
                      <AlertBanner type="success">
                        Dài thẳng: {dxfInfo.straight_len_mm}mm | Cong/Tròn: {dxfInfo.curved_len_mm}mm | Tổng: {dxfInfo.total_len_mm}mm
                      </AlertBanner>

                      {/* Texts (main.py line 193-195) */}
                      {dxfInfo.texts.length > 0 && (
                        <AlertBanner type="info">
                          Ghi chú trong bản vẽ: {dxfInfo.texts.slice(0, 10).join(', ')}
                          {dxfInfo.texts.length > 10 ? '...' : ''}
                        </AlertBanner>
                      )}

                      {/* Warnings (main.py line 196-197) */}
                      {dxfInfo.warnings.length > 0 && (
                        <AlertBanner type="warning">
                          Cảnh báo: {dxfInfo.warnings.join('; ')}
                        </AlertBanner>
                      )}

                      {/* 3 columns: Material, Quantity, Process (main.py line 213-219) */}
                      <div className="columns columns-3">
                        <div className="field-group">
                          <label>Nhóm Vật Liệu</label>
                          <select
                            value={config.material}
                            onChange={e => {
                              const newConfigs = [...fileConfigs];
                              newConfigs[idx] = { ...newConfigs[idx], material: e.target.value };
                              setFileConfigs(newConfigs);
                            }}
                          >
                            {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'].map(m => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </select>
                        </div>
                        <div className="field-group">
                          <label>Số lượng (tấm)</label>
                          <input
                            type="number"
                            min={1}
                            value={config.quantity}
                            onChange={e => {
                              const newConfigs = [...fileConfigs];
                              newConfigs[idx] = { ...newConfigs[idx], quantity: parseInt(e.target.value) || 1 };
                              setFileConfigs(newConfigs);
                            }}
                          />
                        </div>
                        <div className="field-group">
                          <label>Quy trình Gia công phù hợp</label>
                          <select
                            value={config.processType}
                            onChange={e => {
                              const newConfigs = [...fileConfigs];
                              newConfigs[idx] = { ...newConfigs[idx], processType: e.target.value };
                              setFileConfigs(newConfigs);
                            }}
                          >
                            {validProcesses.map(p => (
                              <option key={p} value={p}>{p}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Conditional: Chiều dài chi tiết gia công (main.py line 221-231) */}
                      {needsDetailLength(config.processType) && (
                        <div className="field-group">
                          <label>
                            Chiều dài chi tiết cần gia công (mm) - Dành cho Vát/Rãnh/Biên dạng
                          </label>
                          <input
                            type="number"
                            min={0}
                            step={50}
                            value={config.detailLenMm}
                            onChange={e => {
                              const newConfigs = [...fileConfigs];
                              newConfigs[idx] = { ...newConfigs[idx], detailLenMm: parseFloat(e.target.value) || 0 };
                              setFileConfigs(newConfigs);
                            }}
                          />
                          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                            Hệ thống sẽ dùng chiều dài này để tính toán thời gian thay vì dùng toàn bộ chiều dài phôi.
                          </span>
                        </div>
                      )}
                    </>
                  )}

                  {dxfInfo.status === 'error' && (
                    <AlertBanner type="error">
                      Lỗi khi đọc bản vẽ: {dxfInfo.message}
                    </AlertBanner>
                  )}
                </Expander>
              );
            })}

            {/* Submit button (main.py line 245) */}
            <div className="spacer" />
            <button className="primary full-width">
              Thêm tất cả vào hàng đợi
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default OrderInputTab;
