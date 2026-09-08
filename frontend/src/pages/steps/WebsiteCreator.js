import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { websiteSpec, websiteBuild, siteUrl, downloadUrl } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Working } from '@/components/Loading';
import { Globe, ArrowRight, RefreshCw, Download, ExternalLink, Monitor, Smartphone } from 'lucide-react';
import { toast } from 'sonner';

const STYLES = ['Minimal', 'Modern', 'Premium', 'Editorial', 'Bold'];

export default function WebsiteCreator({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [style, setStyle] = useState((project.website && project.website.style) || 'Modern');
  const [busy, setBusy] = useState(false);
  const [building, setBuilding] = useState(false);
  const [device, setDevice] = useState('desktop');
  const web = project.website;

  const doSpec = () => { if (!ensureAuth(doSpec)) return; (async () => { setBusy(true); try { const p = await websiteSpec(project.id, style); setProject(p); toast.success('Konten website dibuat'); } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal.'); } finally { setBusy(false); } })(); };
  const doBuild = () => { if (!ensureAuth(doBuild)) return; (async () => { setBuilding(true); try { const r = await websiteBuild(project.id); setProject(r.project); toast.success('Website siap'); } catch (e) { toast.error('Gagal build.'); } finally { setBuilding(false); } })(); };

  if (busy) return <Working label="Menulis copy website konversi..." />;

  if (!web) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">Website Creator</h2>
        <p className="text-muted-foreground mb-6">Buat landing page konversi yang responsif (Hero, Masalah, Transformasi, Manfaat, Isi, Cara Kerja, FAQ, CTA).</p>
        <div className="flex items-center gap-3 mb-4">
          <span className="text-sm">Gaya:</span>
          <Select value={style} onValueChange={setStyle}><SelectTrigger className="w-40" data-testid="website-style-selector"><SelectValue /></SelectTrigger><SelectContent>{STYLES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
        </div>
        <Button size="lg" onClick={doSpec} className="gap-2" data-testid="website-spec-button"><Globe className="w-4 h-4" /> {t('common.generate')} Website</Button>
      </div>
    );
  }

  const asset = (project.assets || []).find(a => a.type === 'html');
  const hasHtml = !!(web.html);

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div><h2 className="font-display text-2xl">{web.spec?.hero?.headline || 'Website'}</h2><p className="text-sm text-muted-foreground">Gaya: {web.style}</p></div>
        <div className="flex gap-2 flex-wrap">
          <Select value={style} onValueChange={setStyle}><SelectTrigger className="w-32 h-9" data-testid="website-style-selector"><SelectValue /></SelectTrigger><SelectContent>{STYLES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
          <Button variant="secondary" size="sm" onClick={doSpec} className="gap-1"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button size="sm" onClick={doBuild} disabled={building} data-testid="website-build-button">{building ? 'Membangun...' : (hasHtml ? 'Bangun ulang' : 'Bangun & Pratinjau')}</Button>
          {hasHtml && <a href={siteUrl(project.id)} target="_blank" rel="noopener noreferrer"><Button size="sm" variant="secondary" className="gap-1" data-testid="website-open-button"><ExternalLink className="w-3.5 h-3.5" /> Buka</Button></a>}
          {asset && <a href={downloadUrl(project.id, asset.id)}><Button size="sm" variant="secondary" className="gap-1"><Download className="w-3.5 h-3.5" /> HTML</Button></a>}
          <Button size="sm" variant="secondary" onClick={() => goTo('qa')} className="gap-1">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      {hasHtml ? (
        <Card className="p-3 bg-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-mono">Pratinjau langsung</span>
            <div className="flex gap-1">
              <Button variant={device === 'desktop' ? 'secondary' : 'ghost'} size="icon" onClick={() => setDevice('desktop')}><Monitor className="w-4 h-4" /></Button>
              <Button variant={device === 'mobile' ? 'secondary' : 'ghost'} size="icon" onClick={() => setDevice('mobile')}><Smartphone className="w-4 h-4" /></Button>
            </div>
          </div>
          <div className="flex justify-center bg-secondary rounded-lg p-2">
            <iframe title="website-preview" data-testid="website-preview-iframe" src={siteUrl(project.id)} className="bg-white rounded border border-border" style={{ width: device === 'mobile' ? 390 : '100%', height: 620 }} />
          </div>
        </Card>
      ) : (
        <Card className="p-6 bg-secondary text-center">
          <p className="text-sm text-muted-foreground mb-3">Konten siap. Klik “Bangun & Pratinjau” untuk membuat halaman web nyata.</p>
          <Button onClick={doBuild} disabled={building}>{building ? 'Membangun...' : 'Bangun & Pratinjau'}</Button>
        </Card>
      )}
    </div>
  );
}
