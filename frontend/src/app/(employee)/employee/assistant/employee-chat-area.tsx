"use client";

import { Bot } from "lucide-react";
import { ChatInterface } from "@/components/assistant/chat-interface";
import {
  sendEmployeeChatMessage,
  confirmEmployeeDraftAction,
} from "@/lib/api/employee-assistant";

interface EmployeeChatAreaProps {
  /** Callback when user wants to open the request dialog with prefill */
  onOpenRequestDialog?: (values: {
    leave?: Partial<import("@/app/(employee)/employee/requests/create-request-dialog").LeaveFormState>;
    overtime?: Partial<import("@/app/(employee)/employee/requests/create-request-dialog").OvertimeFormState>;
  }) => void;
}

const EMPLOYEE_SUGGESTIONS = [
  "Xem profile của tôi",
  "Soạn nháp nghỉ phép từ 15/07 đến 17/07",
  "Soạn nháp tăng ca ngày 20/06 từ 18h đến 21h",
];

export function EmployeeChatArea({ onOpenRequestDialog }: EmployeeChatAreaProps) {
  return (
    <ChatInterface
      sendMessage={sendEmployeeChatMessage}
      confirmAction={confirmEmployeeDraftAction}
      title="Trợ lý AI Nhân viên"
      description="Hỏi tôi về thông tin cá nhân, chấm công, yêu cầu nghỉ phép và tăng ca."
      suggestions={EMPLOYEE_SUGGESTIONS}
      icon={<Bot className="h-8 w-8 text-primary" />}
      onOpenRequestDialog={onOpenRequestDialog}
    />
  );
}
