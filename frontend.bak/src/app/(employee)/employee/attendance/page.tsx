"use client";

import { useState, useEffect, useCallback } from "react";
import { Clock, Loader2, MapPin, ArrowLeft, ArrowRight } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useCurrentUser } from "@/hooks/use-current-user";

interface AttendanceRecord {
  id: string;
  employee_id: string;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
  check_in_ip: string | null;
  check_out_ip: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

type TodayState =
  | "loading"
  | "empty"
  | "checked-in"
  | "completed"
  | "error";

interface ErrorResponse {
  error_code?: string;
  detail?: string;
}

function formatTime(isoString: string | null): string {
  if (!isoString) return "—";
  try {
    return new Date(isoString).toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "—";
  }
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("vi-VN");
  } catch {
    return dateStr;
  }
}

function formatCurrentDate(): string {
  return new Date().toLocaleDateString("vi-VN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function getMonthOptions() {
  const options = [];
  const now = new Date();
  for (let i = 0; i <= 3; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const label = d.toLocaleDateString("vi-VN", { month: "long", year: "numeric" });
    options.push({ value, label });
  }
  return options;
}

export default function EmployeeAttendancePage() {
  const { user } = useCurrentUser();
  
  // Today state
  const [todayState, setTodayState] = useState<TodayState>("loading");
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);

  // History state
  const [historyRecords, setHistoryRecords] = useState<AttendanceRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyMode, setHistoryMode] = useState<"recent" | "month">("recent");
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  const monthOptions = getMonthOptions();

  // Fetch today's attendance
  async function fetchToday() {
    setTodayState("loading");
    try {
      const res = await fetch("/api/attendance/me/today", { credentials: "include" });
      if (!res.ok) {
        const errorData: ErrorResponse = await res.json();
        if (res.status === 403) {
          setTodayState("error");
          setErrorMessage(errorData.detail || "Attendance check-in is only allowed from approved office network.");
          return;
        }
        throw new Error(`Lỗi tải dữ liệu (${res.status})`);
      }
      const data: AttendanceRecord | null = await res.json();
      if (!data) {
        setTodayState("empty");
      } else if (data.check_in_at && !data.check_out_at) {
        setTodayState("checked-in");
      } else if (data.check_in_at && data.check_out_at) {
        setTodayState("completed");
      } else {
        setTodayState("empty");
      }
      setTodayRecord(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể tải dữ liệu chấm công");
      setTodayState("empty");
    }
  }

  // Fetch history
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      let url: string;
      if (historyMode === "recent") {
        url = "/api/attendance/me/history?days=7";
      } else {
        const [year, month] = selectedMonth.split("-").map(Number);
        url = `/api/attendance/me/history?year=${year}&month=${month}`;
      }
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) {
        throw new Error(`Lỗi tải lịch sử (${res.status})`);
      }
      const data = await res.json();
      setHistoryRecords(data.records || []);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể tải lịch sử chấm công");
      setHistoryRecords([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [selectedMonth, historyMode]);

  // Check-in
  async function handleCheckIn() {
    setCheckingIn(true);
    try {
      const res = await fetch("/api/attendance/me/check-in", { method: "POST", credentials: "include" });
      const data = await res.json();
      if (!res.ok) {
        if (res.status === 403) {
          setTodayState("error");
          setErrorMessage(data.detail || "Attendance check-in is only allowed from approved office network.");
          return;
        }
        // 409 means already checked in - resolve silently
        if (res.status === 409) {
          await fetchToday();
      await fetchHistory();
          return;
        }
        throw new Error(data.detail || "Không thể check-in");
      }
      toast.success(data.message || "Check-in thành công");
      await fetchToday();
      await fetchHistory();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể check-in");
    } finally {
      setCheckingIn(false);
    }
  }

  // Check-out
  async function handleCheckOut() {
    setCheckingOut(true);
    try {
      const res = await fetch("/api/attendance/me/check-out", { method: "POST", credentials: "include" });
      const data = await res.json();
      if (!res.ok) {
        if (res.status === 403) {
          setTodayState("error");
          setErrorMessage(data.detail || "Attendance check-in is only allowed from approved office network.");
          return;
        }
        // 400 means not checked in - resolve silently
        if (res.status === 400) {
          await fetchToday();
      await fetchHistory();
          return;
        }
        throw new Error(data.detail || "Không thể check-out");
      }
      toast.success(data.message || "Check-out thành công");
      await fetchToday();
      await fetchHistory();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể check-out");
    } finally {
      setCheckingOut(false);
    }
  }

  // Initial fetch
  useEffect(() => {
    if (user?.employee_id) {
      fetchToday();
    }
  }, [user?.employee_id]);

  // Fetch history when month changes
  useEffect(() => {
    if (user?.employee_id) {
      fetchHistory();
    }
  }, [fetchHistory, user?.employee_id]);

  function getStatusBadge() {
    switch (todayState) {
      case "loading":
        return <Skeleton className="h-6 w-24" />;
      case "empty":
        return <Badge variant="secondary">Chưa điểm danh</Badge>;
      case "checked-in":
        return <Badge className="bg-green-600">Đã check-in</Badge>;
      case "completed":
        return <Badge className="bg-blue-600">Hoàn thành</Badge>;
      case "error":
        return <Badge variant="destructive">Lỗi mạng</Badge>;
    }
  }

  function getTodayContent() {
    if (todayState === "loading") {
      return (
        <div className="space-y-3">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      );
    }

    if (todayState === "empty") {
      return <p className="text-sm text-muted-foreground">Bạn chưa check-in hôm nay</p>;
    }

    if (todayState === "error") {
      return <p className="text-sm text-destructive">{errorMessage}</p>;
    }

    if (!todayRecord) return null;

    return (
      <div className="space-y-2 text-sm">
        {todayRecord.check_in_at && (
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Check-in:</span>
            <span className="font-mono">{formatTime(todayRecord.check_in_at)}</span>
            {todayRecord.check_in_ip && (
              <span className="text-muted-foreground">· IP {todayRecord.check_in_ip}</span>
            )}
          </div>
        )}
        {todayRecord.check_out_at && (
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Check-out:</span>
            <span className="font-mono">{formatTime(todayRecord.check_out_at)}</span>
            {todayRecord.check_out_ip && (
              <span className="text-muted-foreground">· IP {todayRecord.check_out_ip}</span>
            )}
          </div>
        )}
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Nguồn:</span>
          <span className="capitalize">{todayRecord.source}</span>
        </div>
      </div>
    );
  }

  function getActionButton() {
    if (todayState === "loading") {
      return <Button disabled><Loader2 className="h-4 w-4 animate-spin" /> Đang tải...</Button>;
    }

    if (todayState === "empty" || todayState === "error") {
      return (
        <Button onClick={handleCheckIn} disabled={checkingIn}>
          {checkingIn ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Clock className="h-4 w-4 mr-2" />}
          Check-in
        </Button>
      );
    }

    if (todayState === "checked-in") {
      return (
        <Button onClick={handleCheckOut} disabled={checkingOut}>
          {checkingOut ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Clock className="h-4 w-4 mr-2" />}
          Check-out
        </Button>
      );
    }

    // completed
    return <Button disabled>Đã hoàn thành</Button>;
  }

      return (
        <div className="animate-fade-in space-y-6 max-w-[900px]">
          <div className="fade-in-section space-y-1">
            <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-foreground">
              Chấm công
            </h1>
            <p className="text-[14px] text-muted-foreground">
              Check-in/check-out và xem lịch sử chấm công
            </p>
          </div>

          {/* Today Card */}
          <div className="fade-in-section">
            <Card className="card-hover">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div>
                  <CardTitle className="text-lg">Hôm nay</CardTitle>
                  <CardDescription>{formatCurrentDate()}</CardDescription>
                </div>
                {getStatusBadge()}
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  {getTodayContent()}
                  <div className="shrink-0">{getActionButton()}</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* History List */}
          <div className="fade-in-section">
            <Card className="card-hover">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <div>
                  <CardTitle className="text-lg">Lịch sử chấm công</CardTitle>
                  <CardDescription>
                    {historyMode === "recent"
                      ? "7 ngày gần nhất"
                      : monthOptions.find((o) => o.value === selectedMonth)?.label || selectedMonth}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {historyMode === "recent" ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setHistoryMode("month")}
                    >
                      Xem theo tháng
                    </Button>
                  ) : (
                    <>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => {
                          const idx = monthOptions.findIndex((o) => o.value === selectedMonth);
                          if (idx < monthOptions.length - 1) {
                            setSelectedMonth(monthOptions[idx + 1].value);
                          }
                        }}
                        disabled={selectedMonth === monthOptions[monthOptions.length - 1].value}
                      >
                        <ArrowLeft className="h-4 w-4" />
                      </Button>
                      <select
                        value={selectedMonth}
                        onChange={(e) => {
                          setSelectedMonth(e.target.value);
                          setHistoryMode("month");
                        }}
                        className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                      >
                        {monthOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => {
                          const idx = monthOptions.findIndex((o) => o.value === selectedMonth);
                          if (idx > 0) {
                            setSelectedMonth(monthOptions[idx - 1].value);
                          }
                        }}
                        disabled={selectedMonth === monthOptions[0].value}
                      >
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setHistoryMode("recent")}
                      >
                        7 ngày
                      </Button>
                    </>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {historyLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : historyRecords.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">
                    {historyMode === "recent"
                      ? "Chưa có bản ghi chấm công trong 7 ngày gần nhất."
                      : "Chưa có bản ghi chấm công trong tháng này."}
                  </p>
                ) : (
                  <div className="overflow-x-auto rounded-lg border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Ngày</TableHead>
                          <TableHead>Check-in</TableHead>
                          <TableHead>Check-out</TableHead>
                          <TableHead>Nguồn</TableHead>
                          <TableHead>Trạng thái</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {historyRecords.map((record) => (
                          <TableRow key={record.id} className="card-hover">
                            <TableCell className="font-mono">
                              {formatDate(record.work_date)}
                            </TableCell>
                            <TableCell className="font-mono">
                              {formatTime(record.check_in_at)}
                            </TableCell>
                            <TableCell className="font-mono">
                              {formatTime(record.check_out_at)}
                            </TableCell>
                            <TableCell className="capitalize">{record.source}</TableCell>
                            <TableCell>
                              {!record.check_in_at ? (
                                <Badge variant="secondary">—</Badge>
                              ) : !record.check_out_at ? (
                                <Badge className="bg-success text-success-foreground">Đã check-in</Badge>
                              ) : (
                                <Badge className="bg-secondary text-secondary-foreground">Hoàn thành</Badge>
                              )}
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
        </div>
  );
}
