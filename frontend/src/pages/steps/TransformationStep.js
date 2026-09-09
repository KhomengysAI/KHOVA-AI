import React, { useState, useEffect } from 'react';
import { useLang } from '@/lib/i18n';
import { genTransformation, patchProject, setPalette } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { isAnonLimit } from '@/lib/economy';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { PalettePicker, PALETTE_PRESETS } from '@/components/PalettePicker';
import { Working } from '@/components/Loading';
import { Wand2, ArrowRight, RefreshCw, Save } from 'lucide-react';
import { toast } from 'sonner';

export default function TransformationStep({ project, setProject, goTo }) {
  const { t, lang } = useLang();
  const { setShowLogin } = useAuth();
  const [busy, setBusy] = useState(false);
  const [tr, setTr] = useState(project.transformation || null);
  useEffect(() => { setTr(project.transformation || null); }, [project.transformation]);

  const gen = async () => {
    setBusy(true);
    try { const p = await genTransformation(project.id); setProject(p); setTr(p.transformation); toast.success(t('toast.trans.done')); }
    catch (e) {
      if (isAnonLimit(e)) { toast.error(e?.response?.data?.detail || t('gen.failed')); setShowLogin && setShowLogin(true); }
      else toast.error(e?.response?.data?.detail || 'Gagal. Pastikan positioning sudah dibuat.');
    }
    finally { setBusy(false); }
  };
  const save = async () => { const p = await patchProject(project.id, { transformation: tr }); setProject(p); toast.success(t('common.saved')); };
  const savePalette = async (pal) => { const np = { ...tr, palette: pal }; setTr(np); const p = await setPalette(project.id, pal); setProject(p); };
  const setCat = (i, field, v) => setTr(o => { const cats = [...o.categories]; cats[i] = { ...cats[i], [field]: v }; return { ...o, categories: cats }; });
  const setField = (k, v) => setTr(o => ({ ...o, [k]: v }));
  const palette = (tr && tr.palette) || PALETTE_PRESETS[0].c;

  if (busy) return <Working label="Memetakan transformasi viseral..." />;

  if (!tr) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">{t('trans.title')}</h2>
        <p className="text-muted-foreground mb-6">Petakan kondisi pelanggan dari Sebelum ke Sesudah di 6 dimensi.</p>
        <Button size="lg" onClick={gen} className="gap-2" data-testid="transformation-generate-button"><Wand2 className="w-4 h-4" /> {t('common.generate')}</Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <h2 className="font-display text-2xl">{t('trans.title')}</h2>
        <div className="flex gap-2 flex-wrap">
          <PalettePicker palette={palette} onChange={savePalette} lang={lang} label={t('trans.palette')} />
          <Button variant="secondary" size="sm" onClick={gen} className="gap-1"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button variant="secondary" size="sm" onClick={save} className="gap-1" data-testid="transformation-save"><Save className="w-3.5 h-3.5" /> {t('common.save')}</Button>
          <Button size="sm" onClick={() => goTo('format')} className="gap-1" data-testid="transformation-continue">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-3 mb-5">
        {[['core_transformation', 'Core Transformation'], ['core_promise', 'Core Promise'], ['customer_win', 'Customer Win']].map(([k, lbl]) => (
          <Card key={k} className="p-4 bg-accent">
            <Label className="text-[10px] uppercase tracking-wide mb-1 block">{lbl}</Label>
            <Textarea rows={3} value={tr[k] || ''} onChange={e => setField(k, e.target.value)} className="bg-card text-sm" data-testid={`trans-${k}`} />
          </Card>
        ))}
      </div>

      <div className="space-y-3">
        <div className="hidden sm:grid grid-cols-[160px_1fr_1fr] gap-3 px-1 text-xs uppercase tracking-wide text-muted-foreground">
          <span>Dimensi</span><span className="text-[hsl(var(--warning))]">{t('trans.before')}</span><span className="text-[hsl(var(--success))]">{t('trans.after')}</span>
        </div>
        {(tr.categories || []).map((c, i) => (
          <Card key={c.key || i} className="p-3 grid sm:grid-cols-[160px_1fr_1fr] gap-3 items-start bg-card">
            <div className="font-medium text-sm pt-2">{c.label}</div>
            <Textarea rows={2} value={c.before || ''} onChange={e => setCat(i, 'before', e.target.value)} className="text-sm border-l-2 border-l-[hsl(var(--warning))]" data-testid={`trans-before-${i}`} />
            <Textarea rows={2} value={c.after || ''} onChange={e => setCat(i, 'after', e.target.value)} className="text-sm border-l-2 border-l-[hsl(var(--success))]" data-testid={`trans-after-${i}`} />
          </Card>
        ))}
      </div>
    </div>
  );
}
