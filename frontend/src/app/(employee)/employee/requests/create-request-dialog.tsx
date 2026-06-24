"use client";

import { useEffect, useState, useImperativeHandle, forwardRef, useRef, type ReactElement } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, Clock, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  createLeave,
  createOvertime,
} from "@/lib/api/employee-requests";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface LeaveFormState {
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string;
}

export interface OvertimeFormState {
  work_date: string;
  start_time: string;
  end_time: string;
  reason: string;
  project_or_task: string;
}

export interface CreateRequestDialogProps {
  /** Initial values to prefill the form (for AI Assistant draft handoff) */
  defaultValues?: {
    leave?: Partial<LeaveFormState>;
    overtime?: Partial<OvertimeFormState>;
    /** Force a specific tab on open */
    initialTab?: "leave" | "overtime";
  };
  /** Callback when a request is successfully created */
  onSuccess?: () => void;
  /** Custom trigger button (defaults to standard button if not provided) */
  trigger?: ReactElement;
}

// ---------------------------------------------------------------------------
// Initial states
// ---------------------------------------------------------------------------

const INITIAL_LEAVE: LeaveFormState = {
  leave_type: "",
  start_date: "",
  end_date: "",
  reason: "",
};

const INITIAL_OVERTIME: OvertimeFormState = {
  work_date: "",
  start_time: "",
  end_time: "",
  reason: "",
  project_or_task: "",
};

const LEAVE_TYPE_OPTIONS = [
  { value: "annual", label: "Nghỉ phép năm" },
  { value: "sick", label: "Nghỉ bệnh" },
  { value: "unpaid", label: "Nghỉ không lương" },
  { value: "other", label: "Khác" },
];

// ---------------------------------------------------------------------------
// Leave form
// ---------------------------------------------------------------------------

function LeaveForm({
  form,
  onChange,
  errors,
}: {
  form: LeaveFormState;
  onChange: (updates: Partial<LeaveFormState>) => void;
  errors: Partial<Record<keyof LeaveFormState, string>>;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="text-[13px] font-medium text-[#f7f8f8]">
          Loại nghỉ phép <span className="text-red-500">*</span>
        </label>
        <Select
          value={form.leave_type}
          onValueChange={(v) => onChange({ leave_type: v })}
        >
          <SelectTrigger
            className={errors.leave_type ? "border-red-500/50" : ""}
          >
            <SelectValue placeholder="Chọn loại nghỉ phép" />
          </SelectTrigger>
          <SelectContent>
            {LEAVE_TYPE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.leave_type && (
          <p className="text-[12px] text-red-400">{errors.leave_type}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-[13px] font-medium text-[#f7f8f8]">
            Ngày bắt đầu <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={form.start_date}
            onChange={(e) => onChange({ start_date: e.target.value })}
            className={`flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.start_date ? "border-red-500/50" : "border-input"}`}
          />
          {errors.start_date && (
            <p className="text-[12px] text-red-400">{errors.start_date}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-[13px] font-medium text-[#f7f8f8]">
            Ngày kết thúc <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={form.end_date}
            onChange={(e) => onChange({ end_date: e.target.value })}
            className={`flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.end_date ? "border-red-500/50" : "border-input"}`}
          />
          {errors.end_date && (
            <p className="text-[12px] text-red-400">{errors.end_date}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-[13px] font-medium text-[#f7f8f8]">
          Lý do <span className="text-red-500">*</span>
        </label>
        <textarea
          value={form.reason}
          onChange={(e) => onChange({ reason: e.target.value })}
          placeholder="Nhập lý do nghỉ phép..."
          rows={3}
          className={`flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none ${errors.reason ? "border-red-500/50" : "border-input"}`}
        />
        {errors.reason && (
          <p className="text-[12px] text-red-400">{errors.reason}</p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Overtime form
// ---------------------------------------------------------------------------

function OvertimeForm({
  form,
  onChange,
  errors,
}: {
  form: OvertimeFormState;
  onChange: (updates: Partial<OvertimeFormState>) => void;
  errors: Partial<Record<keyof OvertimeFormState, string>>;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="text-[13px] font-medium text-[#f7f8f8]">
          Ngày làm việc <span className="text-red-500">*</span>
        </label>
        <input
          type="date"
          value={form.work_date}
          onChange={(e) => onChange({ work_date: e.target.value })}
          className={`flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.work_date ? "border-red-500/50" : "border-input"}`}
        />
        {errors.work_date && (
          <p className="text-[12px] text-red-400">{errors.work_date}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-[13px] font-medium text-[#f7f8f8]">
            Giờ bắt đầu <span className="text-red-500">*</span>
          </label>
          <input
            type="time"
            value={form.start_time}
            onChange={(e) => onChange({ start_time: e.target.value })}
            className={`flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.start_time ? "border-red-500/50" : "border-input"}`}
          />
          {errors.start_time && (
            <p className="text-[12px] text-red-400">{errors.start_time}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-[13px] font-medium text-[#f7f8f8]">
            Giờ kết thúc <span className="text-red-500">*</span>
          </label>
          <input
            type="time"
            value={form.end_time}
            onChange={(e) => onChange({ end_time: e.target.value })}
            className={`flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${errors.end_time ? "border-red-500/50" : "border-input"}`}
          />
          {errors.end_time && (
            <p className="text-[12px] text-red-400">{errors.end_time}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-[13px] font-medium text-[#f7f8f8]">
          Lý do <span className="text-red-500">*</span>
        </label>
        <textarea
          value={form.reason}
          onChange={(e) => onChange({ reason: e.target.value })}
          placeholder="Nhập lý do tăng ca..."
          rows={2}
          className={`flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none ${errors.reason ? "border-red-500/50" : "border-input"}`}
        />
        {errors.reason && (
          <p className="text-[12px] text-red-400">{errors.reason}</p>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-[13px] font-medium text-[#f7f8f8]">Dự án / Công việc</label>
        <input
          type="text"
          value={form.project_or_task}
          onChange={(e) => onChange({ project_or_task: e.target.value })}
          placeholder="Nhập tên dự án (nếu có)..."
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dialog component
// ---------------------------------------------------------------------------

export interface CreateRequestDialogRef {
  open: () => void;
  close: () => void;
}

export const CreateRequestDialog = forwardRef<CreateRequestDialogRef, CreateRequestDialogProps>(
  function CreateRequestDialog({ defaultValues, onSuccess, trigger }, ref) {
    const [open, setOpen] = useState(false);
    const [requestType, setRequestType] = useState<"leave" | "overtime">(
      defaultValues?.initialTab || "leave",
    );
    const [leaveForm, setLeaveForm] = useState<LeaveFormState>(INITIAL_LEAVE);
    const [overtimeForm, setOvertimeForm] = useState<OvertimeFormState>(INITIAL_OVERTIME);
    const [leaveErrors, setLeaveErrors] = useState<Partial<Record<keyof LeaveFormState, string>>>({});
    const [overtimeErrors, setOvertimeErrors] = useState<Partial<Record<keyof OvertimeFormState, string>>>({});
    const queryClient = useQueryClient();

    // Expose open/close methods
    useImperativeHandle(ref, () => ({
      open: () => {
        appliedRef.current = false;
        setOpen(true);
      },
      close: () => {
        setOpen(false);
        resetForms();
      },
    }));

    // Apply default values when dialog opens with prefill data
    const appliedRef = useRef(false);

    useEffect(() => {
      if (open && defaultValues && !appliedRef.current) {
        appliedRef.current = true;
        if (defaultValues.initialTab) {
          setRequestType(defaultValues.initialTab);
        }
        if (defaultValues.leave) {
          setLeaveForm((prev) => ({ ...prev, ...defaultValues.leave }));
        }
        if (defaultValues.overtime) {
          setOvertimeForm((prev) => ({ ...prev, ...defaultValues.overtime }));
        }
      }
    }, [open, defaultValues]);

    const resetForms = () => {
      setLeaveForm(INITIAL_LEAVE);
      setOvertimeForm(INITIAL_OVERTIME);
      setLeaveErrors({});
      setOvertimeErrors({});
      appliedRef.current = false;
    };

    const leaveMutation = useMutation({
      mutationFn: createLeave,
      onSuccess: () => {
        toast.success("Đã gửi đơn nghỉ phép thành công");
        queryClient.invalidateQueries({ queryKey: ["employee-requests"] });
        onSuccess?.();
        setOpen(false);
        resetForms();
      },
      onError: (err: Error) => {
        toast.error(err.message || "Gửi đơn thất bại");
      },
    });

    const overtimeMutation = useMutation({
      mutationFn: createOvertime,
      onSuccess: () => {
        toast.success("Đã gửi đơn tăng ca thành công");
        queryClient.invalidateQueries({ queryKey: ["employee-requests"] });
        onSuccess?.();
        setOpen(false);
        resetForms();
      },
      onError: (err: Error) => {
        toast.error(err.message || "Gửi đơn thất bại");
      },
    });

    // -- Validation helpers --
    function validateLeave(): boolean {
      const errors: Partial<Record<keyof LeaveFormState, string>> = {};
      if (!leaveForm.leave_type) errors.leave_type = "Vui lòng chọn loại nghỉ phép";
      if (!leaveForm.start_date) errors.start_date = "Vui lòng chọn ngày bắt đầu";
      if (!leaveForm.end_date) errors.end_date = "Vui lòng chọn ngày kết thúc";
      if (leaveForm.start_date && leaveForm.end_date && leaveForm.end_date < leaveForm.start_date)
        errors.end_date = "Ngày kết thúc phải sau ngày bắt đầu";
      if (!leaveForm.reason.trim()) errors.reason = "Vui lòng nhập lý do";
      setLeaveErrors(errors);
      return Object.keys(errors).length === 0;
    }

    function validateOvertime(): boolean {
      const errors: Partial<Record<keyof OvertimeFormState, string>> = {};
      if (!overtimeForm.work_date) errors.work_date = "Vui lòng chọn ngày";
      if (!overtimeForm.start_time) errors.start_time = "Vui lòng chọn giờ bắt đầu";
      if (!overtimeForm.end_time) errors.end_time = "Vui lòng chọn giờ kết thúc";
      if (overtimeForm.start_time && overtimeForm.end_time && overtimeForm.end_time <= overtimeForm.start_time)
        errors.end_time = "Giờ kết thúc phải sau giờ bắt đầu";
      if (!overtimeForm.reason.trim()) errors.reason = "Vui lòng nhập lý do";
      setOvertimeErrors(errors);
      return Object.keys(errors).length === 0;
    }

    // -- Submit handlers --
    async function handleSubmitLeave() {
      if (!validateLeave()) return;
      leaveMutation.mutate({
        leave_type: leaveForm.leave_type as "annual" | "sick" | "unpaid" | "other",
        start_date: leaveForm.start_date,
        end_date: leaveForm.end_date,
        reason: leaveForm.reason.trim(),
      });
    }

    async function handleSubmitOvertime() {
      if (!validateOvertime()) return;
      overtimeMutation.mutate({
        work_date: overtimeForm.work_date,
        start_time: overtimeForm.start_time,
        end_time: overtimeForm.end_time,
        reason: overtimeForm.reason.trim(),
        project_or_task: overtimeForm.project_or_task.trim() || null,
      });
    }

    const isPending = leaveMutation.isPending || overtimeMutation.isPending;

    const TriggerComponent = trigger || (
      <Button>
        <Plus className="h-4 w-4" />
        Tạo yêu cầu
      </Button>
    );

    return (
      <Dialog
        open={open}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) resetForms();
        }}
      >
        <DialogTrigger asChild>
          {TriggerComponent}
        </DialogTrigger>

        <DialogContent className="sm:max-w-[520px]">
          <DialogHeader>
            <DialogTitle>Tạo yêu cầu mới</DialogTitle>
            <DialogDescription>
              Chọn loại yêu cầu và điền thông tin bên dưới.
            </DialogDescription>
          </DialogHeader>

          <Tabs value={requestType} onValueChange={(v) => setRequestType(v as "leave" | "overtime")}>
            <TabsList className="w-full">
              <TabsTrigger value="leave" className="flex-1">
                <CalendarDays className="mr-1.5 h-4 w-4" />
                Nghỉ phép
              </TabsTrigger>
              <TabsTrigger value="overtime" className="flex-1">
                <Clock className="mr-1.5 h-4 w-4" />
                Tăng ca
              </TabsTrigger>
            </TabsList>

            <TabsContent value="leave" className="mt-4">
              <LeaveForm
                form={leaveForm}
                onChange={(u) => setLeaveForm((p) => ({ ...p, ...u }))}
                errors={leaveErrors}
              />
            </TabsContent>

            <TabsContent value="overtime" className="mt-4">
              <OvertimeForm
                form={overtimeForm}
                onChange={(u) => setOvertimeForm((p) => ({ ...p, ...u }))}
                errors={overtimeErrors}
              />
            </TabsContent>
          </Tabs>

          <div className="flex justify-end gap-3 pt-2">
            <DialogClose asChild>
              <Button variant="outline" disabled={isPending}>
                Huỷ
              </Button>
            </DialogClose>
            <Button
              onClick={requestType === "leave" ? handleSubmitLeave : handleSubmitOvertime}
              disabled={isPending}
            >
              {isPending && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
              {isPending ? "Đang gửi..." : "Gửi yêu cầu"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  },
);
