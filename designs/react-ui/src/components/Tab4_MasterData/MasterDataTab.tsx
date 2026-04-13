import React, { useState } from 'react';
import DataTable from '../shared/DataTable';
import {
  projects, materials, machines, machineCapabilities,
  machineSpeeds, processDefinitions
} from '../../data/mockData';
import './MasterDataTab.css';

/**
 * TAB 4: QUẢN LÝ MASTER DATA
 * Tương đương ui_master_data.py (toàn bộ file)
 */

// Cấu hình 6 sub-tabs (ui_master_data.py line 82-89)
const subTabs = [
  { key: 'projects', label: 'Dự án (Projects)' },
  { key: 'materials', label: 'Vật liệu (Materials)' },
  { key: 'machines', label: 'Máy móc (Machines)' },
  { key: 'capabilities', label: 'Khả năng Máy (Capabilities)' },
  { key: 'speeds', label: 'Tốc độ Máy (Speeds)' },
  { key: 'processes', label: 'Quy trình (Processes)' }
];

// Cấu hình cột cho mỗi bảng (từ database/models.py)
const tableConfigs: Record<string, { tableName: string; pkCol: string; columns: { key: string; label: string; disabled?: boolean }[] }> = {
  projects: {
    tableName: 'Dự Án',
    pkCol: 'id',
    columns: [
      { key: 'id', label: 'ID', disabled: true },
      { key: 'project_name', label: 'Tên Dự Án' },
      { key: 'project_code', label: 'Mã Công Trình' },
      { key: 'hexcode', label: 'Hexcode' },
      { key: 'notes', label: 'Ghi Chú' }
    ]
  },
  materials: {
    tableName: 'Vật Liệu',
    pkCol: 'id',
    columns: [
      { key: 'id', label: 'Mã VL', disabled: true },
      { key: 'material_name', label: 'Tên Vật Liệu' },
      { key: 'material_type', label: 'Loại' },
      { key: 'group_code', label: 'Nhóm' },
      { key: 'notes', label: 'Ghi Chú' }
    ]
  },
  machines: {
    tableName: 'Máy Móc',
    pkCol: 'id',
    columns: [
      { key: 'id', label: 'Mã Máy', disabled: true },
      { key: 'name', label: 'Tên Máy' },
      { key: 'machine_type', label: 'Loại Máy' },
      { key: 'status', label: 'Trạng Thái' },
      { key: 'max_size_mm', label: 'Kích Thước Tối Đa' },
      { key: 'notes', label: 'Ghi Chú' }
    ]
  },
  capabilities: {
    tableName: 'Khả Năng Cắt',
    pkCol: 'id',
    columns: [
      { key: 'id', label: 'ID', disabled: true },
      { key: 'machine_id', label: 'Mã Máy' },
      { key: 'capability_name', label: 'Khả Năng' },
      { key: 'priority', label: 'Ưu Tiên' },
      { key: 'notes', label: 'Ghi Chú' }
    ]
  },
  speeds: {
    tableName: 'Tốc Độ Cắt',
    pkCol: 'id',
    columns: [
      { key: 'id', label: 'ID', disabled: true },
      { key: 'machine_id', label: 'Mã Máy' },
      { key: 'material_group_code', label: 'Nhóm VL' },
      { key: 'size_category', label: 'Phân Loại KT' },
      { key: 'speed_value', label: 'Tốc Độ (mm/phút)' }
    ]
  },
  processes: {
    tableName: 'Quy Trình Sản Xuất',
    pkCol: 'id',
    columns: [
      { key: 'id', label: 'ID', disabled: true },
      { key: 'process_id', label: 'Mã QT' },
      { key: 'process_name', label: 'Tên Quy Trình' },
      { key: 'product_type', label: 'Loại Sản Phẩm' },
      { key: 'step_order', label: 'Thứ Tự' },
      { key: 'capability_required', label: 'Yêu Cầu Năng Lực' },
      { key: 'notes', label: 'Ghi Chú' }
    ]
  }
};

// Data sources
const dataSources: Record<string, Record<string, unknown>[]> = {
  projects: projects as unknown as Record<string, unknown>[],
  materials: materials as unknown as Record<string, unknown>[],
  machines: machines as unknown as Record<string, unknown>[],
  capabilities: machineCapabilities as unknown as Record<string, unknown>[],
  speeds: machineSpeeds as unknown as Record<string, unknown>[],
  processes: processDefinitions as unknown as Record<string, unknown>[]
};

const MasterDataTab: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState('projects');

  const config = tableConfigs[activeSubTab];
  const data = dataSources[activeSubTab] || [];

  return (
    <div>
      {/* Title (ui_master_data.py line 76) */}
      <h2>QUẢN LÝ Masterdata</h2>

      {/* Sub-tabs bar (ui_master_data.py line 82-89) */}
      <div className="tab-bar">
        {subTabs.map(tab => (
          <button
            key={tab.key}
            className={`tab-bar-item ${activeSubTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveSubTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table editor for active sub-tab (ui_master_data.py render_table_editor) */}
      <h4 style={{ marginBottom: '0.75rem' }}>Quản lý bảng: {config.tableName}</h4>

      <DataTable
        columns={config.columns}
        data={data}
        dynamicRows={true}
      />

      {/* Save button (ui_master_data.py line 34) */}
      <button className="primary" style={{ marginTop: '0.5rem' }}>
        Lưu thay đổi {config.tableName}
      </button>
    </div>
  );
};

export default MasterDataTab;
