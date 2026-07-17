import {
  User,
  FileText,
  Clock,
  ClipboardList,
  Bot,
  DollarSign,
} from "lucide-react";
import type { HeaderNavConfig } from "./header-nav-config";

export const essNavConfig: HeaderNavConfig = {
  logo: { label: "Vroom ESS", href: "/employee/dashboard" },
  groups: [
    {
      id: "ho-so",
      label: "Hồ sơ",
      links: [
        { href: "/employee/profile", label: "Thông tin", icon: User },
        { href: "/employee/attendance", label: "Chấm công", icon: Clock },
        { href: "/employee/payslips", label: "Bảng lương", icon: DollarSign },
        { href: "/employee/documents", label: "Tài liệu", icon: FileText },
        { href: "/employee/requests", label: "Yêu cầu", icon: ClipboardList },
      ],
      activeRoutes: [
        "/employee/profile",
        "/employee/attendance",
        "/employee/payslips",
        "/employee/documents",
        "/employee/requests",
      ],
    },
    {
      id: "tro-ly",
      label: "Trợ lý",
      links: [
        { href: "/employee/assistant", label: "Trợ lý AI", icon: Bot },
      ],
      activeRoutes: [
        "/employee/assistant",
      ],
    },
  ],
};
