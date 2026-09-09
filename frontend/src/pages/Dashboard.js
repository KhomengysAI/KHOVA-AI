import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLang } from '@/lib/i18n';
import { useAuth } from '@/context/AuthContext';
import { listProjects, createProject, createSample, saveDiscover } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Plus, FileText, Table2, Globe, ArrowRight, Sparkles, Info, Wand2 } from 'lucide-react';
import { toast } from 'sonner';

const FMT_ICON = { ebook: FileText, spreadsheet: Table2, website: Globe };

const MORE_FIELDS = [
  ['expertise', { id: 'Keahlian', en: 'Expertise' }],
  ['audience', { id: 'Target audiens', en: 'Target audience' }],
  ['industry', { id: 'Industri', en: 'Industry' }],
  ['skills', { id: 'Keterampilan', en: 'Skills' }],
];

export default function Dashboard() {
  const { t, lang } = useLang();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState(null);
  const [mode, setMode] = useState('know');
  const [idea, setIdea] = useState('');
  const [more, setMore] = useState({ expertise: '', audience: '', industry: '', skills: '' });
  const [busy, setBusy] = useState(false);

  const load = async () => { try { setProjects(await listProjects()); } catch (e) { setProjects([]); } };
  useEffect(() => { load(); }, []);

  const submit = async () => {
    setBusy(true);
    try {
      const p = await createProject({ ui_language: lang, product_language: localStorage.getItem('khova_product_lang') || 'id' });
      const p2 = await saveDiscover(p.id, { mode, idea, ...more });
      navigate(`/project/${p2.id}`);
    } catch (e) { toast.error('Gagal membuat proyek. Coba lagi.'); }
    finally { setBusy(false); }
  };
  const sample = async () => { const p = await createSample(); toast.success('Proyek contoh dibuat'); navigate(`/project/${p.id}`); };

  const complete = (projects || []).filter(p => p.status === 'complete').length;
  const setM = (k, v) => setMore(m => ({ ...m, [k]: v }));

  return (
    <div className="paper-warmth border-b border-border">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 min-h-[80vh]">
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">{t('dash.welcome')}, {user?.name || (lang === 'id' ? 'Kreator' : 'Creator')}</p>
          <h1 className="font-display text-3xl mt-1">{t('discover.q')}</h1>
          <p className="text-muted-foreground mt-1">{t('dash.hero.sub')}</p>
        </div>

        <Card className="p-6 bg-card card-elev mb-10" data-testid="dashboard-ai-input-card">
          <Tabs value={mode} onValueChange={setMode} className="mb-4">
            <TabsList className="grid grid-cols-2 w-full max-w-md">
              <TabsTrigger value="know" data-testid="dash-mode-know">{t('discover.mode.know')}</TabsTrigger>
              <TabsTrigger value="explore" data-testid="dash-mode-explore">{t('discover.mode.explore')}</TabsTrigger>
            </TabsList>
          </Tabs>

          <Textarea
            rows={4}
            value={idea}
            onChange={e => setIdea(e.target.value)}
            placeholder={mode === 'know' ? 'Contoh: Panduan keuangan untuk freelancer' : 'Contoh: Saya suka topik produktivitas dan ingin bantu mahasiswa — tapi belum tahu produknya apa.'}
            className="text-base mb-3"
            data-testid="dashboard-idea-input"
          />

          <Alert className="mb-4 bg-accent border-border">
            <Info className="h-4 w-4" />
            <AlertDescription className="text-accent-foreground">{t('discover.warning')}</AlertDescription>
          </Alert>

          <Accordion type="single" collapsible className="mb-4">
            <AccordionItem value="more">
              <AccordionTrigger data-testid="dash-more-context">{t('discover.more')}</AccordionTrigger>
              <AccordionContent>
                <div className="grid sm:grid-cols-2 gap-4 pt-2">
                  {MORE_FIELDS.map(([k, lbl]) => (
                    <div key={k}>
                      <Label className="mb-1.5 block text-sm">{lbl[lang] || lbl.en} <span className="text-muted-foreground text-xs">({t('common.optional')})</span></Label>
                      <Input value={more[k]} onChange={e => setM(k, e.target.value)} data-testid={`dash-field-${k}`} />
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <div className="flex items-center gap-3 flex-wrap">
            <Button size="lg" onClick={submit} disabled={busy} className="gap-2" data-testid="dashboard-submit-button">
              <Wand2 className="w-4 h-4" /> {busy ? t('common.loading') : t('discover.btn')}
            </Button>
            <Button variant="secondary" onClick={sample} data-testid="dash-sample-button">{t('landing.tryagain')}</Button>
          </div>
        </Card>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-5 bg-card card-elev"><div className="text-3xl font-display text-primary">{projects ? projects.length : '-'}</div><div className="text-sm text-muted-foreground">{t('dash.stats.total')}</div></Card>
          <Card className="p-5 bg-card card-elev"><div className="text-3xl font-display text-[hsl(var(--success))]">{projects ? complete : '-'}</div><div className="text-sm text-muted-foreground">{t('dash.stats.complete')}</div></Card>
          <Card className="p-5 bg-card card-elev"><div className="text-3xl font-display text-[hsl(var(--amber))]">{projects ? (projects.length - complete) : '-'}</div><div className="text-sm text-muted-foreground">{t('dash.stats.progress')}</div></Card>
          <Card className="p-5 bg-card card-elev flex items-center justify-center"><Button variant="ghost" onClick={() => navigate('/projects')} className="gap-1" data-testid="dash-view-all-projects">{t('dash.viewall')} <ArrowRight className="w-4 h-4" /></Button></Card>
        </div>

        <h2 className="font-display text-xl mb-4">{t('dash.recent')}</h2>
        {!projects && <div className="grid md:grid-cols-3 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-40" />)}</div>}
        {projects && projects.length === 0 && (
          <Card className="p-10 text-center bg-card card-elev">
            <Sparkles className="w-8 h-8 text-primary mx-auto mb-3" />
            <p className="text-muted-foreground">{t('projects.empty')}</p>
          </Card>
        )}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(projects || []).slice(0, 6).map(p => {
            const Icon = FMT_ICON[p.format] || Sparkles;
            return (
              <Card key={p.id} className="p-5 bg-card card-elev card-elev-hover cursor-pointer transition-shadow" onClick={() => navigate(`/project/${p.id}`)} data-testid={`dash-project-${p.id}`}>
                <div className="flex items-center justify-between mb-3">
                  <Icon className="w-5 h-5 text-primary" />
                  <Badge variant={p.status === 'complete' ? 'default' : 'secondary'} className="text-[10px]">{p.status}</Badge>
                </div>
                <h3 className="font-semibold mb-1 line-clamp-2">{p.title}</h3>
                <div className="text-xs text-muted-foreground">Langkah: {p.current_step} · {p.opportunity_count} peluang</div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
