import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useLang } from '@/lib/i18n';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';

export const LoginModal = () => {
  const { showLogin, setShowLogin, googleLogin, devLogin } = useAuth();
  const { t } = useLang();
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);

  const doDev = async () => {
    setBusy(true);
    try {
      await devLogin(email || 'tester@khova.ai', 'Tester');
      toast.success('Signed in (dev)');
    } catch (e) { toast.error('Dev login failed'); }
    finally { setBusy(false); }
  };

  return (
    <Dialog open={showLogin} onOpenChange={setShowLogin}>
      <DialogContent className="sm:max-w-md" data-testid="login-modal">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl">{t('auth.title')}</DialogTitle>
          <DialogDescription>{t('auth.desc')}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <Button onClick={googleLogin} className="w-full h-11" data-testid="auth-google-signin-button">
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24"><path fill="currentColor" d="M12 11v2.8h4a3.5 3.5 0 0 1-1.5 2.3v1.9h2.4c1.4-1.3 2.2-3.2 2.2-5.5 0-.5 0-1-.1-1.5H12z"/><path fill="currentColor" d="M12 20c2 0 3.7-.7 4.9-1.8l-2.4-1.9c-.7.4-1.5.7-2.5.7-1.9 0-3.5-1.3-4.1-3H5.4v1.9A8 8 0 0 0 12 20z"/><path fill="currentColor" d="M7.9 13c-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9V7.3H5.4a8 8 0 0 0 0 7.2L7.9 13z"/><path fill="currentColor" d="M12 6.6c1.1 0 2 .4 2.8 1.1l2.1-2.1A8 8 0 0 0 5.4 7.3l2.5 1.9c.6-1.7 2.2-3 4.1-3z"/></svg>
            {t('auth.google')}
          </Button>
          <div className="flex items-center gap-3">
            <Separator className="flex-1" /><span className="text-xs text-muted-foreground">DEV</span><Separator className="flex-1" />
          </div>
          <div className="space-y-2">
            <Input placeholder="email (dev testing)" value={email} onChange={e => setEmail(e.target.value)} data-testid="dev-login-email" />
            <Button variant="secondary" onClick={doDev} disabled={busy} className="w-full" data-testid="dev-login-button">Dev sign in</Button>
            <p className="text-[11px] text-muted-foreground">Dev bypass is for testing only. Remove before production.</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
