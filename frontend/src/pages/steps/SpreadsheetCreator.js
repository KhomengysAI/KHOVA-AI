import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { spreadsheetSpec, spreadsheetBuild, downloadUrl } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Working } from '@/components/Loading';
import { Table2, ArrowRight, RefreshCw, Download, Check } from 'lucide-react';
import { toast } from 'sonner';

export default function SpreadsheetCreator({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [building, setBuilding] = useState(false);
  const ss = project.spreadsheet;

  const doSpec = () => { if (!ensureAuth(doSpec)) return; (async () => { setBusy(true); try { const p = await spreadsheetSpec(project.id); setProject(p); toast.success('Struktur spreadsheet dibuat'); } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal.'); } finally { setBusy(false); } })(); };
  const doBuild = () => { if (!ensureAuth(doBuild)) return; (async () => { setBuilding(true); try { const r = await spreadsheetBuild(project.id); setProject(r.project); toast.success('File XLSX dibuat'); } catch (e) { toast.error('Gagal build XLSX.'); } finally { setBuilding(false); } })(); };

  if (busy) return <Working label="Merancang struktur spreadsheet..." />;

  if (!ss) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">Spreadsheet Creator</h2>
        <p className="text-muted-foreground mb-6">AI merancang planner/tracker/kalkulator dengan beberapa sheet, rumus, dropdown, dan contoh data — lalu membuat file .xlsx asli.</p>
        <Button size="lg" onClick={doSpec} className="gap-2" data-testid="spreadsheet-spec-button"><Table2 className="w-4 h-4" /> {t('common.generate')} Struktur</Button>
      </div>
    );
  }

  const asset = (project.assets || []).find(a => a.type === 'xlsx');

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div><h2 className="font-display text-2xl">{ss.product_type || 'Spreadsheet'}</h2><p className="text-sm text-muted-foreground">{ss.concept}</p></div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="secondary" size="sm" onClick={doSpec} className="gap-1" data-testid="spreadsheet-regenerate"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button size="sm" onClick={doBuild} disabled={building} className="gap-1" data-testid="spreadsheet-generate-button">{building ? 'Membuat...' : 'Buat XLSX'}</Button>
          {asset && <a href={downloadUrl(project.id, asset.id)}><Button size="sm" className="gap-1" data-testid="spreadsheet-download-xlsx-button"><Download className="w-3.5 h-3.5" /> {t('common.download')}</Button></a>}
          <Button size="sm" variant="secondary" onClick={() => goTo('qa')} className="gap-1">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      {asset && <Card className="p-3 bg-[hsl(var(--success-soft))] border-transparent mb-4 flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-[hsl(var(--success))]" /> File siap: <span className="font-mono">{asset.filename}</span> ({Math.round(asset.size/1024)} KB)</Card>}

      <div className="grid md:grid-cols-2 gap-4">
        {(ss.sheets || []).map((sh, i) => (
          <Card key={i} className="p-4 bg-card">
            <div className="flex items-center gap-2 mb-2"><Table2 className="w-4 h-4 text-primary" /><span className="font-semibold text-sm">{sh.name}</span></div>
            <p className="text-xs text-muted-foreground mb-3">{sh.purpose}</p>
            <div className="flex flex-wrap gap-1">
              {(sh.columns || []).map((c, j) => (<Badge key={j} variant={c.type === 'formula' ? 'default' : 'secondary'} className="text-[10px]">{c.header}{c.type === 'formula' ? ' ƒ' : ''}</Badge>))}
            </div>
            {sh.instructions && <p className="text-[11px] text-muted-foreground mt-2 italic">{sh.instructions}</p>}
          </Card>
        ))}
      </div>
    </div>
  );
}
