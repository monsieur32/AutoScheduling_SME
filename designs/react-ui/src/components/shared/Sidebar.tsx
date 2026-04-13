import React from 'react';

interface SidebarProps {
  selectedTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  "1. Nhập liệu đơn hàng",
  "2. Bảng điều độ sản xuất",
  "3. Giao diện Máy (Công nhân)",
  "4. Quản Lý Master Data"
];

const Sidebar: React.FC<SidebarProps> = ({ selectedTab, onTabChange }) => {
  return (
    <div className="sidebar">
      <h2>ĐIỀU HƯỚNG</h2>
      <nav className="sidebar-nav">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`sidebar-nav-item ${selectedTab === tab ? 'active' : ''}`}
            onClick={() => onTabChange(tab)}
          >
            <span className="radio-dot" />
            {tab}
          </button>
        ))}
      </nav>
      <hr style={{ margin: '1.5rem 0' }} />
    </div>
  );
};

export default Sidebar;
