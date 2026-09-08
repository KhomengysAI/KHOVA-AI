import React, { useState } from 'react';
import { useLang } from '@/lib/i18n';
import { ebookPlan, ebookSection, ebookIntro, ebookRewrite, ebookCover, ebookIllustration, ebookPreviewUrl } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Working } from '@/components/Loading';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { BookOpen, ArrowRight, RefreshCw, Wand2, Image as ImageIcon, Eye, Check, Loader2, MoreHorizontal, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { downloadUrl } from '@/lib/api';

export default function EbookCreator({ project, setProject, goTo, ensureAuth }) {
  const { t } = useLang();
  const [busy, setBusy] = useState(false);
  const [genCh, setGenCh] = useState(null);
  const [coverBusy, setCoverBusy] = useState(false);
  const ebook = project.ebook;

  const doPlan = () => { if (!ensureAuth(doPlan)) return; (async () => { setBusy(true); try { const p = await ebookPlan(project.id); setProject(p); toast.success('Rencana ebook dibuat'); } catch (e) { toast.error(e?.response?.data?.detail || 'Gagal.'); } finally { setBusy(false); } })(); };

  const genSection = async (num) => { if (!ensureAuth(() => genSection(num))) return; setGenCh(num); try { const p = await ebookSection(project.id, num); setProject(p); } catch (e) { toast.error('Gagal membuat bab.'); } finally { setGenCh(null); } };

  const genAll = async () => {
    if (!ensureAuth(genAll)) return;
    const toc = ebook.toc || [];
    const doneNums = new Set((ebook.sections || []).map(s => s.chapter_num));
    for (const ch of toc) {
      if (doneNums.has(ch.chapter_num)) continue;
      setGenCh(ch.chapter_num);
      try { const p = await ebookSection(project.id, ch.chapter_num); setProject(p); }
      catch (e) { toast.error(`Bab ${ch.chapter_num} gagal.`); break; }
    }
    setGenCh(null);
    if (!ebook.introduction_html) { try { const p = await ebookIntro(project.id); setProject(p); } catch (e) {} }
    toast.success('Semua bab selesai');
  };

  const doIntro = async () => { if (!ensureAuth(doIntro)) return; setBusy(true); try { const p = await ebookIntro(project.id); setProject(p); toast.success('Pendahuluan dibuat'); } catch (e) { toast.error('Gagal.'); } finally { setBusy(false); } };
  const doCover = async () => { if (!ensureAuth(doCover)) return; setCoverBusy(true); try { const p = await ebookCover(project.id); setProject(p); toast.success('Cover dibuat'); } catch (e) { toast.error('Gagal membuat cover.'); } finally { setCoverBusy(false); } };
  const rewrite = async (num, instruction) => { setGenCh(num); try { const p = await ebookRewrite(project.id, num, instruction); setProject(p); toast.success('Bab diperbarui'); } catch (e) { toast.error('Gagal.'); } finally { setGenCh(null); } };
  const genIllo = async (num) => { setGenCh(num); try { const p = await ebookIllustration(project.id, num); setProject(p); toast.success('Ilustrasi dibuat'); } catch (e) { toast.error('Gagal.'); } finally { setGenCh(null); } };

  if (busy) return <Working label="Menyusun rencana ebook..." sub="Judul, daftar isi, ide visual, dan bonus." />;

  if (!ebook) {
    return (
      <div className="max-w-2xl">
        <h2 className="font-display text-2xl mb-2">eBook Creator</h2>
        <p className="text-muted-foreground mb-6">Buat rencana ebook: judul, daftar isi (6-10 bab), ide visual, dan bonus — lalu tulis bab demi bab.</p>
        <Button size="lg" onClick={doPlan} className="gap-2" data-testid="ebook-plan-button"><BookOpen className="w-4 h-4" /> {t('common.generate')} Rencana eBook</Button>
      </div>
    );
  }

  const toc = ebook.toc || [];
  const sections = ebook.sections || [];
  const doneNums = new Set(sections.map(s => s.chapter_num));
  const progress = toc.length ? Math.round((sections.length / toc.length) * 100) : 0;
  const coverAsset = (project.assets || []).find(a => a.type === 'cover');

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div>
          <h2 className="font-display text-2xl">{ebook.meta?.title}</h2>
          <p className="text-muted-foreground text-sm">{ebook.meta?.subtitle}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <a href={ebookPreviewUrl(project.id)} target="_blank" rel="noopener noreferrer"><Button variant="secondary" size="sm" className="gap-1" data-testid="ebook-preview-button"><Eye className="w-3.5 h-3.5" /> {t('common.preview')}</Button></a>
          <Button size="sm" onClick={() => goTo('qa')} className="gap-1" data-testid="ebook-continue">{t('common.continue')} <ArrowRight className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_300px] gap-6">
        <div>
          <Card className="p-4 bg-secondary mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium" data-testid="ebook-progress-label">{sections.length} / {toc.length} bab</span>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={doIntro} data-testid="ebook-intro-button">{ebook.introduction_html ? 'Perbarui' : 'Buat'} Pendahuluan</Button>
                <Button size="sm" onClick={genAll} disabled={genCh !== null} className="gap-1" data-testid="ebook-generate-all"><Wand2 className="w-3.5 h-3.5" /> Tulis semua bab</Button>
              </div>
            </div>
            <Progress value={progress} className="h-2" />
          </Card>

          <div className="space-y-2">
            {toc.map(ch => {
              const done = doneNums.has(ch.chapter_num);
              const working = genCh === ch.chapter_num;
              return (
                <Card key={ch.chapter_num} className="p-4 bg-card">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${done ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'}`}>{done ? <Check className="w-3.5 h-3.5" /> : ch.chapter_num}</span>
                      <div className="min-w-0">
                        <div className="font-medium text-sm truncate">{ch.title}</div>
                        <div className="text-xs text-muted-foreground truncate">{ch.purpose}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {working ? <Loader2 className="w-4 h-4 animate-spin text-primary" /> : (
                        done ? (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" data-testid={`ebook-chapter-menu-${ch.chapter_num}`}><MoreHorizontal className="w-4 h-4" /></Button></DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => rewrite(ch.chapter_num, 'perluas dan tambah contoh')}>Perluas</DropdownMenuItem>
                              <DropdownMenuItem onClick={() => rewrite(ch.chapter_num, 'ringkas dan padatkan')}>Ringkas</DropdownMenuItem>
                              <DropdownMenuItem onClick={() => rewrite(ch.chapter_num, 'gunakan nada lebih santai')}>Nada santai</DropdownMenuItem>
                              <DropdownMenuItem onClick={() => genSection(ch.chapter_num)}>Tulis ulang</DropdownMenuItem>
                              <DropdownMenuItem onClick={() => genIllo(ch.chapter_num)}>Buat ilustrasi</DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        ) : (
                          <Button size="sm" onClick={() => genSection(ch.chapter_num)} data-testid={`ebook-generate-section-${ch.chapter_num}`}>{t('common.generate')}</Button>
                        )
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>

        <div className="space-y-4">
          <Card className="p-4 bg-card">
            <div className="text-sm font-medium mb-3">Cover</div>
            {coverAsset ? (
              <img src={downloadUrl(project.id, coverAsset.id)} alt="cover" className="w-full rounded-lg border border-border mb-3" data-testid="ebook-cover-image" />
            ) : (
              <div className="aspect-[3/4] rounded-lg bg-secondary flex items-center justify-center mb-3"><ImageIcon className="w-8 h-8 text-muted-foreground" /></div>
            )}
            <Button variant="secondary" size="sm" className="w-full gap-1" onClick={doCover} disabled={coverBusy} data-testid="ebook-cover-button">
              {coverBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ImageIcon className="w-3.5 h-3.5" />} {coverAsset ? 'Buat ulang cover' : 'Buat cover (AI)'}
            </Button>
          </Card>
          <Card className="p-4 bg-card">
            <div className="text-sm font-medium mb-2">Bonus</div>
            <div className="space-y-2">
              {(ebook.bonuses || []).map((b, i) => (<div key={i} className="text-xs"><Badge variant="outline" className="text-[10px] mb-1">{b.type}</Badge><div className="font-medium">{b.title}</div></div>))}
              {(ebook.bonuses || []).length === 0 && <p className="text-xs text-muted-foreground">Tidak ada bonus.</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
