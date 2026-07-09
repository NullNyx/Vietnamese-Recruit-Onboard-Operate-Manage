"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Plus, DollarSign, Edit2, Trash2, Eye } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  fetchPayslips, deletePayslip, publishPayslip,
  type Payslip,
} from "@/lib/api/admin-payslips";

function formatCurrency(amount: string): string {
  const num = parseFloat(amount);
  if (!Number.isFinite(num)) return amount;
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(num);
}

function formatPeriod(periodMonth: string): string {
  const [year, month] = periodMonth.split("-").map(Number);
  const d = new Date(year, month - 1);
  return d.toLocaleDateString("vi-VN", { month: "long", year: "numeric" });
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN");
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
        status: statusFilter === "all" ? undefined : (statusFilter as "draft" | "published"),
      });
      setPayslips(data.payslips);
      setTotal(data.total);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không thể tải bảng lương");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => { load(); }, [load]);

  async function handlePublish(id: string) {
    try {
      await publishPayslip(id);
      toast.success("Đã publish phiếu lương");
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Publish thất bại");
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
      toast.error(err instanceof Error ? err.message : "Xóa thất bại");
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Bảng lương</h1>
          <p className="text-sm text-muted-foreground">Quản lý phiếu lương nhân viên</p>
        </div>
        <Button asChild>
          <Link href="/payroll/new">
            <Plus className="mr-2 h-4 w-4" /> Tạo phiếu lương
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle>Tất cả phiếu lương</CardTitle>
            <div className="flex items-center gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Trạng thái</Label>
                <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
                  <SelectTrigger className="h-8 w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tất cả</SelectItem>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="published">Đã publish</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : payslips.length === 0 ? (
            <div className="py-12 text-center">
              <DollarSign className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-3 font-medium">Chưa có phiếu lương nào</p>
              <p className="text-sm text-muted-foreground">Tạo phiếu lương đầu tiên để bắt đầu</p>
              <Button asChild className="mt-4">
                <Link href="/payroll/new">Tạo phiếu lương</Link>
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
                      <TableHead>Gross</TableHead>
                      <TableHead>Net</TableHead>
                      <TableHead>Thuế TNCN</TableHead>
                      <TableHead>Trạng thái</TableHead>
                      <TableHead>Ngày tạo</TableHead>
                      <TableHead className="text-right">Thao tác</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payslips.map(ps => (
                      <TableRow key={ps.id}>
                        <TableCell className="font-medium">{formatPeriod(ps.period_month)}</TableCell>
                        <TableCell className="font-mono text-sm">{ps.employee_id.slice(0,8)}</TableCell>
                        <TableCell>{formatCurrency(ps.gross_salary)}</TableCell>
                        <TableCell>{formatCurrency(ps.net_salary)}</TableCell>
                        <TableCell>{formatCurrency(ps.pit_amount)}</TableCell>
                        <TableCell>
                          <Badge variant={ps.status === "published" ? "default" : "secondary"}>
                            {ps.status === "published" ? "Đã publish" : "Draft"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm">{formatDate(ps.created_at)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="icon" asChild>
                              <Link href={`/payroll/${ps.id}`}><Eye className="h-4 w-4" /></Link>
                            </Button>
                            {ps.status === "draft" && (
                              <>
                                <Button variant="ghost" size="icon" asChild>
                                  <Link href={`/payroll/${ps.id}?edit=1`}><Edit2 className="h-4 w-4" /></Link>
                                </Button>
                                <Button
                                  variant="ghost" size="icon"
                                  onClick={() => handlePublish(ps.id)}
                                >
                                  <Badge className="h-4 w-4 text-xs cursor-pointer">P</Badge>
                                </Button>
                                <Button
                                  variant="ghost" size="icon"
                                  onClick={() => { setDeleteTarget(ps); setDeleteOpen(true); }}
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Trước</Button>
                  <span className="flex items-center text-sm text-muted-foreground">Trang {page} / {totalPages}</span>
                  <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Sau</Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Xóa phiếu lương?</DialogTitle>
            <DialogDescription>
              Kỳ lương {deleteTarget ? formatPeriod(deleteTarget.period_month) : ""}. Hành động này không thể hoàn tác.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Hủy</Button>
            <Button variant="destructive" onClick={handleDelete}>Xóa</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
