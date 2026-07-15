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
      Link2,
      Plus,
      Scissors,
      Sparkles,
      RefreshCw,
      ChevronLeft,
      ChevronRight,
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
import { JobApplicationActions } from "@/components/recruitment/job-application-actions";

import {
  listInbox,
  correctInboxIntent,
  dismissInboxItem,
  proposeInboxLink,
  resolveInboxLinkProposal,
  splitInboxItem,
} from "@/lib/api/recruitment";
import type {
  ApplicationSource,
  InboxItem,
  InboxStatus,
  JobApplicationInboxResult,
  JobApplicationLinkProposal,
  SplitApplicantInput,
} from "@/lib/api/recruitment";
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

const INBOX_STATUS_VARIANTS: Record<
  string,
  "destructive" | "secondary" | "default" | "outline"
> = {
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
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-5 w-5 rounded-full" />
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-5 w-28 ml-auto" />
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
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 ring-1 ring-border/20">
        <Inbox className="h-6 w-6 text-muted-foreground/50" strokeWidth={1.5} />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        Không có mục nào trong Inbox
      </p>
      <p className="mt-1.5 max-w-[240px] text-xs leading-relaxed text-muted-foreground/60">
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
      className="card-hover cursor-pointer shadow-sm border-border/40"
      onClick={() => onItemClick(item)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
              <StatusIcon
                className="h-4 w-4 text-muted-foreground"
                aria-hidden="true"
              />
            </div>
            <div className="min-w-0">
              <CardTitle className="text-sm font-semibold truncate">
                {item.subject || "(Không có tiêu đề)"}
              </CardTitle>
              <CardDescription className="mt-0.5 text-xs">
                {item.sender_name || item.sender_email}
              </CardDescription>
            </div>
          </div>
          <Badge
            variant={INBOX_STATUS_VARIANTS[item.inbox_status] || "secondary"}
            className="shrink-0 text-xs"
          >
            {INBOX_STATUS_LABELS[item.inbox_status] || item.inbox_status}
          </Badge>
        </div>
        {item.snippet && (
          <p className="text-sm text-muted-foreground mt-1.5 line-clamp-2 pl-11">
            {item.snippet}
          </p>
        )}
      </CardHeader>
      <CardContent className="pt-0 pl-11">
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground/70">
          {item.prediction_intent && (
            <span>
              Dự đoán: <strong>{item.prediction_intent}</strong>
            </span>
          )}
          {item.confidence_calibrated != null && (
            <span>
              Độ tin cậy: {Math.round(item.confidence_calibrated * 100)}%
            </span>
          )}
          {item.has_attachments && (
            <span>
              {item.attachments_metadata?.length
                ? `${item.attachments_metadata.length} tệp đính kèm`
                : "Có tệp đính kèm"}
            </span>
          )}
          {item.is_retry_exhausted && (
            <Badge variant="destructive" className="text-[10px] h-5">
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
  const [splitOpen, setSplitOpen] = React.useState(false);
  const [splitSource, setSplitSource] =
    React.useState<ApplicationSource>("direct");
  const [splitApplicants, setSplitApplicants] = React.useState<
    SplitApplicantInput[]
  >([{ name: "", email: "" }]);
  const [linkOpen, setLinkOpen] = React.useState(false);
  const [targetApplicationId, setTargetApplicationId] = React.useState("");
  const [linkProposal, setLinkProposal] =
    React.useState<JobApplicationLinkProposal | null>(null);
  const [createdApplications, setCreatedApplications] = React.useState<
    JobApplicationInboxResult[]
  >([]);

  const handleCorrect = async () => {
    if (!correctedIntent.trim()) return;
    setLoading(true);
    try {
      await correctInboxIntent(item.id, correctedIntent.trim());
      toast.success("Đã sửa hướng định tuyến");
      setCorrectIntentOpen(false);
      onCorrected();
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Lỗi khi sửa hướng định tuyến"
      );
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
      toast.error(
        err instanceof ApiError ? err.message : "Lỗi khi bỏ qua"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSplit = async () => {
    const applicants = splitApplicants
      .filter((applicant) => applicant.name.trim())
      .map((applicant) => ({
        name: applicant.name.trim(),
        ...(applicant.email?.trim()
          ? { email: applicant.email.trim() }
          : {}),
        ...(applicant.job_opening_id?.trim()
          ? { job_opening_id: applicant.job_opening_id.trim() }
          : {}),
      }));
    if (applicants.length === 0) return;
    setLoading(true);
    try {
      const result = await splitInboxItem(item.id, {
        source: splitSource,
        applicants,
      });
      setCreatedApplications(result.applications);
      toast.success(`Đã tạo ${applicants.length} Job Application`);
      setSplitOpen(false);
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Lỗi khi tách ứng viên"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleProposeLink = async () => {
    if (!targetApplicationId.trim()) return;
    setLoading(true);
    try {
      const proposal = await proposeInboxLink(
        item.id,
        targetApplicationId.trim()
      );
      setLinkProposal(proposal);
      toast.success("Đã tạo đề xuất liên kết; chưa thay đổi Job Application");
    } catch (err) {
      toast.error(
        err instanceof ApiError
          ? err.message
          : "Lỗi khi đề xuất liên kết"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResolveLink = async (
    decision: "confirmed" | "rejected"
  ) => {
    if (!linkProposal) return;
    setLoading(true);
    try {
      await resolveInboxLinkProposal(linkProposal.id, decision);
      toast.success(
        decision === "confirmed"
          ? "Đã xác nhận liên kết"
          : "Đã từ chối liên kết"
      );
      setLinkOpen(false);
      onCorrected();
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Lỗi khi xử lý liên kết"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={true} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MailQuestion className="h-4 w-4 text-muted-foreground" />
            {item.subject || "(Không có tiêu đề)"}
          </DialogTitle>
          <DialogDescription>
            Chi tiết phân loại và lịch sử xử lý
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-3 rounded-lg border bg-muted/30 p-4 text-sm">
            <div>
              <span className="text-xs text-muted-foreground block">
                Người gửi
              </span>
              <span className="font-medium">
                {item.sender_name || item.sender_email}
              </span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">
                Email
              </span>
              <span className="font-medium text-xs">{item.sender_email}</span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">
                Thread ID
              </span>
              <code className="text-xs">{item.gmail_thread_id.slice(0, 20)}...</code>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">
                Message ID
              </span>
              <code className="text-xs">{item.gmail_message_id.slice(0, 20)}...</code>
            </div>
          </div>

          {/* Classification Result */}
          <div className="rounded-lg border p-4 space-y-2">
            <h4 className="flex items-center gap-1.5 text-sm font-semibold">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              Kết quả phân loại AI
            </h4>
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
                <span className="text-muted-foreground">
                  Độ tin cậy đã hiệu chỉnh:
                </span>{" "}
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
              <h4 className="text-sm font-semibold">Bằng chứng</h4>
              <ul className="text-sm space-y-1">
                {item.evidence.map((ev, i) => (
                  <li key={i} className="flex items-start gap-2 text-muted-foreground">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/40" />
                    {ev.signal}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Source Hints */}
          {item.source_hints && item.source_hints.length > 0 && (
            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="text-sm font-semibold">Nguồn gốc</h4>
              <ul className="text-sm space-y-1">
                {item.source_hints.map((hint, i) => (
                  <li key={i} className="flex items-start gap-2 text-muted-foreground">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-secondary/40" />
                    {hint.key}: {hint.value}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Attachment Metadata */}
          {item.has_attachments && (
            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="text-sm font-semibold">Tệp đính kèm</h4>
              {item.attachments_metadata &&
              item.attachments_metadata.length > 0 ? (
                <ul className="text-sm space-y-1">
                  {item.attachments_metadata.map((att, i) => (
                    <li key={i} className="flex items-center gap-2 text-muted-foreground">
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent/40" />
                      {att.name && (
                        <span className="font-medium text-foreground">
                          {att.name}
                        </span>
                      )}
                      {att.type && (
                        <span className="text-xs">({att.type})</span>
                      )}
                      {att.size != null && (
                        <span className="text-xs">
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
          {item.correction_history &&
            item.correction_history.length > 0 && (
              <div className="rounded-lg border p-4 space-y-2">
                <h4 className="text-sm font-semibold">
                  Lịch sử sửa đổi
                </h4>
                <div className="space-y-2">
                  {item.correction_history.map((entry, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded bg-muted/50 px-3 py-2 text-sm"
                    >
                      <span>
                        <span className="text-muted-foreground line-through">
                          {entry.previous_intent || "N/A"}
                        </span>{" "}
                        →{" "}
                        <span className="font-medium">
                          {entry.corrected_intent}
                        </span>
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(entry.corrected_at).toLocaleString(
                          "vi-VN"
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Dismissal Info */}
          {item.dismissed && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 space-y-1">
              <h4 className="flex items-center gap-1.5 text-sm font-semibold text-destructive">
                <X className="h-3.5 w-3.5" />
                Đã bỏ qua
              </h4>
              <p className="text-sm text-muted-foreground">
                Mục này đã bị HR bỏ qua và sẽ không bị tạo lại bởi worker
                retry.
              </p>
              {item.dismissed_at && (
                <p className="text-xs text-muted-foreground">
                  Lúc:{" "}
                  {new Date(item.dismissed_at).toLocaleString("vi-VN")}
                </p>
              )}
            </div>
          )}

          {createdApplications.length > 0 && (
            <JobApplicationActions applications={createdApplications} />
          )}

          {/* Processing Error */}
          {item.processing_error && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 space-y-1">
              <h4 className="flex items-center gap-1.5 text-sm font-semibold text-destructive">
                <AlertTriangle className="h-3.5 w-3.5" />
                Lỗi xử lý
              </h4>
              <p className="text-sm text-muted-foreground">
                {item.processing_error}
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="flex flex-wrap gap-2">
          {!item.dismissed && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSplitOpen(true)}
                disabled={loading}
              >
                <Scissors className="h-3.5 w-3.5 mr-1.5" />
                Tách ứng viên
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setLinkOpen(true)}
                disabled={loading}
              >
                <Link2 className="h-3.5 w-3.5 mr-1.5" />
                Liên kết email
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCorrectIntentOpen(true)}
                disabled={loading}
              >
                <ThumbsUp className="h-3.5 w-3.5 mr-1.5" />
                Sửa hướng
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDismiss}
                disabled={loading}
              >
                <X className="h-3.5 w-3.5 mr-1.5" />
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
              Nhập hướng định tuyến đúng cho email này (ví dụ: other, partner,
              event, internal)
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
            <Button
              variant="outline"
              onClick={() => setCorrectIntentOpen(false)}
            >
              Hủy
            </Button>
            <Button
              onClick={handleCorrect}
              disabled={loading || !correctedIntent.trim()}
            >
              {loading ? (
                <RotateCw className="h-4 w-4 animate-spin mr-1.5" />
              ) : (
                <ThumbsUp className="h-4 w-4 mr-1.5" />
              )}
              Xác nhận
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Split Dialog */}
      <Dialog open={splitOpen} onOpenChange={setSplitOpen}>
        <DialogContent className="sm:max-w-[560px]">
          <DialogHeader>
            <DialogTitle>Tách ứng viên</DialogTitle>
            <DialogDescription>
              Mỗi người sẽ trở thành một Job Application dùng chung email
              nguồn.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
            <div className="space-y-2">
              <Label htmlFor="application-source">Nguồn ứng tuyển</Label>
              <select
                id="application-source"
                className="w-full rounded-lg border bg-background px-3 py-2 text-sm shadow-sm"
                value={splitSource}
                onChange={(event) =>
                  setSplitSource(
                    event.target.value as ApplicationSource
                  )
                }
              >
                <option value="direct">Trực tiếp</option>
                <option value="employee_referral">
                  Nhân viên giới thiệu
                </option>
                <option value="agency">Agency</option>
              </select>
            </div>
            {splitApplicants.map((applicant, index) => (
              <div
                key={index}
                className="grid grid-cols-2 gap-2 rounded-lg border bg-muted/20 p-3"
              >
                <Input
                  aria-label={`Tên ứng viên ${index + 1}`}
                  placeholder="Tên ứng viên"
                  value={applicant.name}
                  onChange={(event) =>
                    setSplitApplicants((current) =>
                      current.map((value, itemIndex) =>
                        itemIndex === index
                          ? { ...value, name: event.target.value }
                          : value
                      )
                    )
                  }
                />
                <Input
                  aria-label={`Email ứng viên ${index + 1}`}
                  placeholder="Email ứng viên"
                  type="email"
                  value={applicant.email ?? ""}
                  onChange={(event) =>
                    setSplitApplicants((current) =>
                      current.map((value, itemIndex) =>
                        itemIndex === index
                          ? { ...value, email: event.target.value }
                          : value
                      )
                    )
                  }
                />
                <Input
                  className="col-span-2"
                  aria-label={`Job Opening ${index + 1}`}
                  placeholder="Job Opening ID (không bắt buộc)"
                  value={applicant.job_opening_id ?? ""}
                  onChange={(event) =>
                    setSplitApplicants((current) =>
                      current.map((value, itemIndex) =>
                        itemIndex === index
                          ? {
                              ...value,
                              job_opening_id:
                                event.target.value || undefined,
                            }
                          : value
                      )
                    )
                  }
                />
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setSplitApplicants((current) => [
                  ...current,
                  { name: "", email: "" },
                ])
              }
            >
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              Thêm ứng viên
            </Button>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSplitOpen(false)}
            >
              Hủy
            </Button>
            <Button
              onClick={handleSplit}
              disabled={
                loading ||
                !splitApplicants.some((a) => a.name.trim())
              }
            >
              Xác nhận tách
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Link Dialog */}
      <Dialog open={linkOpen} onOpenChange={setLinkOpen}>
        <DialogContent className="sm:max-w-[460px]">
          <DialogHeader>
            <DialogTitle>Liên kết email ngoài thread</DialogTitle>
            <DialogDescription>
              Hệ thống chỉ tạo đề xuất. Job Application không đổi cho tới
              khi HR xác nhận.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Label htmlFor="target-job-application">
              Job Application đích
            </Label>
            <Input
              id="target-job-application"
              placeholder="Mã Job Application"
              value={targetApplicationId}
              onChange={(event) =>
                setTargetApplicationId(event.target.value)
              }
              disabled={Boolean(linkProposal)}
            />
            {linkProposal && (
              <p className="rounded-lg border bg-muted/30 p-3 text-sm">
                Đề xuất đang chờ xác nhận:{" "}
                <code className="text-xs font-mono">
                  {linkProposal.id}
                </code>
              </p>
            )}
          </div>
          <DialogFooter>
            {!linkProposal ? (
              <Button
                onClick={handleProposeLink}
                disabled={loading || !targetApplicationId.trim()}
              >
                Tạo đề xuất
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={() => handleResolveLink("rejected")}
                >
                  Từ chối
                </Button>
                <Button
                  onClick={() => handleResolveLink("confirmed")}
                >
                  Xác nhận liên kết
                </Button>
              </>
            )}
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
  const [statusFilter, setStatusFilter] = React.useState<
    "all" | InboxStatus
  >("all");
  const [loading, setLoading] = React.useState(true);
  const [selectedItem, setSelectedItem] =
    React.useState<InboxItem | null>(null);

  const fetchList = React.useCallback(async () => {
    setLoading(true);
    try {
      const inboxStatus =
        statusFilter === "all" ? undefined : statusFilter;
      const result = await listInbox({
        inbox_status: inboxStatus,
        page,
        page_size: pageSize,
      });
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Không thể tải inbox"
      );
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
    <div className="animate-page-enter space-y-6 max-w-[1200px] mx-auto overflow-x-hidden pb-10">
      {/* ─── Header ──────────────────────────────────── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Inbox className="h-4 w-4" strokeWidth={1.5} />
            </div>
            <h1 className="font-heading text-2xl font-bold tracking-tight">
              Hộp thư tuyển dụng
            </h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground ml-10">
            Email tuyển dụng và Job Application cần xử lý
          </p>
        </div>
        <Button
          className="w-full sm:w-auto shrink-0"
          variant="outline"
          onClick={fetchList}
          disabled={loading}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
          />
          Làm mới
        </Button>
      </div>

      {/* ─── Filters Bar ─────────────────────────────── */}
      <div className="flex flex-col gap-3 rounded-xl border border-border/30 bg-card p-4 shadow-sm sm:flex-row sm:items-center sm:gap-4">
        <div className="w-full sm:w-56">
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
              <SelectItem value="needs_classification">
                Cần phân loại
              </SelectItem>
              <SelectItem value="needs_information">
                Cần bổ sung thông tin
              </SelectItem>
              <SelectItem value="ready_for_review">
                Sẵn sàng xem xét
              </SelectItem>
              <SelectItem value="resolved">Đã xử lý</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="w-full sm:w-28">
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

        <span className="text-sm tabular-nums text-muted-foreground">
          Tổng số: <strong className="text-foreground">{total}</strong> mục
        </span>
      </div>

      {/* ─── Content ─────────────────────────────────── */}
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

      {/* ─── Pagination ──────────────────────────────── */}
      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm tabular-nums text-muted-foreground">
            Trang {page}/{totalPages}
          </span>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* ─── Detail Dialog ───────────────────────────── */}
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
