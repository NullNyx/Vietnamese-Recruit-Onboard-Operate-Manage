'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Filter, RefreshCw, Loader2, Paperclip } from 'lucide-react';
import type { EmailMessage } from '@/lib/api/types';
import EmptyState from './empty-state';
import { apiErrorText } from './helpers';

interface MessageListProps {
  category: string;
  onCategoryChange: (cat: string) => void;
  categories: string[];
  messages: EmailMessage[];
  total: number;
  isLoading: boolean;
  isFetching: boolean;
  error: unknown;
  selectedId: string | null;
  onSelect: (id: string) => void;
  page: number;
  pageSize: number;
  hasMore: boolean;
  onNextPage: () => void;
  onRefetch: () => void;
  onAttachmentsReset: () => void;
}

export default function MessageList({
  category,
  onCategoryChange,
  categories,
  messages,
  total,
  isLoading,
  isFetching,
  error,
  selectedId,
  onSelect,
  page,
  pageSize,
  hasMore,
  onNextPage,
  onRefetch,
  onAttachmentsReset,
}: MessageListProps) {
  const t = useTranslations('gmail');
  return (
    <div className="lg:col-span-1 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-2">
        <Filter className="w-3.5 h-3.5 text-slate-400" />
        <select
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="text-xs bg-transparent border-none focus:outline-none text-slate-600"
        >
          <option value="">{t('allCategories')}</option>
          {categories.map((c) => (<option key={c} value={c}>{c}</option>))}
        </select>
        <button onClick={onRefetch} className="ml-auto p-1 rounded hover:bg-slate-100 text-slate-400">
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <div className="max-h-[60vh] overflow-y-auto">
        {isLoading ? (
          <div className="p-6 text-center"><Loader2 className="w-5 h-5 animate-spin text-slate-300 mx-auto" /></div>
        ) : error ? (
          <div className="p-4 text-xs text-rose-500">{t('loadError', { error: apiErrorText(error) })}</div>
        ) : messages.length === 0 ? (
          <EmptyState
            title={category ? t('emptyFilterTitle') : t('emptyInboxTitle')}
            hint={category ? t('emptyFilterHint') : t('emptyInboxHint')}
          />
        ) : (
          <>
            {messages.map((m) => (
              <button
                key={m.id}
                onClick={() => { onSelect(m.id); onAttachmentsReset(); }}
                className={`w-full text-left px-3 py-2.5 border-b border-slate-50 hover:bg-slate-50 transition-colors ${selectedId === m.id ? 'bg-indigo-50' : ''}`}
              >
                <div className="flex items-center gap-2">
                  {m.category && <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600">{m.category}</span>}
                  {m.has_attachments && <Paperclip className="w-3 h-3 text-slate-400" />}
                  <span className="text-xs font-medium text-slate-700 truncate flex-1">{m.subject || t('noSubject')}</span>
                </div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">{m.sender_email}</div>
              </button>
            ))}
            {/* Pagination */}
            {hasMore && (
              <div className="px-3 py-2 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={onNextPage}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
                >
                  {t('loadMore')}
                </button>
                <span className="text-[10px] text-slate-400">
                  {messages.length + (page - 1) * pageSize} / {total}
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
