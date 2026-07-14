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

  return (
    <Link
      href={href}
      className={`group flex items-start gap-4 rounded-xl p-4 transition-all ${
        isPrimary
          ? "bg-primary text-primary-foreground"
          : "border border-border/50 bg-card text-foreground hover:border-border hover:shadow-sm"
      }`}
    >
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
          isPrimary ? "bg-primary-foreground/20" : "bg-secondary"
        }`}
      >
        <Icon
          className={`h-5 w-5 ${isPrimary ? "text-primary-foreground" : "text-muted-foreground"}`}
          aria-hidden="true"
        />
      </div>
      <div className="flex-1 min-w-0 space-y-0.5">
        <h3 className="text-sm font-semibold">{title}</h3>
        {description && (
          <p
            className={`text-xs ${isPrimary ? "text-primary-foreground/70" : "text-muted-foreground"}`}
          >
            {description}
          </p>
        )}
      </div>
      <ArrowUpRight
        className={`mt-1 h-3.5 w-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 ${
          isPrimary ? "text-primary-foreground/70" : "text-muted-foreground"
        }`}
      />
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
    <div className="rounded-xl border border-border/30 bg-card p-6">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        {title}
      </h3>
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
          <Icon className="h-5 w-5 text-muted-foreground/60" aria-hidden="true" />
        </div>
        <p className="text-sm text-muted-foreground">Chưa có dữ liệu</p>
        <p className="mt-1 text-xs text-muted-foreground/60">
          Dữ liệu sẽ hiển thị khi có hoạt động mới
        </p>
      </div>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Chào buổi sáng";
  if (hour < 18) return "Chào buổi chiều";
  return "Chào buổi tối";
}

function formatDate() {
  return new Date().toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
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
    setGreeting(getGreeting());
    setDateStr(formatDate());
  }, []);

  return (
    <div className="space-y-10 max-w-[1440px] mx-auto overflow-x-hidden">
      {/* ─── Welcome ─────────────────────────────────────────────────────── */}
      <div>
        <h1 className="font-heading text-2xl font-semibold text-foreground">
          {greeting}
          {user?.email ? `, ${user.email.split("@")[0]}` : ""}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">{dateStr}</p>
      </div>

      {/* ─── Stats Grid ──────────────────────────────────────────────────── */}
      <div>
        <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          Tổng quan
        </h2>
        {isError ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm">
            <p className="font-medium text-destructive">Không thể tải số liệu tổng quan.</p>
            <p className="mt-1 text-muted-foreground">Kiểm tra kết nối rồi thử lại.</p>
            <Button className="mt-4" variant="outline" size="sm" onClick={() => void refetch()}>
              Thử lại
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
        )}
        </div>

        {user?.role === "admin" && <RuntimeHealthPanel />}

        {/* ─── Quick Actions ───────────────────────────────────────────────── */}
        <div>
        <h2 className="mb-4 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          Thao tác nhanh
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
      </div>

      {/* ─── Bottom Panels ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <EmptyPanel title="Hoạt động gần đây" icon={Clock} />
        <EmptyPanel title="Nhân viên mới tháng này" icon={UserCheck} />
      </div>
    </div>
  );
}
