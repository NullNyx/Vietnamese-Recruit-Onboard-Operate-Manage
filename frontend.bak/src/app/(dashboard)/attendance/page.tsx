"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Loader2, Edit2 } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";

interface AttendanceRecord {
  id: string;
  employee_id: string;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
  check_in_ip: string | null;
  check_out_ip: string | null;
  source: string;
  employee_name: string | null;
  employee_code: string | null;
  corrected_at: string | null;
  correction_reason: string | null;
  created_at: string;
  updated_at: string;
}

interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
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

function getDefaultStartDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
}

function getDefaultEndDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

export default function AttendanceListPage() {
  // Filters
  const [startDate, setStartDate] = useState(getDefaultStartDate);
  const [endDate, setEndDate] = useState(getDefaultEndDate);
  const [employeeId, setEmployeeId] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);

  // Data
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);

  // Correction modal
  const [correctionModalOpen, setCorrectionModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<AttendanceRecord | null>(null);
  const [newCheckIn, setNewCheckIn] = useState("");
  const [newCheckOut, setNewCheckOut] = useState("");
  const [correctionReason, setCorrectionReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const PAGE_SIZE = 20;

  // Fetch employees for filter dropdown
  const fetchEmployees = useCallback(async () => {
    try {
      const res = await fetch("/api/employees", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setEmployees(data.items ?? []);
      }
    } catch {
      // Silently fail - employee filter is optional
    }
  }, []);

  // Fetch attendance records
  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        page: page.toString(),
        page_size: PAGE_SIZE.toString(),
      });

      if (employeeId && employeeId !== "all") {
        params.append("employee_id", employeeId);
      }
      if (statusFilter && statusFilter !== "all") {
        params.append("status", statusFilter);
      }

      const res = await fetch(`/api/attendance/records?${params}`, {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`Lỗi tải dữ liệu (${res.status})`);
      }

      const data = await res.json();
      setRecords(data.records || []);
      setTotal(data.total || 0);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể tải dữ liệu chấm công");
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, employeeId, statusFilter, page]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // Convert UTC ISO string to local YYYY-MM-DDTHH:mm for datetime-local input
  function utcToLocalDatetime(utcStr: string): string {
    const d = new Date(utcStr);
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  // Open correction modal
  function handleOpenCorrection(record: AttendanceRecord) {
    setSelectedRecord(record);
    setNewCheckIn(record.check_in_at ? utcToLocalDatetime(record.check_in_at) : "");
    setNewCheckOut(record.check_out_at ? utcToLocalDatetime(record.check_out_at) : "");
    setCorrectionReason("");
    setCorrectionModalOpen(true);
  }

  // Submit correction
  async function handleSubmitCorrection() {
    if (!selectedRecord) return;
    if (!correctionReason.trim()) {
      toast.error("Vui lòng nhập lý do sửa");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        correction_reason: correctionReason.trim(),
      };

      if (newCheckIn) {
        payload.check_in_at = new Date(newCheckIn).toISOString();
      } else {
        payload.check_in_at = null;
      }

      if (newCheckOut) {
        payload.check_out_at = new Date(newCheckOut).toISOString();
      } else {
        payload.check_out_at = null;
      }

      const res = await fetch(`/api/attendance/records/${selectedRecord.id}/correct`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Không thể cập nhật");
      }

      toast.success("Đã cập nhật bản ghi thành công");
      setCorrectionModalOpen(false);
      fetchRecords();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể cập nhật bản ghi");
    } finally {
      setSubmitting(false);
    }
  }

  function getStatusBadge(record: AttendanceRecord) {
    if (!record.check_in_at) {
      return <Badge variant="secondary">—</Badge>;
    }
    if (!record.check_out_at) {
      return <Badge className="bg-primary/85 text-primary-foreground hover:bg-primary/75">Đã check-in</Badge>;
    }
    return <Badge className="bg-secondary text-secondary-foreground hover:bg-secondary/80">Hoàn thành</Badge>;
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Page Header ── */}
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Search className="h-5 w-5" aria-hidden="true" strokeWidth={1.5} />
        </div>
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
            Quản lý chấm công
          </h1>
          <p className="text-sm text-muted-foreground">
            Xem và quản lý bản ghi chấm công của nhân viên
          </p>
        </div>
      </div>

      {/* ── Filters ── */}
      <Card className="card-hover shadow-warm">
        <CardHeader>
          <CardTitle className="text-base font-semibold">Bộ lọc</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="start-date" className="text-xs font-medium text-muted-foreground">
                Từ ngày
              </Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date" className="text-xs font-medium text-muted-foreground">
                Đến ngày
              </Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-medium text-muted-foreground">Nhân viên</Label>
              <Select value={employeeId} onValueChange={setEmployeeId}>
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.employee_code} - {emp.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-medium text-muted-foreground">Trạng thái</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  <SelectItem value="checked_in">Đã check-in</SelectItem>
                  <SelectItem value="completed">Hoàn thành</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={() => setPage(1)} className="shadow-warm">
              <Search className="mr-2 h-4 w-4" />
              Tìm kiếm
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Results ── */}
      <Card className="shadow-warm">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div>
            <CardTitle className="text-base font-semibold">Kết quả</CardTitle>
            <CardDescription>{total} bản ghi</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : records.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-sm text-muted-foreground">
                Không có bản ghi chấm công phù hợp.
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Mã NV</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Họ tên</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Ngày</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Check-in</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Check-out</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Nguồn</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Trạng thái</TableHead>
                      <TableHead className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Đã sửa</TableHead>
                      <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Thao tác</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {records.map((record) => (
                      <TableRow key={record.id} className="animate-fade-in hover:bg-muted/50">
                        <TableCell className="font-mono text-xs">
                          {record.employee_code || "—"}
                        </TableCell>
                        <TableCell className="text-sm font-medium">
                          {record.employee_name || "—"}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatDate(record.work_date)}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatTime(record.check_in_at)}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatTime(record.check_out_at)}
                        </TableCell>
                        <TableCell className="text-xs capitalize">{record.source}</TableCell>
                        <TableCell>{getStatusBadge(record)}</TableCell>
                        <TableCell>
                          {record.corrected_at ? (
                            <Badge variant="outline" className="text-xs text-muted-foreground">
                              Đã sửa
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleOpenCorrection(record)}
                            className="h-8 w-8 text-muted-foreground hover:text-primary"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-4 flex items-center justify-center gap-3">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                    className="h-8"
                  >
                    Trước
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Trang {page} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === totalPages}
                    onClick={() => setPage(page + 1)}
                    className="h-8"
                  >
                    Sau
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ── Correction Modal ── */}
      <Dialog open={correctionModalOpen} onOpenChange={setCorrectionModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="text-lg font-semibold">Sửa bản ghi chấm công</DialogTitle>
            <DialogDescription>
              {selectedRecord && (
                <>
                  {selectedRecord.employee_code} - {selectedRecord.employee_name}
                  <br />
                  Ngày: {formatDate(selectedRecord.work_date)}
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Current values (read-only) */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1 rounded-lg bg-muted/50 p-3">
                <Label className="text-xs text-muted-foreground">Giờ check-in hiện tại</Label>
                <p className="text-sm font-mono text-foreground">
                  {selectedRecord ? formatTime(selectedRecord.check_in_at) : "—"}
                </p>
              </div>
              <div className="space-y-1 rounded-lg bg-muted/50 p-3">
                <Label className="text-xs text-muted-foreground">Giờ check-out hiện tại</Label>
                <p className="text-sm font-mono text-foreground">
                  {selectedRecord ? formatTime(selectedRecord.check_out_at) : "—"}
                </p>
              </div>
            </div>

            {/* New values (editable) */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="new-checkin" className="text-xs font-medium text-muted-foreground">
                  Giờ check-in mới
                </Label>
                <Input
                  id="new-checkin"
                  type="datetime-local"
                  value={newCheckIn}
                  onChange={(e) => setNewCheckIn(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-checkout" className="text-xs font-medium text-muted-foreground">
                  Giờ check-out mới
                </Label>
                <Input
                  id="new-checkout"
                  type="datetime-local"
                  value={newCheckOut}
                  onChange={(e) => setNewCheckOut(e.target.value)}
                />
              </div>
            </div>

            {/* Correction reason */}
            <div className="space-y-2">
              <Label htmlFor="reason" className="text-xs font-medium text-muted-foreground">
                Lý do sửa <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="reason"
                placeholder="Nhập lý do sửa bản ghi..."
                value={correctionReason}
                onChange={(e) => setCorrectionReason(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCorrectionModalOpen(false)}
              disabled={submitting}
            >
              Hủy
            </Button>
            <Button
              onClick={handleSubmitCorrection}
              disabled={submitting || !correctionReason.trim()}
              className="shadow-warm"
            >
              {submitting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Xác nhận sửa
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
