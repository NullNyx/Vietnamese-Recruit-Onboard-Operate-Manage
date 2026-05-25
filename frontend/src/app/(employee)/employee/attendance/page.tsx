"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Clock,
  LogIn,
  LogOut,
  CalendarDays,
  Timer,
  AlertTriangle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { essApi } from "@/lib/api";
import type {
  TodayAttendanceResponse,
  AttendanceHistoryRecord,
  AttendanceHistorySummary,
} from "@/lib/api/ess";

const statusColors: Record<string, string> = {
  present: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  late: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  early_leave:
    "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  absent: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  on_leave: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  holiday:
    "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
};

const statusLabels: Record<string, string> = {
  present: "Có mặt",
  late: "Đi muộn",
  early_leave: "Về sớm",
  absent: "Vắng mặt",
  on_leave: "Nghỉ phép",
  holiday: "Ngày lễ",
};

function formatTime(isoString: string | null): string {
  if (!isoString) return "—";
  const d = new Date(isoString);
  return d.toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Ho_Chi_Minh",
  });
}

function formatDate(dateString: string): string {
  const d = new Date(dateString);
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Ho_Chi_Minh",
  });
}

function formatHours(hours: number | null): string {
  if (hours === null || hours === undefined) return "—";
  return `${hours.toFixed(1)}h`;
}

export default function EmployeeAttendancePage() {
  const now = new Date();
  const [selectedMonth, setSelectedMonth] = useState(now.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(now.getFullYear());

  const [todayRecord, setTodayRecord] =
    useState<TodayAttendanceResponse | null>(null);
  const [todayLoading, setTodayLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [records, setRecords] = useState<AttendanceHistoryRecord[]>([]);
  const [summary, setSummary] = useState<AttendanceHistorySummary | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);

  const fetchToday = useCallback(async () => {
    setTodayLoading(true);
    try {
      const data = await essApi.getAttendanceToday();
      setTodayRecord(data);
    } catch {
      // If endpoint returns error, treat as no record
      setTodayRecord(null);
    } finally {
      setTodayLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await essApi.getAttendanceHistory(
        selectedMonth,
        selectedYear,
      );
      setRecords(data.records);
      setSummary(data.summary);
    } catch {
      setRecords([]);
      setSummary(null);
    } finally {
      setHistoryLoading(false);
    }
  }, [selectedMonth, selectedYear]);

  useEffect(() => {
    fetchToday();
  }, [fetchToday]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  async function handleCheckIn() {
    setActionLoading(true);
    setActionError(null);
    try {
      await essApi.checkIn();
      await fetchToday();
      // Refresh history if viewing current month
      if (
        selectedMonth === now.getMonth() + 1 &&
        selectedYear === now.getFullYear()
      ) {
        await fetchHistory();
      }
    } catch (err: unknown) {
      const error = err as Error & { statusCode?: number };
      if (error.statusCode === 409) {
        setActionError("Bạn đã chấm công vào ca hôm nay rồi.");
      } else {
        setActionError(error.message || "Không thể chấm công vào ca.");
      }
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCheckOut() {
    setActionLoading(true);
    setActionError(null);
    try {
      await essApi.checkOut();
      await fetchToday();
      if (
        selectedMonth === now.getMonth() + 1 &&
        selectedYear === now.getFullYear()
      ) {
        await fetchHistory();
      }
    } catch (err: unknown) {
      const error = err as Error & { statusCode?: number };
      if (error.statusCode === 409) {
        setActionError("Bạn đã chấm công ra ca hôm nay rồi.");
      } else {
        setActionError(error.message || "Không thể chấm công ra ca.");
      }
    } finally {
      setActionLoading(false);
    }
  }

  // Determine today's status for display
  const todayStatus: "not_checked_in" | "checked_in" | "checked_out" =
    !todayRecord
      ? "not_checked_in"
      : todayRecord.check_out
        ? "checked_out"
        : "checked_in";

  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const currentYear = now.getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Chấm công</h1>

      {/* Today's Status Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Trạng thái hôm nay
          </CardTitle>
        </CardHeader>
        <CardContent>
          {todayLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-10 w-32" />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Status display */}
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">
                  Trạng thái:
                </span>
                {todayStatus === "not_checked_in" && (
                  <Badge variant="secondary">Chưa vào ca</Badge>
                )}
                {todayStatus === "checked_in" && (
                  <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    Đã vào ca
                  </Badge>
                )}
                {todayStatus === "checked_out" && (
                  <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    Đã ra ca
                  </Badge>
                )}
              </div>

              {/* Time info */}
              {todayRecord && (
                <div className="flex gap-6 text-sm">
                  {todayRecord.check_in && (
                    <div>
                      <span className="text-muted-foreground">Giờ vào: </span>
                      <span className="font-medium">
                        {formatTime(todayRecord.check_in)}
                      </span>
                    </div>
                  )}
                  {todayRecord.check_out && (
                    <div>
                      <span className="text-muted-foreground">Giờ ra: </span>
                      <span className="font-medium">
                        {formatTime(todayRecord.check_out)}
                      </span>
                    </div>
                  )}
                  {todayRecord.work_hours !== null && (
                    <div>
                      <span className="text-muted-foreground">Giờ làm: </span>
                      <span className="font-medium">
                        {formatHours(todayRecord.work_hours)}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={handleCheckIn}
                  disabled={actionLoading || todayStatus !== "not_checked_in"}
                >
                  <LogIn className="h-4 w-4 mr-2" />
                  Vào ca
                </Button>
                <Button
                  variant="outline"
                  onClick={handleCheckOut}
                  disabled={actionLoading || todayStatus !== "checked_in"}
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Ra ca
                </Button>
              </div>

              {/* Error message */}
              {actionError && (
                <div className="flex items-center gap-2 text-sm text-destructive">
                  <AlertTriangle className="h-4 w-4" />
                  {actionError}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Monthly Summary Section */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Ngày công
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CalendarDays className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold">
                  {summary.total_work_days}
                </span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Tổng giờ làm
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-500" />
                <span className="text-2xl font-bold">
                  {summary.total_work_hours.toFixed(1)}
                </span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Giờ tăng ca
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Timer className="h-5 w-5 text-purple-500" />
                <span className="text-2xl font-bold">
                  {summary.total_overtime_hours.toFixed(1)}
                </span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Đi muộn
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold text-yellow-600">
                {summary.late_count}
              </span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Về sớm
              </CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-2xl font-bold text-orange-600">
                {summary.early_departure_count}
              </span>
            </CardContent>
          </Card>
        </div>
      )}

      {/* History Section */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="flex items-center gap-2">
              <CalendarDays className="h-5 w-5" />
              Lịch sử chấm công
            </CardTitle>
            <div className="flex items-center gap-2">
              <Select
                value={String(selectedMonth)}
                onValueChange={(v) => setSelectedMonth(Number(v))}
              >
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Tháng" />
                </SelectTrigger>
                <SelectContent>
                  {months.map((m) => (
                    <SelectItem key={m} value={String(m)}>
                      Tháng {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={String(selectedYear)}
                onValueChange={(v) => setSelectedYear(Number(v))}
              >
                <SelectTrigger className="w-[100px]">
                  <SelectValue placeholder="Năm" />
                </SelectTrigger>
                <SelectContent>
                  {years.map((y) => (
                    <SelectItem key={y} value={String(y)}>
                      {y}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : records.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              Không có dữ liệu chấm công cho tháng {selectedMonth}/
              {selectedYear}.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ngày</TableHead>
                    <TableHead>Giờ vào</TableHead>
                    <TableHead>Giờ ra</TableHead>
                    <TableHead>Giờ làm</TableHead>
                    <TableHead>Tăng ca</TableHead>
                    <TableHead>Trạng thái</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.map((rec) => (
                    <TableRow key={rec.id}>
                      <TableCell className="font-medium">
                        {formatDate(rec.work_date)}
                      </TableCell>
                      <TableCell>{formatTime(rec.check_in)}</TableCell>
                      <TableCell>{formatTime(rec.check_out)}</TableCell>
                      <TableCell>{formatHours(rec.work_hours)}</TableCell>
                      <TableCell>
                        {rec.overtime_hours > 0
                          ? formatHours(rec.overtime_hours)
                          : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[rec.status] || ""}>
                          {statusLabels[rec.status] || rec.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
