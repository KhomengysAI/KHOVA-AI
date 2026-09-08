import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLang } from '@/lib/i18n';
import { useAuth } from '@/context/AuthContext';
import { listProjects, createProject, createSample } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, FileText, Table2, Globe, ArrowRight, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const FMT_ICON = { ebook: FileText, spreadsheet: Table2, website: Globe };

export default function Dashboard() {
  const { t, lang } = useLang();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState(null);

  const load = async () => { try { setProjects(await listProjects()); } catch (e) { setProjects([]); } };
  useEffect(() => { load(); }, []);

  const start = async () => {
    const p = await createProject({ ui_language: lang, product_language: localStorage.getItem('khova_product_lang') || 'id' });
    navigate(`/project/${p.id}`);
  };
  const sample = async () => { const p = await createSample(); toast.success('Sample created'); navigate(`/project/${p.id}`); };

  const complete = (projects || []).filter(p => p.status === 'complete').length;

  return (
    <div className="paper-warmth border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 min-h-[80vh]">
        <div className="flex items-center justify-between mb-8 flex-wrap gap-3">
          <div>
            <h1 className="font-display text-3xl">{t('dash.title')}</h1>
            <p className="text-muted-foreground">{t('dash.welcome')}, {user?.name}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={sample} data-testid="dash-sample-button">{t('landing.tryagain')}</Button>
            <Button onClick={start} className="gap-1" data-testid="dash-new-button"><Plus className="w-4 h-4" /> {t('nav.new')}</Button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-5 bg-card card-elev"><div className="text-3xl font-display text-primary">{projects ? projects.length : '-'}</div><div className="text-sm text-muted-foreground">Total Proyek</div></Card>
          <Card className="p-5 bg-card card-elev"><div className="text-3xl font-display text-[hsl(var(--success))]">{projects ? complete : '-'}</div><div className="text-sm text-muted-foreground">Selesai</div></Card>
          <Card className="p-5 bg-card card-elev"><div className="text-3xl font-display text-[hsl(var(--amber))]">{projects ? (projects.length - complete) : '-'}</div><div className="text-sm text-muted-foreground">Dalam proses</div></Card>
          <Card className="p-5 bg-card card-elev flex items-center justify-center"><Button variant="ghost" onClick={() => navigate('/projects')} className="gap-1">{t('nav.projects')} <ArrowRight className="w-4 h-4" /></Button></Card>
        </div>

        <h2 className="font-display text-xl mb-4">{t('projects.title')}</h2>
        {!projects && <div className="grid md:grid-cols-3 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-40" />)}</div>}
        {projects && projects.length === 0 && (
          <Card className="p-10 text-center bg-card card-elev">
            <Sparkles className="w-8 h-8 text-primary mx-auto mb-3" />
            <p className="text-muted-foreground mb-4">{t('projects.empty')}</p>
            <Button onClick={start} className="gap-1"><Plus className="w-4 h-4" /> {t('nav.new')}</Button>
          </Card>
        )}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(projects || []).slice(0, 9).map(p => {
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
