import { useState } from 'react';
import DXFUploader from '../components/manager/DXFUploader';
import JobQueueTable from '../components/manager/JobQueueTable';
import SchedulePanel from '../components/manager/SchedulePanel';
import GanttChart from '../components/manager/GanttChart';
import MasterDataEditor from '../components/manager/MasterDataEditor';
import ReschedulePanel from '../components/manager/ReschedulePanel';

import ThemeToggle from '../components/ThemeToggle';

const TABS = [
  { id: 'orders', label: 'Nhập Đơn Hàng'},
  { id: 'schedule', label: 'Điều Độ Sản Xuất'},
  { id: 'masterdata', label: 'Master Data'},
];

export default function ManagerDashboard() {
  const [activeTab, setActiveTab] = useState('orders');

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div>
            <h2>AutoScheduling</h2>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Trạm Quản Đốc</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {TABS.map(tab => (
            <div
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </div>
          ))}
        </nav>

        <div style={{ padding: 'var(--spacing-md)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <ThemeToggle />
        </div>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 'var(--spacing-md)' }}>
          <a href="/worker" className="nav-item" style={{ color: 'var(--accent-cyan)' }}>
            <span>Chuyển sang tab Công Nhân</span>
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'orders' && <OrdersTab />}
        {activeTab === 'schedule' && <ScheduleTab />}
        {activeTab === 'masterdata' && <MasterDataTab />}
      </main>
    </div>
  );
}

function OrdersTab() {
  return (
    <>
      <div className="page-header">
        <h1>Nhập Đơn Hàng Mới</h1>
        <p>Upload bản vẽ DXF, cấu hình vật liệu và thêm vào hàng đợi sản xuất</p>
      </div>
      <DXFUploader />
      <div style={{ marginTop: 'var(--spacing-xl)' }}>
        <JobQueueTable />
      </div>
    </>
  );
}

function ScheduleTab() {
  return (
    <>
      <div className="page-header">
        <h1>Trung Tâm Điều Độ Sản Xuất</h1>
      </div>
      {/* Job queue (matching original Streamlit Tab 2 — "DANH SÁCH HÀNG ĐỢI CÔNG VIỆC") */}
      <JobQueueTable />
      <div style={{ marginTop: 'var(--spacing-lg)' }}>
        <SchedulePanel />
      </div>
      <div style={{ marginTop: 'var(--spacing-lg)' }}>
        <GanttChart />
      </div>
      <div style={{ marginTop: 'var(--spacing-lg)' }}>
        <ReschedulePanel />
      </div>
    </>
  );
}

function MasterDataTab() {
  return (
    <>
      <div className="page-header">
        <h1>Quản Lý Master Data</h1>
        <p>Quản lý dữ liệu máy móc, vật liệu, quy trình sản xuất</p>
      </div>
      <MasterDataEditor />
    </>
  );
}
