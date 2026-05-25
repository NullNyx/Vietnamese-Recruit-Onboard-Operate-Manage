"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, LogOut } from "lucide-react";

import { useSidebar } from "@/hooks/use-sidebar";
import { useCurrentUser } from "@/hooks/use-current-user";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { employeeNavItems } from "@/lib/employee-navigation";

interface EmployeeSidebarProps {
  className?: string;
}

export function EmployeeSidebar({ className }: EmployeeSidebarProps) {
  const { collapsed, toggle } = useSidebar();
  const pathname = usePathname();
  const { user } = useCurrentUser();

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : "NV";

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex h-screen flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 ease-out overflow-hidden shrink-0",
          collapsed ? "w-16" : "w-64",
          className,
        )}
      >
        {/* Logo section */}
        <div className="flex h-16 items-center gap-3 px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
            V
          </div>
          {!collapsed && (
            <span className="text-lg font-semibold text-sidebar-foreground">
              Vroom ESS
            </span>
          )}
        </div>

        {/* User info section */}
        <div className={cn("px-4 pb-3", collapsed && "px-2")}>
          <div
            className={cn(
              "flex items-center gap-3 rounded-md p-2",
              collapsed && "justify-center p-1",
            )}
          >
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarImage
                src={user?.avatar_url || undefined}
                alt={user?.name || "Nhân viên"}
              />
              <AvatarFallback className="text-xs">{initials}</AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="flex flex-col overflow-hidden">
                <span className="truncate text-sm font-medium text-sidebar-foreground">
                  {user?.name || "Nhân viên"}
                </span>
                <span className="truncate text-xs text-muted-foreground">
                  {user?.email || ""}
                </span>
              </div>
            )}
          </div>
        </div>

        <Separator />

        {/* Navigation section */}
        <nav
          className="flex-1 space-y-1 px-2 py-4"
          aria-label="Điều hướng nhân viên"
        >
          {employeeNavItems.map((item) => {
            const isActive = pathname.startsWith(item.href);

            const linkContent = (
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-muted",
                  collapsed && "justify-center px-0",
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );

            if (collapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              );
            }

            return <div key={item.href}>{linkContent}</div>;
          })}
        </nav>

        {/* Bottom section */}
        <div
          className={cn(
            "mt-auto pb-4 overflow-hidden",
            collapsed ? "px-1" : "px-2",
          )}
        >
          {/* Toggle button */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "default"}
                onClick={toggle}
                className={cn(
                  collapsed
                    ? "mx-auto flex justify-center"
                    : "w-full justify-start gap-3",
                )}
                aria-label={
                  collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"
                }
              >
                {collapsed ? (
                  <ChevronRight className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <>
                    <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                    <span>Thu gọn</span>
                  </>
                )}
              </Button>
            </TooltipTrigger>
            {collapsed && <TooltipContent side="right">Mở rộng</TooltipContent>}
          </Tooltip>

          {/* Logout button */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size={collapsed ? "icon" : "default"}
                onClick={handleLogout}
                className={cn(
                  "mt-1 text-sidebar-foreground hover:bg-muted",
                  collapsed
                    ? "mx-auto flex justify-center"
                    : "w-full justify-start gap-3",
                )}
                aria-label="Đăng xuất"
              >
                <LogOut className="h-5 w-5" aria-hidden="true" />
                {!collapsed && <span>Đăng xuất</span>}
              </Button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">Đăng xuất</TooltipContent>
            )}
          </Tooltip>
        </div>
      </aside>
    </TooltipProvider>
  );
}
