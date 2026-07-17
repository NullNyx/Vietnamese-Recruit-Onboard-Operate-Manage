"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, LogOut } from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { employeeNavItems } from "@/lib/employee-navigation";
import { useCurrentUser } from "@/hooks/use-current-user";

export function EmployeeMobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { user } = useCurrentUser();

  const handleLogout = async () => {
    setOpen(false);
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
    <Sheet open={open} onOpenChange={setOpen}>
      <Button
        variant="ghost"
        size="icon"
        className="min-h-[44px] min-w-[44px] md:hidden"
        onClick={() => setOpen(true)}
        aria-label="Mở menu điều hướng"
      >
        <Menu className="h-6 w-6" aria-hidden="true" />
      </Button>

      <SheetContent side="left" className="flex w-72 flex-col p-0">
        <SheetHeader className="px-4 pt-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
              V
            </div>
            <SheetTitle className="text-lg font-semibold">Vroom ESS</SheetTitle>
          </div>
          <SheetDescription className="sr-only">
            Menu điều hướng nhân viên
          </SheetDescription>
        </SheetHeader>

        {/* User info */}
        <div className="flex items-center gap-3 px-4 py-3">
          <Avatar className="h-9 w-9">
            <AvatarImage
              src={user?.avatar_url || undefined}
              alt={user?.name || "Nhân viên"}
            />
            <AvatarFallback className="text-xs">{initials}</AvatarFallback>
          </Avatar>
          <div className="flex flex-col overflow-hidden">
            <span className="truncate text-sm font-medium">
              {user?.name || "Nhân viên"}
            </span>
            <span className="truncate text-xs text-muted-foreground">
              {user?.email || ""}
            </span>
          </div>
        </div>

        <Separator />

        {/* Navigation links */}
        <nav
          className="flex-1 space-y-1 px-2 py-4"
          aria-label="Điều hướng nhân viên"
        >
          {employeeNavItems.map((item) => {
            const isActive = pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex min-h-[44px] items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-muted",
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="mt-auto px-2 pb-4">
          <Separator className="mb-4" />
          <Button
            variant="ghost"
            onClick={handleLogout}
            className="min-h-[44px] w-full justify-start gap-3 text-sidebar-foreground hover:bg-muted"
            aria-label="Đăng xuất"
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
            <span>Đăng xuất</span>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
