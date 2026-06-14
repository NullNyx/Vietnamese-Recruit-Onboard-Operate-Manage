"use client";

import { Bot } from "lucide-react";
import { ChatInterface } from "@/components/assistant/chat-interface";
import { sendEmployeeChatMessage } from "@/lib/api/employee-assistant";

const EMPLOYEE_SUGGESTIONS = [
  "Xem profile của tôi",
  "Đăng ký nghỉ phép từ 15/07 đến 17/07",
  "Đăng ký tăng ca ngày 20/06 từ 18h đến 21h",
];

export function EmployeeChatArea() {
  return (
    <ChatInterface
      sendMessage={sendEmployeeChatMessage}
      title="Trợ lý AI Nhân viên"
      description="Hỏi tôi về thông tin cá nhân, chấm công, yêu cầu nghỉ phép và tăng ca."
      suggestions={EMPLOYEE_SUGGESTIONS}
      icon={<Bot className="h-8 w-8 text-primary" />}
    />
  );
}
