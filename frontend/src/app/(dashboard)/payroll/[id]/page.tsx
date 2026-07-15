"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Loader2, Save, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogFooter,
  DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import {
  fetchPayslip, updatePayslip, publishPayslip, deletePayslip,
  type Payslip, type UpdatePayslipRequest,
} from "@/lib/api/admin-payslips";

function formatCurrency(amount: string): string {
  const num = parseFloat(amount);
  if (!Number.isFinite(num)) return amount;
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(num);
}

function formatPeriod(periodMonth: string): string {
  const [y, m] = periodMonth.split("-").map(Number);
  return new Date(y, m-1).toLocaleDateString("vi-VN", { month: "long", year: "numeric" });
}

export default function PayslipDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const isEdit = searchParams.get("edit") === "1";

  const [payslip, setPayslip] = useState<Payslip | null>(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // Edit fields
  const [grossSalary, setGrossSalary] = useState("");
  const [deductions, setDeductions] = useState("");
  const [insurance, setInsurance] = useState("");
  const [taxableIncome, setTaxableIncome] = useState("");
  const [pitAmount, setPitAmount] = useState("");
  const [netSalary, setNetSalary] = useState("");

  async function load() {
    setLoading(true);
    try {
      const data = await fetchPayslip(id);
      setPayslip(data);
      setGrossSalary(data.gross_salary);
      setDeductions(data.deductions);
      setInsurance(data.insurance_employee);
      setTaxableIncome(data.taxable_income);
      setPitAmount(data.pit_amount);
      setNetSalary(data.net_salary);
    } catch {
      toast.error("Không tìm thấy phiếu lương");
      router.push("/payroll");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSave() {
    setSaving(true);
    const data: UpdatePayslipRequest = {
      gross_salary: grossSalary,
      deductions: deductions,
      insurance_employee: insurance,
      taxable_income: taxableIncome,
      pit_amount: pitAmount,
      net_salary: netSalary,
    };
    try {
      const updated = await updatePayslip(id, data);
      setPayslip(updated);
      setEditMode(false);
      toast.success("Đã cập nhật phiếu lương");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Cập nhật thất bại");
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    try {
      const updated = await publishPayslip(id);
      setPayslip(updated);
      toast.success("Đã phát hành phiếu lương");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Phát hành thất bại");
    }
  }

  async function handleDelete() {
    try {
      await deletePayslip(id);
      toast.success("Đã xóa phiếu lương");
      router.push("/payroll");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Xóa thất bại");
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 max-w-3xl mx-auto">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!payslip) return null;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        
        <div className="space-y-1 flex-1">
          <h1 className="text-2xl font-semibold tracking-tight">
            Phiếu lương {formatPeriod(payslip.period_month)}
          </h1>
          <p className="text-sm text-muted-foreground">
            Nhân viên: {payslip.employee_id.slice(0, 8)}...
          </p>
        </div>
        <Badge variant={payslip.status === "published" ? "default" : "secondary"} className="text-sm px-3 py-1">
          {payslip.status === "published" ? "Đã phát hành" : "Bản nháp"}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Chi tiết lương</CardTitle>
              <CardDescription>
                {editMode ? "Chỉnh sửa số liệu" : "Xem thông tin lương"}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {payslip.status === "draft" && (
                <>
                  {!editMode ? (
                    <>
                      <Button variant="outline" onClick={() => setEditMode(true)}>
                        <Save className="mr-2 h-4 w-4" /> Chỉnh sửa
                      </Button>
                      <Button onClick={handlePublish}>
                        <Send className="mr-2 h-4 w-4" /> Phát hành
                      </Button>
                      <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button variant="outline" onClick={() => setEditMode(false)}>Hủy</Button>
                      <Button onClick={handleSave} disabled={saving}>
                        {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Lưu thay đổi
                      </Button>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            {editMode ? (
              <>
                <div className="space-y-2">
                  <Label>Lương gộp</Label>
                  <Input value={grossSalary} onChange={e => setGrossSalary(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Lương thực nhận</Label>
                  <Input value={netSalary} onChange={e => setNetSalary(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Bảo hiểm</Label>
                  <Input value={insurance} onChange={e => setInsurance(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Thuế TNCN</Label>
                  <Input value={pitAmount} onChange={e => setPitAmount(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Thu nhập chịu thuế</Label>
                  <Input value={taxableIncome} onChange={e => setTaxableIncome(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Tổng khấu trừ</Label>
                  <Input value={deductions} onChange={e => setDeductions(e.target.value)} />
                </div>
              </>
            ) : (
              <>
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Lương gộp</Label>
                  <p className="text-lg font-semibold font-mono">{formatCurrency(payslip.gross_salary)}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Lương thực nhận</Label>
                  <p className="text-lg font-semibold font-mono text-green-600">{formatCurrency(payslip.net_salary)}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Bảo hiểm</Label>
                  <p className="font-mono">{formatCurrency(payslip.insurance_employee)}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Thuế TNCN</Label>
                  <p className="font-mono text-red-500">{formatCurrency(payslip.pit_amount)}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Thu nhập chịu thuế</Label>
                  <p className="font-mono">{formatCurrency(payslip.taxable_income)}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-muted-foreground">Tổng khấu trừ</Label>
                  <p className="font-mono">{formatCurrency(payslip.deductions)}</p>
                </div>
              </>
            )}
          </div>

          {!editMode && (
            <div className="grid gap-4 sm:grid-cols-2 pt-4 border-t">
              <div className="space-y-1">
                <Label className="text-muted-foreground">Ngày tạo</Label>
                <p className="text-sm">{new Date(payslip.created_at).toLocaleDateString("vi-VN")}</p>
              </div>
              <div className="space-y-1">
                <Label className="text-muted-foreground">Ngày publish</Label>
                <p className="text-sm">{payslip.published_at ? new Date(payslip.published_at).toLocaleDateString("vi-VN") : "—"}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Xóa phiếu lương?</DialogTitle>
            <DialogDescription>
              Phiếu lương {formatPeriod(payslip.period_month)} sẽ bị xóa vĩnh viễn.
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
