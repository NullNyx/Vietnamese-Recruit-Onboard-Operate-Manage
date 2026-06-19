"use client";

import { useEffect, useState, useRef } from "react";
import { EmployeeChatArea } from "./employee-chat-area";
import { CreateRequestDialog } from "../requests/create-request-dialog";
import type {
  CreateRequestDialogRef,
  LeaveFormState,
  OvertimeFormState,
} from "../requests/create-request-dialog";

export function EmployeeAssistantClient() {
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
    <>
      <EmployeeChatArea onOpenRequestDialog={handleOpenRequestDialog} />
      <CreateRequestDialog
        ref={dialogRef}
        defaultValues={prefillData || undefined}
        onSuccess={() => setPrefillData(null)}
      />
    </>
  );
}
