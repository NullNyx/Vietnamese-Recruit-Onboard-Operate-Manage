"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Timer } from "lucide-react";

export default function AttendanceOvertimePage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Tăng ca</h1>
        <p className="text-sm text-muted-foreground">Quản lý đơn tăng ca của nhân viên</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Timer className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Đơn tăng ca</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng quản lý tăng ca sẽ sớm được cập nhật.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
