"use client";

import { HeaderNavigation } from "@/components/header-navigation";

export default function EmployeeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      {/* Header navigation — fixed, full-width */}
      <HeaderNavigation />

      {/* Main content — offset below fixed header (h-14 = 3.5rem) */}
      <main className="w-full pt-14">
        <div className="p-4 sm:p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
