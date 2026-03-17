import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import SelectModule from './pages/SelectModule';
import Dashboard from './pages/Dashboard';
import StudentDashboard from './pages/StudentDashboard';
import ParentDashboard from './pages/ParentDashboard';
import IndividualDashboard from './pages/IndividualDashboard';
import CoupleDashboard from './pages/CoupleDashboard';
import InstituteDashboard from './pages/InstituteDashboard';
import AcademicPortal from './pages/AcademicPortal';
import { api } from './services/api';

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = api.getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/select-module"
          element={
            <ProtectedRoute>
              <SelectModule />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/student"
          element={
            <ProtectedRoute>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/parent"
          element={
            <ProtectedRoute>
              <ParentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/individual"
          element={
            <ProtectedRoute>
              <IndividualDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/couple"
          element={
            <ProtectedRoute>
              <CoupleDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/institute"
          element={
            <ProtectedRoute>
              <InstituteDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/institute_owner"
          element={
            <ProtectedRoute>
              <InstituteDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/institute_teacher"
          element={
            <ProtectedRoute>
              <InstituteDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/academic"
          element={
            <ProtectedRoute>
              <AcademicPortal />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/:module"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
