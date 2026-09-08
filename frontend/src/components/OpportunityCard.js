import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScoreBar } from '@/components/ScoreBar';
import { useLang } from '@/lib/i18n';
import { Bookmark, BookmarkCheck, ArrowRight } from 'lucide-react';

const METRICS = ['pain','worsening','purchasing_power','speed','market_validation','differentiation'];

export const OpportunityCard = ({ opp, onBuild, onSave }) => {
  const { t, lang } = useLang();
  const score = opp.overall_score;
  const scoreColor = score >= 7 ? 'text-[hsl(var(--success))]' : score >= 5 ? 'text-[hsl(var(--amber))]' : 'text-[hsl(var(--warning))]';
  return (
    <Card className="p-5 card-elev card-elev-hover bg-card flex flex-col transition-shadow" data-testid={`opportunity-card-${opp.id}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1">
          <h3 className="font-semibold text-base leading-snug">{opp.name}</h3>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {opp.industry && <Badge variant="secondary" className="text-[10px]">{opp.industry}</Badge>}
            {opp.niche && <Badge variant="outline" className="text-[10px]">{opp.niche}</Badge>}
          </div>
        </div>
        <div className="text-center shrink-0">
          <div className={`font-display text-3xl leading-none ${scoreColor}`}>{score}</div>
          <div className="text-[9px] uppercase tracking-wide text-muted-foreground mt-1">{t('opp.overall')}</div>
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{opp.problem}</p>
      <div className="space-y-1.5 mb-4">
        {METRICS.map(m => <ScoreBar key={m} metricKey={m} value={opp.scores?.[m] ?? 5} lang={lang} />)}
      </div>
      <div className="mt-auto flex items-center gap-2">
        <Button className="flex-1 gap-1" onClick={() => onBuild(opp)} data-testid={`opportunity-build-button-${opp.id}`}>
          {t('opp.build')} <ArrowRight className="w-3.5 h-3.5" />
        </Button>
        <Button variant="secondary" size="icon" onClick={() => onSave(opp)} data-testid={`opportunity-save-button-${opp.id}`}>
          {opp.saved ? <BookmarkCheck className="w-4 h-4 text-primary" /> : <Bookmark className="w-4 h-4" />}
        </Button>
      </div>
    </Card>
  );
};
