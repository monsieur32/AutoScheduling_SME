import React, { useState } from 'react';
import Sidebar from './components/shared/Sidebar';
import OrderInputTab from './components/Tab1_OrderInput/OrderInputTab';
import DashboardTab from './components/Tab2_Dashboard/DashboardTab';
import WorkerTab from './components/Tab3_Worker/WorkerTab';
import MasterDataTab from './components/Tab4_MasterData/MasterDataTab';
import './App.css';

/**
 * ROOT APP COMPONENT
 * Tương đương main.py:
 * - st.set_page_config(page_title="Hệ thống Lập lịch Sản xuất", layout="wide") → line 17
 * - st.sidebar.radio() → lines 41-46
 * - Conditional tab rendering → lines 59, 307, 587, 826
 */
const App: React.FC = () => {
  // Tương đương tab_selection = st.sidebar.radio() (main.py line 41)
  const [selectedTab, setSelectedTab] = useState("1. Nhập liệu đơn hàng");

  // Render tab content dựa trên selectedTab (main.py lines 59, 307, 587, 826)
  const renderTab = () => {
    switch (selectedTab) {
      case "1. Nhập liệu đơn hàng":
        return <OrderInputTab />;
      case "2. Bảng điều độ sản xuất":
        return <DashboardTab />;
      case "3. Giao diện Máy (Công nhân)":
        return <WorkerTab />;
      case "4. Quản Lý Master Data":
        return <MasterDataTab />;
      default:
        return <OrderInputTab />;
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar — tương đương st.sidebar (main.py line 40-46) */}
      <Sidebar selectedTab={selectedTab} onTabChange={setSelectedTab} />

      {/* Main Content — tương đương st.container() chính (layout="wide") */}
      <main className="main-content">
        {renderTab()}
      </main>
    </div>
  );
};

export default App;
