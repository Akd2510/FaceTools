import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import UploadPage    from './pages/UploadPage';
import ClustersPage  from './pages/ClustersPage';
import SearchPage    from './pages/SearchPage';
import FaceswapPage  from './pages/FaceswapPage';
import './styles/globals.css';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{
          flex: 1, padding: '2rem 2.5rem',
          minWidth: 0, overflowX: 'hidden',
        }}>
          <Routes>
            <Route path="/"         element={<DashboardPage />} />
            <Route path="/upload"   element={<UploadPage />} />
            <Route path="/clusters" element={<ClustersPage />} />
            <Route path="/search"   element={<SearchPage />} />
            <Route path="/faceswap" element={<FaceswapPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
