"use client";

import { EmployeeSidebar } from "@/components/employee-sidebar";
import { EmployeeMobileNav } from "@/components/employee-mobile-nav";
import { ThemeToggle } from "@/components/theme-toggle";

export default function EmployeeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar — hidden on mobile, fixed height */}
      <div className="hidden md:block shrink-0">
        <EmployeeSidebar />
      </div>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          {/* Mobile menu trigger */}
          <EmployeeMobileNav />

          {/* Title */}
          <h1 className="text-lg font-semibold text-foreground hidden md:block">
            Cổng nhân viên
          </h1>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Theme toggle */}
          <ThemeToggle />
        </header>

        {/* Main content */}
        <main className="relative flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
