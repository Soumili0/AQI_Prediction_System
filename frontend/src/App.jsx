import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import Layout from './components/common/Layout';
import LoadingSpinner from './components/common/LoadingSpinner';

// Lazy-loaded pages for code splitting
const Landing      = lazy(() => import('./pages/Landing'));
const Login        = lazy(() => import('./pages/Login'));
const Register     = lazy(() => import('./pages/Register'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ResetPassword  = lazy(() => import('./pages/ResetPassword'));
const VerifyEmail    = lazy(() => import('./pages/VerifyEmail'));
const Dashboard    = lazy(() => import('./pages/Dashboard'));
const Prediction   = lazy(() => import('./pages/Prediction'));
const Analytics    = lazy(() => import('./pages/Analytics'));
const History      = lazy(() => import('./pages/History'));
const Reports      = lazy(() => import('./pages/Reports'));
const AdminPanel   = lazy(() => import('./pages/AdminPanel'));
const Profile      = lazy(() => import('./pages/Profile'));
const Settings     = lazy(() => import('./pages/Settings'));
const NotFound     = lazy(() => import('./pages/NotFound'));

/** Guard: redirect to /login if not authenticated */
function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

/** Guard: redirect to /dashboard if already authenticated */
function PublicRoute({ children }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />;
}

/** Guard: only admin role */
function AdminRoute({ children }) {
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Suspense fallback={<LoadingSpinner fullScreen />}>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login"          element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register"       element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/forgot-password"element={<PublicRoute><ForgotPassword /></PublicRoute>} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/verify-email"   element={<VerifyEmail />} />

        {/* Protected routes inside the shared Layout */}
        <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route path="/dashboard"  element={<Dashboard />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/analytics"  element={<Analytics />} />
          <Route path="/history"    element={<History />} />
          <Route path="/reports"    element={<Reports />} />
          <Route path="/profile"    element={<Profile />} />
          <Route path="/settings"   element={<Settings />} />
        </Route>

        {/* Admin-only */}
        <Route path="/admin/*" element={<AdminRoute><Layout /></AdminRoute>}>
          <Route index element={<AdminPanel />} />
          <Route path="*" element={<AdminPanel />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
