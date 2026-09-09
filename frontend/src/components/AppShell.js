import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLang } from '@/lib/i18n';
import { useTheme } from '@/context/ThemeContext';
import { getEconomy } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { LayoutDashboard, FolderKanban, Settings as SettingsIcon, Globe, LogOut, Plus, Moon, Sun, Coins, ShieldCheck } from 'lucide-react';

// Lightweight event bus so any generation action can refresh the credits pill.
export const refreshEconomy = () => window.dispatchEvent(new Event('khova:economy'));

export const AppShell = ({ children }) => {
  const { user, logout, setShowLogin } = useAuth();
  const { lang, setLang, t } = useLang();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [economy, setEconomy] = useState(null);

  const loadEconomy = useCallback(() => {
    if (!user) { setEconomy(null); return; }
    getEconomy().then(setEconomy).catch(() => {});
  }, [user]);

  useEffect(() => { loadEconomy(); }, [loadEconomy, location.pathname]);
  useEffect(() => {
    const h = () => loadEconomy();
    window.addEventListener('khova:economy', h);
    return () => window.removeEventListener('khova:economy', h);
  }, [loadEconomy]);

  const NavLink = ({ to, icon: Icon, label, testid }) => {
    const active = location.pathname === to;
    return (
      <Link to={to} data-testid={testid}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-secondary'}`}>
        <Icon className="w-4 h-4" /> <span className="hidden md:inline">{label}</span>
      </Link>
    );
  };

  const isAdmin = economy?.role === 'admin';

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <img src="/assets/khova-logo.png" alt="Khova AI" className="w-9 h-9 object-contain" data-testid="logo-image" />
            <span className="font-display text-xl">Khova AI</span>
          </Link>

          <nav className="flex items-center gap-1">
            {user && <NavLink to="/dashboard" icon={LayoutDashboard} label={t('nav.dashboard')} testid="nav-dashboard" />}
            {user && <NavLink to="/projects" icon={FolderKanban} label={t('nav.projects')} testid="nav-projects" />}
            <NavLink to="/settings" icon={SettingsIcon} label={t('nav.settings')} testid="nav-settings" />
            {isAdmin && <NavLink to="/admin" icon={ShieldCheck} label="Admin" testid="nav-admin" />}
          </nav>

          <div className="flex items-center gap-2">
            {user && economy && (
              <Link to="/settings" data-testid="credits-pill"
                className="hidden sm:flex items-center gap-1.5 px-3 h-9 rounded-lg bg-secondary text-sm font-semibold hover:bg-accent transition-colors">
                <Coins className="w-4 h-4 text-amber-500" />
                <span data-testid="credits-pill-value">{economy.credits}</span>
                <Badge variant="outline" className="ml-1 text-[10px] uppercase capitalize hidden md:inline-flex">{economy.plan}</Badge>
              </Link>
            )}

            <Button variant="ghost" size="icon" onClick={toggleTheme} data-testid="theme-toggle-button" aria-label="Toggle theme" className="h-9 w-9">
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" data-testid="lang-toggle" className="gap-1">
                  <Globe className="w-4 h-4" /> <span className="uppercase text-xs font-semibold">{lang}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setLang('id')}>Bahasa Indonesia</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setLang('en')}>English</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button size="sm" onClick={() => navigate('/new')} data-testid="nav-new-product" className="gap-1 hidden sm:flex">
              <Plus className="w-4 h-4" /> {t('nav.new')}
            </Button>

            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button data-testid="user-menu" className="outline-none">
                    <Avatar className="w-9 h-9 border border-border">
                      <AvatarImage src={user.picture} />
                      <AvatarFallback>{(user.name || user.email || 'U').slice(0, 1).toUpperCase()}</AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-2 py-1.5 text-sm">
                    <div className="font-medium">{user.name}</div>
                    <div className="text-xs text-muted-foreground font-mono">{user.email}</div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/dashboard')}>{t('nav.dashboard')}</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/settings')}>{t('nav.settings')}</DropdownMenuItem>
                  {isAdmin && <DropdownMenuItem onClick={() => navigate('/admin')} data-testid="menu-admin"><ShieldCheck className="w-4 h-4 mr-2" />Admin</DropdownMenuItem>}
                  <DropdownMenuItem onClick={logout} data-testid="signout-btn"><LogOut className="w-4 h-4 mr-2" />{t('nav.signout')}</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button variant="secondary" size="sm" onClick={() => setShowLogin(true)} data-testid="signin-btn">{t('nav.signin')}</Button>
            )}
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
};
