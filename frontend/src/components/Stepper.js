import React from 'react';
import { useLang } from '@/lib/i18n';
import { CheckCircle2, Lock, Loader2, AlertTriangle, Circle } from 'lucide-react';

export const STEP_KEYS = ['discover','research','opportunities','positioning','transformation','format','create','qa','branding','export'];

export const Stepper = ({ statusMap, current, onSelect }) => {
  const { t } = useLang();
  return (
    <nav data-testid="wizard-stepper" className="space-y-1">
      {STEP_KEYS.map((key, idx) => {
        const st = statusMap[key] || 'locked';
        const isCurrent = current === key;
        const clickable = st !== 'locked';
        const Icon = st === 'done' ? CheckCircle2 : st === 'error' ? AlertTriangle : st === 'locked' ? Lock : Circle;
        return (
          <button key={key} data-testid={`wizard-step-item-${key}`} disabled={!clickable}
            onClick={() => clickable && onSelect(key)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${isCurrent ? 'bg-accent' : clickable ? 'hover:bg-secondary' : 'opacity-50 cursor-not-allowed'}`}>
            <span className={`flex items-center justify-center w-6 h-6 rounded-full text-[11px] font-semibold ${st==='done' ? 'bg-primary text-primary-foreground' : isCurrent ? 'bg-[hsl(var(--amber))] text-white' : 'bg-secondary text-muted-foreground border border-border'}`}>
              {st === 'done' ? <CheckCircle2 className="w-3.5 h-3.5" /> : (idx+1)}
            </span>
            <span className="flex-1">
              <span className={`block text-sm font-medium ${isCurrent ? 'text-foreground' : clickable ? 'text-foreground' : 'text-muted-foreground'}`}>{t('steps.'+key)}</span>
            </span>
            {st === 'locked' && <Lock className="w-3.5 h-3.5 text-muted-foreground" />}
          </button>
        );
      })}
    </nav>
  );
};

export const MobileStepper = ({ statusMap, current, onSelect }) => {
  const { t } = useLang();
  return (
    <div className="lg:hidden overflow-x-auto -mx-4 px-4 pb-2">
      <div className="flex gap-2 min-w-max" data-testid="wizard-stepper-mobile">
        {STEP_KEYS.map((key, idx) => {
          const st = statusMap[key] || 'locked';
          const isCurrent = current === key;
          const clickable = st !== 'locked';
          return (
            <button key={key} disabled={!clickable} onClick={() => clickable && onSelect(key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap border ${isCurrent ? 'bg-accent border-primary text-foreground' : st==='done' ? 'bg-primary text-primary-foreground border-primary' : 'bg-card border-border text-muted-foreground'} ${!clickable && 'opacity-50'}`}>
              {idx+1}. {t('steps.'+key)}
            </button>
          );
        })}
      </div>
    </div>
  );
};
