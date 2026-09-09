import React, { useState, useEffect } from 'react';
import { useLang } from '@/lib/i18n';
import { ebookExport, spreadsheetBuild, websiteBuild, ebookDesignCheck, downloadUrl, siteUrl, ebookPreviewUrl, fetchBundle } from '@/lib/api';
import { generationErrorMessage } from '@/lib/economy';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Working } from '@/components/Loading';
import { Download, FileText, Table2, Globe, ExternalLink, CheckCircle2, Eye, Sparkles, Package } from 'lucide-react';
import { toast } from 'sonner';

export default function ExportStep({ project, setProject, ensureAuth }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [bundling, setBundling] = useState(false);
  const [check, setCheck] = useState(null);
  const fmt = project.format;

  useEffect(() => { if (fmt === 'ebook') ebookDesignCheck(project.id).then(setCheck).catch(() => {}); }, [fmt, project.id]);

  const assetOf = (type) => (project.assets || []).find(a => a.type === type);
  const pdf = assetOf('pdf'), xlsx = assetOf('xlsx'), html = assetOf('html');
  const hasAssets = (project.assets || []).length > 0;

  const exportEbook = () => { if (!ensureAuth(exportEbook)) return; (async () => { setBusy(true); try { const r = await ebookExport(project.id); setProject(r.project); toast.success(t('toast.export.pdf')); } catch (e) { const m = generationErrorMessage(e, t, 'Gagal ekspor PDF.'); toast.error(m.message); } finally { setBusy(false); } })(); };
  const buildXlsx = () => { if (!ensureAuth(buildXlsx)) return; (async () => { setBusy(true); try { const r = await spreadsheetBuild(project.id); setProject(r.project); toast.success(t('toast.export.xlsx')); } catch (e) { const m = generationErrorMessage(e, t, 'Gagal.'); toast.error(m.message); } finally { setBusy(false); } })(); };
  const buildSite = () => { if (!ensureAuth(buildSite)) return; (async () => { setBusy(true); try { const r = await websiteBuild(project.id); setProject(r.project); toast.success(t('toast.export.site'), { action: { label: t('common.preview'), onClick: () => window.open(siteUrl(project.id), '_blank') } }); } catch (e) { toast.error('Gagal.'); } finally { setBusy(false); } })(); };

  const downloadBundle = () => {
    if (!ensureAuth(downloadBundle)) return;
    (async () => {
      setBundling(true);
      try {
        const resp = await fetchBundle(project.id);
        const blob = new Blob([resp.data], { type: 'application/zip' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const safe = (project.title || 'product').replace(/[^a-zA-Z0-9]/g, '_').slice(0, 40) || 'product';
        a.href = url; a.download = `${safe}_bundle.zip`;
        document.body.appendChild(a); a.click(); a.remove();
        window.URL.revokeObjectURL(url);
        toast.success(t('bundle.ready'));
      } catch (e) {
        let msg = t('bundle.failed');
        try {
          if (e?.response?.status === 400) msg = t('bundle.empty');
          else if (e?.response?.data && typeof e.response.data.detail === 'string') msg = e.response.data.detail;
        } catch (_) { /* noop */ }
        toast.error(msg);
      } finally { setBundling(false); }
    })();
  };

  if (busy) return <Working label="Menyiapkan aset final..." sub="Merender dokumen dengan design system Anda." />;

  if (!fmt) return <div className="text-muted-foreground">Pilih format & buat produk terlebih dahulu.</div>;

  return (
    <div className="max-w-3xl">
      <h2 className="font-display text-2xl mb-1">{t('export.title')}</h2>
      <p className="text-muted-foreground mb-6">Hasilkan dan unduh aset digital nyata Anda.</p>

      {fmt === 'ebook' && (
        <Card className="p-6 bg-card card-elev mb-4">
          <div className="flex items-center gap-3 mb-4"><FileText className="w-6 h-6 text-primary" /><div><div className="font-semibold">eBook PDF</div><div className="text-sm text-muted-foreground">{project.ebook?.meta?.title}</div></div></div>
          {check && (
            <div className="mb-4 p-3 rounded-lg bg-secondary">
              <div className="flex items-center gap-2 text-sm mb-2"><CheckCircle2 className={`w-4 h-4 ${check.consistent ? 'text-[hsl(var(--success))]' : 'text-[hsl(var(--warning))]'}`} /> Pemeriksaan konsistensi desain</div>
              <div className="flex flex-wrap gap-2">{(check.checks || []).map((c, i) => (<span key={i} className="inline-flex items-center gap-1 text-xs"><span className="w-3 h-3 rounded-full border border-border" style={{ background: c.hex }} />{c.element}</span>))}</div>
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <a href={ebookPreviewUrl(project.id)} target="_blank" rel="noopener noreferrer"><Button variant="secondary" className="gap-1"><Eye className="w-4 h-4" /> Pratinjau</Button></a>
            <Button onClick={exportEbook} className="gap-1" data-testid="export-generate-pdf-button"><Sparkles className="w-4 h-4" /> {pdf ? 'Buat ulang PDF' : 'Buat PDF Final'}</Button>
            {pdf && <a href={downloadUrl(project.id, pdf.id)}><Button className="gap-1" data-testid="export-download-pdf-button"><Download className="w-4 h-4" /> Unduh PDF</Button></a>}
          </div>
        </Card>
      )}

      {fmt === 'spreadsheet' && (
        <Card className="p-6 bg-card card-elev mb-4">
          <div className="flex items-center gap-3 mb-4"><Table2 className="w-6 h-6 text-primary" /><div><div className="font-semibold">Spreadsheet XLSX</div><div className="text-sm text-muted-foreground">{project.spreadsheet?.product_type}</div></div></div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={buildXlsx} className="gap-1" data-testid="export-build-xlsx-button">{xlsx ? 'Buat ulang XLSX' : 'Buat XLSX'}</Button>
            {xlsx && <a href={downloadUrl(project.id, xlsx.id)}><Button className="gap-1" data-testid="export-download-xlsx-button"><Download className="w-4 h-4" /> Unduh XLSX</Button></a>}
          </div>
        </Card>
      )}

      {fmt === 'website' && (
        <Card className="p-6 bg-card card-elev mb-4">
          <div className="flex items-center gap-3 mb-4"><Globe className="w-6 h-6 text-primary" /><div><div className="font-semibold">Website</div><div className="text-sm text-muted-foreground">{project.website?.spec?.hero?.headline}</div></div></div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={buildSite} className="gap-1" data-testid="export-build-site-button">{html ? 'Bangun ulang' : 'Bangun Website'}</Button>
            {project.website?.html && <a href={siteUrl(project.id)} target="_blank" rel="noopener noreferrer"><Button variant="secondary" className="gap-1" data-testid="export-open-site-button"><ExternalLink className="w-4 h-4" /> Buka Website</Button></a>}
            {html && <a href={downloadUrl(project.id, html.id)}><Button className="gap-1"><Download className="w-4 h-4" /> Unduh HTML</Button></a>}
          </div>
        </Card>
      )}

      <Card className="p-5 bg-secondary">
        <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
          <div className="text-sm font-medium">Semua aset</div>
          <Button size="sm" onClick={downloadBundle} disabled={!hasAssets || bundling} className="gap-1.5" data-testid="download-bundle-button">
            <Package className="w-4 h-4" /> {bundling ? t('bundle.downloading') : t('bundle.download')}
          </Button>
        </div>
        {!hasAssets && <p className="text-sm text-muted-foreground">Belum ada aset.</p>}
        <div className="space-y-2">
          {(project.assets || []).map(a => (
            <div key={a.id} className="flex items-center justify-between bg-card rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 text-sm min-w-0"><Badge variant="outline" className="text-[10px] uppercase">{a.type}</Badge><span className="font-mono text-xs truncate">{a.filename}</span><span className="text-xs text-muted-foreground">{Math.round(a.size/1024)} KB</span></div>
              <a href={downloadUrl(project.id, a.id)}><Button size="sm" variant="ghost" className="gap-1"><Download className="w-3.5 h-3.5" /></Button></a>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
