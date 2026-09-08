import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLang } from '@/lib/i18n';
import { createProject } from '@/lib/api';
import { Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export default function NewProduct() {
  const navigate = useNavigate();
  const { lang } = useLang();
  useEffect(() => {
    (async () => {
      try {
        const p = await createProject({ ui_language: lang, product_language: localStorage.getItem('khova_product_lang') || 'id' });
        navigate(`/project/${p.id}`, { replace: true });
      } catch (e) { toast.error('Could not create project'); navigate('/'); }
    })();
  }, []); // eslint-disable-line
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
      <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center animate-pulse"><Sparkles className="w-6 h-6 text-primary-foreground" /></div>
      <p className="text-muted-foreground">Menyiapkan proyek...</p>
    </div>
  );
}
