import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { ScoreBar, metricLabel } from '@/components/ScoreBar';
import { useLang } from '@/lib/i18n';
import { Bookmark, BookmarkCheck, ArrowRight, Search, ShieldCheck, Lightbulb } from 'lucide-react';

const METRICS = ['pain','worsening','purchasing_power','speed','market_validation','differentiation'];

export const OpportunityCard = ({ opp, onBuild, onSave, researched }) => {
  const { t, lang } = useLang();
  const [open, setOpen] = React.useState(false);
  const score = opp.overall_score;
  const scoreColor = score >= 7 ? 'text-[hsl(var(--success))]' : score >= 5 ? 'text-[hsl(var(--amber))]' : 'text-[hsl(var(--warning))]';

  const detailRows = [
    ['target_customer', t('opp.detail.target'), Search],
    ['problem', t('opp.detail.problem'), null],
    ['desired_outcome', t('opp.detail.outcome'), null],
    ['market_evidence', t('opp.detail.evidence'), ShieldCheck],
    ['existing_alternatives', t('opp.detail.alternatives'), null],
    ['product_gap', t('opp.detail.gap'), Lightbulb],
    ['product_concept', t('opp.detail.concept'), null],
  ];

  return (
    <>
      <Card
        className="p-5 card-elev card-elev-hover bg-card flex flex-col transition-shadow cursor-pointer"
        data-testid={`opportunity-card-${opp.id}`}
        onClick={() => setOpen(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter') setOpen(true); }}
      >
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
          <Button variant="ghost" size="sm" className="text-xs gap-1 text-muted-foreground" onClick={(e) => { e.stopPropagation(); setOpen(true); }} data-testid={`opportunity-details-button-${opp.id}`}>
            {t('opp.viewdetails')}
          </Button>
          <div className="flex-1" />
          <Button className="gap-1" onClick={(e) => { e.stopPropagation(); onBuild(opp); }} data-testid={`opportunity-build-button-${opp.id}`}>
            {t('opp.build')} <ArrowRight className="w-3.5 h-3.5" />
          </Button>
          <Button variant="secondary" size="icon" onClick={(e) => { e.stopPropagation(); onSave(opp); }} data-testid={`opportunity-save-button-${opp.id}`}>
            {opp.saved ? <BookmarkCheck className="w-4 h-4 text-primary" /> : <Bookmark className="w-4 h-4" />}
          </Button>
        </div>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid={`opportunity-dialog-${opp.id}`}>
          <DialogHeader>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              {opp.industry && <Badge variant="secondary" className="text-[10px]">{opp.industry}</Badge>}
              {opp.niche && <Badge variant="outline" className="text-[10px]">{opp.niche}</Badge>}
              <Badge className={`text-[10px] ml-auto ${researched ? 'bg-[hsl(var(--info-soft))] text-[hsl(var(--info))]' : 'bg-[hsl(var(--amber-soft))] text-[hsl(var(--amber))]'}`} data-testid={`opportunity-confidence-${opp.id}`}>
                {researched ? t('opp.confidence.researched') : t('opp.confidence.hypothesis')}
              </Badge>
            </div>
            <DialogTitle className="font-display text-2xl pr-6">{opp.name}</DialogTitle>
            <DialogDescription className="sr-only">{opp.problem}</DialogDescription>
          </DialogHeader>

          <div className="flex items-center gap-4 py-2">
            <div className="text-center">
              <div className={`font-display text-4xl leading-none ${scoreColor}`}>{score}</div>
              <div className="text-[9px] uppercase tracking-wide text-muted-foreground mt-1">{t('opp.overall')}</div>
            </div>
            <div className="flex-1 space-y-1.5">
              {METRICS.map(m => <ScoreBar key={m} metricKey={m} value={opp.scores?.[m] ?? 5} lang={lang} />)}
            </div>
          </div>

          <div className="space-y-4 mt-2">
            {detailRows.map(([key, label, Icon]) => opp[key] ? (
              <div key={key}>
                <div className="flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  {Icon && <Icon className="w-3.5 h-3.5" />} {label}
                </div>
                <p className="text-sm leading-relaxed">{opp[key]}</p>
              </div>
            ) : null)}
          </div>

          <DialogFooter className="mt-2 flex-row justify-between sm:justify-between gap-2">
            <Button variant="secondary" onClick={() => onSave(opp)} className="gap-1" data-testid={`opportunity-dialog-save-${opp.id}`}>
              {opp.saved ? <BookmarkCheck className="w-4 h-4 text-primary" /> : <Bookmark className="w-4 h-4" />} {t('opp.saved')}
            </Button>
            <Button onClick={() => { setOpen(false); onBuild(opp); }} className="gap-1" data-testid={`opportunity-dialog-build-${opp.id}`}>
              {t('opp.build')} <ArrowRight className="w-4 h-4" />
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
