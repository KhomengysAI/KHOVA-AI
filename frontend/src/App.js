import '@/App.css';
import React from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { LanguageProvider } from '@/lib/i18n';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { AppShell } from '@/components/AppShell';
import { LoginModal } from '@/components/LoginModal';
import Landing from '@/pages/Landing';
import AuthCallback from '@/pages/AuthCallback';
import Dashboard from '@/pages/Dashboard';
import Projects from '@/pages/Projects';
import Settings from '@/pages/Settings';
import Wizard from '@/pages/Wizard';
import NewProduct from '@/pages/NewProduct';

const RequireAuth = ({ children }) => {
  const { user, loading, setShowLogin } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-muted-foreground">Loading...</div>;
  if (!user) { setTimeout(() => setShowLogin(true), 10); return <Navigate to="/" replace />; }
  return children;
};

function AppRouter() {
  const location = useLocation();
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/new" element={<NewProduct />} />
        <Route path="/project/:id" element={<Wizard />} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/projects" element={<RequireAuth><Projects /></RequireAuth>} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

function App() {
  return (
    <div className="App">
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRouter />
            <LoginModal />
            <Toaster position="top-right" richColors />
          </BrowserRouter>
        </AuthProvider>
      </LanguageProvider>
    </div>
  );
}

export default App;
