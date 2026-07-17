"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { Search, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";
import { useDebounce } from "@/hooks/use-debounce";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";

export interface ColumnDef<T> {
  key: string;
  header: string;
  cell?: (row: T) => React.ReactNode;
  className?: string;
}

export interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
  };
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  onRowClick?: (row: T) => void;
  emptyDataAction?: React.ReactNode;
  toolbar?: React.ReactNode;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  error = null,
  onRetry,
  pagination,
  searchPlaceholder = "Tìm kiếm...",
  onSearch,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  emptyDataAction,
  toolbar,
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 300);

  useEffect(() => {
    onSearch?.(debouncedSearch);
  }, [debouncedSearch, onSearch]);

  const totalPages = pagination
    ? Math.ceil(pagination.total / pagination.pageSize)
    : 0;

  return (
    <div className="space-y-4">
      {/* Toolbar: Search + Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {onSearch && (
          <div className="relative w-full sm:max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              maxLength={100}
              aria-label={searchPlaceholder}
            />
          </div>
        )}
        {toolbar && <div className="flex items-center gap-2">{toolbar}</div>}
      </div>

      {/* Table (hidden on mobile) */}
      <div className="hidden rounded-md border md:block">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.key} className={column.className}>
                  {column.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody className="stagger-children">
            {/* Error State */}
            {error && (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-32 text-center">
                  <div className="flex flex-col items-center gap-2 text-destructive">
                    <span>Lỗi tải dữ liệu: {error}</span>
                    {onRetry && (
                      <Button variant="outline" size="sm" onClick={onRetry}>
                        <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
                        Thử lại
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )}

            {/* Loading State */}
            {!error && loading && (
              <>
                {Array.from({ length: 5 }).map((_, rowIndex) => (
                  <TableRow key={`skeleton-${rowIndex}`}>
                    {columns.map((column) => (
                      <TableCell key={`skeleton-${rowIndex}-${column.key}`}>
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </>
            )}

            {/* Empty State */}
            {!error && !loading && data.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                  {searchQuery ? (
                    <div className="flex flex-col items-center gap-2">
                      <span>Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại.</span>
                      <Button variant="link" size="sm" onClick={() => setSearchQuery("")}>
                        Xóa bộ lọc
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <span>Chưa có bản ghi nào trong phạm vi này.</span>
                      {emptyDataAction}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            )}

            {/* Data Rows */}
            {!error && !loading &&
              data.map((row, rowIndex) => (
                <TableRow
                  key={rowIndex}
                  className={cn(
                    "animate-fade-in",
                    onRowClick && "cursor-pointer hover:bg-muted"
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => (
                    <TableCell key={column.key} className={column.className}>
                      {column.cell
                        ? column.cell(row)
                        : (row[column.key] as React.ReactNode) ?? "—"}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile card view */}
      <div className="space-y-3 md:hidden">
        {/* Error State */}
          {error && (
            <div className="flex flex-col items-center gap-3 rounded-md border p-6 text-center text-destructive">
              <span>Lỗi tải dữ liệu: {error}</span>
              {onRetry && (
                <Button variant="outline" size="sm" onClick={onRetry}>
                  <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
                  Thử lại
                </Button>
              )}
            </div>
          )}

        {/* Loading State */}
        {!error && loading &&
          Array.from({ length: 3 }).map((_, index) => (
            <Card key={`skeleton-card-${index}`}>
              <CardContent className="grid grid-cols-2 gap-2 p-4">
                {columns.map((column) => (
                  <div key={`skeleton-card-${index}-${column.key}`}>
                    <Skeleton className="mb-1 h-3 w-16" />
                    <Skeleton className="h-5 w-full" />
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}

        {/* Empty State */}
          {!error && !loading && data.length === 0 && (
            <div className="rounded-md border p-6 text-center text-muted-foreground">
              {searchQuery ? (
                <div className="flex flex-col items-center gap-2">
                  <span>Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại.</span>
                  <Button variant="link" size="sm" onClick={() => setSearchQuery("")}>
                    Xóa bộ lọc
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <span>Chưa có bản ghi nào trong phạm vi này.</span>
                  {emptyDataAction}
                </div>
              )}
            </div>
          )}

        {/* Data Cards */}
        {!error && !loading &&
          data.map((row, rowIndex) => (
            <Card
              key={rowIndex}
              className={cn(
                "animate-fade-in",
                onRowClick && "cursor-pointer hover:bg-muted/50"
              )}
              style={{ animationDelay: `${rowIndex * 50}ms` }}
              onClick={() => onRowClick?.(row)}
            >
              <CardContent className="grid grid-cols-2 gap-2 p-4">
                {columns.map((column) => (
                  <div key={column.key}>
                    <dt className="text-xs text-muted-foreground">
                      {column.header}
                    </dt>
                    <dd className="text-sm font-medium">
                      {column.cell
                        ? column.cell(row)
                        : (row[column.key] as React.ReactNode) ?? "—"}
                    </dd>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
      </div>

      {/* Pagination */}
      {pagination && totalPages > 0 && (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Hiển thị</span>
            <Select
              value={String(pagination.pageSize)}
              onValueChange={(value) => onPageSizeChange?.(Number(value))}
            >
              <SelectTrigger className="h-8 w-[70px]" aria-label="Số dòng mỗi trang">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Trang {pagination.page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => onPageChange?.(pagination.page - 1)}
              disabled={pagination.page <= 1}
              aria-label="Trước"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => onPageChange?.(pagination.page + 1)}
              disabled={pagination.page >= totalPages}
              aria-label="Sau"
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
