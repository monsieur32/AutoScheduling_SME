import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ManagerDashboard from './pages/ManagerDashboard';
import WorkerStation from './pages/WorkerStation';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/manager/*" element={<ManagerDashboard />} />
        <Route path="/worker" element={<WorkerStation />} />
        <Route path="*" element={<Navigate to="/manager" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
