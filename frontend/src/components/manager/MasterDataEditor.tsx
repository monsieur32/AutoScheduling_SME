import { useState, useEffect, useCallback } from 'react';
import { listMasterData, createMasterRecord, updateMasterRecord, deleteMasterRecord } from '../../api/httpClient';

/* ── Table definitions ─────────────────────────────────────── */
const TABLES = [
  { key: 'projects', label: 'Dự Án (Projects)', pk: 'id' },
  { key: 'materials', label: 'Vật Liệu (Materials)', pk: 'id' },
  { key: 'machines', label: 'Máy Móc (Machines)', pk: 'id' },
  { key: 'capabilities', label: 'Khả Năng Máy (Capabilities)', pk: 'id' },
  { key: 'speeds', label: 'Tốc Độ Máy (Speeds)', pk: 'id' },
  { key: 'processes', label: 'Quy Trình (Processes)', pk: 'id' },
];

interface CellEdit {
  rowIdx: number;
  col: string;
  value: any;
}

/* ── Component ─────────────────────────────────────────────── */
export default function MasterDataEditor() {
  const [activeTab, setActiveTab] = useState(0);
  const [records, setRecords] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [edits, setEdits] = useState<CellEdit[]>([]);
  const [newRows, setNewRows] = useState<any[]>([]);
  const [deletedIds, setDeletedIds] = useState<(string | number)[]>([]);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState('');

  const table = TABLES[activeTab];
  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000); };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setEdits([]);
    setNewRows([]);
    setDeletedIds([]);
    try {
      const data = await listMasterData(table.key);
      const recs = data.records || [];
      setRecords(recs);
      if (recs.length > 0) {
        setColumns(Object.keys(recs[0]));
      } else {
        // Infer columns from table key
        const defaultCols: Record<string, string[]> = {
          projects: ['id', 'project_name', 'project_code', 'hexcode', 'notes'],
          materials: ['id', 'material_name', 'material_type', 'group_code', 'notes'],
          machines: ['id', 'name', 'machine_type', 'status', 'max_size_mm', 'notes'],
          capabilities: ['id', 'machine_id', 'capability_name', 'priority', 'notes'],
          speeds: ['id', 'machine_id', 'material_group_code', 'size_category', 'speed_value'],
          processes: ['id', 'process_id', 'process_name', 'product_type', 'step_order', 'capability_required', 'notes'],
        };
        setColumns(defaultCols[table.key] || ['id']);
      }
    } catch { setRecords([]); }
    setLoading(false);
  }, [table.key]);

  useEffect(() => { fetchData(); }, [fetchData]);

  /* ── Edit tracking ─────────────────────────────────────── */
  const handleCellEdit = (rowIdx: number, col: string, value: any) => {
    setEdits(prev => {
      const existing = prev.findIndex(e => e.rowIdx === rowIdx && e.col === col);
      if (existing >= 0) {
        const copy = [...prev];
        copy[existing] = { rowIdx, col, value };
        return copy;
      }
      return [...prev, { rowIdx, col, value }];
    });
  };

  const getCellValue = (rowIdx: number, col: string, original: any) => {
    const edit = edits.find(e => e.rowIdx === rowIdx && e.col === col);
    return edit !== undefined ? edit.value : original;
  };

  // Add new row
  const handleAddRow = () => {
    const empty: Record<string, any> = {};
    columns.forEach(c => { empty[c] = c === table.pk ? null : ''; });
    setNewRows(prev => [...prev, empty]);
  };

  // Edit new row
  const handleNewRowEdit = (rowIdx: number, col: string, value: any) => {
    setNewRows(prev => prev.map((r, i) => i === rowIdx ? { ...r, [col]: value } : r));
  };

  // Mark existing row for deletion
  const handleDeleteRow = (id: string | number) => {
    setDeletedIds(prev => prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]);
  };

  // Remove unsaved new row
  const handleRemoveNewRow = (idx: number) => {
    setNewRows(prev => prev.filter((_, i) => i !== idx));
  };

  /* ── Batch Save ────────────────────────────────────────── */
  const handleSave = async () => {
    setSaving(true);
    let errors = 0;

    try {
      // 1. Delete marked rows
      for (const id of deletedIds) {
        try { await deleteMasterRecord(table.key, id); }
        catch { errors++; }
      }

      // 2. Update edited cells
      const editsByRow: Record<number, Record<string, any>> = {};
      for (const e of edits) {
        if (!editsByRow[e.rowIdx]) editsByRow[e.rowIdx] = {};
        editsByRow[e.rowIdx][e.col] = e.value;
      }
      for (const [rowIdxStr, changes] of Object.entries(editsByRow)) {
        const rowIdx = parseInt(rowIdxStr);
        const row = records[rowIdx];
        if (!row) continue;
        const id = row[table.pk];
        if (deletedIds.includes(id)) continue;
        try { await updateMasterRecord(table.key, id, changes); }
        catch { errors++; }
      }

      // 3. Insert new rows
      for (const newRow of newRows) {
        const data = { ...newRow };
        // Remove PK if null/empty (auto-increment)
        if (data[table.pk] === null || data[table.pk] === '' || data[table.pk] === undefined) {
          delete data[table.pk];
        }
        try { await createMasterRecord(table.key, data); }
        catch (e: any) { errors++; showToast(` Lỗi thêm dòng: ${e.message}`); }
      }

      if (errors === 0) {
        showToast(` Cập nhật ${table.label} thành công!`);
      } else {
        showToast(` Hoàn tất với ${errors} lỗi`);
      }
      fetchData();
    } catch (e: any) {
      showToast(`Lỗi khi lưu: ${e.message}`);
    }
    setSaving(false);
  };

  const hasChanges = edits.length > 0 || newRows.length > 0 || deletedIds.length > 0;

  /* ── Render ────────────────────────────────────────────── */
  return (
    <div>
      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 'var(--spacing-xs)', marginBottom: 'var(--spacing-lg)', flexWrap: 'wrap' }}>
        {TABLES.map((t, i) => (
          <button
            key={t.key}
            className={`btn ${activeTab === i ? 'btn-primary' : 'btn-secondary'} btn-sm`}
            onClick={() => setActiveTab(i)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Quản lý bảng: {table.label}</span>
          <div className="flex-gap">
            {hasChanges && <span className="badge badge-warning">Có thay đổi chưa lưu</span>}
            <button className="btn btn-secondary btn-sm" onClick={handleAddRow}>Thêm dòng</button>
            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !hasChanges}>
              {saving ? <><span className="spinner" /> Đang lưu...</> : ` Lưu thay đổi ${table.label}`}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex-center" style={{ padding: 'var(--spacing-xl)' }}><div className="spinner spinner-lg" /></div>
        ) : (
          <div style={{ overflowX: 'auto', marginTop: 'var(--spacing-md)' }}>
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map(col => (
                    <th key={col}>{col}{col === table.pk ? ' LOCKED' : ''}</th>
                  ))}
                  <th style={{ width: 60 }}>Xóa</th>
                </tr>
              </thead>
              <tbody>
                {/* Existing rows */}
                {records.map((row, rowIdx) => {
                  const id = row[table.pk];
                  const isDeleted = deletedIds.includes(id);
                  const isEdited = edits.some(e => e.rowIdx === rowIdx);

                  return (
                    <tr key={id} className={isDeleted ? 'row-deleted' : isEdited ? 'row-edited' : ''}>
                      {columns.map(col => (
                        <td key={col}>
                          {col === table.pk ? (
                            // PK column: read-only (matching original disabled=[pk_col])
                            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', opacity: 0.7 }}>
                              {row[col]}
                            </span>
                          ) : (
                            <input
                              className="cell-input"
                              value={String(getCellValue(rowIdx, col, row[col]) ?? '')}
                              onChange={e => handleCellEdit(rowIdx, col, e.target.value)}
                              disabled={isDeleted}
                            />
                          )}
                        </td>
                      ))}
                      <td>
                        <button
                          className={`btn btn-sm ${isDeleted ? 'btn-secondary' : 'btn-danger'}`}
                          onClick={() => handleDeleteRow(id)}
                          title={isDeleted ? 'Hoàn tác xóa' : 'Đánh dấu xóa'}
                        >
                          {isDeleted ? '↩' : '🗑'}
                        </button>
                      </td>
                    </tr>
                  );
                })}

                {/* New rows (just added, not yet saved) */}
                {newRows.map((row, newIdx) => (
                  <tr key={`new-${newIdx}`} className="row-new">
                    {columns.map(col => (
                      <td key={col}>
                        {col === table.pk ? (
                          <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>Tự động</span>
                        ) : (
                          <input
                            className="cell-input"
                            value={String(row[col] ?? '')}
                            onChange={e => handleNewRowEdit(newIdx, col, e.target.value)}
                            placeholder={col}
                          />
                        )}
                      </td>
                    ))}
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => handleRemoveNewRow(newIdx)} title="Bỏ dòng mới">✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {toast && <div className={`toast ${toast.startsWith('') ? 'success' : 'error'}`}>{toast}</div>}
    </div>
  );
}
