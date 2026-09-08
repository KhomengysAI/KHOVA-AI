import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { setFormat } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Table2, Globe, Lock, Check } from 'lucide-react';
import { toast } from 'sonner';

const ACTIVE = [
  { key: 'ebook', label: 'eBook (PDF)', icon: FileText, desc: 'Manuskrip lengkap dengan desain premium, cover & ekspor PDF asli.' },
  { key: 'spreadsheet', label: 'Spreadsheet (XLSX)', icon: Table2, desc: 'Planner/tracker/kalkulator dengan rumus & beberapa sheet.' },
  { key: 'website', label: 'Simple Website', icon: Globe, desc: 'Landing page konversi yang responsif dan siap tayang.' },
];
const SOON = ['Workbook', 'Checklist', 'Template Pack', 'Prompt Pack', 'Toolkit', 'Social Media', 'Image Pack', 'Video'];

export default function FormatStep({ project, setProject, goTo }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(null);
  const current = project.format;

  const pick = async (key) => {
    setBusy(key);
    try { const p = await setFormat(project.id, key); setProject(p); toast.success('Format dipilih'); goTo('create'); }
    catch (e) { toast.error('Gagal memilih format.'); }
    finally { setBusy(null); }
  };

  return (
    <div>
      <h2 className="font-display text-2xl mb-1">{t('format.title')}</h2>
      <p className="text-muted-foreground mb-6">Peluang, positioning, dan transformasi Anda akan dipakai untuk format apa pun yang dipilih.</p>

      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        {ACTIVE.map(f => (
          <Card key={f.key} onClick={() => !busy && pick(f.key)}
            className={`p-5 cursor-pointer transition-shadow card-elev card-elev-hover bg-card relative ${current === f.key ? 'ring-2 ring-primary' : ''}`}
            data-testid={`format-card-${f.key}`}>
            {current === f.key && <span className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary flex items-center justify-center"><Check className="w-3.5 h-3.5 text-primary-foreground" /></span>}
            <f.icon className="w-7 h-7 text-primary mb-3" />
            <div className="font-semibold mb-1">{f.label}</div>
            <p className="text-sm text-muted-foreground">{f.desc}</p>
            {busy === f.key && <p className="text-xs text-primary mt-2">Memilih...</p>}
          </Card>
        ))}
      </div>

      <h3 className="font-semibold text-sm text-muted-foreground mb-3">{t('landing.comingsoon')}</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {SOON.map(s => (
          <Card key={s} className="p-4 bg-secondary opacity-70">
            <Lock className="w-4 h-4 text-muted-foreground mb-2" />
            <div className="text-sm font-medium">{s}</div>
            <Badge variant="outline" className="text-[10px] mt-1">{t('landing.comingsoon')}</Badge>
          </Card>
        ))}
      </div>
    </div>
  );
}
