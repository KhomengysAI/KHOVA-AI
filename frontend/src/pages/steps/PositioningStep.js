import React, { useState, useEffect } from 'react';
import { useLang } from '@/lib/i18n';
import { genPositioning, patchProject } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Working } from '@/components/Loading';
import { Target, ArrowRight, RefreshCw, Save } from 'lucide-react';
import { toast } from 'sonner';

const FIELDS = [
  ['target_customer', 'Target Customer'], ['problem', 'Problem'], ['desired_result', 'Desired Result'],
  ['unique_angle', 'Unique Angle'], ['positioning', 'Positioning'], ['product_promise', 'Product Promise'],
  ['mechanism', 'Mechanism'], ['suggested_pricing', 'Suggested Pricing'], ['why_choose', 'Why Choose This'],
  ['alternatives', 'Alternatives'], ['competitive_differentiation', 'Competitive Differentiation'],
];

export default function PositioningStep({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [pos, setPos] = useState(project.positioning || null);
  useEffect(() => { setPos(project.positioning || null); }, [project.positioning]);

  const gen = async () => {
    setBusy(true);
    try { const p = await genPositioning(project.id); setProject(p); setPos(p.positioning); }
    catch (e) { toast.error('Gagal. Pastikan peluang sudah dipilih.'); }
    finally { setBusy(false); }
  };
  const save = async () => { const p = await patchProject(project.id, { positioning: pos }); setProject(p); toast.success(t('common.saved')); };
  const set = (k, v) => setPos(o => ({ ...o, [k]: v }));

  if (busy) return <Working label="Menyusun strategi positioning..." />;

  if (!pos) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">{t('pos.title')}</h2>
        <p className="text-muted-foreground mb-6">Buat strategi produk berdasarkan peluang yang Anda pilih.</p>
        <Button size="lg" onClick={gen} className="gap-2" data-testid="positioning-generate-button"><Target className="w-4 h-4" /> {t('common.generate')}</Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <h2 className="font-display text-2xl">{t('pos.title')}</h2>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={gen} className="gap-1" data-testid="positioning-regenerate"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button variant="secondary" size="sm" onClick={save} className="gap-1" data-testid="positioning-save"><Save className="w-3.5 h-3.5" /> {t('common.save')}</Button>
          <Button size="sm" onClick={() => goTo('transformation')} className="gap-1" data-testid="positioning-continue">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <Card className="p-5 bg-accent mb-5">
        <Label className="mb-2 block text-xs uppercase tracking-wide">One-liner</Label>
        <Input value={pos.one_liner || ''} onChange={e => set('one_liner', e.target.value)} className="text-base bg-card" data-testid="positioning-one-liner-input" />
      </Card>

      <div className="grid sm:grid-cols-2 gap-4">
        {FIELDS.map(([k, lbl]) => (
          <div key={k}>
            <Label className="mb-1.5 block text-sm">{lbl}</Label>
            <Textarea rows={2} value={pos[k] || ''} onChange={e => set(k, e.target.value)} data-testid={`positioning-field-${k}`} />
          </div>
        ))}
      </div>
    </div>
  );
}
