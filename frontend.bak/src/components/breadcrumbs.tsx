"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

const labelMap: Record<string, string> = {
  "": "Trang chủ",
  employees: "Nhân viên",
  settings: "Cài đặt",
  departments: "Phòng ban",
  positions: "Chức vụ",
  gmail: "Gmail",
  new: "Thêm mới",
  recruitment: "Tuyển dụng",
  review: "Xem xét CV",
  metrics: "Số liệu",
  payroll: "Bảng lương",
  config: "Cấu hình",
  allowances: "Phụ cấp",
  tax: "Thuế",
  attendance: "Chấm công",
  payslips: "Phiếu lương",
};

interface BreadcrumbItem {
  label: string;
  href: string;
}

interface BreadcrumbsProps {
  /** Optional display names for dynamic route segments, keyed by segment or href. */
  displayNames?: Record<string, string>;
  /** When false, the home breadcrumb ("Trang chủ") is not rendered. */
  showHome?: boolean;
}

interface BreadcrumbContextValue {
  displayNames: Record<string, string>;
  setDisplayName: (key: string, name: string) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue | null>(null);

export function BreadcrumbProvider({ children }: { children: React.ReactNode }) {
  const [displayNames, setDisplayNames] = useState<Record<string, string>>({});
  const setDisplayName = useCallback((key: string, name: string) => {
    setDisplayNames((current) => {
      if (current[key] === name) return current;
      return { ...current, [key]: name };
    });
  }, []);
  const value = useMemo(
    () => ({ displayNames, setDisplayName }),
    [displayNames, setDisplayName],
  );

  return (
    <BreadcrumbContext.Provider value={value}>
      {children}
    </BreadcrumbContext.Provider>
  );
}

export function useBreadcrumbDisplayName() {
  const context = useContext(BreadcrumbContext);
  return context?.setDisplayName ?? (() => undefined);
}

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isInternalIdentifier(segment: string): boolean {
  return uuidPattern.test(segment) || /^[0-9a-f]{24,}$/i.test(segment);
}

export function Breadcrumbs({ displayNames = {}, showHome = true }: BreadcrumbsProps) {
  const pathname = usePathname();
  const context = useContext(BreadcrumbContext);
  const resolvedDisplayNames = { ...context?.displayNames, ...displayNames };
  const segments = pathname.split("/").filter(Boolean);
  const items: BreadcrumbItem[] = showHome ? [{ label: "Trang chủ", href: "/" }] : [];

  segments.forEach((segment, index) => {
    const href = "/" + segments.slice(0, index + 1).join("/");
    const label =
      resolvedDisplayNames[segment] ??
      resolvedDisplayNames[href] ??
      labelMap[segment] ??
      (isInternalIdentifier(segment) ? "Chi tiết" : segment);

    items.push({ label, href });
  });

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={item.href} className="flex items-center gap-1">
            {index > 0 && (
              <ChevronRight
                className="h-3.5 w-3.5 text-muted-foreground"
                aria-hidden="true"
              />
            )}
            {isLast ? (
              <span
                className="font-medium text-foreground"
                aria-current="page"
              >
                {item.label}
              </span>
            ) : index === 0 ? (
              <Link
                href={item.href}
                className="text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-muted-foreground">
                {item.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
