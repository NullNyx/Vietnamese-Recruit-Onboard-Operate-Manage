"use client";

import React from "react";
import Link from "next/link";
import {
  Users,
  Building2,
  Briefcase,
  UserPlus,
  FileText,
  ArrowUpRight,
  Target,
  Mail,
  UserCheck,
  Clock,
  Sparkles,
  Sun,
  Moon,
  Sunrise,
} from "lucide-react";

import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useDashboardStats } from "@/hooks/queries";
import { RuntimeHealthPanel } from "@/components/admin/runtime-health-panel";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";

// ─── Quick Action ───────────────────────────────────────────────────────────
function QuickAction({
  title,
  href,
  icon: Icon,
  description,
  variant = "default",
}: {
  title: string;
  href: string;
  icon: React.ElementType;
  description?: string;
  variant?: "default" | "primary";
}) {
  const isPrimary = variant === "primary";

  if (isPrimary) {
    return (
      <Link
        href={href}
        className="group relative isolate flex items-start gap-4 overflow-hidden rounded-xl bg-primary p-4 text-primary-foreground shadow-warm transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5"
      >
        {/* Subtle radial glow */}
        <span
          className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-primary-foreground/10 blur-xl"
          aria-hidden="true"
        />
        <span
          className="absolute -bottom-4 -left-4 h-16 w-16 rounded-full bg-primary-foreground/5 blur-lg"
          aria-hidden="true"
        />
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-foreground/15">
          <Icon className="h-5 w-5 text-primary-foreground" aria-hidden="true" />
        </div>
        <div className="relative flex-1 min-w-0 space-y-0.5">
          <h3 className="text-sm font-semibold">{title}</h3>
          {description && (
            <p className="text-xs text-primary-foreground/70">{description}</p>
          )}
        </div>
        <ArrowUpRight className="relative mt-1 h-3.5 w-3.5 shrink-0 text-primary-foreground/50 opacity-0 transition-all group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
      </Link>
    );
  }

  return (
    <Link
      href={href}
      className="card-hover group flex items-start gap-4 rounded-xl border border-border/40 bg-card p-4 shadow-sm"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors duration-200">
        <Icon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors duration-200" aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0 space-y-0.5">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="text-xs text-muted-foreground/80">{description}</p>
        )}
      </div>
      <ArrowUpRight className="mt-1 h-3.5 w-3.5 shrink-0 text-muted-foreground/30 transition-all group-hover:text-primary group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
    </Link>
  );
}

// ─── Empty State Panel ──────────────────────────────────────────────────────
function EmptyPanel({
  title,
  icon: Icon,
}: {
  title: string;
  icon: React.ElementType;
}) {
  return (
    <div className="fade-in-section rounded-xl border border-border/30 bg-card p-6 shadow-sm">
      <h3 className="mb-5 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        {title}
      </h3>
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/20">
          <Icon className="h-6 w-6 text-muted-foreground/50" aria-hidden="true" strokeWidth={1.5} />
        </div>
        <p className="text-sm font-medium text-muted-foreground">Chưa có dữ liệu</p>
        <p className="mt-1.5 max-w-[200px] text-xs leading-relaxed text-muted-foreground/60">
          Dữ liệu sẽ hiển thị khi có hoạt động mới
        </p>
      </div>
    </div>
  );
}

// ─── Greeting helpers ──────────────────────────────────────────────────────
function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return { text: "Chào buổi sáng", icon: Sunrise };
  if (hour < 18) return { text: "Chào buổi chiều", icon: Sun };
  return { text: "Chào buổi tối", icon: Moon };
}

function formatDate() {
  return new Date().toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

// ─── Greeting Icon ─────────────────────────────────────────────────────────
function GreetingIcon() {
  const [greeting, setGreeting] = React.useState<{ text: string; icon: React.ElementType } | null>(null);

  React.useEffect(() => {
    setGreeting(getGreeting());
  }, []);

  if (!greeting) return null;
  const Icon = greeting.icon;
  // Lighter bg in light, slightly brighter in dark — tinted with primary hue
  return (
    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary dark:bg-primary/15">
      <Icon className="h-5 w-5" aria-hidden="true" strokeWidth={1.5} />
    </div>
  );
}

// ─── Main Dashboard ─────────────────────────────────────────────────────────
export default function DashboardPage() {
  const {
    data: stats,
    isLoading: loading,
    isError,
    refetch,
  } = useDashboardStats();
  const { user } = useCurrentUser();
  const router = useRouter();

  // Redirect employees to their self-service dashboard
  React.useEffect(() => {
    if (!loading && user && user.role === "user" && user.employee_id) {
      router.replace("/employee/dashboard");
    }
  }, [user, loading, router]);

  const [greeting, setGreeting] = React.useState("");
  const [dateStr, setDateStr] = React.useState("");

  React.useEffect(() => {
    setGreeting(getGreeting().text);
    setDateStr(formatDate());
  }, []);

  // Stats skeleton while loading
  const renderStats = () => {
    if (isError) {
      return (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center shadow-sm">
          <p className="text-sm font-medium text-destructive">Không thể tải số liệu tổng quan.</p>
          <p className="mt-1 text-xs text-muted-foreground">Kiểm tra kết nối rồi thử lại.</p>
          <Button
            className="mt-4"
            variant="outline"
            size="sm"
            onClick={() => void refetch()}
          >
            Thử lại
          </Button>
        </div>
      );
    }

    return (
      <div className="stagger-children grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Nhân viên"
          value={stats?.employees ?? 0}
          icon={Users}
          loading={loading}
        />
        <StatCard
          title="Phòng ban"
          value={stats?.departments ?? 0}
          icon={Building2}
          loading={loading}
        />
        <StatCard
          title="Chức vụ"
          value={stats?.positions ?? 0}
          icon={Briefcase}
          loading={loading}
        />
      </div>
    );
  };

      return (
        <div className="animate-page-enter space-y-8 max-w-[1440px] mx-auto overflow-x-hidden pb-10">
          {/* ─── Welcome ──────────────────────────────────────────────── */}
          <section className="fade-in-section">
            <div className="flex items-start gap-4">
              <GreetingIcon />
              <div className="min-w-0 flex-1">
                <h1 className="font-heading text-2xl font-semibold text-foreground tracking-tight">
                  {greeting}
                  {user?.email ? `, ${user.email.split("@")[0]}` : ""}
                  <span className="ml-1.5 inline-flex items-center">👋</span>
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">{dateStr}</p>
              </div>
            </div>
          </section>

          {/* ─── Stats Grid ───────────────────────────────────────────── */}
          <section className="fade-in-section">
            <div className="mb-4 flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-muted-foreground/60" aria-hidden="true" strokeWidth={1.5} />
              <h2 className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                Tổng quan
              </h2>
            </div>
            {renderStats()}
          </section>

          {user?.role === "admin" && (
            <section className="fade-in-section">
              <RuntimeHealthPanel />
            </section>
          )}

          {/* ─── Quick Actions ────────────────────────────────────────── */}
          <section className="fade-in-section">
            <div className="mb-4 flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-muted-foreground/60" aria-hidden="true" strokeWidth={1.5} />
              <h2 className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                Thao tác nhanh
              </h2>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
              <QuickAction
                title="Thêm nhân viên"
                href="/employees/new"
                icon={UserPlus}
                description="Nhập thông tin nhân viên mới"
                variant="primary"
              />
              <QuickAction
                title="Import Excel"
                href="/employees/import"
                icon={FileText}
                description="Nhập hàng loạt từ file"
              />
              <QuickAction
                title="Tuyển dụng"
                href="/recruitment"
                icon={Target}
                description="Quản lý ứng viên và phỏng vấn"
              />
              <QuickAction
                title="Phòng ban"
                href="/settings/departments"
                icon={Building2}
                description="Cơ cấu tổ chức"
              />
              <QuickAction
                title="Chức vụ"
                href="/settings/positions"
                icon={Briefcase}
                description="Danh sách vị trí"
              />
              <QuickAction
                title="Gmail"
                href="/gmail"
                icon={Mail}
                description="Hộp thư kết nối"
              />
            </div>
          </section>

          {/* ─── Bottom Panels ────────────────────────────────────────── */}
          <section className="fade-in-section">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 stagger-children">
              <EmptyPanel title="Hoạt động gần đây" icon={Clock} />
              <EmptyPanel title="Nhân viên mới tháng này" icon={UserCheck} />
            </div>
          </section>
        </div>
  );
}
