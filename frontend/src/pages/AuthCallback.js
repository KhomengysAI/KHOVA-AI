import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Sparkles } from 'lucide-react';

export default function AuthCallback() {
  const { processSession } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;
    const hash = location.hash || window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    const sessionId = match ? decodeURIComponent(match[1]) : null;
    const returnTo = localStorage.getItem('khova_return_to') || '/dashboard';
    if (!sessionId) { navigate('/dashboard'); return; }
    (async () => {
      try {
        await processSession(sessionId);
        window.history.replaceState({}, document.title, window.location.pathname);
        localStorage.removeItem('khova_return_to');
        navigate(returnTo, { replace: true });
      } catch (e) {
        setError('Sign-in failed. Please try again.');
        setTimeout(() => navigate('/'), 1800);
      }
    })();
  }, [location.hash, navigate, processSession]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background gap-4">
      <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center animate-pulse">
        <Sparkles className="w-6 h-6 text-primary-foreground" />
      </div>
      <p className="text-muted-foreground">{error || 'Menyelesaikan proses masuk...'}</p>
    </div>
  );
}
