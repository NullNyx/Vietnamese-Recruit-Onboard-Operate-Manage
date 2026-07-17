'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, TrendingUp, CheckCircle, XCircle, Clock, Gauge } from 'lucide-react';
import { getMetrics, getJobOpeningMetrics, type MetricsResponse, type JobOpeningMetrics } from '@/lib/api/recruitment';
import { useAuthGuard } from '@/lib/auth/session';
import { ErrorBanner, Loading } from '@/lib/dashboard-ui';

export default function MetricsPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });

  const { data: metrics, isLoading, error } = useQuery<MetricsResponse>({ queryKey: ['recruitment-metrics'], queryFn: getMetrics, staleTime: 30 * 1000 });
  const { data: jobMetrics } = useQuery<JobOpeningMetrics>({ queryKey: ['recruitment-job-openings', 'metrics'], queryFn: getJobOpeningMetrics, staleTime: 30 * 1000 });

  if (isLoading) return <Loading label="Đang tải metrics..." />;
  if (error) return <ErrorBanner error={error} />;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-indigo-600">
        <BarChart3 className="w-5 h-5" />
        <h1 className="text-xl font-bold text-slate-900">Metrics Tuyển dụng</h1>
      </div>
      <p className="text-sm text-slate-500 -mt-3">
        Pipeline processing (cửa sổ 24h cuộn) + trạng thái Job Opening. Dữ liệu live từ BE.
      </p>

      {/* Pipeline metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card icon={TrendingUp} tone="indigo" label="Queue depth" value={String(metrics?.queue_depth ?? 0)} hint="Đang xử lý" />
        <Card icon={CheckCircle} tone="emerald" label="Tỷ lệ thành công" value={`${Math.round((metrics?.success_rate ?? 0) * 100)}%`} hint="CV parse OK" />
        <Card icon={XCircle} tone="rose" label="Tỷ lệ thất bại" value={`${Math.round((metrics?.failure_rate ?? 0) * 100)}%`} hint="CV parse lỗi" />
        <Card icon={Clock} tone="amber" label="Thời gian TB" value={`${((metrics?.average_processing_time_ms ?? 0) / 1000).toFixed(1)}s`} hint="Xử lý trung bình" />
      </div>

      {/* Job opening metrics */}
      {jobMetrics && (
        <>
          <h2 className="text-sm font-bold text-slate-900 pt-2 flex items-center gap-2"><Gauge className="w-4 h-4 text-indigo-600" /> Job Opening theo trạng thái</h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <Mini label="Tổng" value={jobMetrics.total_job_openings} />
            <Mini label="Bản nháp" value={jobMetrics.draft_count} />
            <Mini label="Đang tuyển" value={jobMetrics.open_count} tone="emerald" />
            <Mini label="Đã đóng" value={jobMetrics.closed_count} tone="indigo" />
            <Mini label="Đã hủy" value={jobMetrics.cancelled_count} tone="rose" />
          </div>
        </>
      )}

      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500">
        lưu ý: Metrics pipeline đo trên cửa sổ trượt 24h; Job Opening metrics là tổng snapshot đầy đủ.
      </div>
    </div>
  );
}

function Card({ icon: Icon, tone, label, value, hint }: { icon: React.ElementType; tone: 'indigo' | 'emerald' | 'rose' | 'amber'; label: string; value: string; hint: string }) {
  const tones: Record<string, string> = { indigo: 'text-indigo-600 bg-indigo-50', emerald: 'text-emerald-600 bg-emerald-50', rose: 'text-rose-600 bg-rose-50', amber: 'text-amber-600 bg-amber-50' };
  return (
    <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg ${tones[tone]}`}><Icon className="w-5 h-5" /></div>
        <span className="text-[10px] font-mono uppercase text-slate-400">{label}</span>
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <p className="text-xs text-slate-500 mt-1">{hint}</p>
    </div>
  );
}

function Mini({ label, value, tone = 'slate' }: { label: string; value: number; tone?: string }) {
  const tones: Record<string, string> = { slate: 'text-slate-800', emerald: 'text-emerald-600', indigo: 'text-indigo-600', rose: 'text-rose-600' };
  return (
    <div className="p-3 bg-white rounded-xl border border-slate-200">
      <div className={`text-2xl font-bold ${tones[tone] ?? tones.slate}`}>{value}</div>
      <p className="text-[10px] font-mono uppercase text-slate-400">{label}</p>
    </div>
  );
}