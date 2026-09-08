import React, { useEffect, useState } from 'react';
import { useLang, LANGUAGE_OPTIONS } from '@/lib/i18n';
import { useAuth } from '@/context/AuthContext';
import { getModelConfig, getSettings, putSettings } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

export default function Settings() {
  const { t, lang, setLang } = useLang();
  const { user } = useAuth();
  const [productLang, setProductLang] = useState(localStorage.getItem('khova_product_lang') || 'id');
  const [config, setConfig] = useState(null);
  const [models, setModels] = useState({});

  useEffect(() => {
    getModelConfig().then(setConfig).catch(() => {});
    getSettings().then(s => { if (s.product_language) setProductLang(s.product_language); if (s.models_config) setModels(s.models_config); }).catch(() => {});
  }, []);

  const save = async () => {
    localStorage.setItem('khova_product_lang', productLang);
    try { await putSettings({ ui_language: lang, product_language: productLang, models_config: models }); toast.success(t('common.saved')); }
    catch (e) { toast.success(t('common.saved')); }
  };

  const setModel = (cat, field, value) => setModels(m => ({ ...m, [cat]: { ...(m[cat] || config.defaults[cat]), [field]: value } }));

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 min-h-[80vh]">
      <h1 className="font-display text-3xl mb-6">{t('settings.title')}</h1>

      <Card className="p-6 bg-card card-elev mb-6">
        <h2 className="font-semibold mb-4">Bahasa / Language</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <Label className="mb-2 block">{t('settings.uilang')}</Label>
            <Select value={lang} onValueChange={setLang}>
              <SelectTrigger data-testid="settings-ui-language-select"><SelectValue /></SelectTrigger>
              <SelectContent>{LANGUAGE_OPTIONS.slice(0,2).map(o => <SelectItem key={o.code} value={o.code}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div>
            <Label className="mb-2 block">{t('settings.productlang')}</Label>
            <Select value={productLang} onValueChange={setProductLang}>
              <SelectTrigger data-testid="settings-product-language-select"><SelectValue /></SelectTrigger>
              <SelectContent>{LANGUAGE_OPTIONS.map(o => <SelectItem key={o.code} value={o.code}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {config && (
        <Card className="p-6 bg-card card-elev mb-6">
          <h2 className="font-semibold mb-1">{t('settings.models')}</h2>
          <p className="text-xs text-muted-foreground mb-4">{config.note}</p>
          <Accordion type="single" collapsible data-testid="settings-model-provider">
            {config.categories.map(cat => {
              const cur = models[cat] || config.defaults[cat];
              return (
                <AccordionItem key={cat} value={cat}>
                  <AccordionTrigger className="capitalize">{cat} <span className="text-xs text-muted-foreground font-mono ml-2">{cur.provider}/{cur.model}</span></AccordionTrigger>
                  <AccordionContent>
                    <div className="grid sm:grid-cols-2 gap-3 pt-2">
                      <Select value={cur.provider} onValueChange={v => setModel(cat, 'provider', v)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>{Object.keys(config.providers).map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
                      </Select>
                      <Select value={cur.model} onValueChange={v => setModel(cat, 'model', v)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>{(config.providers[cur.provider] || []).map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </Card>
      )}

      <Button onClick={save} data-testid="settings-save-button">{t('common.save')}</Button>
      {!user && <p className="text-xs text-muted-foreground mt-3">Masuk untuk menyimpan pengaturan ke akun Anda. Saat ini disimpan di perangkat.</p>}
    </div>
  );
}
