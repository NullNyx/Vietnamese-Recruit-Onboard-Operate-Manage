import {
  User,
  FileText,
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
        { href: "/employee/documents", label: "Tài liệu", icon: FileText },
      ],
      activeRoutes: ["/employee/profile", "/employee/documents"],
    },
  ],
};
