'use client';

import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings as SettingsIcon, Bot, ShieldCheck, Activity, FileText, Users, Mail, Plus,
  Trash2, ChevronLeft, ChevronRight, Loader2, Check, X, AlertCircle, Cpu,
  RefreshCw, FlaskConical, Zap, ShieldAlert, Sparkles,
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
import { AUDIT_ACTION_LABELS, formatAuditDetails, SERVICE_LABELS, formatRuntimeDetail, formatLatency } from '@/components/shared-ui';

function apiErrorText(err: unknown): string {
  if (err instanceof ApiError) return getErrorMessage(err.errorCode);
  if (err instanceof Error) return err.message;
  return 'Lỗi không xác định';
}
function notif(set: (s: string) => void, err: unknown) { set(apiErrorText(err)); }

const TABS = [
  { id: 'ai', label: 'Cấu hình AI', icon: Bot },
  { id: 'tools', label: 'Công cụ AI', icon: Cpu },
  { id: 'health', label: 'Tình trạng hệ thống', icon: Activity },
  { id: 'audit', label: 'Nhật ký hoạt động', icon: FileText },
  { id: 'users', label: 'Người dùng & Vai trò', icon: Users },
  { id: 'whitelist', label: 'Danh sách truy cập', icon: ShieldCheck },
  { id: 'domains', label: 'Tên miền email', icon: Mail },
] as const;
type TabId = (typeof TABS)[number]['id'];

export default function SettingsPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const [tab, setTab] = useState<TabId>('ai');
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-xl bg-indigo-100 flex items-center justify-center">
          <SettingsIcon className="w-4 h-4 text-indigo-600" />
        </div>
        <h1 className="text-lg font-bold text-slate-900">Cấu hình hệ thống</h1>
      </div>
      <div className="flex flex-wrap gap-1 pb-3 border-b border-slate-100">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-1.5 text-[13px] font-medium px-3.5 py-2 rounded-lg transition-all ${
              tab === t.id
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-200'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
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
  const { data: policy } = useQuery({
    queryKey: ['ai-data-policy'],
    queryFn: admin.getDataPolicy,
    enabled: !!cfg && !cfg.data_policy_accepted,
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
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['ai-config'] }); setMsg({ kind: 'success', text: 'Đã lưu cấu hình nhà cung cấp AI.' }); },
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });
  const testMut = useMutation({
    mutationFn: () => admin.testOrganizationAIConfiguration({
      provider: form.provider, base_url: form.base_url, model: form.model, api_key: form.api_key,
    }),
    onSuccess: (r) => setMsg({ kind: r.success ? 'success' : 'error', text: r.message }),
    onError: (e) => setMsg({ kind: 'error', text: apiErrorText(e) }),
  });

  const acceptPolicyMut = useMutation({
        mutationFn: async () => {
          await admin.acceptDataPolicy();
          await admin.acceptAutomationConsent();
          await admin.acceptAssistantConsent();
        },
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: ['ai-config'] });
          qc.invalidateQueries({ queryKey: ['ai-data-policy'] });
          setMsg({ kind: 'success', text: 'Đã đồng ý toàn bộ chính sách. Bạn có thể bật tính năng AI ngay bây giờ.' });
        },
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

  if (isLoading) return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
    </div>
  );
  if (error) return <ErrorBox text={apiErrorText(error)} onRetry={() => qc.invalidateQueries({ queryKey: ['ai-config'] })} />;
  if (!cfg) return null;

  const CONNECTION_STATUS = cfg.configured
    ? { label: 'Đã kết nối', color: 'text-emerald-600 bg-emerald-50', dot: 'bg-emerald-500' }
    : { label: 'Chưa kết nối', color: 'text-slate-500 bg-slate-100', dot: 'bg-slate-300' };

  const PRESETS = [
    { value: 'conservative' as const, title: 'Thận trọng', desc: 'Độ chính xác cao nhất. Chỉ tự động khi AI rất chắc chắn. Phù hợp khi mới bắt đầu.', icon: '🛡️' },
    { value: 'balanced' as const, title: 'Cân bằng', desc: 'Dung hòa giữa tự động hóa và kiểm soát. Khuyến nghị cho phần lớn doanh nghiệp.', icon: '⚖️' },
    { value: 'high_recall' as const, title: 'Bao phủ', desc: 'Ưu tiên không bỏ sót ứng viên. Chấp nhận nhiều kết quả cần HR xem lại hơn.', icon: '🔍' },
  ];

  return (
    <div className="space-y-5">
      {/* Notification */}
      {msg && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex items-start gap-2.5 px-4 py-3 rounded-xl text-sm border ${
            msg.kind === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {msg.kind === 'success' ? <Check className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />}
          <span>{msg.text}</span>
        </motion.div>
      )}

      {/* ── Section 1: Nhà cung cấp AI ── */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Nhà cung cấp AI</h2>
            <p className="text-[12px] text-slate-500">Kết nối với dịch vụ AI bên ngoài để xử lý email và CV</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full ${CONNECTION_STATUS.color}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${CONNECTION_STATUS.dot}`} />
              {CONNECTION_STATUS.label}
            </span>
          </div>
        </div>
        <div className="p-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Cột trái: Form cấu hình */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-[12px] font-medium text-slate-700 mb-1.5 block">Nhà cung cấp</span>
                  <input value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}
                    className="w-full h-10 px-3.5 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-50 outline-none transition-all placeholder:text-slate-400"
                    placeholder="Ví dụ: openai, gemini, cline" />
                </label>
                <label className="block">
                  <span className="text-[12px] font-medium text-slate-700 mb-1.5 block">Tên mô hình</span>
                  <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })}
                    className="w-full h-10 px-3.5 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-50 outline-none transition-all placeholder:text-slate-400"
                    placeholder="Ví dụ: gpt-4o, gemini-1.5-pro" />
                </label>
                <label className="block sm:col-span-2">
                  <span className="text-[12px] font-medium text-slate-700 mb-1.5 block">Địa chỉ máy chủ API</span>
                  <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                    className="w-full h-10 px-3.5 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-50 outline-none transition-all placeholder:text-slate-400 font-mono"
                    placeholder="https://api.openai.com/v1" />
                </label>
                <label className="block sm:col-span-2">
                  <span className="text-[12px] font-medium text-slate-700 mb-1.5 block">Khóa API</span>
                  <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                    className="w-full h-10 px-3.5 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-50 outline-none transition-all placeholder:text-slate-400 font-mono"
                    placeholder={cfg.api_key_masked ? '•••••••• (đã lưu, để trống nếu giữ nguyên)' : 'Nhập khóa API'} />
                </label>
              </div>
              <div className="flex flex-wrap items-center gap-2.5 pt-1">
                <button onClick={() => updateMut.mutate()} disabled={updateMut.isPending}
                  className="inline-flex items-center gap-2 h-10 px-5 text-sm font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-sm shadow-indigo-200">
                  {updateMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Lưu cấu hình
                </button>
                <button onClick={() => testMut.mutate()} disabled={testMut.isPending}
                  className="inline-flex items-center gap-2 h-10 px-5 text-sm font-medium rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-all">
                  {testMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
                  Kiểm tra kết nối
                </button>
              </div>
              <div className="flex items-center gap-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                <span>Nguồn xác thực: <strong className="text-slate-700 font-medium">{cfg.credential_source === 'org_api_key' ? 'Khóa API' : cfg.credential_source ?? '—'}</strong></span>
                <span className="text-slate-300">|</span>
                <span>Trạng thái: <strong className={`font-medium ${cfg.configured ? 'text-emerald-600' : 'text-slate-500'}`}>{CONNECTION_STATUS.label}</strong></span>
                <span className="text-slate-300">|</span>
                <span>Cập nhật: <strong className="text-slate-700 font-medium">{cfg.updated_at ? new Date(cfg.updated_at).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }) : '—'}</strong></span>
              </div>
            </div>
                        {/* Cột phải: Hướng dẫn */}
                        <div className="bg-gradient-to-br from-indigo-50/30 to-slate-50 rounded-xl border border-indigo-100 p-4 self-start">
                          <div className="flex items-center gap-2 pb-2 mb-3 border-b border-indigo-100">
                            <span className="text-base">📖</span>
                            <h3 className="text-sm font-bold text-indigo-800">Hướng dẫn kết nối</h3>
                          </div>
                          <div className="space-y-2.5 text-[12px] text-slate-600">
                            <div className="flex gap-2">
                              <span className="text-indigo-400 font-bold shrink-0 mt-0.5">①</span>
                              <p><strong className="text-slate-700">Nhà cung cấp</strong> là dịch vụ AI bên ngoài. Hỗ trợ mọi API chuẩn OpenAI.</p>
                            </div>
                            <div className="flex gap-2">
                              <span className="text-indigo-400 font-bold shrink-0 mt-0.5">②</span>
                              <div><p>Cần 4 thông tin: <strong>tên</strong> (bất kỳ), <strong>model</strong> (mã), <strong>API URL</strong> (endpoint), <strong>key</strong> (xác thực).</p></div>
                            </div>
                            <div className="flex gap-2">
                              <span className="text-indigo-400 font-bold shrink-0 mt-0.5">③</span>
                              <p>Chỉ gửi email tuyển dụng & CV. <strong className="text-slate-700">Không lưu trữ</strong>, không huấn luyện mô hình.</p>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-indigo-100">
                            <p className="text-[10px] font-semibold text-indigo-500 mb-1.5">💡 URL phổ biến</p>
                            <div className="space-y-1 text-[10px] font-mono">
                              <div className="flex justify-between gap-2"><span className="text-slate-400 shrink-0">OpenAI</span><code className="text-indigo-500 truncate">api.openai.com/v1</code></div>
                              <div className="flex justify-between gap-2"><span className="text-slate-400 shrink-0">Gemini</span><code className="text-indigo-500 truncate">generativelanguage.googleapis.com/v1beta/openai</code></div>
                              <div className="flex justify-between gap-2"><span className="text-slate-400 shrink-0">Cline</span><code className="text-indigo-500 truncate">api.cline.bot/api/v1</code></div>
                            </div>
                          </div>
                        </div>
          </div>
        </div>
      </section>

      {/* ── Section 2: Chính sách dữ liệu (chỉ khi chưa đồng ý) ── */}
      {!cfg.data_policy_accepted && (
        <section className="bg-amber-50/50 rounded-2xl border border-amber-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-amber-100 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-100 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-amber-800">Chính sách dữ liệu</h2>
              <p className="text-[12px] text-amber-600">Cần đồng ý trước khi sử dụng AI</p>
            </div>
          </div>
          <div className="p-5 space-y-4">
            <div className="flex gap-3 p-4 bg-white rounded-xl border border-amber-100">
              <span className="text-xl shrink-0">⚠️</span>
              <div className="text-sm text-amber-800">
                <p className="font-semibold mb-1">Bạn cần đồng ý chính sách dữ liệu trước khi bật tính năng AI.</p>
                <p className="text-amber-700">Khi bật AI, một số dữ liệu như nội dung email tuyển dụng và CV sẽ được gửi đến nhà cung cấp AI bên ngoài để xử lý. Dữ liệu chỉ được xử lý tạm thời, không được lưu trữ hay dùng để huấn luyện mô hình.</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-[12px] font-medium text-slate-700">Dữ liệu sẽ được gửi đi:</p>
              {policy?.items?.map((item: { category: string; purpose: string }, i: number) => (
                <div key={i} className="flex items-start gap-2.5 p-3 bg-white rounded-xl border border-slate-100">
                  <div className="w-6 h-6 rounded-lg bg-slate-100 flex items-center justify-center text-xs font-mono text-slate-500 shrink-0 mt-0.5">{i + 1}</div>
                  <div>
                    <p className="text-[13px] font-medium text-slate-800">{item.category}</p>
                    <p className="text-[12px] text-slate-500">{item.purpose}</p>
                  </div>
                </div>
              ))}
            </div>
            <button onClick={() => acceptPolicyMut.mutate()} disabled={acceptPolicyMut.isPending}
              className="w-full h-11 text-sm font-semibold rounded-xl bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 transition-all shadow-sm shadow-amber-200">
              {acceptPolicyMut.isPending ? (
                <span className="flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Đang xử lý...</span>
              ) : 'Tôi đồng ý và kích hoạt AI'}
            </button>
          </div>
        </section>
      )}

      {/* ── Section 3: Mức độ tự động hóa ── */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center">
            <Zap className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Mức độ tự động hóa</h2>
            <p className="text-[12px] text-slate-500">Chọn mức độ AI tự động xử lý email và CV tuyển dụng</p>
          </div>
        </div>
        <div className="p-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PRESETS.map((p) => {
              const active = cfg.ai_policy_preset === p.value;
              return (
                <button key={p.value} onClick={() => presetMut.mutate(p.value)} disabled={presetMut.isPending}
                  className={`relative text-left p-4 rounded-xl border-2 transition-all ${
                    active ? 'border-indigo-500 bg-indigo-50/50 shadow-sm shadow-indigo-100' : 'border-slate-100 hover:border-slate-200 hover:bg-slate-50'
                  }`}>
                  {active && (
                    <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center">
                      <Check className="w-3 h-3 text-white" />
                    </div>
                  )}
                  <div className="text-2xl mb-2">{p.icon}</div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">{p.title}</h3>
                  <p className="text-[11px] text-slate-500 leading-relaxed">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Section 4: Tính năng AI ── */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Tính năng AI</h2>
            <p className="text-[12px] text-slate-500">Bật hoặc tắt từng tính năng AI riêng biệt</p>
          </div>
        </div>
        <div className="divide-y divide-slate-50">
          <ToggleFeature icon="📧" title="Phân loại email & Trích xuất CV"
            desc="AI tự động đọc email đến, phân loại đơn ứng tuyển, và trích xuất thông tin từ CV đính kèm."
            enabled={cfg.automation_enabled} state={stateLabel(cfg.automation_state)}
            loading={toggleAutomation.isPending} onToggle={() => toggleAutomation.mutate(!cfg.automation_enabled)} />
          <ToggleFeature icon="💬" title="Trợ lý AI hỏi đáp"
            desc="Trợ lý ảo giúp HR tra cứu thông tin tuyển dụng và soạn thảo email. Luôn có người kiểm soát trước khi gửi."
            enabled={cfg.assistant_enabled} state={stateLabel(cfg.assistant_state)}
            loading={toggleAssistant.isPending} onToggle={() => toggleAssistant.mutate(!cfg.assistant_enabled)} />
        </div>
      </section>
    </div>
  );
}

function stateLabel(s: string) {
      switch (s) {
        case 'enabled': return { text: 'Đang hoạt động', color: 'bg-emerald-100 text-emerald-700' };
        case 'disabled': return { text: 'Đã tắt', color: 'bg-slate-100 text-slate-500' };
        case 'not_configured': return { text: 'Chưa cấu hình', color: 'bg-slate-100 text-slate-400' };
        case 'ready': return { text: 'Sẵn sàng', color: 'bg-blue-100 text-blue-700' };
        default: return { text: s, color: 'bg-slate-100 text-slate-500' };
      }
    }

function ToggleFeature({ icon, title, desc, enabled, state, loading, onToggle }: {
  icon: string; title: string; desc: string; enabled: boolean;
  state: { text: string; color: string }; loading: boolean; onToggle: () => void;
}) {
  return (
    <div className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50/50 transition-colors">
      <span className="text-xl shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${state.color}`}>{state.text}</span>
        </div>
        <p className="text-[12px] text-slate-500 leading-relaxed">{desc}</p>
      </div>
      <button onClick={onToggle} disabled={loading}
        className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-all ${
          loading ? 'opacity-50' : ''} ${enabled ? 'bg-indigo-600' : 'bg-slate-200'}`}>
        {loading && <Loader2 className="absolute inset-0 m-auto w-4 h-4 animate-spin text-white z-10" />}
        <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-all ${
          enabled ? 'translate-x-6' : 'translate-x-1'}`} />
      </button>
    </div>
  );
}

function StatusBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-[12px] font-medium text-slate-700">{value}</p>
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

  if (isLoading) return <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto mt-10 block" />;
  if (error) return <ErrorBox text={apiErrorText(error)} onRetry={() => qc.invalidateQueries({ queryKey: ['assistant-tools'] })} />;

  const readTools = data?.tools.filter((t) => t.kind === 'read-tool' || t.kind === 'read') ?? [];
  const draftTools = data?.tools.filter((t) => t.kind === 'draft-tool' || t.kind === 'draft') ?? [];

  return (
    <SectionCard icon={<Cpu className="w-4 h-4 text-indigo-600" />} title="Công cụ AI" desc="Bật/tắt các công cụ mà trợ lý AI được phép sử dụng. Hệ thống chỉ cấp công cụ đọc và soạn thảo, không tự động ghi dữ liệu.">
      {msg && <div className="text-[13px] text-rose-600 mb-3 flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5" />{msg}</div>}
      <div className="space-y-4">
        <div>
          <p className="text-[10px] font-semibold uppercase text-slate-400 tracking-wide mb-2">Công cụ đọc dữ liệu</p>
          <div className="space-y-1.5">
            {readTools.map((t) => <ToolRowCheckbox key={t.tool_name} t={t} draft={draft} setDraft={setDraft} />)}
            {readTools.length === 0 && <Empty text="Không có công cụ đọc." />}
          </div>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase text-slate-400 tracking-wide mb-2">Công cụ soạn thảo</p>
          <div className="space-y-1.5">
            {draftTools.map((t) => <ToolRowCheckbox key={t.tool_name} t={t} draft={draft} setDraft={setDraft} />)}
            {draftTools.length === 0 && <Empty text="Không có công cụ soạn thảo." />}
          </div>
        </div>
      </div>
      <div className="mt-4">
        <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="inline-flex items-center gap-2 h-10 px-5 text-sm font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-sm shadow-indigo-200">
          {saveMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Lưu thay đổi
        </button>
      </div>
    </SectionCard>
  );
}

function ToolRowCheckbox({ t, draft, setDraft }: { t: AssistantToolConfig; draft: Record<string, boolean>; setDraft: (d: Record<string, boolean>) => void }) {
  const checked = draft[t.tool_name] ?? t.enabled;
  return (
    <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors">
      <input type="checkbox" checked={checked} onChange={(e) => setDraft({ ...draft, [t.tool_name]: e.target.checked })} className="w-4 h-4 rounded accent-indigo-600" />
      <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-1.5 flex-wrap">
              <span className="text-[13px] font-medium text-slate-800">{t.display_name}</span>
              <span className="text-[10px] text-slate-400 font-mono">{t.tool_name}</span>
            </div>
            {t.description && <p className="text-[11px] text-slate-500 mt-0.5">{t.description}</p>}
          </div>
        </label>
  );
}

// ---------------------------------------------------------------------------
// Runtime health
// ---------------------------------------------------------------------------
function HealthTab() {
  const qc = useQueryClient();
  const { data, isLoading, error, dataUpdatedAt } = useQuery<RuntimeHealthResponse>({
    queryKey: ['runtime-health'], queryFn: admin.getRuntimeHealth, staleTime: 30_000,
  });
  return (
    <SectionCard icon={<Activity className="w-4 h-4 text-indigo-600" />} title="Tình trạng hệ thống" desc="Trạng thái các dịch vụ nền" action={
      <button onClick={() => qc.invalidateQueries({ queryKey: ['runtime-health'] })} aria-label="Làm mới trạng thái" title="Làm mới trạng thái" className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 transition-colors"><RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} /></button>
    }>
      {isLoading ? <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto mt-5 block" /> :
        error ? <ErrorBox text={apiErrorText(error)} onRetry={() => qc.invalidateQueries({ queryKey: ['runtime-health'] })} /> :
        data ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[13px] text-slate-600">Tổng quan:</span>
              <span className={`text-[12px] font-semibold px-2.5 py-0.5 rounded-full ${data.status === 'healthy' ? 'bg-emerald-50 text-emerald-700' : data.status === 'degraded' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'}`}>
                {data.status === 'healthy' ? '✅ Hoạt động tốt' : data.status === 'degraded' ? '⚠️ Suy giảm' : '❌ Lỗi'}
              </span>
              {dataUpdatedAt ? (
                <span className="text-[10px] text-slate-400">
                  · Cập nhật {formatRuntimeDetail(`last beat: ${dataUpdatedAt / 1000}`)}
                </span>
              ) : null}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {data.services.map((s) => (
                <div key={s.name} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl" title={SERVICE_LABELS[s.name] ? `${SERVICE_LABELS[s.name]}: ${s.status === 'healthy' ? 'Hoạt động' : s.status === 'unhealthy' ? 'Lỗi' : 'Suy giảm'}` : undefined}>
                  <span>{s.status === 'healthy' ? '🟢' : s.status === 'unhealthy' ? '🔴' : '🟡'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-slate-700">{SERVICE_LABELS[s.name] ?? s.name}</p>
                    {formatRuntimeDetail(s.detail) && <p className="text-[11px] text-slate-400 truncate">{formatRuntimeDetail(s.detail)}</p>}
                  </div>
                  {s.latency_ms !== null && <span className="text-[11px] text-slate-400">{formatLatency(s.latency_ms)}</span>}
                </div>
              ))}
            </div>
          </div>
        ) : <Empty text="Không có dữ liệu." />}
    </SectionCard>
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
    <SectionCard icon={<FileText className="w-4 h-4 text-indigo-600" />} title="Nhật ký hoạt động" desc="Lịch sử thao tác của quản trị viên">
      <div className="flex flex-wrap gap-2 mb-4">
        <input value={actionType} onChange={(e) => { setActionType(e.target.value); setPage(1); }} className="h-9 px-3 text-[13px] border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:border-indigo-400 outline-none transition-all placeholder:text-slate-400" placeholder="Loại hành động" />
        <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setPage(1); }} className="h-9 px-3 text-[13px] border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:border-indigo-400 outline-none transition-all" />
        <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setPage(1); }} className="h-9 px-3 text-[13px] border border-slate-200 rounded-lg bg-slate-50 focus:bg-white focus:border-indigo-400 outline-none transition-all" />
        <button onClick={() => qc.invalidateQueries({ queryKey: ['audit-logs'] })} className="h-9 px-4 text-[13px] font-medium rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5"><RefreshCw className="w-3.5 h-3.5" /> Làm mới</button>
      </div>
      {isLoading ? <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto mt-5 block" /> :
        (data?.items?.length ?? 0) === 0 ? <Empty text={actionType || startDate || endDate ? 'Không có kết quả phù hợp với bộ lọc.' : 'Chưa có hoạt động nào.'} /> :
        <div className="space-y-2">
          {data!.items.map((log: AuditLog) => (
            <div key={log.id} className="p-3 bg-slate-50 rounded-xl flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center text-[11px] font-bold shrink-0">{log.admin_email?.[0]?.toUpperCase() ?? '?'}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[13px] font-medium text-slate-700">{log.admin_email}</span>
                  <span className="text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded font-medium">{AUDIT_ACTION_LABELS[log.action_type] ?? log.action_type}</span>
                </div>
                <p className="text-[12px] text-slate-500">{formatAuditDetails(log.details)}</p>
              </div>
              <span className="text-[11px] text-slate-400 shrink-0">{new Date(log.created_at).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })}</span>
            </div>
          ))}
          <div className="flex items-center justify-between pt-3">
            <span className="text-[12px] text-slate-500">Trang {page}/{totalPages} · {data!.total} bản ghi</span>
            <div className="flex gap-1">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-30 transition-colors"><ChevronLeft className="w-4 h-4" /></button>
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-30 transition-colors"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        </div>}
    </SectionCard>
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
    <SectionCard icon={<Users className="w-4 h-4 text-indigo-600" />} title="Người dùng & Vai trò" desc="Quản lý tài khoản và phân quyền">
      {isLoading ? <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto mt-5 block" /> :
        (data?.length ?? 0) === 0 ? <Empty text="Chưa có người dùng nào." /> :
        <div className="space-y-2">
          {data!.map((u) => (
            <div key={u.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
              <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold">{u.name?.[0] ?? '?'}</div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-slate-800">{u.name}</p>
                <p className="text-[11px] text-slate-400">{u.email} · Tạo {new Date(u.created_at).toLocaleDateString('vi-VN')}</p>
              </div>
              <select value={u.role} onChange={(e) => roleMut.mutate({ id: u.id, role: e.target.value as 'admin' | 'user' })} disabled={roleMut.isPending}
                className="h-9 px-3 text-[13px] border border-slate-200 rounded-lg bg-white focus:border-indigo-400 outline-none cursor-pointer">
                <option value="user">Nhân viên</option>
                <option value="admin">Quản trị (HR)</option>
              </select>
            </div>
          ))}
        </div>}
    </SectionCard>
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
    <SectionCard icon={<ShieldCheck className="w-4 h-4 text-indigo-600" />} title="Danh sách truy cập" desc="Quản lý email và tên miền được phép đăng nhập">
      <div className="flex gap-2 mb-4">
        <input value={value} onChange={(e) => setValue(e.target.value)} className="flex-1 h-10 px-3.5 text-[13px] border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-indigo-400 outline-none transition-all placeholder:text-slate-400" placeholder="email@congty.com hoặc @congty.com" />
        <button onClick={() => addMut.mutate()} disabled={addMut.isPending || !value.trim()} className="h-10 px-5 text-sm font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center gap-1.5 shadow-sm shadow-indigo-200"><Plus className="w-4 h-4" /> Thêm</button>
      </div>
      {isLoading ? <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto mt-5 block" /> :
        (data?.items?.length ?? 0) === 0 ? <Empty text="Danh sách trống." /> :
        <div className="space-y-1.5">
          {data!.items.map((w: WhitelistEntry) => (
            <div key={w.id ?? w.value} className="flex items-center gap-2.5 p-2.5 bg-slate-50 rounded-lg">
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded ${w.entry_type === 'domain_pattern' ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-200 text-slate-600'}`}>{w.entry_type === 'domain_pattern' ? 'Tên miền' : 'Email'}</span>
              <span className="text-[13px] text-slate-700 flex-1 truncate">{w.value}</span>
              <span className="text-[10px] text-slate-400">{w.source}{w.is_readonly ? ' · chỉ đọc' : ''}</span>
              {w.id && !w.is_readonly && <button onClick={() => delMut.mutate(w.id!)} className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>}
            </div>
          ))}
        </div>}
    </SectionCard>
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
    <SectionCard icon={<Mail className="w-4 h-4 text-indigo-600" />} title="Tên miền email" desc="Quản lý tên miền email được phép trong tổ chức">
      <div className="flex gap-2 mb-4">
        <input value={value} onChange={(e) => setValue(e.target.value)} className="flex-1 h-10 px-3.5 text-[13px] border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:border-indigo-400 outline-none transition-all placeholder:text-slate-400" placeholder="congty.com, congty.vn" />
        <button onClick={() => addMut.mutate()} disabled={addMut.isPending || !value.trim()} className="h-10 px-5 text-sm font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center gap-1.5 shadow-sm shadow-indigo-200"><Plus className="w-4 h-4" /> Thêm</button>
      </div>
      {isLoading ? <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mx-auto mt-5 block" /> :
        (data?.allowed_domains?.length ?? 0) === 0 ? <Empty text="Chưa có tên miền nào." /> :
        <div className="flex flex-wrap gap-2">
          {data!.allowed_domains.map((d) => (
            <span key={d} className="inline-flex items-center gap-1.5 text-[13px] bg-indigo-50 text-indigo-700 border border-indigo-100 px-3 py-1.5 rounded-lg">
              @{d}
              <button onClick={() => rmMut.mutate(d)} className="text-indigo-400 hover:text-rose-500 ml-0.5"><X className="w-3 h-3" /></button>
            </span>
          ))}
        </div>}
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Shared UI
// ---------------------------------------------------------------------------
function SectionCard({ icon, title, desc, action, children }: {
  icon: React.ReactNode; title: string; desc?: string; action?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">{icon}</div>
        <div className="flex-1 min-w-0">
          <h2 className="text-sm font-bold text-slate-900">{title}</h2>
          {desc && <p className="text-[12px] text-slate-500">{desc}</p>}
        </div>
        {action}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function ErrorBox({ text, onRetry }: { text: string; onRetry: () => void }) {
  return (
    <div className="flex items-center gap-3 p-4 bg-rose-50 border border-rose-200 rounded-xl text-[13px] text-rose-700">
      <AlertCircle className="w-5 h-5 shrink-0" /><span className="flex-1">{text}</span>
      <button onClick={onRetry} className="font-medium underline hover:text-rose-800">Thử lại</button>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="text-[13px] text-slate-400 py-10 text-center">{text}</p>;
}
