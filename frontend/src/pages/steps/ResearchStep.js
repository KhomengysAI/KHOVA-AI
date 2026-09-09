import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { runResearch } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Working } from '@/components/Loading';
import { Search, ArrowRight, ExternalLink, RefreshCw, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const LABEL_STYLE = {
  'RESEARCH-BACKED': 'bg-[hsl(var(--info-soft))] text-[hsl(var(--info))] border-transparent',
  'HYPOTHESIS': 'bg-[hsl(var(--amber-soft))] text-[hsl(var(--amber))] border-transparent',
  'ASSUMPTION': 'bg-secondary text-muted-foreground border-transparent',
};

export default function ResearchStep({ project, setProject, goTo }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const research = project.research;

  const run = async () => {
    setBusy(true);
    try {
      const p = await runResearch(project.id);
      setProject(p);
      if (p.research?.status === 'unavailable') toast.warning(t('toast.research.unavailable'));
      else toast.success(t('toast.research.done', { n: (p.research?.findings || []).length, s: (p.research?.sources || []).length }));
    }
    catch (e) { toast.error('Riset gagal. Coba lagi.'); }
    finally { setBusy(false); }
  };

  if (busy) return <Working label="Meriset pasar secara langsung..." sub="Mencari produk, harga, ulasan, komplain, dan celah pasar dari web." />;

  if (!research) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">{t('research.title')}</h2>
        <p className="text-muted-foreground mb-6">Kami melakukan riset pasar waktu-nyata dengan pencarian web untuk memastikan peluang berbasis bukti, bukan tebakan AI.</p>
        <Button size="lg" onClick={run} className="gap-2" data-testid="research-run-button"><Search className="w-4 h-4" /> {t('research.run')}</Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <h2 className="font-display text-2xl">{t('research.title')}</h2>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={run} className="gap-1" data-testid="research-regenerate"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button size="sm" onClick={() => goTo('opportunities')} className="gap-1" data-testid="research-continue">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      {research.status === 'unavailable' && (
        <Alert className="mb-4 bg-[hsl(var(--warning-soft))] border-transparent">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Riset web tidak tersedia</AlertTitle>
          <AlertDescription>{research.note}</AlertDescription>
        </Alert>
      )}

      {research.summary && (
        <Card className="p-5 bg-secondary mb-5">
          <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">{t('research.summary')}</div>
          <p className="text-sm">{research.summary}</p>
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <div>
          <h3 className="font-semibold mb-3">{t('research.findings')} <span className="text-muted-foreground font-normal">({(research.findings||[]).length})</span></h3>
          <div className="space-y-3" data-testid="research-findings">
            {(research.findings || []).map((f, i) => (
              <Card key={i} className="p-4 bg-card">
                <Badge className={`mb-2 text-[10px] ${LABEL_STYLE[f.label] || 'bg-secondary'}`}>{f.label}</Badge>
                <p className="text-sm">{f.text}</p>
                {f.relevance && <p className="text-xs text-muted-foreground mt-1.5">{f.relevance}</p>}
              </Card>
            ))}
          </div>
        </div>
        <div>
          <h3 className="font-semibold mb-3">{t('research.sources')} <span className="text-muted-foreground font-normal">({(research.sources||[]).length})</span></h3>
          <Card className="bg-card overflow-hidden" data-testid="research-sources-table">
            <Table>
              <TableHeader><TableRow><TableHead>Sumber</TableHead><TableHead className="w-16 text-right">Buka</TableHead></TableRow></TableHeader>
              <TableBody>
                {(research.sources || []).map((s, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-mono text-xs text-[hsl(var(--info))] break-all">{s.title}</TableCell>
                    <TableCell className="text-right"><a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex"><ExternalLink className="w-4 h-4 text-muted-foreground hover:text-primary" /></a></TableCell>
                  </TableRow>
                ))}
                {(research.sources || []).length === 0 && <TableRow><TableCell colSpan={2} className="text-sm text-muted-foreground py-4">Tidak ada sumber eksplisit.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </Card>
        </div>
      </div>
    </div>
  );
}
