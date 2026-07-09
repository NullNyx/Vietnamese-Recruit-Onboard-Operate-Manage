"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Receipt } from "lucide-react";

export default function PayrollTaxPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Thuế</h1>
        <p className="text-sm text-muted-foreground">Quản lý thuế thu nhập cá nhân</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Receipt className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Thuế TNCN</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng quản lý thuế sẽ sớm được cập nhật.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
