import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { genBranding } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Working } from '@/components/Loading';
import { Palette, ArrowRight, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const STYLES = ['Minimal', 'Professional', 'Modern', 'Premium', 'Editorial', 'Bold'];

export default function BrandingStep({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [style, setStyle] = useState((project.branding && project.branding.style) || 'Premium');
  const [busy, setBusy] = useState(false);
  const b = project.branding;

  const gen = () => { if (!ensureAuth(gen)) return; (async () => { setBusy(true); try { const p = await genBranding(project.id, style); setProject(p); toast.success('Branding dibuat'); } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal.'); } finally { setBusy(false); } })(); };

  if (busy) return <Working label="Menyusun branding..." />;

  if (!b) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">{t('branding.title')}</h2>
        <p className="text-muted-foreground mb-6">Judul, subjudul, penulis, brand, arah visual, tipografi, nada, warna, dan konsep cover.</p>
        <div className="flex items-center gap-3 mb-4"><span className="text-sm">Gaya:</span>
          <Select value={style} onValueChange={setStyle}><SelectTrigger className="w-44" data-testid="branding-style-selector"><SelectValue /></SelectTrigger><SelectContent>{STYLES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
        </div>
        <Button size="lg" onClick={gen} className="gap-2" data-testid="branding-generate-button"><Palette className="w-4 h-4" /> {t('common.generate')}</Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <h2 className="font-display text-2xl">{t('branding.title')}</h2>
        <div className="flex gap-2 flex-wrap">
          <Select value={style} onValueChange={setStyle}><SelectTrigger className="w-36 h-9"><SelectValue /></SelectTrigger><SelectContent>{STYLES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
          <Button variant="secondary" size="sm" onClick={gen} className="gap-1"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button size="sm" onClick={() => goTo('export')} className="gap-1" data-testid="branding-continue">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card className="p-5 bg-card">
          <div className="font-display text-2xl mb-1">{b.title}</div>
          <div className="text-muted-foreground mb-3">{b.subtitle}</div>
          <div className="text-sm space-y-1.5">
            <div><span className="text-muted-foreground">Penulis:</span> {b.author}</div>
            <div><span className="text-muted-foreground">Brand:</span> {b.brand}</div>
            <div><span className="text-muted-foreground">Nada:</span> {b.tone}</div>
            <div><span className="text-muted-foreground">Tipografi:</span> {b.typography}</div>
          </div>
          <p className="text-sm mt-3">{b.description}</p>
        </Card>
        <Card className="p-5 bg-card">
          <div className="text-sm font-medium mb-2">Palet warna</div>
          <div className="flex flex-wrap gap-2 mb-4">
            {(b.colors || []).map((c, i) => (
              <div key={i} className="text-center">
                <div className="w-12 h-12 rounded-lg border border-border" style={{ background: c.hex }} />
                <div className="text-[10px] font-mono mt-1">{c.hex}</div>
              </div>
            ))}
          </div>
          <div className="text-sm"><span className="text-muted-foreground">Arah visual:</span> {b.visual_direction}</div>
          <div className="text-sm mt-2"><span className="text-muted-foreground">Konsep cover:</span> {b.cover_concept}</div>
        </Card>
      </div>
    </div>
  );
}
