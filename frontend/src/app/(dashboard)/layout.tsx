"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageTransition } from "@/components/page-transition";
import { TourOverlay } from "@/components/tour-overlay";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-[#FAF9F6]">
      <AppSidebar />
      <main className="flex-1 overflow-auto p-6 lg:p-8">
        <Breadcrumbs />
        <div className="mt-6">
          <PageTransition>{children}</PageTransition>
        </div>
      </main>
      <TourOverlay />
    </div>
  );
}
