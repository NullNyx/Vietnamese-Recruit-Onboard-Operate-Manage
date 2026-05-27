"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
<<<<<<< HEAD
import { useParams, useRouter } from "next/navigation";
=======
import { useParams } from "next/navigation";
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
import { ChevronLeft, Save, Plus, Trash2 } from "lucide-react";

import {
  getSalaryConfig,
  createSalaryConfig,
  updateSalaryConfig,
  getAllowances,
  createAllowance,
  deleteAllowance,
  getDependents,
  createDependent,
  deleteDependent,
} from "@/lib/api/payroll";
<<<<<<< HEAD
import type {
  SalaryConfig,
  SalaryConfigCreate,
  Allowance,
  Dependent,
} from "@/lib/api/payroll";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
=======
import type { SalaryConfig, Allowance, Dependent } from "@/lib/api/payroll";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

export default function SalaryConfigPage() {
  const { id } = useParams<{ id: string }>();
<<<<<<< HEAD
  const router = useRouter();
=======
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091

  const [config, setConfig] = useState<SalaryConfig | null>(null);
  const [allowances, setAllowances] = useState<Allowance[]>([]);
  const [dependents, setDependents] = useState<Dependent[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    gross_salary: 0,
    insurance_salary: 0,
    contract_type: "official",
    effective_date: new Date().toISOString().split("T")[0],
  });

  const [showAllowanceDialog, setShowAllowanceDialog] = useState(false);
  const [newAllowance, setNewAllowance] = useState({
    allowance_type: "telephone",
    amount: 0,
    is_taxable: true,
  });

  const [showDependentDialog, setShowDependentDialog] = useState(false);
  const [newDependent, setNewDependent] = useState({
    name: "",
    relationship: "",
    date_of_birth: "",
    tax_dependent: true,
  });

  useEffect(() => {
    if (!id) return;
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [configData, allowancesData, dependentsData] = await Promise.all([
        getSalaryConfig(id!).catch(() => null),
        getAllowances(id!),
        getDependents(id!),
      ]);
      setConfig(configData);
      setAllowances(allowancesData);
      setDependents(dependentsData);
      if (configData) {
        setFormData({
          gross_salary: Number(configData.gross_salary),
          insurance_salary: Number(configData.insurance_salary),
          contract_type: configData.contract_type,
          effective_date: configData.effective_date,
        });
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!id) return;
    setSaving(true);
    try {
      if (config) {
        await updateSalaryConfig(id, formData);
      } else {
        await createSalaryConfig({
          employee_id: id,
          ...formData,
        });
      }
      await loadData();
    } catch (error) {
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  const handleAddAllowance = async () => {
    if (!id) return;
    try {
      await createAllowance({
        employee_id: id,
        ...newAllowance,
      });
      setShowAllowanceDialog(false);
<<<<<<< HEAD
      setNewAllowance({ allowance_type: "telephone", amount: 0, is_taxable: true });
=======
      setNewAllowance({
        allowance_type: "telephone",
        amount: 0,
        is_taxable: true,
      });
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
      loadData();
    } catch (error) {
      console.error(error);
    }
  };

  const handleDeleteAllowance = async (allowanceId: string) => {
    try {
      await deleteAllowance(allowanceId);
      loadData();
    } catch (error) {
      console.error(error);
    }
  };

  const handleAddDependent = async () => {
    if (!id) return;
    try {
      await createDependent({
        employee_id: id,
        ...newDependent,
      });
      setShowDependentDialog(false);
<<<<<<< HEAD
      setNewDependent({ name: "", relationship: "", date_of_birth: "", tax_dependent: true });
=======
      setNewDependent({
        name: "",
        relationship: "",
        date_of_birth: "",
        tax_dependent: true,
      });
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
      loadData();
    } catch (error) {
      console.error(error);
    }
  };

  const handleDeleteDependent = async (dependentId: string) => {
    try {
      await deleteDependent(dependentId);
      loadData();
    } catch (error) {
      console.error(error);
    }
  };

  const formatCurrency = (value: number) =>
<<<<<<< HEAD
    new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
=======
    new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(value);
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Đang tải...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" asChild>
          <Link href={`/employees/${id}`}>
            <ChevronLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Cấu hình lương</h1>
<<<<<<< HEAD
          <p className="text-muted-foreground">Thiết lập lương và phụ cấp cho nhân viên</p>
=======
          <p className="text-muted-foreground">
            Thiết lập lương và phụ cấp cho nhân viên
          </p>
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Thông tin lương cơ bản</CardTitle>
<<<<<<< HEAD
          <CardDescription>Lương gross, lương BH và loại hợp đồng</CardDescription>
=======
          <CardDescription>
            Lương gross, lương BH và loại hợp đồng
          </CardDescription>
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="gross_salary">Lương gross (VNĐ)</Label>
              <Input
                id="gross_salary"
                type="number"
                value={formData.gross_salary}
                onChange={(e) =>
<<<<<<< HEAD
                  setFormData({ ...formData, gross_salary: parseInt(e.target.value) || 0 })
=======
                  setFormData({
                    ...formData,
                    gross_salary: parseInt(e.target.value) || 0,
                  })
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="insurance_salary">Lương BH (VNĐ)</Label>
              <Input
                id="insurance_salary"
                type="number"
                value={formData.insurance_salary}
                onChange={(e) =>
<<<<<<< HEAD
                  setFormData({ ...formData, insurance_salary: parseInt(e.target.value) || 0 })
=======
                  setFormData({
                    ...formData,
                    insurance_salary: parseInt(e.target.value) || 0,
                  })
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                }
              />
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="contract_type">Loại hợp đồng</Label>
              <select
                id="contract_type"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={formData.contract_type}
<<<<<<< HEAD
                onChange={(e) => setFormData({ ...formData, contract_type: e.target.value })}
=======
                onChange={(e) =>
                  setFormData({ ...formData, contract_type: e.target.value })
                }
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
              >
                <option value="official">Chính thức</option>
                <option value="probation">Thử việc</option>
                <option value="contractor">Hợp đồng</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="effective_date">Ngày hiệu lực</Label>
              <Input
                id="effective_date"
                type="date"
                value={formData.effective_date}
<<<<<<< HEAD
                onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
=======
                onChange={(e) =>
                  setFormData({ ...formData, effective_date: e.target.value })
                }
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
              />
            </div>
          </div>
          <Button onClick={handleSaveConfig} disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? "Đang lưu..." : "Lưu thông tin"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Phụ cấp</CardTitle>
            <CardDescription>Các khoản phụ cấp hiện tại</CardDescription>
          </div>
          <Button size="sm" onClick={() => setShowAllowanceDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Thêm phụ cấp
          </Button>
        </CardHeader>
        <CardContent>
          {allowances.length === 0 ? (
<<<<<<< HEAD
            <p className="text-center text-muted-foreground py-4">Chưa có phụ cấp nào</p>
=======
            <p className="text-center text-muted-foreground py-4">
              Chưa có phụ cấp nào
            </p>
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loại</TableHead>
                  <TableHead className="text-right">Số tiền</TableHead>
                  <TableHead>Chịu thuế</TableHead>
                  <TableHead>Ngày hiệu lực</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {allowances.map((allowance) => (
                  <TableRow key={allowance.id}>
<<<<<<< HEAD
                    <TableCell className="font-medium">{allowance.allowance_type}</TableCell>
                    <TableCell className="text-right">{formatCurrency(allowance.amount)}</TableCell>
                    <TableCell>{allowance.is_taxable ? "Có" : "Không"}</TableCell>
=======
                    <TableCell className="font-medium">
                      {allowance.allowance_type}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(allowance.amount)}
                    </TableCell>
                    <TableCell>
                      {allowance.is_taxable ? "Có" : "Không"}
                    </TableCell>
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                    <TableCell>{allowance.effective_date}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteAllowance(allowance.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Người phụ thuộc</CardTitle>
            <CardDescription>Giảm trừ gia cảnh</CardDescription>
          </div>
          <Button size="sm" onClick={() => setShowDependentDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Thêm NPT
          </Button>
        </CardHeader>
        <CardContent>
          {dependents.length === 0 ? (
<<<<<<< HEAD
            <p className="text-center text-muted-foreground py-4">Chưa có người phụ thuộc</p>
=======
            <p className="text-center text-muted-foreground py-4">
              Chưa có người phụ thuộc
            </p>
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tên</TableHead>
                  <TableHead>Quan hệ</TableHead>
                  <TableHead>Ngày sinh</TableHead>
                  <TableHead>Giảm trừ thuế</TableHead>
                  <TableHead className="text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dependents.map((dependent) => (
                  <TableRow key={dependent.id}>
<<<<<<< HEAD
                    <TableCell className="font-medium">{dependent.name}</TableCell>
                    <TableCell>{dependent.relationship}</TableCell>
                    <TableCell>{dependent.date_of_birth || "-"}</TableCell>
                    <TableCell>{dependent.tax_dependent ? "Có" : "Không"}</TableCell>
=======
                    <TableCell className="font-medium">
                      {dependent.name}
                    </TableCell>
                    <TableCell>{dependent.relationship}</TableCell>
                    <TableCell>{dependent.date_of_birth || "-"}</TableCell>
                    <TableCell>
                      {dependent.tax_dependent ? "Có" : "Không"}
                    </TableCell>
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteDependent(dependent.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={showAllowanceDialog} onOpenChange={setShowAllowanceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thêm phụ cấp mới</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Loại phụ cấp</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={newAllowance.allowance_type}
                onChange={(e) =>
<<<<<<< HEAD
                  setNewAllowance({ ...newAllowance, allowance_type: e.target.value })
=======
                  setNewAllowance({
                    ...newAllowance,
                    allowance_type: e.target.value,
                  })
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                }
              >
                <option value="telephone">Điện thoại</option>
                <option value="transport">Xăng xe</option>
                <option value="meal">Cơm trưa</option>
                <option value="housing">Nhà ở</option>
                <option value="responsibility">Trách nhiệm</option>
                <option value="other">Khác</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Số tiền</Label>
              <Input
                type="number"
                value={newAllowance.amount}
                onChange={(e) =>
<<<<<<< HEAD
                  setNewAllowance({ ...newAllowance, amount: parseInt(e.target.value) || 0 })
=======
                  setNewAllowance({
                    ...newAllowance,
                    amount: parseInt(e.target.value) || 0,
                  })
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                }
              />
            </div>
          </div>
          <DialogFooter>
<<<<<<< HEAD
            <Button variant="outline" onClick={() => setShowAllowanceDialog(false)}>
=======
            <Button
              variant="outline"
              onClick={() => setShowAllowanceDialog(false)}
            >
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
              Hủy
            </Button>
            <Button onClick={handleAddAllowance}>Thêm</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showDependentDialog} onOpenChange={setShowDependentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thêm người phụ thuộc</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Tên</Label>
              <Input
                value={newDependent.name}
<<<<<<< HEAD
                onChange={(e) => setNewDependent({ ...newDependent, name: e.target.value })}
=======
                onChange={(e) =>
                  setNewDependent({ ...newDependent, name: e.target.value })
                }
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
              />
            </div>
            <div className="space-y-2">
              <Label>Quan hệ</Label>
              <Input
                value={newDependent.relationship}
                onChange={(e) =>
<<<<<<< HEAD
                  setNewDependent({ ...newDependent, relationship: e.target.value })
=======
                  setNewDependent({
                    ...newDependent,
                    relationship: e.target.value,
                  })
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
                }
              />
            </div>
          </div>
          <DialogFooter>
<<<<<<< HEAD
            <Button variant="outline" onClick={() => setShowDependentDialog(false)}>
=======
            <Button
              variant="outline"
              onClick={() => setShowDependentDialog(false)}
            >
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
              Hủy
            </Button>
            <Button onClick={handleAddDependent}>Thêm</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
<<<<<<< HEAD
}
=======
}
>>>>>>> f5aeb85f5b6ec0b64bb5157cf41fa7dec8199091
