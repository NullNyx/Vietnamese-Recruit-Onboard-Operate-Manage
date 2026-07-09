"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign } from "lucide-react";

export default function PayrollPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Bảng lương</h1>
        <p className="text-sm text-muted-foreground">Quản lý lương và thanh toán cho nhân viên</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <DollarSign className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Bảng lương</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng quản lý bảng lương sẽ sớm được cập nhật. 
            Hiện tại, nhân viên có thể xem lương tại /employee/payslips.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
