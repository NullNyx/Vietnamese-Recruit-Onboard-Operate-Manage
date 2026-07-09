"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings } from "lucide-react";

export default function PayrollConfigPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Cấu hình lương</h1>
        <p className="text-sm text-muted-foreground">Cấu hình tham số tính lương</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Settings className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Cấu hình</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng cấu hình lương sẽ sớm được cập nhật.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
