"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Gift } from "lucide-react";

export default function PayrollAllowancesPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Phụ cấp</h1>
        <p className="text-sm text-muted-foreground">Quản lý các khoản phụ cấp cho nhân viên</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Gift className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Phụ cấp</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng quản lý phụ cấp sẽ sớm được cập nhật.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
