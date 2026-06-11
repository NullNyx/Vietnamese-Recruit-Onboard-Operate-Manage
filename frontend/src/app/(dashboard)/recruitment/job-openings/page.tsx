"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, ChevronLeft, ChevronRight } from "lucide-react";

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

const JO_STATUS_COLORS: Record<JobOpeningStatus, string> = {
  draft:
    "bg-gray-100 text-gray-700",
  open: "bg-green-100 text-green-800",
  closed:
    "bg-yellow-100 text-yellow-800",
  cancelled:
    "bg-red-100 text-red-800",
};

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
    [router],
  );

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleFilterChange = (value: string) => {
    setStatusFilter(value as JobOpeningStatus | "all");
    setPage(1);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-heading text-2xl font-bold">
            Vị trí tuyển dụng
          </h1>
          <p className="text-sm text-muted-foreground">
            Kế hoạch tuyển dụng theo vị trí
          </p>
        </div>
      </div>

      {/* Status filter tabs */}
      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Lọc theo trạng thái">
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
          ),
        )}
      </div>

      {/* aria-live */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      {/* Error State */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center rounded-md border p-12 text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={fetchData} variant="outline">
            Thử lại
          </Button>
        </div>
      )}

      {/* Loading */}
      {loading && <JobOpeningTableSkeleton />}

      {/* Empty */}
      {!loading && !error && data.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-md border p-12 text-center">
          <Briefcase className="h-12 w-12 text-muted-foreground mb-4" aria-hidden="true" />
          <p className="text-muted-foreground">Chưa có vị trí tuyển dụng nào</p>
        </div>
      )}

      {/* Data */}
      {!loading && !error && data.length > 0 && (
        <>
          {/* Desktop Table */}
          <div className="hidden rounded-md border md:block">
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
                      className="cursor-pointer hover:bg-muted"
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
                      <TableCell className="max-w-[200px] truncate font-medium" title={jo.title}>
                        {jo.title}
                        {jo.position_name && (
                          <span className="block text-xs text-muted-foreground truncate">
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
                            "tabular-nums",
                            remaining > 0 && "",
                            remaining === 0 && "text-green-600 font-medium",
                            remaining < 0 && "text-orange-600 font-medium",
                          )}
                        >
                          {remaining > 0
                            ? remaining
                            : remaining === 0
                              ? "Đã đủ"
                              : `Vượt ${Math.abs(remaining)}`}
                        </span>
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {jo.total_candidates}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={JO_STATUS_COLORS[jo.status]}
                        >
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
                  className="cursor-pointer hover:bg-muted/50"
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
                      <span className="font-medium text-sm truncate min-w-0 flex-1">{jo.title}</span>
                      <Badge
                        className={JO_STATUS_COLORS[jo.status] + " shrink-0"}
                      >
                        {JO_STATUS_LABELS[jo.status]}
                      </Badge>
                    </div>
                    {jo.position_name && (
                      <span className="text-xs text-muted-foreground truncate block">{jo.position_name}</span>
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
                            remaining > 0 && "",
                            remaining === 0 && "text-green-600 font-medium",
                            remaining < 0 && "text-orange-600 font-medium",
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
                <SelectTrigger className="h-8 w-[70px]" aria-label="Số dòng mỗi trang">
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
              <span className="text-sm text-muted-foreground">
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
        "inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-primary text-primary-foreground"
          : "bg-muted text-muted-foreground hover:bg-muted/80",
      )}
    >
      {label}
    </button>
  );
}

function JobOpeningTableSkeleton() {
  return (
    <>
      <div className="hidden rounded-md border md:block">
        <Table aria-label="Đang tải">
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
          <Card key={`sk-card-${i}`}>
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
