import {
  User,
  FileText,
  Clock,
  ClipboardList,
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
        { href: "/employee/documents", label: "Tài liệu", icon: FileText },
        { href: "/employee/requests", label: "Yêu cầu", icon: ClipboardList },
      ],
      activeRoutes: [
        "/employee/profile",
        "/employee/attendance",
        "/employee/documents",
        "/employee/requests",
      ],
    },
  ],
};
