import React from 'react';

const METRIC_LABELS = {
  pain: { id: 'Rasa Sakit', en: 'Pain' },
  worsening: { id: 'Memburuk', en: 'Worsening' },
  purchasing_power: { id: 'Daya Beli', en: 'Purchasing Power' },
  speed: { id: 'Kecepatan', en: 'Speed' },
  market_validation: { id: 'Validasi Pasar', en: 'Market Validation' },
  differentiation: { id: 'Diferensiasi', en: 'Differentiation' },
};

export const metricLabel = (key, lang) => (METRIC_LABELS[key] ? METRIC_LABELS[key][lang] || METRIC_LABELS[key].en : key);

export const ScoreBar = ({ metricKey, value, lang = 'id' }) => {
  const pct = Math.round((value / 10) * 100);
  let color = 'hsl(var(--warning))', track = 'hsl(var(--warning-soft))';
  if (pct >= 70) { color = 'hsl(var(--success))'; track = 'hsl(var(--success-soft))'; }
  else if (pct >= 40) { color = 'hsl(var(--amber))'; track = 'hsl(var(--amber-soft))'; }
  return (
    <div data-testid={`opportunity-score-bar-${metricKey}`} className="flex items-center gap-2">
      <span className="text-[11px] text-muted-foreground w-28 shrink-0">{metricLabel(metricKey, lang)}</span>
      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: track }}>
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[11px] font-semibold w-5 text-right">{value}</span>
    </div>
  );
};
