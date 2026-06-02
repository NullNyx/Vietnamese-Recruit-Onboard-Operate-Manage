"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listOnboardingProcesses, onboardingKeys, type ProcessFilter, type OnboardingProcess } from "@/lib/api/onboarding";
import { ProcessCard } from "@/components/onboarding/ProcessCard";
import { OnboardingDetail } from "@/components/onboarding/OnboardingDetail";
import { Users, AlertCircle } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

function LoadingList() {
  return (
    <div className="p-3 space-y-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-xl border bg-card p-4 space-y-3">
          <div className="flex items-start gap-3">
            <Skeleton className="size-9 rounded-lg" />
            <div className="flex-1 space-y-1.5">
              <Skeleton className="h-3.5 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-1.5 w-full rounded-full" />
        </div>
      ))}
    </div>
  );
}

function ErrorList({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="p-4">
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="text-xs">
          {error.message || "Tải danh sách thất bại"}
        </AlertDescription>
      </Alert>
      <Button variant="outline" size="sm" className="w-full mt-3" onClick={onRetry}>
        Thử lại
      </Button>
    </div>
  );
}

function EmptyList() {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-2 text-muted-foreground">
      <Users className="h-8 w-8 opacity-30" />
      <p className="text-sm">Không có kết quả</p>
    </div>
  );
}

export default function OnboardingPage() {
  const [filter, setFilter] = useState<ProcessFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: onboardingKeys.list(filter),
    queryFn: () => listOnboardingProcesses(filter),
  });

  const processes = data?.items ?? [];
  
  // Compute counts for badge
  const counts = {
    all: data?.total ?? 0,
    in_progress: filter === "in_progress" ? processes.length : (data?.total ?? 0),
    complete: filter === "complete" ? processes.length : 0,
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Left panel: list */}
      <aside className="w-[360px] shrink-0 border-r flex flex-col bg-muted/20">
        {/* Header */}
        <div className="px-5 pt-6 pb-4 border-b">
          <h1 className="text-xl font-semibold tracking-tight">Onboarding</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Theo dõi tiến độ nhân viên mới
          </p>
        </div>

        {/* Filter tabs */}
        <div className="px-4 py-3 border-b">
          <Tabs
            value={filter}
            onValueChange={(v) => {
              setFilter(v as ProcessFilter);
              setSelectedId(null);
            }}
          >
            <TabsList className="w-full h-8 p-0.5">
              {(
                [
                  { value: "all", label: "Tất cả" },
                  { value: "in_progress", label: "Đang làm" },
                  { value: "complete", label: "Xong" },
                ] as { value: ProcessFilter; label: string }[]
              ).map((tab) => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  className="flex-1 text-xs gap-1.5 h-7"
                >
                  {tab.label}
                  {!isLoading && data && (
                    <Badge
                      variant="secondary"
                      className="text-[10px] px-1.5 py-0 h-4 font-normal"
                    >
                      {tab.value === "all" 
                        ? (processes.length > 0 ? data.total : 0)
                        : tab.value === "in_progress"
                          ? processes.filter((p: OnboardingProcess) => p.status === "in_progress").length
                          : processes.filter((p: OnboardingProcess) => p.status === "complete").length}
                    </Badge>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* List body */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && <LoadingList />}
          {isError && <ErrorList error={error as Error} onRetry={() => refetch()} />}
          {!isLoading && !isError && processes.length === 0 && <EmptyList />}
          {!isLoading && !isError && processes.length > 0 && (
            <div className="p-3 space-y-2">
              {processes.map((p: OnboardingProcess) => (
                <ProcessCard
                  key={p.id}
                  process={p}
                  selected={selectedId === p.id}
                  onClick={() => setSelectedId(selectedId === p.id ? null : p.id)}
                />
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Right panel: detail */}
      <main className="flex-1 overflow-hidden">
        {selectedId ? (
          <OnboardingDetail key={selectedId} processId={selectedId} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <Users className="h-10 w-10 opacity-20" />
            <p className="text-sm">Chọn nhân viên để xem chi tiết</p>
          </div>
        )}
      </main>
    </div>
  );
}
