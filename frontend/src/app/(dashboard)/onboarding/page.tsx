"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { getOnboardingCounts, listOnboardingProcesses, onboardingKeys } from "@/lib/api/onboarding";
import { Sparkles, Activity, Target, CheckCircle2, UserPlus } from "lucide-react";
import { StatCard } from "@/components/stat-card";
import { ProcessCard } from "@/components/onboarding/ProcessCard";

export default function OnboardingDashboard() {
  const router = useRouter();
  const { data: counts, isLoading } = useQuery({
    queryKey: onboardingKeys.counts(),
    queryFn: getOnboardingCounts,
  });

  const { data: processes } = useQuery({
    queryKey: onboardingKeys.list("in_progress"),
    queryFn: () => listOnboardingProcesses("in_progress"),
  });

  const activeProcesses = processes?.items ?? [];

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
              {counts && counts.ready_for_completion > 0 ? (
                <> Có <strong>{counts.ready_for_completion}</strong> hồ sơ sẵn sàng kích hoạt.</>
              ) : (
                <> Không có hồ sơ nào cần xử lý ngay.</>
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
          title="Sẵn sàng"
          value={counts?.ready_for_completion ?? 0}
          icon={CheckCircle2}
          subtitle="Chờ kích hoạt"
          loading={isLoading}
        />
        <StatCard
          title="Hoàn tất"
          value={counts?.complete ?? 0}
          icon={CheckCircle2}
          subtitle="Đã kích hoạt"
          loading={isLoading}
        />
      </div>

      {/* ─── Active Processes ─────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            Hồ sơ đang xử lý
          </h2>
          <span className="text-xs text-muted-foreground">
            {counts?.in_progress ?? 0} hồ sơ
          </span>
        </div>

        {activeProcesses.length === 0 ? (
          <div className="rounded-xl border border-dashed bg-card p-12 text-center">
            <UserPlus className="mx-auto h-8 w-8 text-muted-foreground/40" />
            <p className="mt-3 text-sm text-muted-foreground">Không có hồ sơ đang xử lý</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {activeProcesses.map((p) => (
              <ProcessCard
                key={p.id}
                process={p}
                selected={false}
                onClick={() => router.push(`/onboarding/cases/${p.id}`)}
              />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
