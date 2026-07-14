"use client";

import { Search, Bell, LogOut, Settings } from "lucide-react";

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
  return (
    <div className="flex items-center gap-1">
      {/* Search trigger */}
      <Button
        variant="ghost"
        size="sm"
        className="gap-2 text-muted-foreground"
        onClick={onSearchClick}
        aria-label="Tìm kiếm (Ctrl+K)"
      >
            <Search className="h-4 w-4" aria-hidden="true" />
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>

      {/* Notifications indicator */}
      <Button
        variant="ghost"
        size="icon"
        className="relative"
        aria-label="Thông báo"
      >
            <Bell className="h-4 w-4" aria-hidden="true" />
        <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
          3
        </span>
      </Button>

      {/* Account menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full"
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
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <a href="/employee/profile" className="cursor-pointer">
              <Settings className="mr-2 h-4 w-4" />
              <span>Cài đặt hồ sơ</span>
            </a>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="cursor-pointer text-destructive focus:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            <span>Đăng xuất</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
