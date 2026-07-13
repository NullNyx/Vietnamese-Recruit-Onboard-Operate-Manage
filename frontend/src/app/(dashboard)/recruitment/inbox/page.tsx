"use client";

import * as React from "react";
import {
  Inbox,
  AlertTriangle,
  CheckCircle2,
  Info,
  MailQuestion,
  X,
  ThumbsUp,
  RotateCw,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { listInbox, correctInboxIntent, dismissInboxItem } from "@/lib/api/recruitment";
import type { InboxItem, InboxStatus } from "@/lib/api/recruitment";
import { ApiError } from "@/lib/api/types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;
const DEFAULT_PAGE_SIZE = 20;

const INBOX_STATUS_LABELS: Record<string, string> = {
  needs_classification: "Cần phân loại",
  needs_information: "Cần bổ sung thông tin",
  ready_for_review: "Sẵn sàng xem xét",
  resolved: "Đã xử lý",
};

const INBOX_STATUS_VARIANTS: Record<string, "destructive" | "secondary" | "default" | "outline"> = {
  needs_classification: "destructive",
  needs_information: "secondary",
  ready_for_review: "default",
  resolved: "outline",
};

const INBOX_STATUS_ICONS: Record<string, React.ElementType> = {
  needs_classification: AlertTriangle,
  needs_information: Info,
  ready_for_review: MailQuestion,
  resolved: CheckCircle2,
};

// ---------------------------------------------------------------------------
// Skeleton Loading
// ---------------------------------------------------------------------------

function InboxSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-4 w-4 rounded-full" />
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty State
// ---------------------------------------------------------------------------

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Inbox className="h-12 w-12 text-muted-foreground mb-4" />
      <p className="text-lg font-medium text-muted-foreground">
        Không có mục nào trong Inbox
      </p>
      <p className="text-sm text-muted-foreground mt-1">
        Email tuyển dụng cần phân loại hoặc xử lý sẽ xuất hiện ở đây
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inbox Item Card Component
// ---------------------------------------------------------------------------

function InboxItemCard({
  item,
  onItemClick,
}: {
  item: InboxItem;
  onItemClick: (item: InboxItem) => void;
}) {
  const StatusIcon = INBOX_STATUS_ICONS[item.inbox_status] || Inbox;

  return (
    <Card
      className="cursor-pointer hover:bg-accent/50 transition-colors"
      onClick={() => onItemClick(item)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <StatusIcon className="h-5 w-5 mt-0.5 shrink-0 text-muted-foreground" />
            <div className="min-w-0">
              <CardTitle className="text-base truncate">
                {item.subject || "(Không có tiêu đề)"}
              </CardTitle>
              <CardDescription className="mt-0.5">
                {item.sender_name || item.sender_email}
              </CardDescription>
            </div>
          </div>
          <Badge variant={INBOX_STATUS_VARIANTS[item.inbox_status] || "secondary"}>
            {INBOX_STATUS_LABELS[item.inbox_status] || item.inbox_status}
          </Badge>
        </div>
        {item.snippet && (
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
            {item.snippet}
          </p>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {item.prediction_intent && (
            <span>Dự đoán: {item.prediction_intent}</span>
          )}
          {item.confidence_calibrated != null && (
            <span>
              Độ tin cậy: {Math.round(item.confidence_calibrated * 100)}%
            </span>
          )}
              {item.has_attachments && (
                <span>
                  Có tệp đính kèm
                  {item.attachments_metadata?.length
                    ? ` (${item.attachments_metadata.length} tệp)`
                    : ""}
                </span>
              )}
              {item.is_retry_exhausted && (
            <Badge variant="destructive" className="text-xs">
              Hết lượt thử lại
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Inbox Item Detail Dialog
// ---------------------------------------------------------------------------

function InboxItemDetailDialog({
  item,
  onClose,
  onCorrected,
  onDismissed,
}: {
  item: InboxItem;
  onClose: () => void;
  onCorrected: () => void;
  onDismissed: () => void;
}) {
  const [correctIntentOpen, setCorrectIntentOpen] = React.useState(false);
  const [correctedIntent, setCorrectedIntent] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const handleCorrect = async () => {
    if (!correctedIntent.trim()) return;
    setLoading(true);
    try {
      await correctInboxIntent(item.id, correctedIntent.trim());
      toast.success("Đã sửa hướng định tuyến");
      setCorrectIntentOpen(false);
      onCorrected();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Lỗi khi sửa hướng định tuyến");
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = async () => {
    setLoading(true);
    try {
      await dismissInboxItem(item.id);
      toast.success("Đã bỏ qua mục này");
      onDismissed();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Lỗi khi bỏ qua");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={true} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{item.subject || "(Không có tiêu đề)"}</DialogTitle>
          <DialogDescription>
            Chi tiết phân loại và lịch sử xử lý
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Người gửi:</span>{" "}
              {item.sender_name || item.sender_email}
            </div>
            <div>
              <span className="text-muted-foreground">Email:</span>{" "}
              {item.sender_email}
            </div>
            <div>
              <span className="text-muted-foreground">Thread:</span>{" "}
              <code className="text-xs">{item.gmail_thread_id.slice(0, 20)}...</code>
            </div>
            <div>
              <span className="text-muted-foreground">Tin nhắn:</span>{" "}
              <code className="text-xs">{item.gmail_message_id.slice(0, 20)}...</code>
            </div>
          </div>

          {/* Classification Result */}
          <div className="rounded-lg border p-4 space-y-2">
            <h4 className="font-medium text-sm">Kết quả phân loại AI</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Dự đoán:</span>{" "}
                {item.prediction_intent || "N/A"}
              </div>
              <div>
                <span className="text-muted-foreground">Độ tin cậy thô:</span>{" "}
                {item.confidence_raw != null
                  ? `${Math.round(item.confidence_raw * 100)}%`
                  : "N/A"}
              </div>
              <div>
                <span className="text-muted-foreground">Độ tin cậy đã hiệu chỉnh:</span>{" "}
                {item.confidence_calibrated != null
                  ? `${Math.round(item.confidence_calibrated * 100)}%`
                  : "N/A"}
              </div>
              {item.corrected_intent && (
                <div>
                  <span className="text-muted-foreground">Đã sửa thành:</span>{" "}
                  {item.corrected_intent}
                </div>
              )}
            </div>
          </div>

          {/* Evidence */}
          {item.evidence && item.evidence.length > 0 && (
            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="font-medium text-sm">Bằng chứng</h4>
              <ul className="text-sm space-y-1">
                {item.evidence.map((ev, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-muted-foreground">•</span>
                    {ev.signal}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Source Hints */}
          {item.source_hints && item.source_hints.length > 0 && (
            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="font-medium text-sm">Nguồn gốc</h4>
              <ul className="text-sm space-y-1">
                {item.source_hints.map((hint, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-muted-foreground">•</span>
                    {hint.key}: {hint.value}
                  </li>
                ))}
              </ul>
            </div>
          )}

              {/* Attachment Metadata */}
              {item.has_attachments && (
                <div className="rounded-lg border p-4 space-y-2">
                  <h4 className="font-medium text-sm">Tệp đính kèm</h4>
                  {item.attachments_metadata && item.attachments_metadata.length > 0 ? (
                    <ul className="text-sm space-y-1">
                      {item.attachments_metadata.map((att, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <span className="text-muted-foreground">\u2022</span>
                          {att.name && <span className="font-medium">{att.name}</span>}
                          {att.type && (
                            <span className="text-muted-foreground text-xs">
                              ({att.type})
                            </span>
                          )}
                          {att.size != null && (
                            <span className="text-muted-foreground text-xs">
                              {att.size > 1024 * 1024
                                ? `${(att.size / (1024 * 1024)).toFixed(1)} MB`
                                : att.size > 1024
                                  ? `${(att.size / 1024).toFixed(0)} KB`
                                  : `${att.size} B`}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Email này có tệp đính kèm
                    </p>
                  )}
                </div>
              )}

          {/* Correction History */}
          {item.correction_history && item.correction_history.length > 0 && (
            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="font-medium text-sm">Lịch sử sửa đổi</h4>
              <div className="space-y-2">
                {item.correction_history.map((entry, i) => (
                  <div key={i} className="text-sm p-2 bg-muted rounded">
                    <div className="flex justify-between">
                      <span>
                        {entry.previous_intent || "N/A"} → {entry.corrected_intent}
                      </span>
                      <span className="text-muted-foreground text-xs">
                        {new Date(entry.corrected_at).toLocaleString("vi-VN")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dismissal Info */}
          {item.dismissed && (
            <div className="rounded-lg border border-destructive/50 p-4 space-y-1">
              <h4 className="font-medium text-sm text-destructive">Đã bỏ qua</h4>
              <p className="text-sm text-muted-foreground">
                Mục này đã bị HR bỏ qua và sẽ không bị tạo lại bởi worker retry.
              </p>
              {item.dismissed_at && (
                <p className="text-xs text-muted-foreground">
                  Lúc: {new Date(item.dismissed_at).toLocaleString("vi-VN")}
                </p>
              )}
            </div>
          )}

          {/* Processing Error */}
          {item.processing_error && (
            <div className="rounded-lg border border-destructive/50 p-4 space-y-1">
              <h4 className="font-medium text-sm text-destructive">Lỗi xử lý</h4>
              <p className="text-sm text-muted-foreground">{item.processing_error}</p>
            </div>
          )}
        </div>

        <DialogFooter className="flex gap-2">
          {!item.dismissed && (
            <>
              <Button
                variant="outline"
                onClick={() => setCorrectIntentOpen(true)}
                disabled={loading}
              >
                <ThumbsUp className="h-4 w-4 mr-2" />
                Sửa hướng định tuyến
              </Button>
              <Button
                variant="destructive"
                onClick={handleDismiss}
                disabled={loading}
              >
                <X className="h-4 w-4 mr-2" />
                Bỏ qua
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>

      {/* Correct Intent Dialog */}
      <Dialog open={correctIntentOpen} onOpenChange={setCorrectIntentOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Sửa hướng định tuyến</DialogTitle>
            <DialogDescription>
              Nhập hướng định tuyến đúng cho email này (ví dụ: other, partner, event, internal)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Label htmlFor="corrected-intent">Hướng định tuyến</Label>
            <Input
              id="corrected-intent"
              value={correctedIntent}
              onChange={(e) => setCorrectedIntent(e.target.value)}
              placeholder="Ví dụ: other"
              maxLength={50}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCorrectIntentOpen(false)}>
              Hủy
            </Button>
            <Button onClick={handleCorrect} disabled={loading || !correctedIntent.trim()}>
              {loading ? <RotateCw className="h-4 w-4 animate-spin" /> : <ThumbsUp className="h-4 w-4 mr-2" />}
              Xác nhận
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Main Page Component
// ---------------------------------------------------------------------------

export default function RecruitmentInboxPage() {
  const [items, setItems] = React.useState<InboxItem[]>([]);
  const [total, setTotal] = React.useState(0);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(DEFAULT_PAGE_SIZE);
  const [statusFilter, setStatusFilter] = React.useState<"all" | InboxStatus>("all");
  const [loading, setLoading] = React.useState(true);
  const [selectedItem, setSelectedItem] = React.useState<InboxItem | null>(null);

  const fetchList = React.useCallback(async () => {
    setLoading(true);
    try {
      const inboxStatus = statusFilter === "all" ? undefined : statusFilter;
      const result = await listInbox({
        inbox_status: inboxStatus,
        page,
        page_size: pageSize,
      });
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể tải inbox");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page, pageSize]);

  React.useEffect(() => {
    fetchList();
  }, [fetchList]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Recruitment Inbox</h1>
          <p className="text-muted-foreground mt-1">
            Email tuyển dụng và Job Application cần xử lý
          </p>
        </div>
        <Button variant="outline" onClick={fetchList} disabled={loading}>
          <RotateCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Làm mới
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="w-64">
          <Select
            value={statusFilter}
            onValueChange={(v) => {
              setStatusFilter(v as "all" | InboxStatus);
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Bộ lọc trạng thái" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tất cả</SelectItem>
              <SelectItem value="needs_classification">Cần phân loại</SelectItem>
              <SelectItem value="needs_information">Cần bổ sung thông tin</SelectItem>
              <SelectItem value="ready_for_review">Sẵn sàng xem xét</SelectItem>
              <SelectItem value="resolved">Đã xử lý</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="w-32">
          <Select
            value={String(pageSize)}
            onValueChange={(v) => {
              setPageSize(Number(v));
              setPage(1);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Số lượng" />
            </SelectTrigger>
            <SelectContent>
              {PAGE_SIZE_OPTIONS.map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n} mục
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <span className="text-sm text-muted-foreground">
          Tổng số: {total} mục
        </span>
      </div>

      {/* Content */}
      {loading ? (
        <InboxSkeleton />
      ) : items.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <InboxItemCard
              key={item.id}
              item={item}
              onItemClick={setSelectedItem}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Trang trước
          </Button>
          <span className="text-sm text-muted-foreground">
            Trang {page}/{totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Trang sau
          </Button>
        </div>
      )}

      {/* Detail Dialog */}
      {selectedItem && (
        <InboxItemDetailDialog
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onCorrected={() => {
            setSelectedItem(null);
            fetchList();
          }}
          onDismissed={() => {
            setSelectedItem(null);
            fetchList();
          }}
        />
      )}
    </div>
  );
}
