"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MailQuestion, Users } from "lucide-react";

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
import { ChevronLeft, ChevronRight } from "lucide-react";

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
// Page Component
// ---------------------------------------------------------------------------

export default function RecruitmentPage() {
  const router = useRouter();

  // State
  const [data, setData] = useState<CandidateListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<CandidateFilterChangePayload>({});
  const [announcement, setAnnouncement] = useState("");

  // Fetch candidates
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

  // Handlers
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

  // Computed
  const totalPages = Math.ceil(totalCount / pageSize);

  // Check if any filter is active
  const hasActiveFilters = Object.keys(filters).length > 0;

  return (
    <div className="space-y-6 p-6">
          {/* Page Header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <h1 className="font-heading text-2xl font-bold">Tuyển dụng</h1>
              <p className="text-sm text-muted-foreground">
                Quản lý ứng viên trong quy trình tuyển dụng
              </p>
            </div>
            <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
              <Button className="w-full sm:w-auto" variant="outline" size="sm" asChild>
                <a href="/recruitment/inbox">
                  <MailQuestion className="mr-2 h-4 w-4" />
                  Hộp thư
                </a>
              </Button>
              <Button className="w-full sm:w-auto" variant="outline" size="sm" asChild>
                <a href="/recruitment/review">
                  <Users className="mr-2 h-4 w-4" />
                  Xem xét
                </a>
              </Button>
            </div>
          </div>

      {/* Filter Panel */}
      <CandidateFilterPanel onFilterChange={handleFilterChange} />

      {/* aria-live region for data refresh announcements */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </div>

      {/* Error State */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center rounded-md border p-12 text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={handleRetry} variant="outline">
            Thử lại
          </Button>
        </div>
      )}

      {/* Loading State */}
      {loading && <CandidateTableSkeleton />}

      {/* Empty State — no data */}
      {!loading && !error && data.length === 0 && !hasActiveFilters && (
      <div className="flex flex-col items-center justify-center rounded-md border p-12 text-center">
        <Users className="h-12 w-12 text-muted-foreground mb-4" aria-hidden="true" />
        <p className="text-muted-foreground">Chưa có ứng viên nào</p>
      </div>
      )}

      {/* Empty State — filter returned no results */}
      {!loading && !error && data.length === 0 && hasActiveFilters && (
      <div className="flex flex-col items-center justify-center rounded-md border p-12 text-center">
        <Users className="h-12 w-12 text-muted-foreground mb-4" aria-hidden="true" />
        <p className="text-muted-foreground mb-1">
          Không có ứng viên phù hợp với bộ lọc
        </p>
        <p className="text-xs text-muted-foreground/60 mb-4">
          Thử điều chỉnh bộ lọc để tìm kết quả khác
        </p>
        <Button
          variant="outline"
          size="sm"
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
          <div className="hidden overflow-x-auto rounded-md border md:block">
            <Table aria-label="Danh sách ứng viên">
              <TableHeader>
                <TableRow>
                  <TableHead scope="col">Tên</TableHead>
                  <TableHead scope="col">Email</TableHead>
                  <TableHead scope="col">Số điện thoại</TableHead>
                  <TableHead scope="col">Kỹ năng</TableHead>
                  <TableHead scope="col">Độ tin cậy (%)</TableHead>
                  <TableHead scope="col">Vị trí TD</TableHead>
                  <TableHead scope="col">Trạng thái</TableHead>
                  <TableHead scope="col">Ngày tạo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((candidate) => (
                  <TableRow
                    key={candidate.id}
                    className="cursor-pointer hover:bg-muted"
                    tabIndex={0}
                    role="link"
                    aria-label={`Xem chi tiết ứng viên ${candidate.name}`}
                    onClick={() => handleRowClick(candidate.id)}
                    onKeyDown={(e) => handleRowKeyDown(e, candidate.id)}
                  >
                    <TableCell className="font-medium">
                      {candidate.name}
                    </TableCell>
                    <TableCell>{candidate.email}</TableCell>
                    <TableCell>{candidate.phone || "—"}</TableCell>
                    <TableCell>
                      <SkillsBadges skills={candidate.skills} />
                    </TableCell>
                    <TableCell>
                      <ConfidenceScore score={candidate.confidence_score} />
                    </TableCell>
                    <TableCell className="max-w-[180px]">
                      <span className="block truncate text-sm" title={candidate.job_opening_title || undefined}>
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
                    <TableCell>{formatDate(candidate.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Card Layout (below 768px) */}
          <div className="space-y-3 md:hidden">
            {data.map((candidate) => (
              <Card
                key={candidate.id}
                className="cursor-pointer hover:bg-muted/50"
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

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Renders skill badges with a max of 5 + "+N" indicator */
function SkillsBadges({ skills }: { skills: string[] }) {
  if (!skills || skills.length === 0) {
    return <span className="text-muted-foreground">—</span>;
  }

  const displayed = skills.slice(0, 5);
  const remaining = skills.length - 5;

  return (
    <div className="flex flex-wrap gap-1">
      {displayed.map((skill) => (
        <Badge key={skill} variant="secondary" className="text-xs">
          {skill}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="outline" className="text-xs">
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
      {/* Desktop skeleton */}
      <div className="hidden overflow-x-auto rounded-md border md:block">
        <Table aria-label="Danh sách ứng viên">
          <TableHeader>
            <TableRow>
              <TableHead>Tên</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Số điện thoại</TableHead>
              <TableHead>Kỹ năng</TableHead>
              <TableHead>Độ tin cậy (%)</TableHead>
              <TableHead>Vị trí TD</TableHead>
              <TableHead>Trạng thái</TableHead>
              <TableHead>Ngày tạo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={`skeleton-${i}`}>
                <TableCell>
                  <Skeleton className="h-5 w-24" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-36" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-24" />
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Skeleton className="h-5 w-12" />
                    <Skeleton className="h-5 w-12" />
                    <Skeleton className="h-5 w-12" />
                  </div>
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-16" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-20" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-20" />
                </TableCell>
                <TableCell>
                  <Skeleton className="h-5 w-20" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile skeleton */}
      <div className="space-y-3 md:hidden">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={`skeleton-card-${i}`}>
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
        <span className="text-sm text-muted-foreground">
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
