import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import OverviewPage from './pages/OverviewPage';
import KPIDetailPage from './pages/KPIDetailPage';
import InsightsPage from './pages/InsightsPage';
import DriversPage from './pages/DriversPage';
import RecommendationsPage from './pages/RecommendationsPage';
import DataSourcesPage from './pages/DataSourcesPage';
import FeedbackPage from './pages/FeedbackPage';
import ReportsPage from './pages/ReportsPage';
import AdminPage from './pages/AdminPage';
import AssistantPage from './pages/AssistantPage';
import DataUploadPage from './pages/DataUploadPage';
import HelpPage from './pages/HelpPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<OverviewPage />} />
            <Route path="kpis" element={<OverviewPage />} />
            <Route path="kpis/:id" element={<KPIDetailPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="drivers" element={<DriversPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="datasources" element={<DataSourcesPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="upload" element={<DataUploadPage />} />
            <Route path="assistant" element={<AssistantPage />} />
            <Route path="help" element={<HelpPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
