"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  MailQuestion,
  Users,
  UserPlus,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Search,
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
import {
  CandidateFilterPanel,
  type CandidateFilterChangePayload,
} from "@/components/recruitment/candidate-filter-panel";
import { CandidateStatusBadge } from "@/components/recruitment/candidate-status-badge";
import { ConfidenceScore } from "@/components/recruitment/confidence-score";
import { formatDate, type CandidateStatus as UtilsCandidateStatus } from "@/lib/recruitment-utils";
import {
  listCandidates,
  type CandidateListParams,
  type CandidateListItem,
} from "@/lib/api/recruitment";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Renders skill badges with a max of 5 + "+N" indicator */
function SkillsBadges({ skills }: { skills: string[] }) {
  if (!skills || skills.length === 0) {
    return <span className="text-muted-foreground/60">—</span>;
  }

  const displayed = skills.slice(0, 5);
  const remaining = skills.length - 5;

  return (
    <div className="flex flex-wrap gap-1">
      {displayed.map((skill) => (
        <Badge
          key={skill}
          variant="secondary"
          className="text-xs font-normal bg-muted/70 text-muted-foreground dark:bg-muted/50"
        >
          {skill}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="outline" className="text-xs text-muted-foreground/60">
          +{remaining}
        </Badge>
      )}
    </div>
  );
}

/** Skeleton loading state for the table */
function CandidateTableSkeleton() {
  return (
    <>
      <div className="hidden overflow-x-auto rounded-xl border md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tên</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Số điện thoại</TableHead>
              <TableHead>Kỹ năng</TableHead>
              <TableHead>Độ tin cậy</TableHead>
              <TableHead>Vị trí TD</TableHead>
              <TableHead>Trạng thái</TableHead>
              <TableHead>Ngày tạo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={`skeleton-${i}`}>
                <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                <TableCell><Skeleton className="h-5 w-36" /></TableCell>
                <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Skeleton className="h-5 w-12" />
                    <Skeleton className="h-5 w-12" />
                    <Skeleton className="h-5 w-12" />
                  </div>
                </TableCell>
                <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                <TableCell><Skeleton className="h-5 w-20" /></TableCell>
                <TableCell><Skeleton className="h-5 w-20" /></TableCell>
                <TableCell><Skeleton className="h-5 w-20" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="space-y-3 md:hidden">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={`skeleton-card-${i}`} className="shadow-sm">
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-16" />
              </div>
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-4 w-24" />
              <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}

/** Pagination controls with page size selector */
function PaginationControls({
  page,
  pageSize,
  totalPages,
  onPageChange,
  onPageSizeChange,
}: {
  page: number;
  pageSize: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Hiển thị</span>
        <Select
          value={String(pageSize)}
          onValueChange={(value) => onPageSizeChange(Number(value))}
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
        <span className="text-sm tabular-nums text-muted-foreground">
          Trang {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Trang trước"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Trang sau"
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function RecruitmentPage() {
  const router = useRouter();

  const [data, setData] = useState<CandidateListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<CandidateFilterChangePayload>({});
  const [announcement, setAnnouncement] = useState("");

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: CandidateListParams = {
        page,
        page_size: pageSize,
        search: filters.search || undefined,
        status: filters.status
          ? [filters.status as unknown as import("@/lib/api/recruitment").CandidateStatus]
          : undefined,
        from_date: filters.date_from || undefined,
        to_date: filters.date_to || undefined,
        min_confidence: filters.min_confidence || undefined,
        skills: filters.skills || undefined,
      };
      const result = await listCandidates(params);
      setData(result.candidates);
      setTotalCount(result.total_count);
      setAnnouncement(
        `Đã tải ${result.candidates.length} ứng viên trong tổng số ${result.total_count}`
      );
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Không thể tải danh sách ứng viên";
      setError(message);
      setAnnouncement("Lỗi khi tải danh sách ứng viên");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const handleFilterChange = useCallback(
    (newFilters: CandidateFilterChangePayload) => {
      setFilters(newFilters);
      setPage(1);
    },
    []
  );

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const handlePageSizeChange = useCallback((newSize: number) => {
    setPageSize(newSize);
    setPage(1);
  }, []);

  const handleRowClick = useCallback(
    (candidateId: string) => {
      router.push(`/recruitment/${candidateId}`);
    },
    [router]
  );

  const handleRowKeyDown = useCallback(
    (e: React.KeyboardEvent, candidateId: string) => {
      if (e.key === "Enter") {
        e.preventDefault();
        router.push(`/recruitment/${candidateId}`);
      }
    },
    [router]
  );

  const handleRetry = useCallback(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const totalPages = Math.ceil(totalCount / pageSize);
  const hasActiveFilters = Object.keys(filters).length > 0;

  return (
    <div className="animate-page-enter space-y-6 max-w-[1440px] mx-auto overflow-x-hidden pb-10">
      {/* ─── Page Header ──────────────────────────────── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <UserPlus className="h-4 w-4" strokeWidth={1.5} />
            </div>
            <h1 className="font-heading text-2xl font-bold">Tuyển dụng</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground ml-10">
            Quản lý ứng viên trong quy trình tuyển dụng
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
          <Button variant="outline" size="sm" asChild>
            <a href="/recruitment/inbox">
              <MailQuestion className="mr-2 h-4 w-4" />
              Hộp thư
            </a>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href="/recruitment/review">
              <Users className="mr-2 h-4 w-4" />
              Xem xét
            </a>
          </Button>
        </div>
      </div>

      {/* ─── Quick stats bar ──────────────────────────── */}
      {!loading && !error && data.length > 0 && (
        <div className="animate-fade-in flex flex-wrap items-center gap-4 rounded-xl border border-border/30 bg-card px-5 py-3 shadow-sm">
          <div className="flex items-center gap-2 text-sm">
            <Sparkles className="h-3.5 w-3.5 text-muted-foreground/60" strokeWidth={1.5} />
            <span className="text-muted-foreground">
              Tìm thấy <strong className="text-foreground tabular-nums">{totalCount}</strong> ứng viên
            </span>
          </div>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => {
                setFilters({});
                setPage(1);
              }}
            >
              Xóa bộ lọc
            </Button>
          )}
        </div>
      )}

      {/* Filter Panel */}
      <CandidateFilterPanel onFilterChange={handleFilterChange} />

      {/* aria-live */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      {/* Error State */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-destructive/20 bg-destructive/5 p-12 text-center shadow-sm">
          <Search className="h-10 w-10 text-destructive/60 mb-3" strokeWidth={1.5} />
          <p className="text-sm font-medium text-destructive">{error}</p>
          <Button onClick={handleRetry} variant="outline" size="sm" className="mt-4">
            Thử lại
          </Button>
        </div>
      )}

      {/* Loading State */}
      {loading && <CandidateTableSkeleton />}

      {/* Empty State — no data */}
      {!loading && !error && data.length === 0 && !hasActiveFilters && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border/30 bg-card p-14 text-center shadow-sm">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/20">
            <Users className="h-6 w-6 text-muted-foreground/50" strokeWidth={1.5} />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Chưa có ứng viên nào</p>
          <p className="mt-1 text-xs text-muted-foreground/60">Ứng viên sẽ xuất hiện khi có dữ liệu</p>
        </div>
      )}

      {/* Empty State — filter returned no results */}
      {!loading && !error && data.length === 0 && hasActiveFilters && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-border/30 bg-card p-14 text-center shadow-sm">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/20">
            <Search className="h-6 w-6 text-muted-foreground/50" strokeWidth={1.5} />
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            Không có ứng viên phù hợp
          </p>
          <p className="mt-1 text-xs text-muted-foreground/60">
            Thử điều chỉnh bộ lọc để tìm kết quả khác
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => {
              setFilters({});
              setPage(1);
            }}
          >
            Xóa bộ lọc
          </Button>
        </div>
      )}

      {/* Data Table (desktop) */}
      {!loading && !error && data.length > 0 && (
        <>
          <div className="hidden overflow-x-auto rounded-xl border shadow-sm md:block">
            <Table aria-label="Danh sách ứng viên">
              <TableHeader>
                <TableRow>
                  <TableHead scope="col">Tên</TableHead>
                  <TableHead scope="col">Email</TableHead>
                  <TableHead scope="col">Số điện thoại</TableHead>
                  <TableHead scope="col">Kỹ năng</TableHead>
                  <TableHead scope="col">Độ tin cậy</TableHead>
                  <TableHead scope="col">Vị trí TD</TableHead>
                  <TableHead scope="col">Trạng thái</TableHead>
                  <TableHead scope="col">Ngày tạo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((candidate) => (
                  <TableRow
                    key={candidate.id}
                    className="cursor-pointer hover:bg-muted/70 transition-colors"
                    tabIndex={0}
                    role="link"
                    aria-label={`Xem chi tiết ứng viên ${candidate.name}`}
                    onClick={() => handleRowClick(candidate.id)}
                    onKeyDown={(e) => handleRowKeyDown(e, candidate.id)}
                  >
                    <TableCell className="font-medium">
                      {candidate.name}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{candidate.email}</TableCell>
                    <TableCell className="text-muted-foreground">{candidate.phone || "—"}</TableCell>
                    <TableCell>
                      <SkillsBadges skills={candidate.skills} />
                    </TableCell>
                    <TableCell>
                      <ConfidenceScore score={candidate.confidence_score} />
                    </TableCell>
                    <TableCell className="max-w-[180px]">
                      <span
                        className="block truncate text-sm"
                        title={candidate.job_opening_title || undefined}
                      >
                        {candidate.job_opening_title || (
                          <span className="text-muted-foreground italic">—</span>
                        )}
                      </span>
                    </TableCell>
                    <TableCell>
                      <CandidateStatusBadge
                        status={candidate.status as UtilsCandidateStatus}
                      />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(candidate.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Card Layout */}
          <div className="space-y-3 md:hidden">
            {data.map((candidate) => (
              <Card
                key={candidate.id}
                className="card-hover cursor-pointer shadow-sm"
                tabIndex={0}
                role="link"
                aria-label={`Xem chi tiết ứng viên ${candidate.name}`}
                onClick={() => handleRowClick(candidate.id)}
                onKeyDown={(e) => handleRowKeyDown(e, candidate.id)}
              >
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">
                      {candidate.name}
                    </span>
                    <CandidateStatusBadge
                      status={candidate.status as UtilsCandidateStatus}
                    />
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {candidate.email}
                  </div>
                  {candidate.phone && (
                    <div className="text-sm text-muted-foreground">
                      {candidate.phone}
                    </div>
                  )}
                  <div className="break-words text-sm text-muted-foreground">
                    {candidate.job_opening_title
                      ? `Vị trí TD: ${candidate.job_opening_title}`
                      : "Chưa gán vị trí"}
                  </div>
                  <div className="flex items-center justify-between">
                    <ConfidenceScore score={candidate.confidence_score} />
                    <span className="text-xs text-muted-foreground">
                      {formatDate(candidate.created_at)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination Controls */}
          <PaginationControls
            page={page}
            pageSize={pageSize}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        </>
      )}
    </div>
  );
}
