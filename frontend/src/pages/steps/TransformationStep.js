import React, { useState, useEffect } from 'react';
import { useLang } from '@/lib/i18n';
import { genTransformation, patchProject, setPalette } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Working } from '@/components/Loading';
import { Wand2, ArrowRight, ArrowLeft, RefreshCw, Save, Palette } from 'lucide-react';
import { toast } from 'sonner';

const PALETTE_KEYS = [['primary', 'Primer'], ['secondary', 'Sekunder'], ['accent', 'Aksen'], ['background', 'Latar'], ['text', 'Teks']];
const PRESETS = [
  { name: 'Ocean', c: { primary: '#0B6E6B', secondary: '#111C2E', accent: '#C07A2B', background: '#FBFAF7', text: '#0B1220' } },
  { name: 'Royal', c: { primary: '#1E3A8A', secondary: '#0F172A', accent: '#D97706', background: '#F8FAFC', text: '#0F172A' } },
  { name: 'Forest', c: { primary: '#166534', secondary: '#14532D', accent: '#CA8A04', background: '#F7FEE7', text: '#1A2E05' } },
  { name: 'Rose', c: { primary: '#9F1239', secondary: '#4C0519', accent: '#0F766E', background: '#FFF1F2', text: '#1F2937' } },
  { name: 'Slate', c: { primary: '#334155', secondary: '#0F172A', accent: '#EA580C', background: '#F8FAFC', text: '#0F172A' } },
];

export default function TransformationStep({ project, setProject, goTo }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [tr, setTr] = useState(project.transformation || null);
  useEffect(() => { setTr(project.transformation || null); }, [project.transformation]);

  const gen = async () => {
    setBusy(true);
    try { const p = await genTransformation(project.id); setProject(p); setTr(p.transformation); }
    catch (e) { toast.error('Gagal. Pastikan positioning sudah dibuat.'); }
    finally { setBusy(false); }
  };
  const save = async () => { const p = await patchProject(project.id, { transformation: tr }); setProject(p); toast.success(t('common.saved')); };
  const savePalette = async (pal) => { const np = { ...tr, palette: pal }; setTr(np); const p = await setPalette(project.id, pal); setProject(p); };
  const setCat = (i, field, v) => setTr(o => { const cats = [...o.categories]; cats[i] = { ...cats[i], [field]: v }; return { ...o, categories: cats }; });
  const setField = (k, v) => setTr(o => ({ ...o, [k]: v }));
  const palette = (tr && tr.palette) || PRESETS[0].c;

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
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="secondary" size="sm" className="gap-1" data-testid="product-palette-picker"><Palette className="w-3.5 h-3.5" /> {t('trans.palette')}</Button>
            </PopoverTrigger>
            <PopoverContent className="w-80">
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {PRESETS.map(p => (
                    <button key={p.name} onClick={() => savePalette(p.c)} className="flex items-center gap-1 border border-border rounded-full pl-1 pr-2 py-1 hover:bg-secondary">
                      <span className="w-4 h-4 rounded-full" style={{ background: p.c.primary }} />
                      <span className="text-xs">{p.name}</span>
                    </button>
                  ))}
                </div>
                <div className="space-y-2">
                  {PALETTE_KEYS.map(([k, lbl]) => (
                    <div key={k} className="flex items-center gap-2">
                      <input type="color" value={palette[k] || '#000000'} onChange={e => savePalette({ ...palette, [k]: e.target.value })} className="w-8 h-8 rounded border border-border p-0" data-testid={`palette-${k}`} />
                      <span className="text-xs w-20">{lbl}</span>
                      <Input value={palette[k] || ''} onChange={e => savePalette({ ...palette, [k]: e.target.value })} className="h-8 font-mono text-xs" />
                    </div>
                  ))}
                </div>
              </div>
            </PopoverContent>
          </Popover>
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
