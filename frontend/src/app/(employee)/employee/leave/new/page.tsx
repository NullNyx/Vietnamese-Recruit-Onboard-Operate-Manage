"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, CalendarDays, Info } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { essApi } from "@/lib/api";
import type { LeaveBalance } from "@/lib/api/ess";

function getTodayString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function calculateTotalDays(start: string, end: string): number {
  if (!start || !end) return 0;
  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffTime = endDate.getTime() - startDate.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
  return diffDays > 0 ? diffDays : 0;
}

export default function NewLeaveRequestPage() {
  const router = useRouter();
  const today = getTodayString();

  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [balancesLoading, setBalancesLoading] = useState(true);

  const [leaveTypeId, setLeaveTypeId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validation state
  const [dateError, setDateError] = useState<string | null>(null);

  useEffect(() => {
    async function loadBalances() {
      setBalancesLoading(true);
      try {
        const data = await essApi.getLeaveBalances();
        setBalances(data);
      } catch {
        setBalances([]);
      } finally {
        setBalancesLoading(false);
      }
    }
    loadBalances();
  }, []);

  // Find selected balance
  const selectedBalance = useMemo(() => {
    if (!leaveTypeId) return null;
    return balances.find((b) => b.leave_type_id === leaveTypeId) || null;
  }, [leaveTypeId, balances]);

  // Calculate total days
  const totalDays = useMemo(
    () => calculateTotalDays(startDate, endDate),
    [startDate, endDate],
  );

  // Validate dates
  useEffect(() => {
    setDateError(null);

    if (startDate && startDate < today) {
      setDateError("Ngày bắt đầu không được trong quá khứ");
      return;
    }

    if (startDate && endDate && endDate < startDate) {
      setDateError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu");
      return;
    }
  }, [startDate, endDate, today]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Validate required fields
    if (!leaveTypeId) {
      setError("Vui lòng chọn loại phép");
      return;
    }
    if (!startDate) {
      setError("Vui lòng chọn ngày bắt đầu");
      return;
    }
    if (!endDate) {
      setError("Vui lòng chọn ngày kết thúc");
      return;
    }

    // Validate dates
    if (startDate < today) {
      setError("Ngày bắt đầu không được trong quá khứ");
      return;
    }
    if (endDate < startDate) {
      setError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu");
      return;
    }

    // Validate reason length
    if (reason.length > 500) {
      setError("Lý do không được vượt quá 500 ký tự");
      return;
    }

    setSubmitting(true);
    try {
      await essApi.createLeaveRequest({
        leave_type_id: leaveTypeId,
        start_date: startDate,
        end_date: endDate,
        reason: reason || undefined,
      });
      toast.success("Tạo đơn nghỉ phép thành công");
      router.push("/employee/leave");
    } catch (err: unknown) {
      const apiError = err as Error & {
        statusCode?: number;
        errorCode?: string;
      };
      if (apiError.errorCode === "INSUFFICIENT_LEAVE_BALANCE") {
        setError(
          `Số ngày phép còn lại không đủ. Còn lại: ${selectedBalance?.remaining_days ?? 0} ngày`,
        );
      } else {
        setError(apiError.message || "Không thể tạo đơn nghỉ phép");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/employee/leave")}
          aria-label="Quay lại"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">Tạo đơn nghỉ phép</h1>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5" />
            Thông tin đơn nghỉ
          </CardTitle>
        </CardHeader>
        <CardContent>
          {balancesLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Leave Type Selector */}
              <div className="space-y-2">
                <Label htmlFor="leaveType">Loại phép *</Label>
                <Select value={leaveTypeId} onValueChange={setLeaveTypeId}>
                  <SelectTrigger id="leaveType">
                    <SelectValue placeholder="Chọn loại phép" />
                  </SelectTrigger>
                  <SelectContent>
                    {balances.map((balance) => (
                      <SelectItem
                        key={balance.leave_type_id}
                        value={balance.leave_type_id}
                      >
                        {balance.leave_type_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Show remaining balance for selected type */}
                {selectedBalance && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                    <Info className="h-4 w-4" />
                    <span>
                      Số ngày còn lại:{" "}
                      <span className="font-medium text-foreground">
                        {selectedBalance.remaining_days}
                      </span>{" "}
                      / {selectedBalance.total_days} ngày
                    </span>
                  </div>
                )}
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="startDate">Ngày bắt đầu *</Label>
                  <Input
                    id="startDate"
                    type="date"
                    min={today}
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="endDate">Ngày kết thúc *</Label>
                  <Input
                    id="endDate"
                    type="date"
                    min={startDate || today}
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>
              </div>

              {/* Date validation error */}
              {dateError && (
                <p className="text-sm text-destructive">{dateError}</p>
              )}

              {/* Total days display */}
              {totalDays > 0 && !dateError && (
                <div className="flex items-center gap-2 text-sm">
                  <CalendarDays className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    Tổng số ngày nghỉ:{" "}
                    <span className="font-medium text-foreground">
                      {totalDays} ngày
                    </span>
                  </span>
                </div>
              )}

              {/* Reason */}
              <div className="space-y-2">
                <Label htmlFor="reason">
                  Lý do{" "}
                  <span className="text-muted-foreground font-normal">
                    (không bắt buộc, tối đa 500 ký tự)
                  </span>
                </Label>
                <Textarea
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Nhập lý do nghỉ phép..."
                  rows={3}
                  maxLength={500}
                />
                <p className="text-xs text-muted-foreground text-right">
                  {reason.length}/500
                </p>
              </div>

              {/* Error message */}
              {error && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button type="submit" disabled={submitting || !!dateError}>
                  {submitting ? "Đang gửi..." : "Gửi đơn"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push("/employee/leave")}
                >
                  Hủy
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
