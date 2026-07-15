"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
    import {
      Plus,
      DollarSign,
      Edit2,
      Trash2,
      Eye,
      FileSpreadsheet,
      Send,
      Ban,
      ChevronLeft,
      ChevronRight,
    } from "lucide-react";
import { toast } from "sonner";
import { AnimatePresence, m, LazyMotion, domAnimation } from "motion/react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  fetchPayslips,
  deletePayslip,
  publishPayslip,
  type Payslip,
} from "@/lib/api/admin-payslips";

function formatCurrency(amount: string): string {
  const num = parseFloat(amount);
  if (!Number.isFinite(num)) return amount;
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(num);
}

function formatPeriod(periodMonth: string): string {
  const [year, month] = periodMonth.split("-").map(Number);
  const d = new Date(year, month - 1);
  return d.toLocaleDateString("vi-VN", {
    month: "long",
    year: "numeric",
  });
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN");
}

function StatusBadge({ status }: { status: "draft" | "published" }) {
  if (status === "published") {
    return (
      <Badge className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-0">
        <Send className="mr-1 h-3 w-3" />
        Đã phát hành
      </Badge>
    );
  }
  return (
    <Badge
      variant="secondary"
      className="bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-0"
    >
      <Ban className="mr-1 h-3 w-3" />
      Bản nháp
    </Badge>
  );
}

function PayslipSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-8 w-24 ml-auto" />
        </div>
      ))}
    </div>
  );
}

export default function PayrollPage() {
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Payslip | null>(null);
  const PAGE_SIZE = 20;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPayslips({
        page,
        page_size: PAGE_SIZE,
        status:
          statusFilter === "all"
            ? undefined
            : (statusFilter as "draft" | "published"),
      });
      setPayslips(data.payslips);
      setTotal(data.total);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Không thể tải bảng lương"
      );
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handlePublish(id: string) {
    try {
      await publishPayslip(id);
      toast.success("Đã phát hành phiếu lương");
      load();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Phát hành thất bại"
      );
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await deletePayslip(deleteTarget.id);
      toast.success("Đã xóa phiếu lương");
      setDeleteOpen(false);
      setDeleteTarget(null);
      load();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Xóa thất bại"
      );
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <LazyMotion features={domAnimation}>
      <div className="animate-page-enter space-y-6 max-w-[1440px] mx-auto overflow-x-hidden pb-10">
        {/* ─── Header ────────────────────────────────── */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <DollarSign className="h-4 w-4" strokeWidth={1.5} />
              </div>
              <h1 className="font-heading text-2xl font-semibold tracking-tight">
                Bảng lương
              </h1>
            </div>
            <p className="text-sm text-muted-foreground ml-10">
              Quản lý phiếu lương nhân viên
            </p>
          </div>
          <Button asChild className="shrink-0">
            <Link href="/payroll/new">
              <Plus className="mr-2 h-4 w-4" /> Tạo phiếu lương
            </Link>
          </Button>
        </div>

        {/* ─── Period Summary Cards ─────────────────────── */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="card-hover rounded-xl border border-border/40 bg-card p-4 shadow-sm">
            <p className="text-xs font-label uppercase tracking-[0.08em] text-muted-foreground">
              Kỳ lương hiện tại
            </p>
            <p className="mt-1 font-heading text-lg font-semibold text-foreground">
              {formatPeriod(
                payslips.length > 0 ? payslips[0].period_month : "2025-01"
              )}
            </p>
          </div>
          <div className="card-hover rounded-xl border border-border/40 bg-card p-4 shadow-sm">
            <p className="text-xs font-label uppercase tracking-[0.08em] text-muted-foreground">
              Tổng phiếu lương
            </p>
            <p className="mt-1 font-heading text-lg font-semibold text-foreground">
              {total}
            </p>
          </div>
          <div className="card-hover rounded-xl border border-border/40 bg-card p-4 shadow-sm">
            <p className="text-xs font-label uppercase tracking-[0.08em] text-muted-foreground">
              Đã phát hành / Nháp
            </p>
            <p className="mt-1 font-heading text-lg font-semibold text-foreground">
              {payslips.filter((p) => p.status === "published").length}
              <span className="text-muted-foreground/60 font-normal"> · </span>
              {payslips.filter((p) => p.status === "draft").length}
            </p>
          </div>
        </div>

        {/* ─── Payslip Table ──────────────────────────── */}
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-muted-foreground/60" strokeWidth={1.5} />
                <CardTitle className="text-sm font-semibold">
                  Tất cả phiếu lương
                </CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-xs sr-only sm:not-sr-only">Trạng thái</Label>
                <Select
                  value={statusFilter}
                  onValueChange={(v) => {
                    setStatusFilter(v);
                    setPage(1);
                  }}
                >
                  <SelectTrigger className="h-8 w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tất cả</SelectItem>
                    <SelectItem value="draft">Bản nháp</SelectItem>
                    <SelectItem value="published">Đã phát hành</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <PayslipSkeleton />
            ) : payslips.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 text-center">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/20">
                  <DollarSign
                    className="h-6 w-6 text-muted-foreground/50"
                    strokeWidth={1.5}
                  />
                </div>
                <p className="text-sm font-medium text-muted-foreground">
                  Chưa có phiếu lương nào
                </p>
                <p className="mt-1 text-xs text-muted-foreground/60">
                  Tạo phiếu lương đầu tiên để bắt đầu
                </p>
                <Button asChild className="mt-5">
                  <Link href="/payroll/new">
                    <Plus className="mr-2 h-4 w-4" /> Tạo phiếu lương
                  </Link>
                </Button>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Kỳ lương</TableHead>
                        <TableHead>Mã NV</TableHead>
                        <TableHead className="text-right">Lương gộp</TableHead>
                        <TableHead className="text-right">Thực nhận</TableHead>
                        <TableHead className="text-right">Thuế TNCN</TableHead>
                        <TableHead>Trạng thái</TableHead>
                        <TableHead>Ngày tạo</TableHead>
                        <TableHead className="text-right">Thao tác</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <AnimatePresence mode="popLayout">
                        {payslips.map((ps) => (
                          <m.tr
                            key={ps.id}
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -4 }}
                            transition={{ duration: 0.15 }}
                            className="group"
                          >
                            <TableCell className="font-medium">
                              {formatPeriod(ps.period_month)}
                            </TableCell>
                            <TableCell className="font-mono text-xs text-muted-foreground">
                              {ps.employee_id.slice(0, 8)}
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              {formatCurrency(ps.gross_salary)}
                            </TableCell>
                            <TableCell className="text-right tabular-nums font-medium">
                              {formatCurrency(ps.net_salary)}
                            </TableCell>
                            <TableCell className="text-right tabular-nums text-muted-foreground">
                              {formatCurrency(ps.pit_amount)}
                            </TableCell>
                            <TableCell>
                              <StatusBadge status={ps.status} />
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {formatDate(ps.created_at)}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-0.5 opacity-60 group-hover:opacity-100 transition-opacity">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  asChild
                                >
                                  <Link href={`/payroll/${ps.id}`}>
                                    <Eye className="h-3.5 w-3.5" />
                                  </Link>
                                </Button>
                                {ps.status === "draft" && (
                                  <>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-8 w-8"
                                      asChild
                                    >
                                      <Link
                                        href={`/payroll/${ps.id}?edit=1`}
                                      >
                                        <Edit2 className="h-3.5 w-3.5" />
                                      </Link>
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-950/30"
                                      onClick={() => handlePublish(ps.id)}
                                      title="Phát hành"
                                    >
                                      <Send className="h-3.5 w-3.5" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                                      onClick={() => {
                                        setDeleteTarget(ps);
                                        setDeleteOpen(true);
                                      }}
                                      title="Xóa"
                                    >
                                      <Trash2 className="h-3.5 w-3.5" />
                                    </Button>
                                  </>
                                )}
                              </div>
                            </TableCell>
                          </m.tr>
                        ))}
                      </AnimatePresence>
                    </TableBody>
                  </Table>
                </div>

                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-3 mt-5">
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm tabular-nums text-muted-foreground">
                      {page} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* ─── Delete Dialog ──────────────────────────── */}
        <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Xóa phiếu lương?</DialogTitle>
              <DialogDescription>
                Kỳ lương{" "}
                {deleteTarget
                  ? formatPeriod(deleteTarget.period_month)
                  : ""}
                . Hành động này không thể hoàn tác.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteOpen(false)}
              >
                Hủy
              </Button>
              <Button variant="destructive" onClick={handleDelete}>
                Xóa
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </LazyMotion>
  );
}
