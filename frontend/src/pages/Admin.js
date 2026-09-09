import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { adminOverview, adminListUsers, adminListJobs, adminListCodes, adminCreateCode, adminUpdateUser } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Label } from '@/components/ui/label';
import { ShieldCheck, Users, Ticket, Activity, RefreshCw, Plus } from 'lucide-react';
import { toast } from 'sonner';

const STATUS_COLOR = {
  completed: 'bg-[hsl(var(--success-soft))] text-[hsl(var(--success))]',
  running: 'bg-[hsl(var(--info-soft))] text-[hsl(var(--info))]',
  failed: 'bg-destructive/15 text-destructive',
  queued: 'bg-secondary text-muted-foreground',
  cancelled: 'bg-secondary text-muted-foreground',
};

export default function Admin() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [codes, setCodes] = useState([]);
  const [forbidden, setForbidden] = useState(false);
  const [form, setForm] = useState({ plan: 'creator', credits: 200, max_redemptions: 1, expires_days: 30, prefix: 'KHOVA' });

  const loadAll = () => {
    adminOverview().then(setOverview).catch((e) => { if (e?.response?.status === 403) setForbidden(true); });
    adminListUsers().then(setUsers).catch(() => {});
    adminListJobs().then(setJobs).catch(() => {});
    adminListCodes().then(setCodes).catch(() => {});
  };

  useEffect(() => { loadAll(); }, []);

  const createCode = async () => {
    try {
      const res = await adminCreateCode({
        plan: form.plan,
        credits: Number(form.credits) || 0,
        max_redemptions: Number(form.max_redemptions) || 1,
        expires_days: Number(form.expires_days) || null,
        prefix: form.prefix || 'KHOVA',
      });
      toast.success(`Code created: ${res.code}`);
      adminListCodes().then(setCodes).catch(() => {});
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed to create code.'); }
  };

  const changePlan = async (userId, plan) => {
    try { await adminUpdateUser(userId, { plan }); toast.success('User plan updated.'); adminListUsers().then(setUsers); }
    catch (e) { toast.error('Update failed.'); }
  };

  if (forbidden) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <ShieldCheck className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
        <h1 className="font-display text-2xl mb-2">Admin only</h1>
        <p className="text-muted-foreground mb-4">You don't have permission to view this page.</p>
        <Button onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 min-h-[80vh]">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-3xl flex items-center gap-2" data-testid="admin-title"><ShieldCheck className="w-7 h-7 text-primary" /> Admin</h1>
        <Button variant="secondary" size="sm" onClick={loadAll} className="gap-1"><RefreshCw className="w-3.5 h-3.5" /> Refresh</Button>
      </div>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Users', value: overview.users, icon: Users },
            { label: 'Jobs', value: overview.jobs, icon: Activity },
            { label: 'Active Codes', value: overview.active_codes, icon: Ticket },
            { label: 'Credits Consumed', value: overview.credits_consumed, icon: ShieldCheck },
          ].map((s, i) => (
            <Card key={i} className="p-4 bg-card card-elev" data-testid={`admin-stat-${s.label.toLowerCase().replace(/ /g, '-')}`}>
              <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground"><s.icon className="w-3.5 h-3.5" /> {s.label}</div>
              <div className="font-display text-3xl mt-1">{s.value}</div>
            </Card>
          ))}
        </div>
      )}

      <Tabs defaultValue="users">
        <TabsList data-testid="admin-tabs">
          <TabsTrigger value="users" data-testid="admin-tab-users">Users</TabsTrigger>
          <TabsTrigger value="codes" data-testid="admin-tab-codes">Redeem Codes</TabsTrigger>
          <TabsTrigger value="jobs" data-testid="admin-tab-jobs">Generation Jobs</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card className="p-0 overflow-hidden bg-card">
            <Table data-testid="admin-users-table">
              <TableHeader><TableRow><TableHead>Email</TableHead><TableHead>Role</TableHead><TableHead>Plan</TableHead><TableHead>Credits</TableHead><TableHead>Creations</TableHead></TableRow></TableHeader>
              <TableBody>
                {users.map(u => (
                  <TableRow key={u.user_id}>
                    <TableCell className="font-mono text-xs">{u.email}</TableCell>
                    <TableCell>{u.role === 'admin' ? <Badge className="bg-primary text-primary-foreground">admin</Badge> : <span className="text-muted-foreground text-sm">user</span>}</TableCell>
                    <TableCell>
                      <Select value={u.plan} onValueChange={(v) => changePlan(u.user_id, v)}>
                        <SelectTrigger className="h-8 w-28 capitalize"><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="free">Free</SelectItem><SelectItem value="creator">Creator</SelectItem><SelectItem value="pro">Pro</SelectItem></SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell className="font-semibold">{u.credits}</TableCell>
                    <TableCell className="text-muted-foreground">{u.creations_used}</TableCell>
                  </TableRow>
                ))}
                {users.length === 0 && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-8">No users.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="codes">
          <Card className="p-5 bg-card card-elev mb-4">
            <div className="text-sm font-medium mb-3">Create redeem code</div>
            <div className="grid sm:grid-cols-5 gap-3 items-end">
              <div><Label className="text-xs mb-1 block">Prefix</Label><Input value={form.prefix} onChange={e => setForm({ ...form, prefix: e.target.value.toUpperCase() })} data-testid="admin-code-prefix" /></div>
              <div><Label className="text-xs mb-1 block">Plan</Label>
                <Select value={form.plan} onValueChange={(v) => setForm({ ...form, plan: v })}><SelectTrigger data-testid="admin-code-plan"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="free">Free</SelectItem><SelectItem value="creator">Creator</SelectItem><SelectItem value="pro">Pro</SelectItem></SelectContent></Select>
              </div>
              <div><Label className="text-xs mb-1 block">Credits</Label><Input type="number" value={form.credits} onChange={e => setForm({ ...form, credits: e.target.value })} data-testid="admin-code-credits" /></div>
              <div><Label className="text-xs mb-1 block">Max uses</Label><Input type="number" value={form.max_redemptions} onChange={e => setForm({ ...form, max_redemptions: e.target.value })} data-testid="admin-code-maxuses" /></div>
              <div><Label className="text-xs mb-1 block">Expires (days)</Label><Input type="number" value={form.expires_days} onChange={e => setForm({ ...form, expires_days: e.target.value })} data-testid="admin-code-expires" /></div>
            </div>
            <Button onClick={createCode} className="mt-4 gap-1" data-testid="admin-create-code-button"><Plus className="w-4 h-4" /> Create code</Button>
          </Card>
          <Card className="p-0 overflow-hidden bg-card">
            <Table data-testid="admin-codes-table">
              <TableHeader><TableRow><TableHead>Code</TableHead><TableHead>Plan</TableHead><TableHead>Credits</TableHead><TableHead>Uses</TableHead><TableHead>Expires</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
              <TableBody>
                {codes.map(c => (
                  <TableRow key={c.code}>
                    <TableCell className="font-mono text-xs">{c.code}</TableCell>
                    <TableCell className="capitalize">{c.plan || '—'}</TableCell>
                    <TableCell>{c.credits}</TableCell>
                    <TableCell>{c.redemptions}/{c.max_redemptions}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{c.expires_at ? new Date(c.expires_at).toLocaleDateString() : 'never'}</TableCell>
                    <TableCell>{c.active ? <Badge className="bg-[hsl(var(--success-soft))] text-[hsl(var(--success))]">active</Badge> : <Badge variant="outline">inactive</Badge>}</TableCell>
                  </TableRow>
                ))}
                {codes.length === 0 && <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">No codes yet.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="jobs">
          <Card className="p-0 overflow-hidden bg-card">
            <Table data-testid="admin-jobs-table">
              <TableHeader><TableRow><TableHead>Task</TableHead><TableHead>Tier</TableHead><TableHead>Model</TableHead><TableHead>Status</TableHead><TableHead>Credits</TableHead><TableHead>When</TableHead></TableRow></TableHeader>
              <TableBody>
                {jobs.map(j => (
                  <TableRow key={j.id}>
                    <TableCell className="text-sm">{j.task}</TableCell>
                    <TableCell><Badge variant="outline" className="uppercase text-[10px]">{j.tier}</Badge></TableCell>
                    <TableCell className="font-mono text-[11px] text-muted-foreground">{j.model}</TableCell>
                    <TableCell><Badge className={`text-[10px] ${STATUS_COLOR[j.status] || ''}`}>{j.status}</Badge></TableCell>
                    <TableCell>{j.credits_charged}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{j.created_at ? new Date(j.created_at).toLocaleString() : ''}</TableCell>
                  </TableRow>
                ))}
                {jobs.length === 0 && <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">No jobs yet.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
