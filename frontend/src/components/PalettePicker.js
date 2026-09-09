import React from 'react';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Palette } from 'lucide-react';

export const PALETTE_KEYS = [['primary', 'Primer', 'Primary'], ['secondary', 'Sekunder', 'Secondary'], ['accent', 'Aksen', 'Accent'], ['background', 'Latar', 'Background'], ['text', 'Teks', 'Text']];

export const PALETTE_PRESETS = [
  { name: 'Ocean', c: { primary: '#0B6E6B', secondary: '#111C2E', accent: '#C07A2B', background: '#FBFAF7', text: '#0B1220' } },
  { name: 'Royal', c: { primary: '#1E3A8A', secondary: '#0F172A', accent: '#D97706', background: '#F8FAFC', text: '#0F172A' } },
  { name: 'Forest', c: { primary: '#166534', secondary: '#14532D', accent: '#CA8A04', background: '#F7FEE7', text: '#1A2E05' } },
  { name: 'Rose', c: { primary: '#9F1239', secondary: '#4C0519', accent: '#0F766E', background: '#FFF1F2', text: '#1F2937' } },
  { name: 'Slate', c: { primary: '#334155', secondary: '#0F172A', accent: '#EA580C', background: '#F8FAFC', text: '#0F172A' } },
];

/**
 * Reusable canonical product-palette editor. Single source of truth used by
 * TransformationStep and BrandingStep (and consumed by all exporters).
 */
export const PalettePicker = ({ palette, onChange, lang = 'id', label, triggerTestId = 'product-palette-picker' }) => {
  const palLangIdx = lang === 'en' ? 2 : 1;
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="secondary" size="sm" className="gap-1" data-testid={triggerTestId}>
          <Palette className="w-3.5 h-3.5" /> {label}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {PALETTE_PRESETS.map(p => (
              <button key={p.name} onClick={() => onChange(p.c)} type="button" className="flex items-center gap-1 border border-border rounded-full pl-1 pr-2 py-1 hover:bg-secondary transition-colors" data-testid={`palette-preset-${p.name.toLowerCase()}`}>
                <span className="w-4 h-4 rounded-full" style={{ background: p.c.primary }} />
                <span className="text-xs">{p.name}</span>
              </button>
            ))}
          </div>
          <div className="space-y-2">
            {PALETTE_KEYS.map(([k, idLbl, enLbl]) => (
              <div key={k} className="flex items-center gap-2">
                <input type="color" value={palette[k] || '#000000'} onChange={e => onChange({ ...palette, [k]: e.target.value })} className="w-8 h-8 rounded border border-border p-0 cursor-pointer" data-testid={`palette-${k}`} />
                <span className="text-xs w-20">{[k, idLbl, enLbl][palLangIdx]}</span>
                <Input value={palette[k] || ''} onChange={e => onChange({ ...palette, [k]: e.target.value })} className="h-8 font-mono text-xs" data-testid={`palette-input-${k}`} />
              </div>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};
