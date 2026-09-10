import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLang, LANGUAGE_OPTIONS } from '@/lib/i18n';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { getSettings, putSettings, getEconomy, redeemCode, getUsage } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Moon, Sun, Ticket, ShieldCheck, Sparkles, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';

const PLAN_LABEL = { free: 'plan.free', creator: 'plan.creator', pro: 'plan.pro' };

export default function Settings() {
  const { t, lang, setLang } = useLang();
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [productLang, setProductLang] = useState(localStorage.getItem('khova_product_lang') || 'id');
  const [economy, setEconomy] = useState(null);
  const [usage, setUsage] = useState(null);
  const [code, setCode] = useState('');
  const [redeeming, setRedeeming] = useState(false);

  const loadEconomy = () => { getEconomy().then(setEconomy).catch(() => setEconomy(null)); };
  const loadUsage = () => { getUsage().then(setUsage).catch(() => setUsage(null)); };

  useEffect(() => {
    getSettings().then(s => { if (s.product_language) setProductLang(s.product_language); }).catch(() => {});
    loadEconomy();
    loadUsage();
  }, []);

  const save = async () => {
    localStorage.setItem('khova_product_lang', productLang);
    try { await putSettings({ ui_language: lang, product_language: productLang }); toast.success(t('common.saved')); }
    catch (e) { toast.error(t('common.saveFailed') || 'Could not save settings'); }
  };

  const doRedeem = async () => {
    if (!code.trim()) return;
    setRedeeming(true);
    try {
      const res = await redeemCode(code.trim());
      toast.success(res.message || 'Code redeemed', {
        description: res.credits_granted ? t('credits.remaining', { n: res.balance }) : undefined,
      });
      setCode('');
      loadEconomy();
      loadUsage();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Invalid or expired code.');
    } finally { setRedeeming(false); }
  };

  const isAdmin = economy?.role === 'admin' || user?.role === 'admin';

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 min-h-[80vh]">
      <h1 className="font-display text-3xl mb-6" data-testid="settings-title">{t('settings.title')}</h1>

      {/* Language */}
      <Card className="p-6 bg-card card-elev mb-6">
        <h2 className="font-semibold mb-4">{t('settings.langcard')}</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <Label className="mb-2 block">{t('settings.uilang')}</Label>
            <Select value={lang} onValueChange={setLang}>
              <SelectTrigger data-testid="settings-ui-language-select"><SelectValue /></SelectTrigger>
              <SelectContent>{LANGUAGE_OPTIONS.slice(0, 2).map(o => <SelectItem key={o.code} value={o.code}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div>
            <Label className="mb-2 block">{t('settings.productlang')}</Label>
            <Select value={productLang} onValueChange={setProductLang}>
              <SelectTrigger data-testid="settings-product-language-select"><SelectValue /></SelectTrigger>
              <SelectContent>{LANGUAGE_OPTIONS.map(o => <SelectItem key={o.code} value={o.code}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>
        <Button onClick={save} data-testid="settings-save-button" className="mt-5">{t('common.save')}</Button>
      </Card>

      {/* Appearance / Dark mode */}
      <Card className="p-6 bg-card card-elev mb-6">
        <h2 className="font-semibold mb-4">{t('settings.appearance')}</h2>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="w-9 h-9 rounded-lg bg-secondary flex items-center justify-center">
              {isDark ? <Moon className="w-4 h-4 text-primary" /> : <Sun className="w-4 h-4 text-amber-500" />}
            </span>
            <div>
              <div className="text-sm font-medium">{t('settings.darkmode')}</div>
              <div className="text-xs text-muted-foreground">{t('settings.darkmode.desc')}</div>
            </div>
          </div>
          <Switch checked={isDark} onCheckedChange={toggleTheme} data-testid="settings-darkmode-toggle" aria-label={t('settings.darkmode')} />
        </div>
      </Card>

      {/* Plan & Credits */}
      {economy && (
        <Card className="p-6 bg-card card-elev mb-6" data-testid="settings-plan-card">
          <h2 className="font-semibold mb-4">{t('settings.plan')}</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="rounded-xl bg-secondary p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{t('settings.plan.current')}</div>
              <div className="flex items-center gap-2 mt-1">
                <Badge className="bg-primary text-primary-foreground capitalize" data-testid="settings-plan-badge">{t(PLAN_LABEL[economy.plan] || 'plan.free')}</Badge>
              </div>
            </div>
            <div className="rounded-xl bg-secondary p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{t('settings.plan.credits')}</div>
              <div className="font-display text-2xl mt-1" data-testid="settings-credits-value">{economy.credits}</div>
            </div>
            <div className="rounded-xl bg-secondary p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{t('settings.plan.creations')}</div>
              <div className="font-display text-2xl mt-1" data-testid="settings-creations-value">
                {economy.creations_remaining === null || economy.creations_remaining === undefined ? '∞' : economy.creations_remaining}
              </div>
            </div>
          </div>
          {isAdmin && (
            <Button variant="secondary" className="mt-5 gap-2" onClick={() => navigate('/admin')} data-testid="settings-admin-link">
              <ShieldCheck className="w-4 h-4" /> {t('settings.admin')}
            </Button>
          )}
        </Card>
      )}

      {/* Usage Insights (own data only) */}
      {usage && (
        <Card className="p-6 bg-card card-elev mb-6" data-testid="settings-usage-card">
          <h2 className="font-semibold mb-4 flex items-center gap-2"><BarChart3 className="w-4 h-4 text-primary" /> {t('usage.title')}</h2>
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="rounded-xl bg-secondary p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{t('usage.remaining')}</div>
              <div className="font-display text-2xl mt-1" data-testid="usage-credits-remaining">{usage.credits_remaining}</div>
            </div>
            <div className="rounded-xl bg-secondary p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{t('usage.used')}</div>
              <div className="font-display text-2xl mt-1" data-testid="usage-credits-used">{usage.total_credits_used}</div>
            </div>
            <div className="rounded-xl bg-secondary p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">{t('usage.gens')}</div>
              <div className="font-display text-2xl mt-1" data-testid="usage-generations">{usage.product_generations}</div>
            </div>
          </div>

          {(usage.products || []).length > 0 ? (
            <div className="mt-6">
              <div className="text-xs uppercase tracking-wide text-muted-foreground mb-3">{t('usage.perproduct')}</div>
              <div className="space-y-3" data-testid="usage-per-product">
                {usage.products.map((p) => {
                  const max = Math.max(...usage.products.map(x => x.credits_used), 1);
                  const pct = Math.max(4, Math.round((p.credits_used / max) * 100));
                  return (
                    <div key={p.project_id}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="truncate max-w-[70%]">{p.title}</span>
                        <span className="font-mono text-xs text-muted-foreground">{p.credits_used} · {t('usage.gencount', { n: p.generations })}</span>
                      </div>
                      <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground mt-5" data-testid="usage-empty">{t('usage.empty')}</p>
          )}
        </Card>
      )}

      {/* Redeem code */}
      <Card className="p-6 bg-card card-elev mb-6">
        <h2 className="font-semibold mb-1 flex items-center gap-2"><Ticket className="w-4 h-4 text-primary" /> {t('settings.redeem')}</h2>
        <p className="text-xs text-muted-foreground mb-4">{t('settings.redeem.desc')}</p>
        <div className="flex gap-2">
          <Input placeholder={t('settings.redeem.placeholder')} value={code} onChange={e => setCode(e.target.value.toUpperCase())} data-testid="settings-redeem-input" className="font-mono" />
          <Button onClick={doRedeem} disabled={redeeming || !code.trim()} data-testid="settings-redeem-button" className="gap-1">
            <Sparkles className="w-4 h-4" /> {redeeming ? '...' : t('settings.redeem.btn')}
          </Button>
        </div>
      </Card>

      {!user && <p className="text-xs text-muted-foreground mt-3" data-testid="settings-signin-hint">Sign in to save settings to your account and manage credits. Currently stored on this device.</p>}
    </div>
  );
}
