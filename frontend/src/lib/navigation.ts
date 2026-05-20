import {
  LayoutDashboard,
  Users,
  Building2,
  Briefcase,
  Mail,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { href: "/", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/employees", label: "Nhân viên", icon: Users },
  { href: "/settings/departments", label: "Phòng ban", icon: Building2 },
  { href: "/settings/positions", label: "Chức vụ", icon: Briefcase },
  { href: "/gmail", label: "Gmail", icon: Mail },
];
