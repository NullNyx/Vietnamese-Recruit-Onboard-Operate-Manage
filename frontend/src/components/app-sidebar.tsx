"use client";

import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, LogOut } from "lucide-react";

import { useSidebar } from "@/hooks/use-sidebar";
import { useCurrentUser } from "@/hooks/use-current-user";
import { NavLink } from "@/components/nav-link";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { navItems, adminNavSection } from "@/lib/navigation";

interface AppSidebarProps {
  className?: string;
}

export function AppSidebar({ className }: AppSidebarProps) {
  const { collapsed, toggle } = useSidebar();
  const pathname = usePathname();
  const { user } = useCurrentUser();
  const isAdmin = user?.role === "admin";

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "flex h-screen flex-col border-r border-[#6C7278]/20 bg-white transition-[width] duration-200 ease-out overflow-hidden shrink-0",
          collapsed ? "w-[60px]" : "w-[240px]",
          className,
        )}
      >
        {/* Logo section */}
        <div className="flex h-14 items-center gap-3 px-4 border-b border-[#6C7278]/10">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#B8422E]">
            <span className="text-[12px] font-bold text-white">V</span>
          </div>
          {!collapsed && (
            <span className="text-[14px] font-semibold tracking-tight text-[#1A1C1E]">
              Vroom
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav
          className="flex-1 space-y-0.5 px-2 py-3 overflow-y-auto"
          aria-label="Điều hướng chính"
        >
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            const linkContent = (
              <NavLink
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-[13px] font-medium transition-all rounded-none",
                  isActive
                    ? "border-l-[3px] border-[#B8422E] text-[#1A1C1E] bg-[#F7F5F2]"
                    : "border-l-[3px] border-transparent text-[#6C7278] hover:bg-[#F7F5F2] hover:text-[#1A1C1E]",
                  collapsed && "justify-center px-2",
                )}
              >
                <item.icon
                  className="h-[18px] w-[18px] shrink-0"
                  aria-hidden="true"
                />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );

            if (collapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent
                    side="right"
                    className="bg-[#1A1C1E] text-white border-[#6C7278]/20"
                  >
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              );
            }

            return <div key={item.href}>{linkContent}</div>;
          })}

          {/* Admin section */}
          {isAdmin && (
            <>
              <div className="my-3 h-px bg-[#6C7278]/10" />
              {!collapsed && (
                <div className="flex items-center gap-2 px-3 py-1.5">
                  <adminNavSection.icon
                    className="h-3.5 w-3.5 text-[#6C7278]"
                    aria-hidden="true"
                  />
                  <span className="text-[10px] font-medium uppercase tracking-widest text-[#6C7278]">
                    {adminNavSection.title}
                  </span>
                </div>
              )}
              {adminNavSection.items.map((item) => {
                const isActive = pathname.startsWith(item.href);

                const linkContent = (
                  <NavLink
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 text-[13px] font-medium transition-all rounded-none",
                      isActive
                        ? "border-l-[3px] border-[#B8422E] text-[#1A1C1E] bg-[#F7F5F2]"
                        : "border-l-[3px] border-transparent text-[#6C7278] hover:bg-[#F7F5F2] hover:text-[#1A1C1E]",
                      collapsed && "justify-center px-2",
                    )}
                  >
                    <item.icon
                      className="h-[18px] w-[18px] shrink-0"
                      aria-hidden="true"
                    />
                    {!collapsed && <span>{item.label}</span>}
                  </NavLink>
                );

                if (collapsed) {
                  return (
                    <Tooltip key={item.href}>
                      <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                      <TooltipContent
                        side="right"
                        className="bg-[#1A1C1E] text-white border-[#6C7278]/20"
                      >
                        {item.label}
                      </TooltipContent>
                    </Tooltip>
                  );
                }

                return <div key={item.href}>{linkContent}</div>;
              })}
            </>
          )}
        </nav>

        {/* Bottom section */}
        <div
          className={cn(
            "mt-auto border-t border-[#6C7278]/10 py-3 space-y-1",
            collapsed ? "px-1" : "px-2",
          )}
        >
          {/* User info */}
          {!collapsed && user && (
            <div className="px-3 py-1.5">
              <p className="text-[12px] font-medium text-[#1A1C1E] truncate">
                {user.email?.split("@")[0]}
              </p>
              <p className="text-[10px] text-[#6C7278] truncate">
                {user.email}
              </p>
            </div>
          )}

          {/* Toggle */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={toggle}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-[13px] text-[#6C7278] transition-all hover:bg-[#F7F5F2] hover:text-[#1A1C1E] rounded-md",
                  collapsed ? "mx-auto justify-center px-2 w-full" : "w-full",
                )}
                aria-label={collapsed ? "Mở rộng" : "Thu gọn"}
              >
                {collapsed ? (
                  <ChevronRight
                    className="h-[18px] w-[18px]"
                    aria-hidden="true"
                  />
                ) : (
                  <>
                    <ChevronLeft
                      className="h-[18px] w-[18px]"
                      aria-hidden="true"
                    />
                    <span>Thu gọn</span>
                  </>
                )}
              </button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent
                side="right"
                className="bg-[#1A1C1E] text-white border-[#6C7278]/20"
              >
                Mở rộng
              </TooltipContent>
            )}
          </Tooltip>

          {/* Logout */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={handleLogout}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-[13px] text-[#6C7278] transition-all hover:bg-[#F7F5F2] hover:text-[#B8422E] rounded-md",
                  collapsed ? "mx-auto justify-center px-2 w-full" : "w-full",
                )}
                aria-label="Đăng xuất"
              >
                <LogOut className="h-[18px] w-[18px]" aria-hidden="true" />
                {!collapsed && <span>Đăng xuất</span>}
              </button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent
                side="right"
                className="bg-[#1A1C1E] text-white border-[#6C7278]/20"
              >
                Đăng xuất
              </TooltipContent>
            )}
          </Tooltip>
        </div>
      </aside>
    </TooltipProvider>
  );
}
