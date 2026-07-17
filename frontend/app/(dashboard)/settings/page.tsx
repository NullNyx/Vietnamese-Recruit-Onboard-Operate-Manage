'use client';

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings as SettingsIcon, Bot, ShieldCheck, Activity, FileText, Users, Mail, Plus,
  Trash2, ChevronLeft, ChevronRight, Loader2, Check, X, AlertCircle, Cpu, ToggleLeft,
  ToggleRight, RefreshCw, FlaskConical,
} from 'lucide-react';
import { motion } from 'motion/react';
import * as admin from '@/lib/api/admin';
import type {
  OrganizationAIConfiguration, RuntimeHealthResponse, AuditLog, AdminUser,
  WhitelistEntry, AssistantToolConfig,
} from '@/lib/api/admin';
import { useAuthGuard } from '@/lib/auth/session';
import { ApiError } from '@/lib/api/types';
import { getErrorMessage } from '@/lib/api/error-codes';
import { AUDIT_ACTION_LABELS, formatAuditDetails } from '@/components/shared-ui';

function apiErrorText(err: unknown): string {
  if (err instanceof ApiError) return getErrorMessage(err.errorCode);
  if (err instanceof Error) return err.message;
  return 'Lỗi không xác định';
}
function notif(set: (s: string) => void, err: unknown) { set(apiErrorText(err)); }

const TABS = [
  { id: 'ai', label: 'Cấu hình AI', icon: Bot },
  { id: 'tools', label: 'Tool registry', icon: Cpu },
  { id: 'health', label: 'Runtime health', icon: Activity },
  { id: 'audit', label: 'Audit logs', icon: FileText },
  { id: 'users', label: 'Người dùng & vai trò', icon: Users },
  { id: 'whitelist', label: 'Whitelist', icon: ShieldCheck },
  { id: 'domains', label: 'Email domains', icon: Mail },
] as const;
type TabId = (typeof TABS)[number]['id'];

export default function SettingsPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const [tab, setTab] = useState<TabId>('ai');
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-indigo-600">
        <SettingsIcon className="w-5 h-5" />
        <h1 className="text-xl font-bold text-slate-900">Cấu hình AI & Hệ thống</h1>
      </div>
      <div className="flex flex-wrap gap-1.5 border-b border-slate-200 pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
              tab === t.id ? 'bg-indigo-50 text-indigo-600 border border-indigo-100' : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'ai' && <AITab />}
      {tab === 'tools' && <ToolsTab />}
      {tab === 'health' && <HealthTab />}
      {tab === 'audit' && <AuditTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'whitelist' && <WhitelistTab />}
      {tab === 'domains' && <DomainsTab />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AI Configuration
// ---------------------------------------------------------------------------
function AITab() {
  const qc = useQueryClient();
  const { data: cfg, isLoading, error } = useQuery<OrganizationAIConfiguration>({
    queryKey: ['ai-config'],
    queryFn: admin.getOrganizationAIConfiguration,
  });
  const [form, setForm] = useState({ provider: '', base_url: '', model: '', api_key: '' });
  const [msg, setMsg] = useState<{ kind: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (cfg) setForm({ provider: cfg.provider ?? '', base_url: cfg.base_url ?? '', model: cfg.model ?? '', api_key: '' });
  }, [cfg]);

  const updateMut = useMutation({
    mutationFn: () => admin.updateOrganizationAIConfiguration({
      provider: form.provider, base_url: form.base_url, model: form.model, api_key: form.api_key,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-config'] }); setMsg({ kind: 'success', text: 'Đã cập nhật cấu hình AI.' }); },
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });
  const testMut = useMutation({
    mutationFn: () => admin.testOrganizationAIConfiguration({
      provider: form.provider, base_url: form.base_url, model: form.model, api_key: form.api_key,
    }),
    onSuccess: (r) => setMsg({ kind: r.success ? 'success' : 'error', text: r.message }),
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });

  const presetMut = useMutation({
    mutationFn: (preset: 'conservative' | 'balanced' | 'high_recall') => admin.setAIPolicyPreset(preset),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-config'] }),
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });
  const toggleAutomation = useMutation({
    mutationFn: (enable: boolean) => (enable ? admin.enableAutomation() : admin.disableAutomation()),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-config'] }),
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });
  const toggleAssistant = useMutation({
    mutationFn: (enable: boolean) => (enable ? admin.enableAssistant() : admin.disableAssistant()),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-config'] }),
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });

  if (isLoading) return <Loader2 className="w-5 h-5 animate-spin text-slate-300" />;
  if (error) return <ErrorBox text={apiErrorText(error)} onRetry={() => qc.invalidateQueries({ queryKey: ['ai-config'] })} />;
  if (!cfg) return null;

  const PRESETS: { value: 'conservative' | 'balanced' | 'high_recall'; label: string }[] = [
    { value: 'conservative', label: 'Conservative (ít sai, ưu tiên precision)' },
    { value: 'balanced', label: 'Balanced (cân bằng)' },
    { value: 'high_recall', label: 'High-recall (ưu tiên recall)' },
  ];

  return (
    <div className="space-y-4">
      {msg && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs border ${msg.kind === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-rose-50 border-rose-200 text-rose-700'}`}>
          {msg.kind === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {msg.text}
        </div>
      )}

      {/* Provider / model */}
      <Card title="Provider & Model" icon={<Cpu className="w-4 h-4 text-indigo-600" />}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <InField label="Provider"><input value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} className="inp" placeholder="openai / gemini / ..." /></InField>
          <InField label="Model"><input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} className="inp" placeholder="gpt-4o / gemini-1.5-pro" /></InField>
          <InField label="Base URL" full><input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} className="inp" placeholder="https://api.openai.com/v1" /></InField>
          <InField label="API key (để trống nếu giữ nguyên)" full>
            <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} className="inp" placeholder={cfg.api_key_masked ?? '••••••••'} />
          </InField>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          <button onClick={() => updateMut.mutate()} disabled={updateMut.isPending} className="btn-primary">
            {updateMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />} Lưu cấu hình
          </button>
          <button onClick={() => testMut.mutate()} disabled={testMut.isPending} className="btn-outline">
            {testMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FlaskConical className="w-3.5 h-3.5" />} Test kết nối
          </button>
        </div>
        <StatusRow label="Credential source" value={cfg.credential_source ?? '—'} />
        <StatusRow label="Provider đã cấu hình" value={cfg.configured ? 'Có' : 'Chưa'} />
        <StatusRow label="Cập nhật lần cuối" value={cfg.updated_at ? new Date(cfg.updated_at).toLocaleString('vi-VN') : '—'} />
      </Card>

      {/* Policy preset */}
      <Card title="AI Policy Preset" icon={<ShieldCheck className="w-4 h-4 text-indigo-600" />}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {PRESETS.map((p) => {
            const active = cfg.ai_policy_preset === p.value;
            return (
              <button
                key={p.value}
                onClick={() => presetMut.mutate(p.value)}
                disabled={presetMut.isPending}
                className={`text-left p-3 rounded-xl border text-xs transition-all ${active ? 'border-indigo-400 bg-indigo-50 ring-1 ring-indigo-200' : 'border-slate-200 hover:bg-slate-50'}`}
              >
                <div className="font-semibold text-slate-800 flex items-center gap-1.5">{active && <Check className="w-3.5 h-3.5 text-indigo-600" />}{p.label}</div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5">{p.value} · v{cfg.ai_policy_preset_version || '—'}</div>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Capability toggles */}
      <Card title="Capability toggles (độc lập)" icon={<ToggleRight className="w-4 h-4 text-indigo-600" />}>
        <ToggleRow
          title="AI Automation"
          desc="Phân loại email + parse CV (pipeline nền)."
          enabled={cfg.automation_enabled}
          state={cfg.automation_state}
          loading={toggleAutomation.isPending}
          onToggle={() => toggleAutomation.mutate(!cfg.automation_enabled)}
        />
        <ToggleRow
          title="AI Assistant"
          desc="Chatbot hội thoại HR (human-in-the-loop)."
          enabled={cfg.assistant_enabled}
          state={cfg.assistant_state}
          loading={toggleAssistant.isPending}
          onToggle={() => toggleAssistant.mutate(!cfg.assistant_enabled)}
        />
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Assistant tools registry
// ---------------------------------------------------------------------------
function ToolsTab() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ['assistant-tools'], queryFn: admin.listAssistantTools });
  const [draft, setDraft] = useState<Record<string, boolean>>({});
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (data?.tools) {
      const map: Record<string, boolean> = {};
      data.tools.forEach((t) => { map[t.tool_name] = t.enabled; });
      setDraft(map);
    }
  }, [data]);

  const saveMut = useMutation({
    mutationFn: () => admin.updateAssistantTools(draft),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assistant-tools'] }); setMsg(null); },
    onError: (e) => notif(setMsg, e),
  });

  if (isLoading) return <Loader2 className="w-5 h-5 animate-spin text-slate-300" />;
  if (error) return <ErrorBox text={apiErrorText(error)} onRetry={() => qc.invalidateQueries({ queryKey: ['assistant-tools'] })} />;

  const readTools = data?.tools.filter((t) => t.kind === 'read-tool' || t.kind === 'read') ?? [];
  const draftTools = data?.tools.filter((t) => t.kind === 'draft-tool' || t.kind === 'draft') ?? [];
  const others = data?.tools.filter((t) => !readTools.includes(t) && !draftTools.includes(t)) ?? [];

  const ToolRow = ({ t }: { t: AssistantToolConfig }) => (
    <label className="flex items-start gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer">
      <input
        type="checkbox"
        checked={draft[t.tool_name] ?? t.enabled}
        onChange={(e) => setDraft({ ...draft, [t.tool_name]: e.target.checked })}
        className="mt-0.5 accent-indigo-600"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-800">{t.display_name}</span>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">{t.kind}</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-0.5">{t.description}</p>
        <p className="text-[10px] text-slate-400 font-mono mt-0.5">{t.tool_name}</p>
      </div>
    </label>
  );

  return (
    <Card title="Tool registry (Read-Tool / Draft-Tool)" icon={<Cpu className="w-4 h-4 text-indigo-600" />}>
      <p className="text-[11px] text-slate-500 mb-3">Bật/tắt công cụ cung cấp cho LLM. Chỉ có Read-Tool và Draft-Tool — không có write-tool cho LLM.</p>
      {msg && <div className="text-xs text-rose-600 mb-2 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{msg}</div>}
      <div className="space-y-4">
        <div><p className="text-[10px] font-mono uppercase text-slate-400 mb-1.5">Read-Tool</p><div className="space-y-1.5">{readTools.map((t) => <ToolRow key={t.tool_name} t={t} />)}{readTools.length === 0 && <Empty text="Không có Read-Tool." />}</div></div>
        <div><p className="text-[10px] font-mono uppercase text-slate-400 mb-1.5">Draft-Tool</p><div className="space-y-1.5">{draftTools.map((t) => <ToolRow key={t.tool_name} t={t} />)}{draftTools.length === 0 && <Empty text="Không có Draft-Tool." />}</div></div>
        {others.length > 0 && <div><p className="text-[10px] font-mono uppercase text-slate-400 mb-1.5">Khác</p><div className="space-y-1.5">{others.map((t) => <ToolRow key={t.tool_name} t={t} />)}</div></div>}
      </div>
      <div className="mt-3">
        <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="btn-primary">
          {saveMut.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />} Lưu cấu hình tool
        </button>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Runtime health
// ---------------------------------------------------------------------------
function HealthTab() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery<RuntimeHealthResponse>({
    queryKey: ['runtime-health'],
    queryFn: admin.getRuntimeHealth,
    staleTime: 30_000,
  });
  return (
    <Card title="Runtime health" icon={<Activity className="w-4 h-4 text-indigo-600" />} action={
      <button onClick={() => qc.invalidateQueries({ queryKey: ['runtime-health'] })} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400"><RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} /></button>
    }>
      {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-300" /> :
        error ? <ErrorBox text={apiErrorText(error)} onRetry={() => qc.invalidateQueries({ queryKey: ['runtime-health'] })} /> :
        data ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-700">Trạng thái tổng:</span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold border ${
                data.status === 'healthy' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                data.status === 'degraded' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                'bg-rose-50 text-rose-700 border-rose-200'
              }`}>{data.status === 'healthy' ? 'KHỎE' : data.status === 'degraded' ? 'SUY GIẢM' : 'KHÔNG KHỎE'}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {data.services.map((s) => (
                <div key={s.name} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-semibold text-slate-700">{s.name}</span>
                    {s.status === 'healthy' ? <Check className="w-4 h-4 text-emerald-500" /> : s.status === 'unhealthy' ? <X className="w-4 h-4 text-rose-500" /> : <AlertCircle className="w-4 h-4 text-amber-500" />}
                  </div>
                  {s.latency_ms !== null && <span className="text-[10px] font-mono text-slate-400">{s.latency_ms}ms</span>}
                  {s.detail && <p className="text-[10px] text-slate-400 truncate mt-0.5">{s.detail}</p>}
                </div>
              ))}
            </div>
          </div>
        ) : <Empty text="Không có dữ liệu." />}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Audit logs
// ---------------------------------------------------------------------------
function AuditTab() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [actionType, setActionType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const params: admin.AuditLogQueryParams = { page, page_size: 15 };
  if (actionType) params.action_type = actionType;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const { data, isLoading } = useQuery({ queryKey: ['audit-logs', params], queryFn: () => admin.getAuditLogs(params), staleTime: 30_000 });
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <Card title="Audit logs" icon={<FileText className="w-4 h-4 text-indigo-600" />}>
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 mb-3">
        <InField label="Hành động"><input value={actionType} onChange={(e) => { setActionType(e.target.value); setPage(1); }} className="inp" placeholder="role_change ..." /></InField>
        <InField label="Từ ngày"><input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }} className="inp" /></InField>
        <InField label="Đến ngày"><input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }} className="inp" /></InField>
        <div className="flex items-end"><button onClick={() => qc.invalidateQueries({ queryKey: ['audit-logs'] })} className="btn-outline"><RefreshCw className="w-3.5 h-3.5" /> Làm mới</button></div>
      </div>
      {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-300" /> :
        (data?.items?.length ?? 0) === 0 ? <Empty text={actionType || startDate || endDate ? 'Trạng thái rỗng do bộ lọc.' : 'Chưa có bản ghi audit.'} /> :
        <div className="space-y-2">
          {data!.items.map((log: AuditLog) => (
            <div key={log.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-slate-700 truncate">{log.admin_email}</span>
                  <span className="text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">{AUDIT_ACTION_LABELS[log.action_type] ?? log.action_type}</span>
                </div>
                <p className="text-[11px] text-slate-500 break-words">{formatAuditDetails(log.details)}</p>
              </div>
              <span className="text-[10px] font-mono text-slate-400 shrink-0">{new Date(log.created_at).toLocaleString('vi-VN')}</span>
            </div>
          ))}
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-500">Trang {page} / {totalPages} · {data!.total} bản ghi</span>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        </div>}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Users & role
// ---------------------------------------------------------------------------
function UsersTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery<AdminUser[]>({ queryKey: ['admin-users'], queryFn: admin.listUsers });
  const roleMut = useMutation({
    mutationFn: ({ id, role }: { id: string; role: 'admin' | 'user' }) => admin.updateUserRole(id, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-users'] }),
  });
  return (
    <Card title="Người dùng & vai trò" icon={<Users className="w-4 h-4 text-indigo-600" />}>
      {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-300" /> :
        (data?.length ?? 0) === 0 ? <Empty text="Chưa có người dùng." /> :
        <div className="space-y-2">
          {data!.map((u) => (
            <div key={u.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">{u.name?.[0] ?? 'U'}</div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-slate-800 truncate">{u.name} · {u.email}</div>
                <div className="text-[10px] text-slate-400">Tạo: {new Date(u.created_at).toLocaleDateString('vi-VN')} · Đăng nhập: {u.last_login || '—'}</div>
              </div>
              <select
                value={u.role}
                onChange={(e) => roleMut.mutate({ id: u.id, role: e.target.value as 'admin' | 'user' })}
                disabled={roleMut.isPending}
                className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white focus:outline-none"
              >
                <option value="user">user (Employee)</option>
                <option value="admin">admin (HR)</option>
              </select>
            </div>
          ))}
        </div>}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Whitelist
// ---------------------------------------------------------------------------
function WhitelistTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['whitelist'], queryFn: admin.listWhitelist });
  const [value, setValue] = useState('');
  const addMut = useMutation({
    mutationFn: () => admin.addWhitelistEntry(value.trim()),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['whitelist'] }); setValue(''); },
    onError: (e) => alert(apiErrorText(e)),
  });
  const delMut = useMutation({
    mutationFn: (id: string) => admin.removeWhitelistEntry(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['whitelist'] }),
    onError: (e) => alert(apiErrorText(e)),
  });
  return (
    <Card title="Whitelist đăng nhập" icon={<ShieldCheck className="w-4 h-4 text-indigo-600" />}>
      <div className="flex gap-2 mb-3">
        <input value={value} onChange={(e) => setValue(e.target.value)} className="inp" placeholder="email@congty.com hoặc @congty.com" />
        <button onClick={() => addMut.mutate()} disabled={addMut.isPending || !value.trim()} className="btn-primary shrink-0"><Plus className="w-3.5 h-3.5" /> Thêm</button>
      </div>
      {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-300" /> :
        (data?.items?.length ?? 0) === 0 ? <Empty text="Whitelist trống." /> :
        <div className="space-y-1.5">
          {data!.items.map((w: WhitelistEntry) => (
            <div key={w.id ?? w.value} className="flex items-center gap-2 p-2.5 bg-slate-50 rounded-lg border border-slate-100">
              <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${w.entry_type === 'domain_pattern' ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>{w.entry_type}</span>
              <span className="text-xs text-slate-700 flex-1 truncate">{w.value}</span>
              <span className="text-[10px] text-slate-400">{w.source}{w.is_readonly ? ' · readonly' : ''}</span>
              {w.id && !w.is_readonly && <button onClick={() => delMut.mutate(w.id!)} className="p-1 text-slate-400 hover:text-rose-500"><Trash2 className="w-3.5 h-3.5" /></button>}
            </div>
          ))}
        </div>}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Domains
// ---------------------------------------------------------------------------
function DomainsTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['org-domains'], queryFn: admin.listDomains });
  const [value, setValue] = useState('');
  const addMut = useMutation({
    mutationFn: () => admin.addDomains(value.split(',').map((s) => s.trim()).filter(Boolean)),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['org-domains'] }); setValue(''); },
    onError: (e) => alert(apiErrorText(e)),
  });
  const rmMut = useMutation({
    mutationFn: (d: string) => admin.removeDomain(d),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['org-domains'] }),
    onError: (e) => alert(apiErrorText(e)),
  });
  return (
    <Card title="Allowed email domains" icon={<Mail className="w-4 h-4 text-indigo-600" />}>
      <div className="flex gap-2 mb-3">
        <input value={value} onChange={(e) => setValue(e.target.value)} className="inp" placeholder="congty.com, congty.vn" />
        <button onClick={() => addMut.mutate()} disabled={addMut.isPending || !value.trim()} className="btn-primary shrink-0"><Plus className="w-3.5 h-3.5" /> Thêm</button>
      </div>
      {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-slate-300" /> :
        (data?.allowed_domains?.length ?? 0) === 0 ? <Empty text="Chưa có domain nào." /> :
        <div className="flex flex-wrap gap-1.5">
          {data!.allowed_domains.map((d) => (
            <span key={d} className="inline-flex items-center gap-1.5 text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-1 rounded-lg">
              {d}
              <button onClick={() => rmMut.mutate(d)} className="text-indigo-400 hover:text-rose-500"><X className="w-3 h-3" /></button>
            </span>
          ))}
        </div>}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Shared UI
// ---------------------------------------------------------------------------
function Card({ title, icon, action, children }: { title: string; icon: React.ReactNode; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h2 className="font-bold text-sm text-slate-900">{title}</h2>
        <div className="ml-auto">{action}</div>
      </div>
      {children}
    </div>
  );
}
function InField({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <label className={`block ${full ? 'sm:col-span-2' : ''}`}>
      <span className="text-[10px] font-mono uppercase text-slate-400">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
function ToggleRow({ title, desc, enabled, state, loading, onToggle }: { title: string; desc: string; enabled: boolean; state: string; loading: boolean; onToggle: () => void; }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl border border-slate-100">
      <div className="flex-1">
        <div className="text-xs font-semibold text-slate-800">{title}</div>
        <div className="text-[11px] text-slate-500">{desc}</div>
        <div className="text-[10px] text-slate-400 font-mono mt-0.5">state: {state}</div>
      </div>
      <button onClick={onToggle} disabled={loading} className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors ${enabled ? 'bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
        {enabled ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
        {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : enabled ? 'Bật' : 'Tắt'}
      </button>
    </div>
  );
}
function StatusRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1.5"><span>{label}</span><span className="text-slate-700 font-mono">{value}</span></div>;
}
function ErrorBox({ text, onRetry }: { text: string; onRetry: () => void }) {
  return (
    <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
      <AlertCircle className="w-4 h-4" /><span className="flex-1">{text}</span>
      <button onClick={onRetry} className="underline">Thử lại</button>
    </div>
  );
}
function Empty({ text }: { text: string }) { return <p className="text-xs text-slate-400 py-6 text-center">{text}</p>; }

// Tailwind component shorthands via @layer not available; use plain class strings.
// (inp / btn-primary / btn-outline used through JSX className)