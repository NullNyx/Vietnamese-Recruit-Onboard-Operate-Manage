"use client";

import { useEffect, useState, useRef } from "react";
import { EmployeeChatArea } from "./employee-chat-area";
import { CreateRequestDialog } from "../requests/create-request-dialog";
import type {
  CreateRequestDialogRef,
  LeaveFormState,
  OvertimeFormState,
} from "../requests/create-request-dialog";

export const metadata = {
  title: "Trợ lý AI | Vroom HR",
  description: "AI Assistant for employees — view your data and draft requests",
};

export default function AssistantPage() {
  const dialogRef = useRef<CreateRequestDialogRef>(null);
  const [prefillData, setPrefillData] = useState<{
    leave?: Partial<LeaveFormState>;
    overtime?: Partial<OvertimeFormState>;
    initialTab?: "leave" | "overtime";
  } | null>(null);

  useEffect(() => {
    if (prefillData && dialogRef.current) {
      dialogRef.current.open();
    }
  }, [prefillData]);

  const handleOpenRequestDialog = (values: {
    leave?: Record<string, string>;
    overtime?: Record<string, string>;
  }) => {
    if (values.leave) {
      setPrefillData({
        leave: {
          leave_type: values.leave.leave_type || "",
          start_date: values.leave.start_date || "",
          end_date: values.leave.end_date || "",
          reason: values.leave.reason || "",
        },
        initialTab: "leave",
      });
    } else if (values.overtime) {
      setPrefillData({
        overtime: {
          work_date: values.overtime.work_date || "",
          start_time: values.overtime.start_time || "",
          end_time: values.overtime.end_time || "",
          reason: values.overtime.reason || "",
          project_or_task: values.overtime.project_or_task || "",
        },
        initialTab: "overtime",
      });
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Trợ lý AI</h1>
        <p className="text-muted-foreground">
          Hỏi về thông tin cá nhân, chấm công, yêu cầu nghỉ phép / tăng ca
        </p>
      </div>
      <EmployeeChatArea onOpenRequestDialog={handleOpenRequestDialog} />
      <CreateRequestDialog
        ref={dialogRef}
        defaultValues={prefillData || undefined}
        onSuccess={() => setPrefillData(null)}
      />
    </div>
  );
}
