import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getProject } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useLang } from '@/lib/i18n';
import { Stepper, MobileStepper, STEP_KEYS } from '@/components/Stepper';
import { Working } from '@/components/Loading';
import { Card } from '@/components/ui/card';
import DiscoverStep from '@/pages/steps/DiscoverStep';
import ResearchStep from '@/pages/steps/ResearchStep';
import OpportunitiesStep from '@/pages/steps/OpportunitiesStep';
import PositioningStep from '@/pages/steps/PositioningStep';
import TransformationStep from '@/pages/steps/TransformationStep';
import FormatStep from '@/pages/steps/FormatStep';
import CreateStep from '@/pages/steps/CreateStep';
import QAStep from '@/pages/steps/QAStep';
import BrandingStep from '@/pages/steps/BrandingStep';
import ExportStep from '@/pages/steps/ExportStep';

export function computeStatus(p) {
  if (!p) return {};
  const hasDiscover = p.discover && Object.entries(p.discover).some(([k, v]) => k !== 'mode' && v && (Array.isArray(v) ? v.length : String(v).trim()));
  const done = {
    discover: !!p.research || hasDiscover,
    research: !!p.research,
    opportunities: (p.opportunities || []).length > 0,
    positioning: !!p.positioning,
    transformation: !!p.transformation,
    format: !!p.format,
    create: (p.ebook && (p.ebook.sections || []).length > 0) || (p.spreadsheet && p.spreadsheet.asset_id) || (p.website && p.website.html),
    qa: (p.qa || []).length > 0,
    branding: !!p.branding,
    export: (p.assets || []).some(a => ['pdf', 'xlsx', 'html'].includes(a.type)),
  };
  const statusMap = {};
  STEP_KEYS.forEach((key, i) => {
    if (done[key]) statusMap[key] = 'done';
    else if (i === 0 || done[STEP_KEYS[i - 1]]) statusMap[key] = 'available';
    else statusMap[key] = 'locked';
  });
  return { statusMap, done };
}

export default function Wizard() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { ensureAuth, user } = useAuth();
  const { t } = useLang();
  const [project, setProject] = useState(null);
  const [active, setActive] = useState('discover');
  const [loadingProj, setLoadingProj] = useState(true);

  useEffect(() => {
    (async () => {
      setLoadingProj(true);
      try {
        const p = await getProject(id);
        setProject(p);
        setActive(p.current_step && STEP_KEYS.includes(p.current_step) ? p.current_step : 'discover');
      } catch (e) { navigate('/'); }
      finally { setLoadingProj(false); }
    })();
  }, [id]); // eslint-disable-line

  const { statusMap } = computeStatus(project);

  const goTo = (key) => { setActive(key); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const onProject = (p) => setProject(p);

  if (loadingProj || !project) return <Working label="Memuat proyek..." />;

  const stepProps = { project, setProject: onProject, goTo, ensureAuth, user };
  const STEP_COMPONENTS = {
    discover: DiscoverStep, research: ResearchStep, opportunities: OpportunitiesStep,
    positioning: PositioningStep, transformation: TransformationStep, format: FormatStep,
    create: CreateStep, qa: QAStep, branding: BrandingStep, export: ExportStep,
  };
  const ActiveComp = STEP_COMPONENTS[active];

  return (
    <div className="paper-warmth border-b border-border min-h-[90vh]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-10">
        <div className="mb-5">
          <h1 className="font-display text-2xl lg:text-3xl truncate">{project.title}</h1>
          <p className="text-sm text-muted-foreground">Lini produksi Khova AI</p>
        </div>
        <MobileStepper statusMap={statusMap} current={active} onSelect={goTo} />
        <div className="grid lg:grid-cols-[280px_1fr] gap-6 mt-3">
          <aside className="hidden lg:block">
            <Card className="p-3 bg-card card-elev sticky top-20">
              <Stepper statusMap={statusMap} current={active} onSelect={goTo} />
            </Card>
          </aside>
          <motion.div key={active} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
            <Card className="p-5 sm:p-7 bg-card card-elev min-h-[500px]">
              <ActiveComp {...stepProps} />
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
