"use client";

import { Search, Bell } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { CurrentUser } from "@/hooks/use-current-user";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

export interface HeaderUtilitiesProps {
  onSearchClick: () => void;
  user: CurrentUser | null;
}

function getInitials(name?: string | null, email?: string | null): string {
  if (name) {
    return name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  }
  if (email) {
    return email[0].toUpperCase();
  }
  return "U";
}

async function handleLogout() {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.href = "/login";
}

export function HeaderUtilities({
  onSearchClick,
  user,
}: HeaderUtilitiesProps): JSX.Element {
  const roleBadgeColor = user?.role === "admin" ? "bg-destructive" : "bg-sky-500";

  return (
    <div className="flex items-center gap-1">
      {/* Search trigger — styled as a small search box */}
      <Button
        variant="ghost"
        size="sm"
        className="gap-2 rounded-lg bg-muted/50 border border-border/30 px-3 py-1.5 text-muted-foreground hover:bg-muted/70 hover:text-foreground w-auto min-w-[140px] justify-between"
        onClick={onSearchClick}
        aria-label="Tìm kiếm (Ctrl+K)"
      >
        <span className="flex items-center gap-2">
          <Search className="h-4 w-4" aria-hidden="true" />
          <span className="text-xs text-muted-foreground/70">Tìm kiếm...</span>
        </span>
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>

      {/* Theme toggle */}
      <ThemeToggle />

      {/* Notifications: no badge until unread data is backed by a real source. */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Thông báo"
            className="relative"
          >
            <Bell className="h-4 w-4" aria-hidden="true" />
            {/* Badge with 0 — disabled style until real data */}
            <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-[14px] items-center justify-center rounded-full bg-muted-foreground/20 px-1 text-[9px] font-semibold text-muted-foreground opacity-30">
              0
            </span>
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-80">
          <div className="flex flex-col items-center gap-3 py-6">
            <Bell className="h-10 w-10 text-muted-foreground/40" aria-hidden="true" />
            <div className="space-y-1 text-center">
              <h2 className="text-sm font-semibold">Thông báo</h2>
              <p className="text-sm text-muted-foreground">
                Bạn không có thông báo mới.
              </p>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Account menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full relative"
            aria-label="Tài khoản"
          >
            <Avatar className="h-8 w-8">
              {user?.avatar_url && (
                <AvatarImage src={user.avatar_url} alt={user.name || ""} />
              )}
              <AvatarFallback className="text-xs">
                {getInitials(user?.name, user?.email)}
              </AvatarFallback>
            </Avatar>
            {/* Role badge — bottom-right corner of avatar */}
            <span
              className={cn(
                "absolute -bottom-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full ring-2 ring-background",
                roleBadgeColor,
              )}
              aria-label={user?.role === "admin" ? "Quản trị viên" : "Nhân viên"}
            >
              <span className="sr-only">
                {user?.role === "admin" ? "Quản trị viên" : "Nhân viên"}
              </span>
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium leading-none">
                {user?.name || "User"}
              </p>
              <p className="text-xs leading-none text-muted-foreground">
                {user?.email || ""}
              </p>
              <p className="text-[10px] leading-none text-muted-foreground/60 mt-1">
                {user?.role === "admin" ? "Quản trị viên" : "Nhân viên"}
              </p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <a href="/employee/profile" className="cursor-pointer">
              <span className="mr-2">⚙️</span>
              <span>Cài đặt hồ sơ</span>
            </a>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          {/* Role switch links */}
          {user?.role === "admin" && (
            <DropdownMenuItem asChild>
              <a href="/employee/dashboard" className="cursor-pointer">
                <span className="mr-2">👤</span>
                <span>Kênh nhân viên</span>
              </a>
            </DropdownMenuItem>
          )}
          {user?.role === "user" && (
            <DropdownMenuItem asChild>
              <a href="/" className="cursor-pointer">
                <span className="mr-2">🔧</span>
                <span>Kênh quản trị</span>
              </a>
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="cursor-pointer text-destructive focus:text-destructive"
            onClick={handleLogout}
          >
            <span className="mr-2">🚪</span>
            <span>Đăng xuất</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

