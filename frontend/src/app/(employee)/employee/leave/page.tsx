"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { CalendarDays, Plus, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import type { LeaveBalance, LeaveRequestResponse } from "@/lib/api/ess";

const statusColors: Record<string, string> = {
  pending:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  approved: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  rejected: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  cancelled: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

const statusLabels: Record<string, string> = {
  pending: "Chờ duyệt",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
};

function formatDate(dateString: string): string {
  const d = new Date(dateString);
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Ho_Chi_Minh",
  });
}

export default function EmployeeLeavePage() {
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [requests, setRequests] = useState<LeaveRequestResponse[]>([]);
  const [balancesLoading, setBalancesLoading] = useState(true);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchBalances = useCallback(async () => {
    setBalancesLoading(true);
    try {
      const data = await essApi.getLeaveBalances();
      setBalances(data);
    } catch {
      setBalances([]);
    } finally {
      setBalancesLoading(false);
    }
  }, []);

  const fetchRequests = useCallback(async () => {
    setRequestsLoading(true);
    try {
      const data = await essApi.getLeaveRequests();
      setRequests(data);
    } catch {
      setRequests([]);
    } finally {
      setRequestsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBalances();
    fetchRequests();
  }, [fetchBalances, fetchRequests]);

  async function handleCancel(requestId: string) {
    setCancellingId(requestId);
    setError(null);
    try {
      await essApi.cancelLeaveRequest(requestId);
      await fetchRequests();
      await fetchBalances();
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || "Không thể hủy đơn nghỉ phép.");
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Nghỉ phép</h1>
        <Link href="/employee/leave/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Tạo đơn mới
          </Button>
        </Link>
      </div>

      {/* Leave Balances */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Số dư phép</h2>
        {balancesLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : balances.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Không có dữ liệu số dư phép.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {balances.map((balance) => (
              <Card key={balance.leave_type_id}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {balance.leave_type_name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold">
                      {balance.remaining_days}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      / {balance.total_days} ngày
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Đã sử dụng: {balance.used_days} ngày
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Leave Requests Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5" />
            Đơn nghỉ phép
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 text-sm text-destructive">{error}</div>
          )}
          {requestsLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : requests.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              Chưa có đơn nghỉ phép nào.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Loại phép</TableHead>
                    <TableHead>Ngày bắt đầu</TableHead>
                    <TableHead>Ngày kết thúc</TableHead>
                    <TableHead>Số ngày</TableHead>
                    <TableHead>Trạng thái</TableHead>
                    <TableHead>Thao tác</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requests.map((req) => (
                    <TableRow key={req.id}>
                      <TableCell className="font-medium">
                        {req.leave_type_name}
                      </TableCell>
                      <TableCell>{formatDate(req.start_date)}</TableCell>
                      <TableCell>{formatDate(req.end_date)}</TableCell>
                      <TableCell>{req.total_days}</TableCell>
                      <TableCell>
                        <Badge className={statusColors[req.status] || ""}>
                          {statusLabels[req.status] || req.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {req.status === "pending" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCancel(req.id)}
                            disabled={cancellingId === req.id}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            {cancellingId === req.id ? "Đang hủy..." : "Hủy"}
                          </Button>
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
  );
}
