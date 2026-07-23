'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Sparkles, CheckCircle, Circle, ExternalLink, ArrowLeft, X } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { getGuideProgress, dismissGuide, markTaskDone, type GuideProgress } from '@/lib/api/guide';
import { useAuthGuard } from '@/lib/auth/session';

const TASK_DETAILS: Record<string, { desc: string; href: string }> = {
  google_workspace_connected: {
    desc: 'Kết nối Google Workspace để hệ thống có thể nhận email tuyển dụng, đồng bộ lịch phỏng vấn. Bắt buộc để Recruitment Inbox hoạt động.',
    href: '/gmail',
  },
  ai_configured: {
    desc: 'Cấu hình provider AI (OpenAI, Anthropic, v.v.) để AI Automation có thể phân loại email và parse CV, và AI Assistant có thể trả lời câu hỏi.',
    href: '/settings?tab=ai',
  },
  first_job_opening: {
    desc: 'Tạo vị trí tuyển dụng đầu tiên để bắt đầu nhận ứng viên vào pipeline. Cần ít nhất một Job Opening để gán Candidate.',
    href: '/recruitment/job-openings',
  },
  first_kb_document: {
    desc: 'Upload tài liệu nội bộ (nội quy, sổ tay nhân viên) vào Employee Knowledge Base để AI Assistant có context trả lời cho Employee.',
    href: '/knowledge-base',
  },
};

export default function GuidePage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const router = useRouter();
  const t = useTranslations('guide');
  const qc = useQueryClient();

  const { data } = useQuery<GuideProgress>({
    queryKey: ['guide-progress'],
    queryFn: getGuideProgress,
  });

  const dismissMut = useMutation({
    mutationFn: dismissGuide,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['guide-progress'] });
      router.push('/dashboard');
    },
  });

  const markMut = useMutation({
    mutationFn: markTaskDone,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['guide-progress'] }),
  });

  if (!data) return null;

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fadeSlideIn">
      {/* Header */}
      <div className="flex items-center gap-2">
        <button onClick={() => router.back()} className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <Sparkles className="w-5 h-5 text-indigo-600" />
        <h1 className="text-lg font-bold text-slate-900">{t('pageTitle')}</h1>
      </div>

      <p className="text-sm text-slate-500">{t('pageDesc')}</p>

      {/* Progress bar */}
      <div className="p-4 bg-white rounded-2xl border border-slate-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-slate-700">{t('progress', { done: data.completed_tasks.length, total: data.tasks.length })}</span>
          <span className="text-xs font-mono text-indigo-600 font-bold">{data.progress}%</span>
        </div>
        <div className="w-full h-2 bg-slate-100 rounded-full">
          <div className="h-2 bg-indigo-600 rounded-full transition-all" style={{ width: `${data.progress}%` }} />
        </div>
      </div>

      {/* Task list with details */}
      <div className="space-y-3">
        {data.tasks.map((task) => {
          const detail = TASK_DETAILS[task.id];
          return (
            <div
              key={task.id}
              className={`p-4 rounded-2xl border transition-all ${
                task.done
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-white border-slate-200 hover:border-indigo-200 hover:shadow-sm'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {task.done ? (
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                  ) : (
                    <Circle className="w-5 h-5 text-slate-300" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className={`text-sm font-bold ${task.done ? 'text-emerald-700' : 'text-slate-900'}`}>
                    {task.label}
                  </h3>
                  {detail && (
                    <p className={`text-xs mt-1 leading-relaxed ${task.done ? 'text-emerald-600' : 'text-slate-500'}`}>
                      {detail.desc}
                    </p>
                  )}
                  {!task.done && detail && (
                    <button
                      onClick={() => router.push(detail.href)}
                      className="mt-3 text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg inline-flex items-center gap-1.5 font-medium transition-all"
                    >
                      {t('goTo', { label: task.label })}
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  )}
                  {!task.done && (
                    <button
                      onClick={() => markMut.mutate(task.id)}
                      className="mt-3 ml-2 text-xs px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg inline-flex items-center gap-1.5 font-medium transition-all"
                    >
                      {t('markDone')}
                    </button>
                  )}
                </div>
                {task.done && (
                  <span className="text-[10px] px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full font-medium">
                    {t('completed')}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-2">
        <button
          onClick={() => dismissMut.mutate()}
          className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium rounded-xl text-sm transition-all"
        >
          {t('dismissAndGo')}
        </button>
        {data.all_completed && (
          <button
            onClick={() => router.push('/dashboard')}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-xl text-sm transition-all"
          >
            {t('goToDashboard')}
          </button>
        )}
      </div>
    </div>
  );
}
