import React, { useState, useMemo } from 'react';
import { useLang } from '@/lib/i18n';
import { genOpportunities, toggleSaveOpp, selectOpportunity } from '@/lib/api';
import { OpportunityCard } from '@/components/OpportunityCard';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Working } from '@/components/Loading';
import { metricLabel } from '@/components/ScoreBar';
import { Lightbulb, RefreshCw, HelpCircle } from 'lucide-react';
import { toast } from 'sonner';

const METRICS = ['pain', 'worsening', 'purchasing_power', 'speed', 'market_validation', 'differentiation'];

const ScoringHelpDialog = () => {
  const { t, lang } = useLang();
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground" onClick={() => setOpen(true)} data-testid="scoring-help-button">
        <HelpCircle className="w-3.5 h-3.5" /> {t('score.how')}
      </Button>
      <DialogContent className="max-w-lg" data-testid="scoring-help-dialog">
        <DialogHeader>
          <DialogTitle>{t('score.how')}</DialogTitle>
          <DialogDescription>{t('score.how.desc')}</DialogDescription>
        </DialogHeader>
        <div className="space-y-3 mt-1">
          {METRICS.map(m => (
            <div key={m} className="border-b border-border pb-2 last:border-0">
              <div className="text-sm font-semibold mb-0.5">{metricLabel(m, lang)}</div>
              <p className="text-xs text-muted-foreground">{t(`score.desc.${m}`)}</p>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default function OpportunitiesStep({ project, setProject, goTo }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [sort, setSort] = useState('overall');
  const [filter, setFilter] = useState('all');
  const opps = project.opportunities || [];
  const researched = (project.research && project.research.status === 'complete');

  const gen = async () => {
    setBusy(true);
    try { const p = await genOpportunities(project.id); setProject(p); toast.success(t('toast.opp.done', { n: (p.opportunities || []).length })); }
    catch (e) { toast.error('Gagal membuat peluang. Coba lagi.'); }
    finally { setBusy(false); }
  };

  const save = async (opp) => { const p = await toggleSaveOpp(project.id, opp.id); setProject(p); };
  const build = async (opp) => {
    try { const p = await selectOpportunity(project.id, opp.id); setProject(p); toast.success('Peluang dipilih. Menyiapkan positioning produk...'); goTo('positioning'); }
    catch (e) { toast.error('Gagal memilih.'); }
  };

  const shown = useMemo(() => {
    let list = [...opps];
    if (filter === 'saved') list = list.filter(o => o.saved);
    list.sort((a, b) => (sort === 'overall' ? b.overall_score - a.overall_score : (b.scores?.[sort] || 0) - (a.scores?.[sort] || 0)));
    return list;
  }, [opps, sort, filter]);

  if (busy) return <Working label="Menemukan kantong menguntungkan..." sub="Menganalisis riset untuk menghasilkan ~20 peluang tervalidasi dengan skor." />;

  if (opps.length === 0) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">{t('opp.title')}</h2>
        <p className="text-muted-foreground mb-6">Berdasarkan riset pasar, kami menghasilkan sekitar 20 peluang produk yang tervalidasi dan diberi skor.</p>
        <Button size="lg" onClick={gen} className="gap-2" data-testid="opportunities-generate-button"><Lightbulb className="w-4 h-4" /> {t('common.generate')} Peluang</Button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-1 flex-wrap">
        <h2 className="font-display text-2xl">{t('opp.title')} <span className="text-muted-foreground text-lg">({opps.length})</span></h2>
        <div className="flex items-center gap-2 flex-wrap">
          <ToggleGroup type="single" value={filter} onValueChange={v => v && setFilter(v)} size="sm">
            <ToggleGroupItem value="all" data-testid="opp-filter-all">Semua</ToggleGroupItem>
            <ToggleGroupItem value="saved" data-testid="opp-filter-saved">{t('opp.saved')}</ToggleGroupItem>
          </ToggleGroup>
          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger className="w-40 h-9" data-testid="opp-sort-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="overall">{t('opp.overall')}</SelectItem>
              <SelectItem value="pain">Pain</SelectItem>
              <SelectItem value="purchasing_power">Purchasing Power</SelectItem>
              <SelectItem value="market_validation">Market Validation</SelectItem>
              <SelectItem value="differentiation">Differentiation</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="secondary" size="sm" onClick={gen} className="gap-1" data-testid="opportunities-regenerate"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
        </div>
      </div>
      <div className="mb-4"><ScoringHelpDialog /></div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {shown.map(o => <OpportunityCard key={o.id} opp={o} onBuild={build} onSave={save} researched={researched} />)}
      </div>
    </div>
  );
}
