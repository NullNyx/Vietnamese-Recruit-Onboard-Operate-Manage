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
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { navItems, adminNavSection } from "@/lib/navigation";
import { useCurrentUser } from "@/hooks/use-current-user";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { user } = useCurrentUser();
  const isAdmin = user?.role === "admin";

  const handleLogout = async () => {
    setOpen(false);
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <Button
        variant="ghost"
        size="icon"
        className="min-h-[44px] min-w-[44px] text-[#1A1C1E] hover:bg-[#F7F5F2] md:hidden"
        onClick={() => setOpen(true)}
        aria-label="Mở menu điều hướng"
      >
        <Menu className="h-6 w-6" aria-hidden="true" />
      </Button>

      <SheetContent
        side="left"
        className="flex w-72 flex-col border-r border-[#6C7278]/20 bg-white p-0"
      >
        <SheetHeader className="px-4 pt-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[#B8422E] text-sm font-bold text-white">
              V
            </div>
            <SheetTitle className="text-lg font-semibold text-[#1A1C1E]">
              Vroom HR
            </SheetTitle>
          </div>
          <SheetDescription className="sr-only">
            Menu điều hướng chính
          </SheetDescription>
        </SheetHeader>

        <div className="mx-4 mt-4 h-px bg-[#6C7278]/10" />

        {/* Navigation links */}
        <nav
          className="flex-1 space-y-0.5 px-2 py-4"
          aria-label="Điều hướng chính"
        >
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex min-h-[44px] items-center gap-3 px-3 py-2 text-[13px] font-medium transition-colors rounded-none",
                  isActive
                    ? "border-l-[3px] border-[#B8422E] text-[#1A1C1E] bg-[#F7F5F2]"
                    : "border-l-[3px] border-transparent text-[#6C7278] hover:bg-[#F7F5F2] hover:text-[#1A1C1E]",
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          {/* Admin navigation section — only visible to admin users */}
          {isAdmin && (
            <>
              <div className="my-3 h-px bg-[#6C7278]/10" />
              <div className="flex items-center gap-2 px-3 py-1.5">
                <adminNavSection.icon
                  className="h-3.5 w-3.5 text-[#6C7278]"
                  aria-hidden="true"
                />
                <span className="text-[10px] font-medium uppercase tracking-widest text-[#6C7278]">
                  {adminNavSection.title}
                </span>
              </div>
              {adminNavSection.items.map((item) => {
                const isActive = pathname.startsWith(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex min-h-[44px] items-center gap-3 px-3 py-2 text-[13px] font-medium transition-colors rounded-none",
                      isActive
                        ? "border-l-[3px] border-[#B8422E] text-[#1A1C1E] bg-[#F7F5F2]"
                        : "border-l-[3px] border-transparent text-[#6C7278] hover:bg-[#F7F5F2] hover:text-[#1A1C1E]",
                    )}
                  >
                    <item.icon
                      className="h-5 w-5 shrink-0"
                      aria-hidden="true"
                    />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </>
          )}
        </nav>

        {/* Bottom section */}
        <div className="mt-auto border-t border-[#6C7278]/10 px-2 pb-4 pt-3">
          {user && (
            <div className="px-3 py-1.5 mb-2">
              <p className="text-[12px] font-medium text-[#1A1C1E] truncate">
                {user.email?.split("@")[0]}
              </p>
              <p className="text-[10px] text-[#6C7278] truncate">
                {user.email}
              </p>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex min-h-[44px] w-full items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium text-[#6C7278] transition-colors hover:bg-[#F7F5F2] hover:text-[#B8422E]"
            aria-label="Đăng xuất"
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
