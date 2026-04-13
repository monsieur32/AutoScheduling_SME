import React from 'react';

interface DataTableProps {
  columns: { key: string; label: string; disabled?: boolean }[];
  data: Record<string, unknown>[];
  dynamicRows?: boolean;
}

const DataTable: React.FC<DataTableProps> = ({ columns, data, dynamicRows = false }) => {
  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
            {dynamicRows && <th style={{ width: 40 }}></th>}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr key={rowIdx}>
              {columns.map((col) => (
                <td key={col.key} className={col.disabled ? 'disabled' : ''}>
                  {col.disabled ? (
                    String(row[col.key] ?? '')
                  ) : (
                    <input
                      type="text"
                      defaultValue={String(row[col.key] ?? '')}
                      readOnly
                    />
                  )}
                </td>
              ))}
              {dynamicRows && (
                <td>
                  <button style={{ padding: '2px 8px', fontSize: '12px', color: 'var(--color-error)' }}>🗑</button>
                </td>
              )}
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td colSpan={columns.length + (dynamicRows ? 1 : 0)} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-secondary)' }}>
                Không có dữ liệu
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {dynamicRows && (
        <button style={{ marginTop: '8px', fontSize: '12px' }}>+ Thêm dòng mới</button>
      )}
    </div>
  );
};

export default DataTable;
