'use client';

import AiChat from '@/components/AiChat';
import type { AiChatApi } from '@/components/AiChat';
import {
  sendChatMessage,
  sendStreamMessage,
  startSession,
  endSession,
  sendFeedback,
  confirmDraftAction,
  recordDraftDecision,
} from '@/lib/api/assistant';
import { useAuthGuard } from '@/lib/auth/session';
import { Sparkles } from 'lucide-react';

/**
 * HR AI Assistant page.
 *
 * The LLM only reads data or returns a Draft Action. Confirming a draft fires
 * the real write endpoint directly (e.g. create interview / accept candidate),
 * never through the LLM — human-in-the-loop (ADR-0006).
 */
const hrAssistantApi: AiChatApi = {
  sendMessage: sendChatMessage,
  sendStreamMessage,
  confirmAction: confirmDraftAction,
  startSession,
  endSession,
  sendFeedback,
  recordDecision: recordDraftDecision,
};

export default function HRAssistantPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });

  return (
    <div className="space-y-4 h-full">
      <div className="flex items-center gap-2 text-indigo-600">
        <Sparkles className="w-5 h-5" />
        <h1 className="text-xl font-bold text-slate-900">Trợ lý AI (HR)</h1>
      </div>
      <p className="text-sm text-slate-500 -mt-2">
        Đọc dữ liệu tuyển dụng/onboarding và soạn nháp action. Mọi ghi dữ liệu do HR xác nhận.
      </p>

      <div className="h-[calc(100vh-13rem)]">
        <AiChat assistantType="hr" api={hrAssistantApi} className="h-full" />
      </div>
    </div>
  );
}