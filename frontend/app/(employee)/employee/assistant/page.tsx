'use client';

import AiChat from '@/components/AiChat';
import type { AiChatApi } from '@/components/AiChat';
import {
  sendEmployeeChatMessage,
  startEmployeeSession,
  endEmployeeSession,
  sendEmployeeFeedback,
  confirmEmployeeDraftAction,
} from '@/lib/api/employee-assistant';
import { useAuthGuard } from '@/lib/auth/session';
import { Sparkles } from 'lucide-react';

/**
 * Employee AI Assistant (ESS) page.
 *
 * employee_id is taken from the session on the backend — never from the LLM.
 * The assistant only READs the employee's own data and DRAFTs the employee's
 * own requests (leave / overtime). Confirming a draft fires the real
 * `/api/employee-requests/me/*` write endpoint directly (the employee is the
 * human-in-the-loop). The LLM never writes.
 */
const employeeAssistantApi: AiChatApi = {
  sendMessage: sendEmployeeChatMessage,
  confirmAction: confirmEmployeeDraftAction,
  startSession: startEmployeeSession,
  endSession: endEmployeeSession,
  sendFeedback: sendEmployeeFeedback,
  // ESS assistant has no separate decision-audit endpoint; recordDecision unused.
};

export default function EmployeeAssistantPage() {
  useAuthGuard({ requireAuth: true, requireEmployee: true });

  return (
    <div className="space-y-4 h-full">
      <div className="flex items-center gap-2 text-indigo-600">
        <Sparkles className="w-5 h-5" />
        <h1 className="text-xl font-bold text-slate-900">Trợ lý Nhân viên (ESS)</h1>
      </div>
      <p className="text-sm text-slate-500 -mt-2">
        Trợ lý chỉ đọc dữ liệu cá nhân của bạn và soạn nháp yêu cầu của chính bạn. Bạn xác nhận trước khi ghi.
      </p>

      <div className="h-[calc(100vh-13rem)]">
        <AiChat assistantType="employee" api={employeeAssistantApi} className="h-full" />
      </div>
    </div>
  );
}