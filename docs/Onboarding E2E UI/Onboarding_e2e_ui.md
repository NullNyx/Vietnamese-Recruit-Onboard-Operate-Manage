# Task 2 — Onboarding E2E UI

**Owner:** Thành viên 2
**Stack:** Next.js App Router · Tailwind CSS · shadcn/ui · React Query (TanStack)
**Route:** `/onboarding` (dashboard layout)

---

## Kế hoạch

### Mục tiêu
HR có thể xem danh sách Candidate đang onboarding, mở detail, tick task, và khi tick hết thì Employee tự động `is_active = true`.

### API sử dụng (không thêm backend)

| Method | Endpoint | Dùng cho |
|--------|----------|----------|
| GET | `/api/onboarding/processes` | List tất cả process, filter theo `?status=` |
| GET | `/api/onboarding/processes/{id}` | Detail 1 process + danh sách task |
| PATCH | `/api/onboarding/tasks/{id}` | Mark task done/undone |

> **Patch nhỏ backend được phép:** bổ sung `employee_full_name`, `employee_email`, `employee_code` vào response của GET processes — chỉ là read-model enrichment, không đổi domain flow.

### Files cần tạo

```
frontend/src/
├── lib/api/
│   └── onboarding.ts                        ← API client + types + query keys
├── components/onboarding/
│   ├── ProcessCard.tsx                       ← Card + StatusBadge component
│   └── OnboardingDetail.tsx                 ← Detail panel + task checklist
└── app/(dashboard)/onboarding/
    └── page.tsx                              ← Route chính
```

### Dependencies cần install

```bash
npm install @tanstack/react-query sonner
```

### shadcn components cần add

```bash
npx shadcn@latest add tabs badge progress skeleton alert button scroll-area
```

### Acceptance checklist

- [ ] HR thấy danh sách Candidate đang onboarding với tên đọc được (không UUID)
- [ ] Filter All / In Progress / Complete hoạt động
- [ ] Progress bar `completed_count / total_count` hiển thị đúng
- [ ] HR mở detail, thấy danh sách Onboarding Task
- [ ] HR tick task → task cập nhật ngay
- [ ] Tick hết task → process `status = complete` → Employee `is_active = true`
- [ ] Loading skeleton, error state, empty state đầy đủ
- [ ] Không chạm `backend/src/main.py`, Gmail/recruitment code, shared header

---

## Code

### 1. `frontend/src/lib/api/onboarding.ts`

```typescript
// frontend/src/lib/api/onboarding.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────

export type ProcessStatus = "in_progress" | "complete";

export interface OnboardingTask {
  id: string;
  title: string;
  description?: string;
  is_done: boolean;
  due_date?: string;
  completed_at?: string;
}

export interface OnboardingProcess {
  id: string;
  status: ProcessStatus;
  employee_id: string;
  employee_full_name: string;
  employee_email: string;
  employee_code?: string;
  start_date: string;
  completed_count: number;
  total_count: number;
  tasks?: OnboardingTask[];
}

export type ProcessFilter = "all" | "in_progress" | "complete";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Query Keys ───────────────────────────────────────────────────────────────

export const onboardingKeys = {
  all: ["onboarding"] as const,
  lists: () => [...onboardingKeys.all, "list"] as const,
  list: (filter: ProcessFilter) => [...onboardingKeys.lists(), filter] as const,
  details: () => [...onboardingKeys.all, "detail"] as const,
  detail: (id: string) => [...onboardingKeys.details(), id] as const,
};

// ─── API Functions ────────────────────────────────────────────────────────────

/** GET /api/onboarding/processes */
export async function listOnboardingProcesses(
  filter: ProcessFilter = "all"
): Promise<OnboardingProcess[]> {
  const params = filter !== "all" ? `?status=${filter}` : "";
  return apiFetch<OnboardingProcess[]>(`/api/onboarding/processes${params}`);
}

/** GET /api/onboarding/processes/{process_id} */
export async function getOnboardingProcess(
  processId: string
): Promise<OnboardingProcess> {
  return apiFetch<OnboardingProcess>(`/api/onboarding/processes/${processId}`);
}

/** PATCH /api/onboarding/tasks/{task_id} */
export async function markTaskDone(
  taskId: string,
  isDone: boolean = true
): Promise<OnboardingTask> {
  return apiFetch<OnboardingTask>(`/api/onboarding/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ is_done: isDone }),
  });
}
```

---

### 2. `frontend/src/components/onboarding/ProcessCard.tsx`

```tsx
// frontend/src/components/onboarding/ProcessCard.tsx
"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { OnboardingProcess } from "@/lib/api/onboarding";

interface ProcessCardProps {
  process: OnboardingProcess;
  selected?: boolean;
  onClick?: () => void;
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function ProcessCard({ process, selected, onClick }: ProcessCardProps) {
  const pct =
    process.total_count > 0
      ? Math.round((process.completed_count / process.total_count) * 100)
      : 0;

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left rounded-xl border bg-card p-4 transition-all duration-150",
        "hover:border-border/80 hover:bg-accent/40",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        selected
          ? "border-primary bg-primary/5 shadow-sm"
          : "border-border"
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="size-9 rounded-lg bg-primary/10 text-primary text-sm font-semibold flex items-center justify-center shrink-0">
          {getInitials(process.employee_full_name)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground truncate">
            {process.employee_full_name}
          </p>
          <p className="text-xs text-muted-foreground truncate">
            {process.employee_email}
          </p>
          {process.employee_code && (
            <p className="text-xs text-primary/70 mt-0.5">
              {process.employee_code}
            </p>
          )}
        </div>
        <StatusBadge status={process.status} />
      </div>

      {/* Progress */}
      <div className="space-y-1.5">
        <Progress value={pct} className="h-1.5" />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {process.completed_count}/{process.total_count} tasks
          </span>
          <span className="text-xs text-muted-foreground">
            {new Date(process.start_date).toLocaleDateString("vi-VN")}
          </span>
        </div>
      </div>
    </button>
  );
}

export function StatusBadge({ status }: { status: string }) {
  if (status === "complete") {
    return (
      <Badge
        variant="outline"
        className="text-emerald-600 border-emerald-200 bg-emerald-50 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-400 text-[10px] px-2 py-0 shrink-0"
      >
        ✓ Done
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="text-amber-600 border-amber-200 bg-amber-50 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-400 text-[10px] px-2 py-0 shrink-0"
    >
      In Progress
    </Badge>
  );
}
```

---

### 3. `frontend/src/components/onboarding/OnboardingDetail.tsx`

```tsx
// frontend/src/components/onboarding/OnboardingDetail.tsx
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Circle, Loader2, CalendarDays, AlertCircle, PartyPopper } from "lucide-react";
import { toast } from "sonner";

import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  getOnboardingProcess,
  markTaskDone,
  onboardingKeys,
  type OnboardingTask,
} from "@/lib/api/onboarding";
import { StatusBadge } from "./ProcessCard";

interface OnboardingDetailProps {
  processId: string;
}

export function OnboardingDetail({ processId }: OnboardingDetailProps) {
  const queryClient = useQueryClient();

  const {
    data: process,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: onboardingKeys.detail(processId),
    queryFn: () => getOnboardingProcess(processId),
  });

  const { mutate: toggleTask, isPending: isToggling, variables } = useMutation({
    mutationFn: ({ taskId, isDone }: { taskId: string; isDone: boolean }) =>
      markTaskDone(taskId, isDone),
    onSuccess: (_, { isDone }) => {
      // Invalidate cả detail lẫn list để progress bar sync
      queryClient.invalidateQueries({ queryKey: onboardingKeys.detail(processId) });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.lists() });
      if (isDone) toast.success("Task hoàn thành!");
    },
    onError: () => {
      toast.error("Cập nhật thất bại, thử lại.");
    },
  });

  // Loading
  if (isLoading) {
    return (
      <div className="flex flex-col h-full p-6 gap-6">
        <div className="flex items-start gap-4">
          <Skeleton className="size-12 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-3.5 w-56" />
          </div>
        </div>
        <Skeleton className="h-2 w-full rounded-full" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  // Error
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-6">
        <Alert variant="destructive" className="max-w-sm">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error instanceof Error ? error.message : "Không tải được dữ liệu"}
          </AlertDescription>
        </Alert>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Thử lại
        </Button>
      </div>
    );
  }

  if (!process) return null;

  const pct =
    process.total_count > 0
      ? Math.round((process.completed_count / process.total_count) * 100)
      : 0;

  const isComplete = process.status === "complete";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Complete banner */}
      {isComplete && (
        <div className="mx-6 mt-6 flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 dark:bg-emerald-950/40 dark:border-emerald-800 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-400 animate-in slide-in-from-top-2">
          <PartyPopper className="h-4 w-4 shrink-0" />
          <span className="font-medium">Onboarding hoàn tất — Employee đã được kích hoạt!</span>
        </div>
      )}

      {/* Employee header */}
      <div className="flex items-start gap-4 px-6 pt-6 pb-4 border-b">
        <div className="size-12 rounded-xl bg-primary/10 text-primary text-base font-semibold flex items-center justify-center shrink-0">
          {getInitials(process.employee_full_name)}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-semibold text-foreground">
            {process.employee_full_name}
          </h2>
          <p className="text-sm text-muted-foreground">{process.employee_email}</p>
          {process.employee_code && (
            <p className="text-xs text-primary/70 mt-0.5">ID: {process.employee_code}</p>
          )}
        </div>
        <StatusBadge status={process.status} />
      </div>

      {/* Progress */}
      <div className="px-6 py-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-foreground">
            {pct}% hoàn thành
          </span>
          <span className="text-xs text-muted-foreground">
            {process.completed_count}/{process.total_count} tasks
          </span>
        </div>
        <Progress value={pct} className="h-2" />
      </div>

      {/* Task list */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Onboarding Tasks
        </p>

        {!process.tasks || process.tasks.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">
            Chưa có task nào.
          </p>
        ) : (
          <div className="space-y-1.5">
            {process.tasks.map((task) => (
              <TaskRow
                key={task.id}
                task={task}
                isLoading={isToggling && variables?.taskId === task.id}
                onToggle={(isDone) => toggleTask({ taskId: task.id, isDone })}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── TaskRow ──────────────────────────────────────────────────────────────────

interface TaskRowProps {
  task: OnboardingTask;
  isLoading: boolean;
  onToggle: (isDone: boolean) => void;
}

function TaskRow({ task, isLoading, onToggle }: TaskRowProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border px-3 py-2.5 transition-all duration-150",
        task.is_done
          ? "border-border/50 bg-muted/30 opacity-60"
          : "border-border bg-card hover:bg-accent/30"
      )}
    >
      <button
        onClick={() => !isLoading && onToggle(!task.is_done)}
        disabled={isLoading}
        className="mt-0.5 shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
        aria-label={task.is_done ? "Bỏ hoàn thành" : "Đánh dấu hoàn thành"}
      >
        {isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        ) : task.is_done ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
        ) : (
          <Circle className="h-5 w-5 text-muted-foreground/50 hover:text-primary transition-colors" />
        )}
      </button>

      <div className="flex-1 min-w-0">
        <p
          className={cn(
            "text-sm font-medium leading-snug",
            task.is_done ? "line-through text-muted-foreground" : "text-foreground"
          )}
        >
          {task.title}
        </p>
        {task.description && (
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            {task.description}
          </p>
        )}
      </div>

      {task.due_date && !task.is_done && (
        <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 shrink-0">
          <CalendarDays className="h-3 w-3" />
          {new Date(task.due_date).toLocaleDateString("vi-VN")}
        </div>
      )}
    </div>
  );
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}
```

---

### 4. `frontend/src/app/(dashboard)/onboarding/page.tsx`

```tsx
// frontend/src/app/(dashboard)/onboarding/page.tsx
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, AlertCircle } from "lucide-react";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  listOnboardingProcesses,
  onboardingKeys,
  type ProcessFilter,
} from "@/lib/api/onboarding";
import { ProcessCard } from "@/components/onboarding/ProcessCard";
import { OnboardingDetail } from "@/components/onboarding/OnboardingDetail";

export default function OnboardingPage() {
  const [filter, setFilter] = useState<ProcessFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: processes, isLoading, isError, error, refetch } = useQuery({
    queryKey: onboardingKeys.list(filter),
    queryFn: () => listOnboardingProcesses(filter),
  });

  const counts = {
    all: processes?.length ?? 0,
    in_progress: processes?.filter((p) => p.status === "in_progress").length ?? 0,
    complete: processes?.filter((p) => p.status === "complete").length ?? 0,
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* ── Left panel: list ────────────────────────────────── */}
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
                  {!isLoading && (
                    <Badge
                      variant="secondary"
                      className="text-[10px] px-1.5 py-0 h-4 font-normal"
                    >
                      {counts[tab.value]}
                    </Badge>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* List body */}
        <ScrollArea className="flex-1">
          <div className="p-3 space-y-2">
            {/* Loading skeletons */}
            {isLoading &&
              [1, 2, 3].map((i) => (
                <div key={i} className="rounded-xl border bg-card p-4 space-y-3">
                  <div className="flex items-start gap-3">
                    <Skeleton className="size-9 rounded-lg" />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton className="h-3.5 w-32" />
                      <Skeleton className="h-3 w-44" />
                    </div>
                    <Skeleton className="h-4 w-16 rounded-full" />
                  </div>
                  <Skeleton className="h-1.5 w-full rounded-full" />
                </div>
              ))}

            {/* Error */}
            {isError && (
              <div className="px-1 py-4 space-y-3">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    {error instanceof Error ? error.message : "Tải danh sách thất bại"}
                  </AlertDescription>
                </Alert>
                <Button variant="outline" size="sm" className="w-full" onClick={() => refetch()}>
                  Thử lại
                </Button>
              </div>
            )}

            {/* Empty */}
            {!isLoading && !isError && processes?.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 gap-2 text-muted-foreground">
                <Users className="h-8 w-8 opacity-30" />
                <p className="text-sm">Không có kết quả</p>
              </div>
            )}

            {/* Cards */}
            {!isLoading &&
              !isError &&
              processes?.map((p) => (
                <ProcessCard
                  key={p.id}
                  process={p}
                  selected={selectedId === p.id}
                  onClick={() => setSelectedId(selectedId === p.id ? null : p.id)}
                />
              ))}
          </div>
        </ScrollArea>
      </aside>

      {/* ── Right panel: detail ─────────────────────────────── */}
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
```

---

## Ghi chú khi tích hợp

- Wrap app với `<QueryClientProvider>` trong `layout.tsx` nếu chưa có
- Thêm `<Toaster />` từ `sonner` vào root layout để toast hoạt động
- `NEXT_PUBLIC_API_URL` set trong `.env.local`
- Backend cần trả `employee_full_name` + `employee_email` trong response của GET processes — nếu chưa có, patch nhỏ vào serializer, không đụng domain logic
