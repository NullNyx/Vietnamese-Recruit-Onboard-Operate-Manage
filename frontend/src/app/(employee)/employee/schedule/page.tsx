"use client";

import { useState, useEffect, useCallback } from "react";
import { Clock, Calendar, CalendarDays } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { essApi } from "@/lib/api";
import type { ScheduleResult, ScheduleResponse } from "@/lib/api/ess";

function isSchedule(result: ScheduleResult): result is ScheduleResponse {
  return "schedule_name" in result;
}

const DAY_LABELS: Record<string, string> = {
  monday: "Thứ Hai",
  tuesday: "Thứ Ba",
  wednesday: "Thứ Tư",
  thursday: "Thứ Năm",
  friday: "Thứ Sáu",
  saturday: "Thứ Bảy",
  sunday: "Chủ Nhật",
};

function formatDayName(day: string): string {
  return DAY_LABELS[day.toLowerCase()] || day;
}

function formatHolidayDate(isoString: string): string {
  const d = new Date(isoString);
  return d.toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Ho_Chi_Minh",
  });
}

export default function EmployeeSchedulePage() {
  const [schedule, setSchedule] = useState<ScheduleResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedule = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await essApi.getSchedule();
      setSchedule(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Không thể tải lịch làm việc.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Lịch làm việc</h1>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-5 w-64" />
            <Skeleton className="h-5 w-64" />
            <Skeleton className="h-5 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Lịch làm việc</h1>
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <CalendarDays className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground text-sm">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // No schedule assigned
  if (schedule && !isSchedule(schedule)) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Lịch làm việc</h1>
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <CalendarDays className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground text-sm">
                {schedule.message}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!schedule) return null;

  const scheduleData = schedule as ScheduleResponse;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Lịch làm việc</h1>

      {/* Work Schedule Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Ca làm việc
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Tên lịch</p>
              <p className="font-medium">{scheduleData.schedule_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Giờ làm việc</p>
              <p className="font-medium">
                {scheduleData.shift_start} - {scheduleData.shift_end}
              </p>
            </div>
          </div>

          <div>
            <p className="text-sm text-muted-foreground mb-2">Ngày làm việc</p>
            <div className="flex flex-wrap gap-2">
              {scheduleData.working_days.map((day) => (
                <Badge key={day} variant="secondary">
                  {formatDayName(day)}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Holidays Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Ngày lễ sắp tới
          </CardTitle>
        </CardHeader>
        <CardContent>
          {scheduleData.holidays.length === 0 ? (
            <div className="text-center py-6">
              <Calendar className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
              <p className="text-muted-foreground text-sm">
                Không có ngày lễ sắp tới.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ngày</TableHead>
                    <TableHead>Tên ngày lễ</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scheduleData.holidays.map((holiday) => (
                    <TableRow key={holiday.holiday_date}>
                      <TableCell>
                        {formatHolidayDate(holiday.holiday_date)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {holiday.name}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
