"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Target,
  CheckCircle2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  listJobOpenings,
  type JobOpeningListItem,
  type JobOpeningStatus,
  type JobOpeningListParams,
} from "@/lib/api/recruitment";

// ---------------------------------------------------------------------------
// Status labels and colors
// ---------------------------------------------------------------------------

const JO_STATUS_LABELS: Record<JobOpeningStatus, string> = {
  draft: "Nháp",
  open: "Đang tuyển",
  closed: "Đã đóng",
  cancelled: "Đã huỷ",
};

const JO_BADGE_VARIANTS: Record<JobOpeningStatus, "secondary" | "default" | "outline" | "destructive"> = {
  draft: "secondary",
  open: "default",
  closed: "outline",
  cancelled: "destructive",
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FilterTab({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      role="radio"
      aria-checked={active}
      onClick={onClick}
      className={cn(
        "inline-flex items-center rounded-lg px-3.5 py-1.5 text-sm font-medium transition-all duration-150",
        active
          ? "bg-primary text-primary-foreground shadow-sm"
          : "bg-muted/60 text-muted-foreground hover:bg-muted border border-transparent",
      )}
    >
      {label}
    </button>
  );
}

function JobOpeningTableSkeleton() {
  return (
    <>
      <div className="hidden rounded-xl border shadow-sm md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Vị trí</TableHead>
              <TableHead>Mục tiêu</TableHead>
              <TableHead>Đã nhận</TableHead>
              <TableHead>Còn thiếu</TableHead>
              <TableHead>Tổng ứng viên</TableHead>
              <TableHead>Trạng thái</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={`sk-${i}`}>
                <TableCell><Skeleton className="h-5 w-32" /></TableCell>
                <TableCell><Skeleton className="h-5 w-8" /></TableCell>
                <TableCell><Skeleton className="h-5 w-8" /></TableCell>
                <TableCell><Skeleton className="h-5 w-12" /></TableCell>
                <TableCell><Skeleton className="h-5 w-8" /></TableCell>
                <TableCell><Skeleton className="h-5 w-20" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="space-y-3 md:hidden">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={`sk-card-${i}`} className="shadow-sm">
            <CardContent className="p-4 space-y-2">
              <div className="flex justify-between">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-16" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-16" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function JobOpeningsPage() {
  const router = useRouter();

  const [data, setData] = useState<JobOpeningListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<JobOpeningStatus | "all">("all");
  const [announcement, setAnnouncement] = useState("");

  const latestReqId = useRef<symbol | null>(null);

  const fetchData = useCallback(async () => {
    const requestId = Symbol();
    latestReqId.current = requestId;
    setLoading(true);
    setError(null);
    try {
      const params: JobOpeningListParams = {
        page,
        page_size: pageSize,
        status: statusFilter !== "all" ? [statusFilter] : undefined,
      };
      const result = await listJobOpenings(params);
      if (latestReqId.current !== requestId) return;
      setData(result.job_openings);
      setTotalCount(result.total_count);
      setAnnouncement(
        `Đã tải ${result.job_openings.length} vị trí trong tổng số ${result.total_count}`
      );
    } catch (err) {
      if (latestReqId.current !== requestId) return;
      const message =
        err instanceof Error
          ? err.message
          : "Không thể tải danh sách vị trí tuyển dụng";
      setError(message);
      setAnnouncement("Lỗi khi tải danh sách vị trí");
    } finally {
      if (latestReqId.current === requestId) {
        setLoading(false);
      }
    }
  }, [page, pageSize, statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRowClick = useCallback(
    (jo: JobOpeningListItem) => {
      router.push(`/recruitment/job-openings/${jo.id}`);
    },
    [router]
  );

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleFilterChange = (value: string) => {
    setStatusFilter(value as JobOpeningStatus | "all");
    setPage(1);
  };

  return (
    <div className="animate-page-enter space-y-6 max-w-[1200px] mx-auto overflow-x-hidden pb-10">
      {/* ─── Page Header ──────────────────────────────── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Briefcase className="h-4 w-4" strokeWidth={1.5} />
            </div>
            <h1 className="font-heading text-2xl font-bold">
              Vị trí tuyển dụng
            </h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground ml-10">
            Kế hoạch tuyển dụng theo vị trí
          </p>
        </div>
      </div>

      {/* ─── Filters / Tabs ───────────────────────────── */}
      <div
        className="flex flex-wrap gap-2"
        role="radiogroup"
        aria-label="Lọc theo trạng thái"
      >
        <FilterTab
          active={statusFilter === "all"}
          onClick={() => handleFilterChange("all")}
          label="Tất cả"
        />
        {(["draft", "open", "closed", "cancelled"] as JobOpeningStatus[]).map(
          (s) => (
            <FilterTab
              key={s}
              active={statusFilter === s}
              onClick={() => handleFilterChange(s)}
              label={JO_STATUS_LABELS[s]}
            />
          )
        )}
      </div>

      {/* aria-live */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      {/* Error State */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-destructive/20 bg-destructive/5 p-12 text-center shadow-sm">
          <Target className="h-10 w-10 text-destructive/60 mb-3" strokeWidth={1.5} />
          <p className="text-sm font-medium text-destructive">{error}</p>
          <Button
            onClick={fetchData}
            variant="outline"
            size="sm"
            className="mt-4"
          >
            Thử lại
          </Button>
        </div>
      )}

      {/* Loading */}
      {loading && <JobOpeningTableSkeleton />}

      {/* Empty */}
      {!loading && !error && data.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border/30 bg-card p-14 text-center shadow-sm">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/20">
            <Briefcase
              className="h-6 w-6 text-muted-foreground/50"
              strokeWidth={1.5}
            />
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            Chưa có vị trí tuyển dụng nào
          </p>
          <p className="mt-1 text-xs text-muted-foreground/60">
            Tạo vị trí tuyển dụng đầu tiên để bắt đầu
          </p>
        </div>
      )}

      {/* Data */}
      {!loading && !error && data.length > 0 && (
        <>
          {/* Stats summary */}
          <div className="animate-fade-in flex flex-wrap items-center gap-4 rounded-xl border border-border/30 bg-card px-5 py-3 shadow-sm">
            <div className="flex items-center gap-2 text-sm">
              <Sparkles className="h-3.5 w-3.5 text-muted-foreground/60" strokeWidth={1.5} />
              <span className="text-muted-foreground">
                <strong className="text-foreground tabular-nums">{data.length}</strong> vị trí
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="inline-flex h-2 w-2 rounded-full bg-green-500" />
              {data.filter((j) => j.status === "open").length} đang tuyển
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <CheckCircle2 className="h-3 w-3" strokeWidth={1.5} />
              {data.filter((j) => j.target_headcount - j.accepted_count <= 0).length} đã đủ chỉ tiêu
            </div>
          </div>

          {/* Desktop Table */}
          <div className="hidden rounded-xl border shadow-sm md:block">
            <Table aria-label="Danh sách vị trí tuyển dụng">
              <TableHeader>
                <TableRow>
                  <TableHead scope="col">Vị trí</TableHead>
                  <TableHead scope="col">Mục tiêu</TableHead>
                  <TableHead scope="col">Đã nhận</TableHead>
                  <TableHead scope="col">Còn thiếu</TableHead>
                  <TableHead scope="col">Tổng ứng viên</TableHead>
                  <TableHead scope="col">Trạng thái</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((jo) => {
                  const remaining = jo.target_headcount - jo.accepted_count;
                  return (
                    <TableRow
                      key={jo.id}
                      className="cursor-pointer hover:bg-muted/70 transition-colors"
                      tabIndex={0}
                      role="link"
                      aria-label={`Xem chi tiết ${jo.title}`}
                      onClick={() => handleRowClick(jo)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleRowClick(jo);
                        }
                      }}
                    >
                      <TableCell
                        className="max-w-[200px] truncate font-medium"
                        title={jo.title}
                      >
                        {jo.title}
                        {jo.position_name && (
                          <span className="block text-xs text-muted-foreground/70 truncate">
                            {jo.position_name}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {jo.target_headcount}
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {jo.accepted_count}
                      </TableCell>
                      <TableCell className="tabular-nums">
                        <span
                          className={cn(
                            remaining > 0 && "text-muted-foreground",
                            remaining === 0 && "text-green-600 dark:text-green-400 font-medium",
                            remaining < 0 && "text-amber-600 dark:text-amber-400 font-medium",
                          )}
                        >
                          {remaining > 0
                            ? remaining
                            : remaining === 0
                              ? "Đã đủ"
                              : `Vượt ${Math.abs(remaining)}`}
                        </span>
                      </TableCell>
                      <TableCell className="tabular-nums text-muted-foreground">
                        {jo.total_candidates}
                      </TableCell>
                      <TableCell>
                        <Badge variant={JO_BADGE_VARIANTS[jo.status]}>
                          {JO_STATUS_LABELS[jo.status]}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Cards */}
          <div className="space-y-3 md:hidden">
            {data.map((jo) => {
              const remaining = jo.target_headcount - jo.accepted_count;
              return (
                <Card
                  key={jo.id}
                  className="card-hover cursor-pointer shadow-sm"
                  tabIndex={0}
                  role="link"
                  aria-label={`Xem chi tiết ${jo.title}`}
                  onClick={() => handleRowClick(jo)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleRowClick(jo);
                    }
                  }}
                >
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-medium text-sm truncate min-w-0 flex-1">
                        {jo.title}
                      </span>
                      <Badge
                        variant={JO_BADGE_VARIANTS[jo.status]}
                        className="shrink-0"
                      >
                        {JO_STATUS_LABELS[jo.status]}
                      </Badge>
                    </div>
                    {jo.position_name && (
                      <span className="text-xs text-muted-foreground truncate block">
                        {jo.position_name}
                      </span>
                    )}
                    <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
                      <div>
                        <span className="text-xs">
                          Mục tiêu: {jo.target_headcount}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs">
                          Đã nhận: {jo.accepted_count}
                        </span>
                      </div>
                      <div>
                        <span
                          className={cn(
                            "text-xs",
                            remaining > 0 && "text-muted-foreground",
                            remaining === 0 &&
                              "text-green-600 dark:text-green-400 font-medium",
                            remaining < 0 &&
                              "text-amber-600 dark:text-amber-400 font-medium",
                          )}
                        >
                          {remaining > 0
                            ? `Còn: ${remaining}`
                            : remaining === 0
                              ? "Đã đủ"
                              : `Vượt ${Math.abs(remaining)}`}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs">
                          Ứng viên: {jo.total_candidates}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Hiển thị</span>
              <Select
                value={String(pageSize)}
                onValueChange={(v) => {
                  setPageSize(Number(v));
                  setPage(1);
                }}
              >
                <SelectTrigger
                  className="h-8 w-[70px]"
                  aria-label="Số dòng mỗi trang"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm tabular-nums text-muted-foreground">
                Trang {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
                aria-label="Trang trước"
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
                aria-label="Trang sau"
              >
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
