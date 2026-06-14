import {
  LayoutDashboard,
  User,
  FileText,
  Clock,
  ClipboardList,
  Bot,
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
  { href: "/employee/documents", label: "Tài liệu", icon: FileText },
  { href: "/employee/requests", label: "Yêu cầu", icon: ClipboardList },
  { href: "/employee/assistant", label: "Trợ lý", icon: Bot },
];
