import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { websiteSpec, websiteBuild, websiteRegenSection, websitePublish, websiteUnpublish, siteUrl, sitePreviewUrl, downloadUrl } from '@/lib/api';
import { afterGeneration, creditDescription } from '@/lib/economy';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Working } from '@/components/Loading';
import { Globe, ArrowRight, RefreshCw, Download, ExternalLink, Monitor, Smartphone, Rocket, Link2, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

const STYLES = ['Minimal', 'Modern', 'Premium', 'Editorial', 'Bold'];
const SECTIONS = [
  { key: 'hero', label: 'Hero' }, { key: 'problem', label: 'Problem' }, { key: 'transformation', label: 'Transformation' },
  { key: 'benefits', label: 'Benefits' }, { key: 'whats_included', label: "What's Included" }, { key: 'how_it_works', label: 'How It Works' },
  { key: 'social_proof', label: 'Social Proof' }, { key: 'faq', label: 'FAQ' }, { key: 'final_cta', label: 'Final CTA' },
];

const STATUS_STYLE = {
  draft: 'bg-secondary text-muted-foreground',
  published: 'bg-[hsl(var(--success-soft))] text-[hsl(var(--success))]',
};

export default function WebsiteCreator({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [style, setStyle] = useState((project.website && project.website.style) || 'Modern');
  const [busy, setBusy] = useState(false);
  const [building, setBuilding] = useState(false);
  const [regenSection, setRegenSection] = useState('hero');
  const [device, setDevice] = useState('desktop');
  const web = project.website;
  const status = web?.status || 'draft';
  const isPublished = status === 'published';

  const doSpec = () => { if (!ensureAuth(doSpec)) return; (async () => { setBusy(true); try { const p = await websiteSpec(project.id, style); setProject(p); toast.success('Website content generated', { description: creditDescription(p, t) }); afterGeneration(p, t); } catch (e) { toast.error(e?.response?.data?.detail || 'Failed.'); } finally { setBusy(false); } })(); };
  const doBuild = () => { if (!ensureAuth(doBuild)) return; (async () => { setBuilding(true); try { const r = await websiteBuild(project.id); setProject(r.project); toast.success('Preview built'); } catch (e) { toast.error('Build failed.'); } finally { setBuilding(false); } })(); };
  const doRegen = () => { if (!ensureAuth(doRegen)) return; (async () => { setBuilding(true); try { const p = await websiteRegenSection(project.id, regenSection); setProject(p); toast.success(`Section "${regenSection}" regenerated`, { description: creditDescription(p, t) }); afterGeneration(p, t); } catch (e) { toast.error(e?.response?.data?.detail || 'Failed.'); } finally { setBuilding(false); } })(); };

  const doPublish = () => { if (!ensureAuth(doPublish)) return; (async () => { setBuilding(true); try { const p = await websitePublish(project.id); setProject(p); toast.success(t('web.published.toast'), { action: { label: t('web.openpublic'), onClick: () => window.open(siteUrl(project.id), '_blank') } }); afterGeneration(p, t); } catch (e) { toast.error(e?.response?.data?.detail || t('web.publish.locked')); } finally { setBuilding(false); } })(); };
  const doUnpublish = () => { (async () => { setBuilding(true); try { const p = await websiteUnpublish(project.id); setProject(p); toast.success(t('web.unpublished.toast')); } catch (e) { toast.error('Failed.'); } finally { setBuilding(false); } })(); };

  const copyUrl = () => {
    const url = `${window.location.origin}`.replace(/\/$/, '') && siteUrl(project.id);
    navigator.clipboard.writeText(siteUrl(project.id)).then(() => toast.success(t('web.copied'))).catch(() => toast.error('Copy failed'));
  };

  if (busy) return <Working label="Writing conversion website copy..." />;

  if (!web) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">Website Creator</h2>
        <p className="text-muted-foreground mb-6">Build a responsive conversion landing page (Hero, Problem, Transformation, Benefits, What's Included, How It Works, Social Proof, FAQ, CTA).</p>
        <div className="flex items-center gap-3 mb-4">
          <span className="text-sm">Style:</span>
          <Select value={style} onValueChange={setStyle}><SelectTrigger className="w-40" data-testid="website-style-selector"><SelectValue /></SelectTrigger><SelectContent>{STYLES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
        </div>
        <Button size="lg" onClick={doSpec} className="gap-2" data-testid="website-spec-button"><Globe className="w-4 h-4" /> {t('common.generate')} Website</Button>
      </div>
    );
  }

  const asset = (project.assets || []).find(a => a.type === 'html');
  const hasDraftHtml = !!(web.draft_html);

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div><h2 className="font-display text-2xl">{web.spec?.hero?.headline || 'Website'}</h2><p className="text-sm text-muted-foreground">Style: {web.style}</p></div>
          <Badge className={`uppercase text-[10px] ${STATUS_STYLE[status]}`} data-testid="website-status-badge">{t(`web.${status}`)}</Badge>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Select value={style} onValueChange={setStyle}><SelectTrigger className="w-32 h-9" data-testid="website-style-selector"><SelectValue /></SelectTrigger><SelectContent>{STYLES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select>
          <Button variant="secondary" size="sm" onClick={doSpec} className="gap-1"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          <Button size="sm" onClick={doBuild} disabled={building} data-testid="website-build-button">{building ? '...' : t('web.preview')}</Button>
          <Button size="sm" variant="secondary" onClick={() => goTo('qa')} className="gap-1">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      {/* Section regenerate + publish controls */}
      <Card className="p-4 bg-card card-elev mb-4">
        <div className="flex flex-wrap items-center gap-3 justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{t('web.regen')}:</span>
            <Select value={regenSection} onValueChange={setRegenSection}>
              <SelectTrigger className="w-44 h-9" data-testid="website-section-select"><SelectValue /></SelectTrigger>
              <SelectContent>{SECTIONS.filter(s => (web.spec || {})[s.key]).map(s => <SelectItem key={s.key} value={s.key}>{s.label}</SelectItem>)}</SelectContent>
            </Select>
            <Button size="sm" variant="secondary" onClick={doRegen} disabled={building} className="gap-1" data-testid="website-regen-section-button"><RefreshCw className="w-3.5 h-3.5" /> {t('common.regenerate')}</Button>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {!isPublished ? (
              <Button size="sm" onClick={doPublish} disabled={building} className="gap-1" data-testid="website-publish-button"><Rocket className="w-3.5 h-3.5" /> {t('web.publish')}</Button>
            ) : (
              <>
                <Button size="sm" onClick={doPublish} disabled={building} className="gap-1" data-testid="website-republish-button"><Rocket className="w-3.5 h-3.5" /> {t('web.republish')}</Button>
                <Button size="sm" variant="secondary" onClick={copyUrl} className="gap-1" data-testid="website-copy-url-button"><Link2 className="w-3.5 h-3.5" /> {t('web.copyurl')}</Button>
                <a href={siteUrl(project.id)} target="_blank" rel="noopener noreferrer"><Button size="sm" variant="secondary" className="gap-1" data-testid="website-open-public-button"><ExternalLink className="w-3.5 h-3.5" /> {t('web.openpublic')}</Button></a>
                <Button size="sm" variant="ghost" onClick={doUnpublish} disabled={building} className="gap-1 text-muted-foreground" data-testid="website-unpublish-button"><EyeOff className="w-3.5 h-3.5" /> {t('web.unpublish')}</Button>
              </>
            )}
            {asset && <a href={downloadUrl(project.id, asset.id)}><Button size="sm" variant="ghost" className="gap-1"><Download className="w-3.5 h-3.5" /> HTML</Button></a>}
          </div>
        </div>
        {isPublished && <p className="text-xs text-muted-foreground mt-3">{t('web.draftnote')}</p>}
      </Card>

      {hasDraftHtml ? (
        <Card className="p-3 bg-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground font-mono">{t('web.preview')} ({t('web.draft')})</span>
            <div className="flex gap-1">
              <Button variant={device === 'desktop' ? 'secondary' : 'ghost'} size="icon" onClick={() => setDevice('desktop')}><Monitor className="w-4 h-4" /></Button>
              <Button variant={device === 'mobile' ? 'secondary' : 'ghost'} size="icon" onClick={() => setDevice('mobile')}><Smartphone className="w-4 h-4" /></Button>
            </div>
          </div>
          <div className="flex justify-center bg-secondary rounded-lg p-2">
            <iframe title="website-preview" data-testid="website-preview-iframe" src={sitePreviewUrl(project.id)} className="bg-white rounded border border-border" style={{ width: device === 'mobile' ? 390 : '100%', height: 620 }} />
          </div>
        </Card>
      ) : (
        <Card className="p-6 bg-secondary text-center">
          <p className="text-sm text-muted-foreground mb-3">Draft ready. Click Preview to build a live preview.</p>
          <Button onClick={doBuild} disabled={building}>{building ? '...' : t('web.preview')}</Button>
        </Card>
      )}
    </div>
  );
}
