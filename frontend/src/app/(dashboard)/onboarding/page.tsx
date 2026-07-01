"use client";

import { useQuery } from "@tanstack/react-query";
import { getOnboardingCounts, onboardingKeys } from "@/lib/api/onboarding";
import { Sparkles, Activity, Target, CheckCircle2, AlertTriangle } from "lucide-react";
import { StatCard } from "@/components/stat-card";

export default function OnboardingDashboard() {
  const { data: counts, isLoading } = useQuery({
    queryKey: onboardingKeys.counts(),
    queryFn: getOnboardingCounts,
  });

  return (
    <div className="space-y-8 max-w-[1440px] mx-auto">
      {/* ─── Header ──────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-semibold text-[#09090B]">Onboarding Dashboard</h1>
        <p className="mt-1 text-sm text-[#71717A]">Theo dõi tiến độ nhân viên mới</p>
      </div>

      {/* ─── AI Assistant Card ────────────────────────────────────────── */}
      <div className="rounded-xl border border-primary/40 bg-white p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-[#09090B]">Trợ lý AI</p>
            <p className="text-sm text-[#71717A]">
              Hôm nay có <strong>{counts?.in_progress ?? 0}</strong> onboarding đang tiến hành.
              Tổng số <strong>{counts?.total ?? 0}</strong> hồ sơ từ trước đến nay.
              {counts && counts.in_progress > 0 ? (
                <> Còn <strong>{counts.in_progress}</strong> hồ sơ cần hoàn tất.</>
              ) : (
                <> Không có hồ sơ nào quá hạn.</>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* ─── Metrics Grid ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Tổng hồ sơ"
          value={counts?.total ?? 0}
          icon={Activity}
          loading={isLoading}
        />
        <StatCard
          title="Đang thực hiện"
          value={counts?.in_progress ?? 0}
          icon={Target}
          loading={isLoading}
        />
        <StatCard
          title="Hoàn tất"
          value={counts?.complete ?? 0}
          icon={CheckCircle2}
          loading={isLoading}
        />
        <StatCard
          title="Cần chú ý"
          value={counts?.total ?? 0} // ponytail: show total; replace with real "attention" count when available
          icon={AlertTriangle}
          subtitle="Hồ sơ thiếu thông tin"
          loading={isLoading}
        />
      </div>
    </div>
  );
}
