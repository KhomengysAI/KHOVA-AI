import React, { useState, useMemo } from 'react';
import { useLang } from '@/lib/i18n';
import { genOpportunities, toggleSaveOpp, selectOpportunity } from '@/lib/api';
import { OpportunityCard } from '@/components/OpportunityCard';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Working } from '@/components/Loading';
import { Lightbulb, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

export default function OpportunitiesStep({ project, setProject, goTo }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [sort, setSort] = useState('overall');
  const [filter, setFilter] = useState('all');
  const opps = project.opportunities || [];

  const gen = async () => {
    setBusy(true);
    try { const p = await genOpportunities(project.id); setProject(p); }
    catch (e) { toast.error('Gagal membuat peluang. Coba lagi.'); }
    finally { setBusy(false); }
  };

  const save = async (opp) => { const p = await toggleSaveOpp(project.id, opp.id); setProject(p); };
  const build = async (opp) => {
    try { const p = await selectOpportunity(project.id, opp.id); setProject(p); toast.success('Peluang dipilih'); goTo('positioning'); }
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
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
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
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {shown.map(o => <OpportunityCard key={o.id} opp={o} onBuild={build} onSave={save} />)}
      </div>
    </div>
  );
}
