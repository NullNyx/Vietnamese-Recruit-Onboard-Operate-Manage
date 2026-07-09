"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar } from "lucide-react";

export default function AttendanceSchedulesPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Lịch làm việc</h1>
        <p className="text-sm text-muted-foreground">Quản lý lịch làm việc của nhân viên</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Calendar className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Lịch làm</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng quản lý lịch làm việc sẽ sớm được cập nhật.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
