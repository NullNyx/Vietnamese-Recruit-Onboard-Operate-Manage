"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2, Save } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { createPayslip, type CreatePayslipRequest } from "@/lib/api/admin-payslips";

interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
}

function formatCurrencyInput(value: string): string {
  return value.replace(/[^\d.]/g, "").replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,");
}

export default function NewPayslipPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [employeeId, setEmployeeId] = useState("");
  const [periodMonth, setPeriodMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
  const [grossSalary, setGrossSalary] = useState("");
  const [deductions, setDeductions] = useState("0");
  const [insurance, setInsurance] = useState("0");
  const [taxableIncome, setTaxableIncome] = useState("0");
  const [pitAmount, setPitAmount] = useState("0");
  const [netSalary, setNetSalary] = useState("");

  useEffect(() => {
    fetch("/api/employees", { credentials: "include" })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => setEmployees(data.items || data))
      .catch(() => toast.error("Không tải được danh sách NV"));
  }, []);

  function parseAmount(s: string): string {
    return s.replace(/,/g, "") || "0";
  }

  async function handleSubmit() {
    if (!employeeId) { toast.error("Chọn nhân viên"); return; }
    if (!netSalary) { toast.error("Nhập lương net"); return; }

    setLoading(true);
    const payload: CreatePayslipRequest = {
      employee_id: employeeId,
      period_month: periodMonth + "-01",
      gross_salary: parseAmount(grossSalary) || "0",
      deductions: parseAmount(deductions),
      insurance_employee: parseAmount(insurance),
      taxable_income: parseAmount(taxableIncome),
      pit_amount: parseAmount(pitAmount),
      net_salary: parseAmount(netSalary),
    };

    try {
      await createPayslip(payload);
      toast.success("Tạo phiếu lương thành công");
      router.push("/payroll");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Tạo thất bại");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/payroll"><ArrowLeft className="h-5 w-5" /></Link>
        </Button>
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Tạo phiếu lương mới</h1>
          <p className="text-sm text-muted-foreground">Nhập thông tin lương cho nhân viên</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Thông tin phiếu lương</CardTitle>
          <CardDescription>
            Nhập lương gross, các khoản khấu trừ và lương net. Tất cệ giá trị là VND.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Nhân viên *</Label>
              <Select value={employeeId} onValueChange={setEmployeeId}>
                <SelectTrigger><SelectValue placeholder="Chọn nhân viên" /></SelectTrigger>
                <SelectContent>
                  {employees.map(emp => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.employee_code} - {emp.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Kỳ lương *</Label>
              <Input
                type="month"
                value={periodMonth}
                onChange={e => setPeriodMonth(e.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Lương Gross (VND) *</Label>
              <Input
                placeholder="15,000,000"
                value={grossSalary}
                onChange={e => setGrossSalary(formatCurrencyInput(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Lương Net (VND) *</Label>
              <Input
                placeholder="12,082,500"
                value={netSalary}
                onChange={e => setNetSalary(formatCurrencyInput(e.target.value))}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Bảo hiểm (VND)</Label>
              <Input
                placeholder="0"
                value={insurance}
                onChange={e => setInsurance(formatCurrencyInput(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Thuế TNCN (VND)</Label>
              <Input
                placeholder="0"
                value={pitAmount}
                onChange={e => setPitAmount(formatCurrencyInput(e.target.value))}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Thu nhập chịu thuế (VND)</Label>
              <Input
                placeholder="0"
                value={taxableIncome}
                onChange={e => setTaxableIncome(formatCurrencyInput(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label>Tổng khấu trừ (VND)</Label>
              <Input
                placeholder="0"
                value={deductions}
                onChange={e => setDeductions(formatCurrencyInput(e.target.value))}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" asChild><Link href="/payroll">Hủy</Link></Button>
            <Button onClick={handleSubmit} disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              Lưu phiếu lương
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
