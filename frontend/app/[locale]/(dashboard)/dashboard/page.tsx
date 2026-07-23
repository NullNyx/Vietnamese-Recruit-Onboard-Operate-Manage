    'use client';

    import React, { useState } from 'react';
    import { useQuery } from '@tanstack/react-query';
    import { useTranslations, useLocale } from 'next-intl';
    import {
      LayoutDashboard, Activity, Users, TrendingUp, AlertTriangle,
      CheckCircle, XCircle, Clock, FileText, ChevronLeft, ChevronRight, Search
    } from 'lucide-react';
    import { getMetrics } from '@/lib/api/recruitment';
    import type { MetricsResponse } from '@/lib/api/recruitment';
    import { getRuntimeHealth, getAuditLogs } from '@/lib/api/admin';
    import type { RuntimeHealthResponse, PaginatedAuditLogs, AuditLogQueryParams } from '@/lib/api/admin';
    import { useAuthGuard } from '@/lib/auth/session';
    import { AUDIT_ACTION_LABELS, formatAuditDetails, SERVICE_LABELS, formatRuntimeDetail, formatLatency } from '@/components/shared-ui';

    export default function DashboardPage() {
      useAuthGuard({ requireAuth: true, requireAdmin: true });
      const t = useTranslations('dashboard');
      const ta = useTranslations('audit');
      const locale = useLocale();
          const ts = useTranslations('system');
      const [auditPage, setAuditPage] = useState(1);
      const [auditFilter, setAuditFilter] = useState('');

      // Recruitment metrics
      const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery<MetricsResponse>({
        queryKey: ['recruitment-metrics'],
        queryFn: getMetrics,
        staleTime: 30 * 1000,
        placeholderData: (prev) => prev,
      });

      // Runtime health
      const { data: health, isLoading: healthLoading, error: healthError, dataUpdatedAt: healthUpdatedAt } = useQuery<RuntimeHealthResponse>({
        queryKey: ['runtime-health'],
        queryFn: getRuntimeHealth,
        staleTime: 30 * 1000,
        placeholderData: (prev) => prev,
      });

      // Audit logs (paginated)
      const auditParams: AuditLogQueryParams = { page: auditPage, page_size: 10 };
      if (auditFilter) auditParams.action_type = auditFilter;

      const { data: auditData, isLoading: auditLoading } = useQuery<PaginatedAuditLogs>({
        queryKey: ['audit-logs', auditPage, auditFilter],
        queryFn: () => getAuditLogs(auditParams),
        staleTime: 30 * 1000,
        placeholderData: (prev) => prev,
      });

      return (
        <div className="space-y-6 animate-fadeSlideIn">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 text-indigo-600 mb-1">
                <LayoutDashboard className="w-5 h-5" />
                <h1 className="text-xl font-bold text-slate-900">{t('title')}</h1>
              </div>
              <p className="text-sm text-slate-500">
                {t('subtitle')}
              </p>
            </div>
          </div>

          {/* Metrics Cards — Bento Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Recruitment Pipeline */}
            <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-indigo-50 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                </div>
                <span className="text-[10px] font-mono uppercase text-slate-400">{t('queue')}</span>
              </div>
              {metricsLoading ? (
                <div className="animate-pulse h-8 bg-slate-100 rounded w-3/4" />
              ) : metricsError ? (
                <p className="text-xs text-rose-500">{t('metricsLoadError')}</p>
              ) : (
                <>
                  <div className="text-2xl font-bold text-slate-900">{metrics?.queue_depth ?? 0}</div>
                  <p className="text-xs text-slate-500 mt-1">{t('queueDepth')}</p>
                </>
              )}
            </div>

            {/* Success Rate */}
            <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-emerald-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                </div>
                <span className="text-[10px] font-mono uppercase text-slate-400">{t('successRate')}</span>
              </div>
              {metricsLoading ? (
                <div className="animate-pulse h-8 bg-slate-100 rounded w-3/4" />
              ) : metricsError ? (
                <p className="text-xs text-rose-500">—</p>
              ) : (
                <>
                  <div className="text-2xl font-bold text-slate-900">
                    {metrics ? Math.round(metrics.success_rate * 100) : 0}%
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{t('cvSuccess')}</p>
                </>
              )}
            </div>

            {/* Failure Rate */}
            <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-rose-50 rounded-lg">
                  <XCircle className="w-5 h-5 text-rose-600" />
                </div>
                <span className="text-[10px] font-mono uppercase text-slate-400">{t('failureRate')}</span>
              </div>
              {metricsLoading ? (
                <div className="animate-pulse h-8 bg-slate-100 rounded w-3/4" />
              ) : metricsError ? (
                <p className="text-xs text-rose-500">—</p>
              ) : (
                <>
                  <div className="text-2xl font-bold text-slate-900">
                    {metrics ? Math.round(metrics.failure_rate * 100) : 0}%
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{t('cvFailed')}</p>
                </>
              )}
            </div>

            {/* Avg Processing Time */}
            <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-amber-50 rounded-lg">
                  <Clock className="w-5 h-5 text-amber-600" />
                </div>
                <span className="text-[10px] font-mono uppercase text-slate-400">{t('avgTime')}</span>
              </div>
              {metricsLoading ? (
                <div className="animate-pulse h-8 bg-slate-100 rounded w-3/4" />
              ) : metricsError ? (
                <p className="text-xs text-rose-500">—</p>
              ) : (
                <>
                  <div className="text-2xl font-bold text-slate-900">
                    {metrics ? (metrics.average_processing_time_ms / 1000).toFixed(1) : 0}s
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{t('avgProcessing')}</p>
                </>
              )}
            </div>
          </div>

          {/* Runtime Health */}
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-indigo-600" />
              <h2 className="font-bold text-slate-900">{t('systemHealth')}</h2>
              {healthUpdatedAt ? (
                <span className="text-[10px] text-slate-400 ml-1">
                  · {t('lastUpdated', { time: formatRuntimeDetail(`last beat: ${healthUpdatedAt / 1000}`, locale) })}
                </span>
              ) : null}
              {health?.status && (
                <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full ${
                  health.status === 'healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : health.status === 'degraded' ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-rose-50 text-rose-700 border border-rose-200'
                }`}>
                  {health.status === 'healthy' ? t('healthy') : health.status === 'degraded' ? t('degraded') : t('error')}
                </span>
              )}
            </div>

            {healthLoading ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse h-16 bg-slate-100 rounded-xl" />
                ))}
              </div>
            ) : healthError ? (
              <p className="text-sm text-rose-500">{t('healthLoadError')}</p>
            ) : health?.services?.length ? (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {health.services.map((svc) => (
                  <div key={svc.name} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-slate-700">{ts(svc.name) ?? svc.name}</span>
                      {svc.status === 'healthy' ? (
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                      ) : svc.status === 'unhealthy' ? (
                        <XCircle className="w-4 h-4 text-rose-500" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      )}
                    </div>
                    {svc.latency_ms !== null && (
                      <span className="text-[10px] text-slate-400">{formatLatency(svc.latency_ms, locale)}</span>
                    )}
                    {formatRuntimeDetail(svc.detail, locale) && (
                      <p className="text-[10px] text-slate-400 truncate mt-0.5">{formatRuntimeDetail(svc.detail, locale)}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">{t('noHealthData')}</p>
            )}
          </div>

          {/* Audit Logs */}
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-indigo-600" />
              <h2 className="font-bold text-slate-900">{t('auditLog')}</h2>
            </div>

            {auditLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse h-10 bg-slate-100 rounded-lg" />
                ))}
              </div>
            ) : auditData?.items?.length ? (
              <div className="space-y-2">
                {auditData.items.map((log) => (
                  <div key={log.id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-slate-700 truncate">{log.admin_email}</span>
                        <span className="text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded font-medium">
                          
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 truncate">{formatAuditDetails(log.details, locale)}</p>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 shrink-0">
                      {new Date(log.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                ))}

                {/* Pagination */}
                {auditData.total > 10 && (
                  <div className="flex items-center justify-between pt-3">
                    <span className="text-xs text-slate-500">
                      {t('pageOf', { page: auditData.page, total: Math.ceil(auditData.total / auditData.page_size) })}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setAuditPage((p) => Math.max(1, p - 1))}
                        disabled={auditPage <= 1}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setAuditPage((p) => p + 1)}
                        disabled={auditPage >= Math.ceil(auditData.total / auditData.page_size)}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-40 transition-all"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-400 py-6 text-center">
                {t('noAuditLogs')}
              </p>
            )}
          </div>
        </div>
      );
    }
    