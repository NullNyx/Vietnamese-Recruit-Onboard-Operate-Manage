"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PartyPopper } from "lucide-react";

export default function AttendanceHolidaysPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Ngày lễ</h1>
        <p className="text-sm text-muted-foreground">Quản lý ngày lễ trong năm</p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <PartyPopper className="h-6 w-6 text-muted-foreground" />
            <div>
              <CardTitle>Ngày lễ</CardTitle>
              <CardDescription>Tính năng đang phát triển</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chức năng quản lý ngày lễ sẽ sớm được cập nhật.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
