'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, CheckCircle, Circle, ArrowRight, Sparkles, ExternalLink } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { getGuideProgress, dismissGuide, type GuideProgress } from '@/lib/api/guide';

export default function GuideWidget() {
  const t = useTranslations('guide');
  const router = useRouter();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery<GuideProgress>({
    queryKey: ['guide-progress'],
    queryFn: getGuideProgress,
    staleTime: 30 * 1000,
  });

  const dismissMut = useMutation({
    mutationFn: dismissGuide,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['guide-progress'] }),
  });

  // Don't show if loading, all completed, or dismissed
  if (isLoading || !data || data.all_completed || data.dismissed) return null;

  const doneCount = data.completed_tasks.length;
  const totalCount = data.tasks.length;

  return (
    <div className="p-5 bg-gradient-to-br from-indigo-50 to-white rounded-2xl border border-indigo-100 shadow-sm shadow-indigo-50 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-600" />
          <h2 className="text-sm font-bold text-slate-900">{t('title')}</h2>
        </div>
        <button
          onClick={() => dismissMut.mutate()}
          className="p-1.5 rounded-full hover:bg-indigo-100 text-indigo-400 hover:text-indigo-600 transition-all"
          title={t('dismiss')}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <p className="text-xs text-slate-500 mb-2">
        {t('progress', { done: doneCount, total: totalCount })}
      </p>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-indigo-100 rounded-full mb-3">
        <div
          className="h-1.5 bg-indigo-600 rounded-full transition-all duration-500"
          style={{ width: `${data.progress}%` }}
        />
      </div>

      {/* Task list */}
      <div className="space-y-1.5">
        {data.tasks.map((task) => {
          const href = getTaskHref(task.id);
          return (
            <div
              key={task.id}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-white transition-all"
            >
              {task.done ? (
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-slate-300 shrink-0" />
              )}
              <span className={`text-xs flex-1 ${task.done ? 'text-slate-400 line-through' : 'text-slate-700 font-medium'}`}>
                {task.label}
              </span>
              {!task.done && href && (
                <button
                  onClick={() => router.push(href)}
                  className="text-[10px] px-2.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex items-center gap-1 font-medium transition-all"
                >
                  {t('go')}
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-3 pt-3 border-t border-indigo-100">
        <button
          onClick={() => router.push('/guide')}
          className="text-xs text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
        >
          {t('viewAll')}
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

function getTaskHref(taskId: string): string | null {
  switch (taskId) {
    case 'google_workspace_connected': return '/gmail';
    case 'ai_configured': return '/settings?tab=ai';
    case 'first_job_opening': return '/recruitment/job-openings';
    case 'first_kb_document': return '/knowledge-base';
    default: return null;
  }
}
