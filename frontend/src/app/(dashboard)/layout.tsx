"use client";

import { HeaderNavigation } from "@/components/header-navigation";
import {
  BreadcrumbProvider,
  Breadcrumbs,
} from "@/components/breadcrumbs";
import { NavigationProgress } from "@/components/navigation-progress";
import { PageTransition } from "@/components/page-transition";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <BreadcrumbProvider>
      <div className="min-h-screen bg-background">
        <NavigationProgress />
        <HeaderNavigation />
        <main className="w-full pt-14">
          <div className="group/content p-5 lg:p-8 has-[.gmail-fullbleed]:p-0 has-[.gmail-fullbleed]:overflow-hidden has-[.gmail-fullbleed]:h-[calc(100vh-3.5rem)]">
            <div className="group-has-[.gmail-fullbleed]/content:hidden">
              <Breadcrumbs />
            </div>
            <PageTransition>{children}</PageTransition>
          </div>
        </main>
      </div>
    </BreadcrumbProvider>
  );
}
