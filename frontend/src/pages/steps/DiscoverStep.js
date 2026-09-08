import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { saveDiscover } from '@/lib/api';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Info, ArrowRight, Upload, X } from 'lucide-react';
import { toast } from 'sonner';

const FIELDS = [
  ['expertise', { id: 'Keahlian', en: 'Expertise' }],
  ['experience', { id: 'Pengalaman', en: 'Experience' }],
  ['audience', { id: 'Target audiens', en: 'Target audience' }],
  ['interests', { id: 'Minat', en: 'Interests' }],
  ['skills', { id: 'Keterampilan', en: 'Skills' }],
  ['story', { id: 'Cerita pribadi', en: 'Personal story' }],
  ['problem', { id: 'Masalah yang dipahami', en: 'Problem you understand' }],
  ['framework', { id: 'Kerangka yang ada', en: 'Existing framework' }],
  ['industry', { id: 'Industri', en: 'Industry' }],
  ['preferred_audience', { id: 'Audiens pilihan', en: 'Preferred audience' }],
];

export default function DiscoverStep({ project, setProject, goTo }) {
  const { t, lang } = useLang();
  const d = project.discover || {};
  const [mode, setMode] = useState(d.mode === 'explore' ? 'explore' : 'know');
  const [form, setForm] = useState({ idea: d.idea || '', expertise: d.expertise || '', experience: d.experience || '', audience: d.audience || '', interests: d.interests || '', skills: d.skills || '', story: d.story || '', problem: d.problem || '', framework: d.framework || '', industry: d.industry || '', preferred_audience: d.preferred_audience || '' });
  const [uploads, setUploads] = useState(d.uploads || []);
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const onFile = async (e) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      const readable = /\.(txt|md|csv|json)$/i.test(file.name);
      if (readable) {
        const text = await file.text();
        setUploads(u => [...u, { name: file.name, text: text.slice(0, 6000) }]);
      } else {
        setUploads(u => [...u, { name: file.name, text: '' }]);
        toast.info(`${file.name} dilampirkan (teks .txt/.md/.csv diproses; format lain hanya nama).`);
      }
    }
    e.target.value = '';
  };

  const submit = async () => {
    setBusy(true);
    try {
      const p = await saveDiscover(project.id, { mode, ...form, uploads });
      setProject(p);
      goTo('research');
    } catch (e) { toast.error('Gagal menyimpan.'); }
    finally { setBusy(false); }
  };

  return (
    <div className="max-w-3xl">
      <h2 className="font-display text-2xl mb-1">{t('discover.q')}</h2>
      <p className="text-muted-foreground mb-5">Masukkan seluas mungkin. Contoh: “Saya paham soal fitness”, “Bantu orang kelola uang”, atau “Belum ada ide”.</p>

      <Tabs value={mode} onValueChange={setMode} className="mb-5">
        <TabsList className="grid grid-cols-2 w-full max-w-md">
          <TabsTrigger value="know" data-testid="discover-mode-know">{t('discover.mode.know')}</TabsTrigger>
          <TabsTrigger value="explore" data-testid="discover-mode-explore">{t('discover.mode.explore')}</TabsTrigger>
        </TabsList>
        <TabsContent value="know" className="mt-4">
          <Label className="mb-2 block">Ide / produk yang ingin dibuat</Label>
          <Textarea data-testid="discover-idea-input" rows={4} value={form.idea} onChange={e => set('idea', e.target.value)} placeholder="Contoh: Panduan keuangan untuk freelancer" />
        </TabsContent>
        <TabsContent value="explore" className="mt-4">
          <Label className="mb-2 block">Ceritakan sedikit tentang Anda (opsional)</Label>
          <Textarea data-testid="discover-idea-input" rows={4} value={form.idea} onChange={e => set('idea', e.target.value)} placeholder="Contoh: Saya suka topik produktivitas dan ingin bantu mahasiswa — tapi belum tahu produknya apa." />
          <p className="text-xs text-muted-foreground mt-2">Kami akan meriset pasar untuk menemukan arah produk yang cocok untuk Anda.</p>
        </TabsContent>
      </Tabs>

      <Alert className="mb-5 bg-accent border-border">
        <Info className="h-4 w-4" />
        <AlertDescription className="text-accent-foreground">{t('discover.warning')}</AlertDescription>
      </Alert>

      <Accordion type="single" collapsible className="mb-5">
        <AccordionItem value="more">
          <AccordionTrigger data-testid="discover-more-context">{t('discover.more')}</AccordionTrigger>
          <AccordionContent>
            <div className="grid sm:grid-cols-2 gap-4 pt-2">
              {FIELDS.map(([k, lbl]) => (
                <div key={k}>
                  <Label className="mb-1.5 block text-sm">{lbl[lang] || lbl.en} <span className="text-muted-foreground text-xs">({t('common.optional')})</span></Label>
                  <Input value={form[k]} onChange={e => set(k, e.target.value)} data-testid={`discover-field-${k}`} />
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Label className="mb-1.5 block text-sm">Materi referensi ({t('common.optional')})</Label>
              <label className="flex items-center gap-2 border border-dashed border-border rounded-lg p-4 cursor-pointer hover:bg-secondary" data-testid="discover-file-upload">
                <Upload className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Unggah PDF/DOCX/TXT/MD (opsional)</span>
                <input type="file" multiple className="hidden" onChange={onFile} accept=".pdf,.docx,.txt,.md,.csv,.json" />
              </label>
              <div className="flex flex-wrap gap-2 mt-2">
                {uploads.map((u, i) => (
                  <span key={i} className="inline-flex items-center gap-1 bg-secondary rounded-full px-3 py-1 text-xs">
                    {u.name}<button onClick={() => setUploads(uploads.filter((_, idx) => idx !== i))}><X className="w-3 h-3" /></button>
                  </span>
                ))}
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Button size="lg" onClick={submit} disabled={busy} className="gap-2" data-testid="discover-submit-button">
        {t('discover.btn')} <ArrowRight className="w-4 h-4" />
      </Button>
    </div>
  );
}
