import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLang } from '@/lib/i18n';
import { listProjects, deleteProject, duplicateProject } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { MoreVertical, Plus, Copy, Trash2, Play } from 'lucide-react';
import { toast } from 'sonner';

export default function Projects() {
  const { t } = useLang();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => { setLoading(true); try { setProjects(await listProjects()); } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);

  const doDelete = async (id) => { await deleteProject(id); toast.success('Proyek dihapus'); load(); };
  const doDup = async (id) => { const p = await duplicateProject(id); toast.success('Proyek diduplikasi'); navigate(`/project/${p.id}`); };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 min-h-[80vh]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-3xl">{t('projects.title')}</h1>
        <Button onClick={() => navigate('/new')} className="gap-1" data-testid="projects-new-button"><Plus className="w-4 h-4" /> {t('nav.new')}</Button>
      </div>
      <Card className="bg-card card-elev overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Judul</TableHead><TableHead>Format</TableHead><TableHead>Status</TableHead><TableHead>Langkah</TableHead><TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-8">Loading...</TableCell></TableRow>}
            {!loading && projects.length === 0 && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-8">{t('projects.empty')}</TableCell></TableRow>}
            {projects.map(p => (
              <TableRow key={p.id} data-testid={`projects-row-${p.id}`} className="cursor-pointer">
                <TableCell className="font-medium" onClick={() => navigate(`/project/${p.id}`)}>{p.title}</TableCell>
                <TableCell onClick={() => navigate(`/project/${p.id}`)}>{p.format ? <Badge variant="secondary">{p.format}</Badge> : '-'}</TableCell>
                <TableCell onClick={() => navigate(`/project/${p.id}`)}><Badge variant={p.status==='complete'?'default':'outline'}>{p.status}</Badge></TableCell>
                <TableCell className="text-muted-foreground text-sm" onClick={() => navigate(`/project/${p.id}`)}>{p.current_step}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreVertical className="w-4 h-4" /></Button></DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => navigate(`/project/${p.id}`)}><Play className="w-4 h-4 mr-2" />Lanjutkan</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => doDup(p.id)}><Copy className="w-4 h-4 mr-2" />Duplikasi</DropdownMenuItem>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <div className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm text-destructive hover:bg-secondary" onClick={e => e.stopPropagation()}><Trash2 className="w-4 h-4 mr-2" />Hapus</div>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader><AlertDialogTitle>Hapus proyek?</AlertDialogTitle><AlertDialogDescription>Tindakan ini tidak bisa dibatalkan.</AlertDialogDescription></AlertDialogHeader>
                          <AlertDialogFooter><AlertDialogCancel>Batal</AlertDialogCancel><AlertDialogAction onClick={() => doDelete(p.id)} data-testid={`projects-delete-button-${p.id}`}>Hapus</AlertDialogAction></AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
