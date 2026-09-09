import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useLang } from '@/lib/i18n';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { createProject, createSample } from '@/lib/api';
import { motion } from 'framer-motion';
import { Search, Sparkles, BarChart3, Target, Wand2, FileText, Table2, Globe, ShieldCheck, Palette, Download, ArrowRight, CheckCircle2, Lock } from 'lucide-react';

const STEP_ICONS = [Search, BarChart3, Target, Wand2, Sparkles, FileText, Wand2, ShieldCheck, Palette, Download];

export default function Landing() {
  const { t, lang } = useLang();
  const navigate = useNavigate();
  const { user } = useAuth();

  const start = async () => {
    try {
      const p = await createProject({ ui_language: lang, product_language: localStorage.getItem('khova_product_lang') || 'id' });
      navigate(`/project/${p.id}`);
    } catch (e) { toast.error('Could not start. Please retry.'); }
  };

  const trySample = async () => {
    try {
      const p = await createSample();
      toast.success('Sample project created');
      navigate(`/project/${p.id}`);
    } catch (e) { toast.error('Could not create sample.'); }
  };

  const stepKeys = ['discover','research','opportunities','positioning','transformation','format','create','qa','branding','export'];
  const formats = [
    { icon: FileText, label: 'eBook (PDF)', active: true },
    { icon: Table2, label: 'Spreadsheet (XLSX)', active: true },
    { icon: Globe, label: 'Website', active: true },
    { icon: Sparkles, label: 'Workbook', active: false },
    { icon: Sparkles, label: 'Checklist', active: false },
    { icon: Sparkles, label: 'Prompt Pack', active: false },
    { icon: Sparkles, label: 'Video', active: false },
    { icon: Sparkles, label: 'Image Pack', active: false },
  ];

  return (
    <div className="bg-background">
      {/* HERO */}
      <section className="hero-mist border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24 grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <Badge variant="secondary" className="mb-5 font-mono text-[11px] tracking-wide">{t('landing.kicker')}</Badge>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl leading-[1.05] tracking-tight mb-5">{t('landing.title')}</h1>
            <p className="text-lg text-muted-foreground max-w-xl mb-4">{t('landing.subtitle')}</p>
            <p className="text-sm text-muted-foreground max-w-xl mb-8">{t('landing.problem')}</p>
            <div className="flex flex-wrap gap-3">
              <Button size="lg" className="h-12 px-6 text-base gap-2" onClick={start} data-testid="landing-primary-cta-button">
                {t('landing.cta')} <ArrowRight className="w-4 h-4" />
              </Button>
              <Button size="lg" variant="secondary" className="h-12 px-6 text-base" onClick={trySample} data-testid="landing-sample-button">
                {t('landing.tryagain')}
              </Button>
            </div>
            <div className="flex flex-wrap gap-5 mt-8">
              {['landing.proof1','landing.proof2','landing.proof3'].map(k => (
                <div key={k} className="flex items-center gap-2 text-sm text-foreground">
                  <CheckCircle2 className="w-4 h-4 text-primary" /> {t(k)}
                </div>
              ))}
            </div>
          </div>

          {/* Factory-line preview card */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <Card className="p-6 card-elev bg-card">
              <div className="flex items-center justify-between mb-4">
                <span className="font-mono text-xs text-muted-foreground">KHOVA / LINI PRODUKSI</span>
                <Badge className="bg-primary text-primary-foreground">10 langkah</Badge>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {stepKeys.map((k, i) => {
                  const Icon = STEP_ICONS[i];
                  return (
                    <div key={k} className="flex items-center gap-2 p-2.5 rounded-lg bg-secondary border border-border">
                      <div className="w-7 h-7 rounded-md bg-card border border-border flex items-center justify-center">
                        <Icon className="w-3.5 h-3.5 text-primary" />
                      </div>
                      <span className="text-xs font-medium truncate">{t('steps.'+k)}</span>
                    </div>
                  );
                })}
              </div>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="font-display text-2xl sm:text-3xl mb-8">{t('landing.how')}</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {stepKeys.map((k, i) => {
            const Icon = STEP_ICONS[i];
            return (
              <Card key={k} className="p-5 card-elev bg-card">
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-display text-2xl text-primary">{i+1}</span>
                  <Icon className="w-5 h-5 text-[hsl(var(--amber))]" />
                </div>
                <div className="font-semibold text-sm">{t('steps.'+k)}</div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* FORMATS */}
      <section className="bg-card border-y border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h2 className="font-display text-2xl sm:text-3xl mb-8">{t('landing.formats')}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {formats.map((f, i) => (
              <Card key={i} className={`p-5 ${f.active ? 'card-elev bg-card' : 'bg-secondary opacity-70'}`}>
                <f.icon className={`w-6 h-6 mb-3 ${f.active ? 'text-primary' : 'text-muted-foreground'}`} />
                <div className="font-semibold text-sm mb-1">{f.label}</div>
                {f.active
                  ? <Badge variant="secondary" className="text-[10px]">V1</Badge>
                  : <Badge variant="outline" className="text-[10px] gap-1"><Lock className="w-2.5 h-2.5" />{t('landing.comingsoon')}</Badge>}
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* QUALITY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Card className="p-8 lg:p-12 card-elev bg-card paper-warmth">
          <div className="max-w-2xl">
            <ShieldCheck className="w-8 h-8 text-primary mb-4" />
            <h2 className="font-display text-2xl sm:text-3xl mb-3">{t('landing.quality')}</h2>
            <p className="text-muted-foreground mb-6">{t('landing.quality.desc')}</p>
            <Button size="lg" className="gap-2" onClick={start} data-testid="landing-cta-bottom">{t('landing.cta')} <ArrowRight className="w-4 h-4" /></Button>
          </div>
        </Card>
      </section>

      <footer className="border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-sm text-muted-foreground flex items-center justify-between">
          <span className="font-display flex items-center gap-2">
            <img src="/assets/khova-logo.png" alt="Khova AI" className="w-6 h-6 object-contain" data-testid="footer-logo-image" />
            Khova AI
          </span>
          <span>Solusi untuk membangun produk digital Anda sendiri.</span>
        </div>
      </footer>
    </div>
  );
}
