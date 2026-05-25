"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Clock,
  CalendarDays,
  Timer,
  TreePalm,
  LogIn,
  LogOut,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { essApi } from "@/lib/api";
import type { DashboardData, AttendanceStatus } from "@/lib/api/ess";

const attendanceStatusLabels: Record<AttendanceStatus, string> = {
  not_checked_in: "Chưa chấm công",
  checked_in: "Đã check-in",
  checked_out: "Đã check-out",
};

const attendanceStatusColors: Record<AttendanceStatus, string> = {
  not_checked_in: "text-yellow-600",
  checked_in: "text-green-600",
  checked_out: "text-blue-600",
};

export default function EmployeeDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDashboard = useCallback(async () => {
    try {
      setError(null);
      const result = await essApi.getDashboard();
      setData(result);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Không thể tải dữ liệu";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  async function handleCheckIn() {
    setActionLoading(true);
    try {
      await essApi.checkIn();
      toast.success("Check-in thành công!");
      await fetchDashboard();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Check-in thất bại";
      toast.error(message);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCheckOut() {
    setActionLoading(true);
    try {
      await essApi.checkOut();
      toast.success("Check-out thành công!");
      await fetchDashboard();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Check-out thất bại";
      toast.error(message);
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Tổng quan</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-24 mb-3" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-6 w-48 mb-4" />
            <Skeleton className="h-10 w-32" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Tổng quan</h1>
        <Card>
          <CardContent className="p-6">
            <p className="text-destructive">{error}</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => {
                setLoading(true);
                fetchDashboard();
              }}
            >
              Thử lại
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Tổng quan</h1>

      {/* Attendance status and action */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" aria-hidden="true" />
            Chấm công hôm nay
          </CardTitle>
          <CardDescription>
            Trạng thái:{" "}
            <span
              className={`font-medium ${attendanceStatusColors[data.today_attendance]}`}
            >
              {attendanceStatusLabels[data.today_attendance]}
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.today_attendance === "not_checked_in" && (
            <Button onClick={handleCheckIn} disabled={actionLoading}>
              {actionLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <LogIn className="h-4 w-4" aria-hidden="true" />
              )}
              Check-in
            </Button>
          )}
          {data.today_attendance === "checked_in" && (
            <Button
              onClick={handleCheckOut}
              disabled={actionLoading}
              variant="secondary"
            >
              {actionLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <LogOut className="h-4 w-4" aria-hidden="true" />
              )}
              Check-out
            </Button>
          )}
          {data.today_attendance === "checked_out" && (
            <p className="text-sm text-muted-foreground">
              Bạn đã hoàn thành chấm công hôm nay.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pending leave requests */}
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/20">
              <CalendarDays
                className="h-6 w-6 text-orange-600"
                aria-hidden="true"
              />
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Đơn nghỉ phép chờ duyệt
              </p>
              <p className="text-2xl font-bold">{data.pending_leave_count}</p>
            </div>
          </CardContent>
        </Card>

        {/* Pending overtime requests */}
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/20">
              <Timer className="h-6 w-6 text-purple-600" aria-hidden="true" />
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Yêu cầu tăng ca chờ duyệt
              </p>
              <p className="text-2xl font-bold">
                {data.pending_overtime_count}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Monthly attendance summary */}
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/20">
              <Clock className="h-6 w-6 text-green-600" aria-hidden="true" />
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Ngày làm việc (tháng này)
              </p>
              <p className="text-2xl font-bold">
                {data.monthly_summary.days_worked}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Annual leave remaining */}
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/20">
              <TreePalm className="h-6 w-6 text-blue-600" aria-hidden="true" />
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Phép năm còn lại</p>
              <p className="text-2xl font-bold">
                {data.annual_leave_remaining !== null
                  ? data.annual_leave_remaining
                  : "—"}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly summary detail */}
      <Card>
        <CardHeader>
          <CardTitle>Tổng hợp chấm công tháng này</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground">Ngày làm việc</p>
              <p className="text-3xl font-bold mt-1">
                {data.monthly_summary.days_worked}
              </p>
            </div>
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground">Ngày vắng</p>
              <p className="text-3xl font-bold mt-1">
                {data.monthly_summary.days_absent}
              </p>
            </div>
            <div className="text-center p-4 rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground">Tổng giờ làm</p>
              <p className="text-3xl font-bold mt-1">
                {data.monthly_summary.total_hours}h
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
