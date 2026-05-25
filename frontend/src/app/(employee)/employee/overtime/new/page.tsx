"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Clock } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { essApi } from "@/lib/api";

function getTodayString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

interface FormErrors {
  work_date?: string;
  planned_hours?: string;
  reason?: string;
}

export default function NewOvertimeRequestPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const [workDate, setWorkDate] = useState("");
  const [plannedHours, setPlannedHours] = useState("");
  const [reason, setReason] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});

  function validate(): boolean {
    const newErrors: FormErrors = {};
    const today = getTodayString();

    // Validate work_date
    if (!workDate) {
      newErrors.work_date = "Vui lòng chọn ngày làm việc";
    } else if (workDate < today) {
      newErrors.work_date = "Ngày làm việc không được trong quá khứ";
    }

    // Validate planned_hours
    const hours = parseFloat(plannedHours);
    if (!plannedHours) {
      newErrors.planned_hours = "Vui lòng nhập số giờ dự kiến";
    } else if (isNaN(hours)) {
      newErrors.planned_hours = "Số giờ không hợp lệ";
    } else if (hours < 0.5 || hours > 4.0) {
      newErrors.planned_hours = "Số giờ phải từ 0.5 đến 4.0";
    }

    // Validate reason
    if (!reason.trim()) {
      newErrors.reason = "Vui lòng nhập lý do tăng ca";
    } else if (reason.length > 500) {
      newErrors.reason = "Lý do không được vượt quá 500 ký tự";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      await essApi.createOvertimeRequest({
        work_date: workDate,
        planned_hours: parseFloat(plannedHours),
        reason: reason.trim(),
      });
      toast.success("Tạo yêu cầu tăng ca thành công");
      router.push("/employee/overtime");
    } catch (err: unknown) {
      const error = err as Error;
      toast.error(error.message || "Không thể tạo yêu cầu tăng ca");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/employee/overtime")}
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
          Tạo yêu cầu tăng ca
        </h1>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Thông tin yêu cầu tăng ca
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="work_date">Ngày làm việc *</Label>
              <Input
                id="work_date"
                type="date"
                min={getTodayString()}
                value={workDate}
                onChange={(e) => {
                  setWorkDate(e.target.value);
                  if (errors.work_date) {
                    setErrors((prev) => ({ ...prev, work_date: undefined }));
                  }
                }}
                aria-invalid={!!errors.work_date}
                aria-describedby={
                  errors.work_date ? "work_date-error" : undefined
                }
              />
              {errors.work_date && (
                <p
                  id="work_date-error"
                  className="text-sm text-destructive"
                  role="alert"
                >
                  {errors.work_date}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="planned_hours">Số giờ dự kiến *</Label>
              <Input
                id="planned_hours"
                type="number"
                min={0.5}
                max={4.0}
                step={0.5}
                placeholder="Ví dụ: 1.5"
                value={plannedHours}
                onChange={(e) => {
                  setPlannedHours(e.target.value);
                  if (errors.planned_hours) {
                    setErrors((prev) => ({
                      ...prev,
                      planned_hours: undefined,
                    }));
                  }
                }}
                aria-invalid={!!errors.planned_hours}
                aria-describedby={
                  errors.planned_hours ? "planned_hours-error" : undefined
                }
              />
              <p className="text-xs text-muted-foreground">
                Từ 0.5 đến 4.0 giờ (bước 0.5 giờ)
              </p>
              {errors.planned_hours && (
                <p
                  id="planned_hours-error"
                  className="text-sm text-destructive"
                  role="alert"
                >
                  {errors.planned_hours}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="reason">Lý do tăng ca *</Label>
              <Textarea
                id="reason"
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  if (errors.reason) {
                    setErrors((prev) => ({ ...prev, reason: undefined }));
                  }
                }}
                placeholder="Nhập lý do yêu cầu tăng ca..."
                rows={4}
                maxLength={500}
                aria-invalid={!!errors.reason}
                aria-describedby={errors.reason ? "reason-error" : undefined}
              />
              <p className="text-xs text-muted-foreground">
                {reason.length}/500 ký tự
              </p>
              {errors.reason && (
                <p
                  id="reason-error"
                  className="text-sm text-destructive"
                  role="alert"
                >
                  {errors.reason}
                </p>
              )}
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {loading ? "Đang gửi..." : "Gửi yêu cầu"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/employee/overtime")}
                disabled={loading}
              >
                Hủy
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
