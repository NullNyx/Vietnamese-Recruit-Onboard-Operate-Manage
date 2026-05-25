import {
  LayoutDashboard,
  User,
  Clock,
  CalendarDays,
  Timer,
  FileText,
  Calendar,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface EmployeeNavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const employeeNavItems: EmployeeNavItem[] = [
  { href: "/employee/dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/employee/profile", label: "Hồ sơ", icon: User },
  { href: "/employee/attendance", label: "Chấm công", icon: Clock },
  { href: "/employee/leave", label: "Nghỉ phép", icon: CalendarDays },
  { href: "/employee/overtime", label: "Tăng ca", icon: Timer },
  { href: "/employee/documents", label: "Tài liệu", icon: FileText },
  { href: "/employee/schedule", label: "Lịch làm việc", icon: Calendar },
];
