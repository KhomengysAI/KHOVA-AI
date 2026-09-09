import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { runQA, applyQA, applyQAIssue } from '@/lib/api';
import { afterGeneration, creditDescription } from '@/lib/economy';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Working } from '@/components/Loading';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { ShieldCheck, ArrowRight, RefreshCw, Wand2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

const SEV = { high: 'bg-[hsl(var(--danger,0_76%_40%))] text-white', medium: 'bg-[hsl(var(--amber-soft))] text-[hsl(var(--amber))]', low: 'bg-secondary text-muted-foreground' };

export default function QAStep({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applyingId, setApplyingId] = useState(null);
  const report = (project.qa || [])[0];

  const run = () => { if (!ensureAuth(run)) return; (async () => { setBusy(true); try { const p = await runQA(project.id); setProject(p); toast.success(t('toast.qa.done', { n: p.qa?.[0]?.overall }), { description: creditDescription(p, t) }); afterGeneration(p, t); } catch (e) { toast.error(e?.response?.data?.detail || 'QA failed.'); } finally { setBusy(false); } })(); };
  const apply = async () => {
    setApplying(true);
    try {
      const p = await applyQA(project.id);
      setProject(p);
      toast.success(t('toast.qa.apply.done'), { description: creditDescription(p, t), action: { label: t('toast.qa.apply.open'), onClick: () => goTo('create') } });
      afterGeneration(p, t);
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed.'); }
    finally { setApplying(false); }
  };
  const applyOne = (iss) => {
    if (!ensureAuth(() => applyOne(iss))) return;
    setApplyingId(iss.id);
    (async () => {
      try {
        const p = await applyQAIssue(project.id, iss.id);
        setProject(p);
        const target = p._applied?.target ? ` (${p._applied.target})` : '';
        toast.success(`${t('qa.applied')}${target}`, { description: [t('qa.preview.updated'), creditDescription(p, t)].filter(Boolean).join(' · '), action: { label: t('toast.qa.apply.open'), onClick: () => goTo('create') } });
        afterGeneration(p, t);
      } catch (e) { toast.error(e?.response?.data?.detail || 'Failed.'); }
      finally { setApplyingId(null); }
    })();
  };

  if (busy) return <Working label="Memeriksa kualitas konten..." sub="Kontradiksi, pengulangan, logika, klaim, dan keselarasan transformasi." />;

  if (!report) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">{t('qa.title')}</h2>
        <p className="text-muted-foreground mb-6">Editor QA memberi skor 1-10, mendeteksi masalah, dan menyarankan perbaikan sebelum ekspor.</p>
        <Button size="lg" onClick={run} className="gap-2" data-testid="qa-run-button"><ShieldCheck className="w-4 h-4" /> Jalankan QA</Button>
      </div>
    );
  }

  const dims = report.scores || {};
  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <h2 className="font-display text-2xl">{t('qa.title')}</h2>
        <div className="flex gap-2 flex-wrap">
          <Button variant="secondary" size="sm" onClick={run} className="gap-1"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          {project.format === 'ebook' && (
            <AlertDialog>
              <AlertDialogTrigger asChild><Button size="sm" className="gap-1" data-testid="qa-apply-improvements-button"><Wand2 className="w-3.5 h-3.5" /> {t('qa.apply')}</Button></AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader><AlertDialogTitle>Terapkan perbaikan?</AlertDialogTitle><AlertDialogDescription>Versi asli setiap bab akan disimpan. Konten akan diperbarui sesuai saran QA.</AlertDialogDescription></AlertDialogHeader>
                <AlertDialogFooter><AlertDialogCancel>Batal</AlertDialogCancel><AlertDialogAction onClick={apply} disabled={applying}>{applying ? 'Menerapkan...' : 'Terapkan'}</AlertDialogAction></AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
          <Button size="sm" onClick={() => goTo('branding')} className="gap-1" data-testid="qa-continue">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[220px_1fr] gap-6">
        <div>
          <Card className="p-5 bg-accent text-center mb-4">
            <div className="font-display text-5xl text-primary">{report.overall}</div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground mt-1">Skor Keseluruhan</div>
          </Card>
          <div className="space-y-2">
            {Object.entries(dims).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-32 capitalize">{k.replace(/_/g, ' ')}</span>
                <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden"><div className="h-full bg-primary" style={{ width: `${(v/10)*100}%` }} /></div>
                <span className="text-xs font-semibold w-4">{v}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h3 className="font-semibold mb-3">Masalah <span className="text-muted-foreground font-normal">({(report.issues||[]).length})</span></h3>
          <div className="space-y-2 mb-5" data-testid="qa-issues">
            {(report.issues || []).map((iss, i) => (
              <Card key={iss.id || i} className="p-3 bg-card" data-testid={`qa-issue-${i}`}>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge className={`text-[10px] ${SEV[iss.severity] || SEV.low}`}>{iss.severity}</Badge>
                  <span className="text-xs font-mono text-muted-foreground">{iss.type}</span>
                  {iss.chapter_num !== undefined && iss.chapter_num !== null && (
                    <span className="text-[10px] text-muted-foreground">{iss.chapter_num === 0 ? 'Intro' : `Ch. ${iss.chapter_num}`}</span>
                  )}
                  <div className="ml-auto">
                    {iss.resolved ? (
                      <Badge className="text-[10px] bg-[hsl(var(--success-soft))] text-[hsl(var(--success))] gap-1" data-testid={`qa-issue-resolved-${i}`}><CheckCircle2 className="w-3 h-3" /> {t('qa.resolved')}</Badge>
                    ) : (project.format === 'ebook' && iss.id) ? (
                      <Button size="sm" variant="secondary" className="h-7 gap-1 text-xs" disabled={applyingId === iss.id} onClick={() => applyOne(iss)} data-testid={`qa-issue-apply-${i}`}>
                        <Wand2 className="w-3 h-3" /> {applyingId === iss.id ? '...' : t('qa.applyone')}
                      </Button>
                    ) : null}
                  </div>
                </div>
                <p className="text-sm">{iss.detail}</p>
                {iss.fix && <p className="text-xs text-primary mt-1">→ {iss.fix}</p>}
              </Card>
            ))}
            {(report.issues||[]).length === 0 && <Card className="p-4 bg-[hsl(var(--success-soft))] border-transparent flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[hsl(var(--success))]" /> No significant issues found.</Card>}
          </div>
          {(report.recommended_improvements || []).length > 0 && (
            <Card className="p-4 bg-secondary">
              <div className="text-sm font-medium mb-2">Saran perbaikan</div>
              <ul className="list-disc ml-5 space-y-1 text-sm text-muted-foreground">{report.recommended_improvements.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
