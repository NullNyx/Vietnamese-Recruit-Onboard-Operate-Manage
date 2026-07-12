"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Building2, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CandidateStatusBadge } from "@/components/recruitment/candidate-status-badge";
import { ConfidenceScore } from "@/components/recruitment/confidence-score";
import { CVSections } from "@/components/recruitment/cv-sections";
import { DocumentList } from "@/components/recruitment/document-list";
import { CandidateActions } from "@/components/recruitment/candidate-actions";
import { AssignJobOpeningDialog } from "@/components/recruitment/assign-job-opening-dialog";
import { UnassignDialog } from "@/components/recruitment/unassign-dialog";
import { RejectDialog } from "@/components/recruitment/reject-dialog";
import { AcceptDialog } from "@/components/recruitment/accept-dialog";
import { ArchiveDialog } from "@/components/recruitment/archive-dialog";
import { InterviewFormDialog } from "@/components/recruitment/interview-form-dialog";
import type { InterviewFormData, Interviewer } from "@/components/recruitment/interview-form-dialog";
import { InterviewList } from "@/components/recruitment/interview-list";
import { ConflictManager } from "@/components/recruitment/conflict-manager";
import { SendEmailDialog } from "@/components/recruitment/send-email-dialog";
import {
  getCandidate,
  createInterview,
  completeInterview,
  cancelInterview,
  createReplacementInterview,
  listCalendarConflicts,
  sendEmail,
  rejectCandidate,
  acceptCandidate,
  archiveCandidate,
  assignCandidate,
  reassignCandidate,
  unassignCandidate,
    type CandidateDetail,
    type CalendarConflict,
  type SendEmailRequest,
  type RejectRequest,
} from "@/lib/api/recruitment";
import { ApiError } from "@/lib/api/types";
import { listEmployees } from "@/lib/api/employees";
import { formatDate, type CandidateStatus } from "@/lib/recruitment-utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type DialogType =
  | "reject"
  | "accept"
  | "archive"
  | "schedule"
  | "replacement"
  | "email"
  | "assign"
  | "unassign"
  | null;

type PageState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; candidate: CandidateDetail };

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

function isTerminalStatus(status: string): boolean {
  return ["accepted", "rejected", "archived"].includes(status);
}

export default function CandidateDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [pageState, setPageState] = useState<PageState>({ kind: "loading" });
  const [activeDialog, setActiveDialog] = useState<DialogType>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionAnnouncement, setActionAnnouncement] = useState("");
  const [errorAnnouncement, setErrorAnnouncement] = useState("");
  const [currentJobOpeningId, setCurrentJobOpeningId] = useState<string | null>(null);
  const [currentJobOpeningTitle, setCurrentJobOpeningTitle] = useState("");
  const [replacementSourceId, setReplacementSourceId] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<CalendarConflict[]>([]);
    const [interviewers, setInterviewers] = useState<Interviewer[]>([]);

  // -------------------------------------------------------------------------
  // Data Fetching
  // -------------------------------------------------------------------------

  const fetchCandidate = useCallback(async () => {
    setPageState({ kind: "loading" });
    try {
      const candidate = await getCandidate(id);
      setCurrentJobOpeningId(candidate.job_opening_id ?? null);
      setCurrentJobOpeningTitle(candidate.job_opening_title);
      setPageState({ kind: "loaded", candidate });
    } catch (err) {
      if (err instanceof ApiError && err.statusCode === 404) {
        setPageState({ kind: "not_found" });
      } else if (err instanceof ApiError && err.statusCode >= 500) {
        setPageState({
          kind: "error",
          message: "Không thể tải thông tin ứng viên. Vui lòng thử lại.",
        });
      } else {
        setPageState({
          kind: "error",
          message:
            err instanceof ApiError
              ? err.message
              : "Đã xảy ra lỗi. Vui lòng thử lại.",
        });
      }
    }
  }, [id]);

  const fetchConflicts = useCallback(async () => {
    try {
      const result = await listCalendarConflicts({ candidate_id: id });
      setConflicts(result.conflicts);
    } catch {
      // Conflicts are non-critical; silently ignore errors
    }
  }, [id]);

  useEffect(() => {
    fetchCandidate();
  }, [fetchCandidate]);

  useEffect(() => {
    if (pageState.kind === "loaded") {
      fetchConflicts();
    }
  }, [pageState.kind, fetchConflicts]);

  useEffect(() => {
    void listEmployees({ page: 1, page_size: 100, is_active: true })
      .then((result) => {
        setInterviewers(
          result.items
            .filter((employee) => Boolean(employee.email))
            .map((employee) => ({
              id: employee.id,
              name: employee.full_name,
              email: employee.email,
            })),
        );
      })
      .catch(() => {
        // External interviewers remain available if Employee loading fails.
        setInterviewers([]);
      });
  }, []);

  // -------------------------------------------------------------------------
  // Action Handlers
  // -------------------------------------------------------------------------

  async function handleActionSuccess(successMessage: string) {
    setActiveDialog(null);
    setActionLoading(false);
    toast.success(successMessage);
    setActionAnnouncement(successMessage);
    await fetchCandidate();
    await fetchConflicts();
  }

  function handleActionError(err: unknown) {
    if (err instanceof ApiError && err.statusCode === 409) {
      toast.error("Không thể thực hiện hành động này với trạng thái hiện tại");
      setErrorAnnouncement(
        "Không thể thực hiện hành động này với trạng thái hiện tại",
      );
      setActiveDialog(null);
    } else {
      const message =
        err instanceof ApiError
          ? err.message
          : "Đã xảy ra lỗi. Vui lòng thử lại.";
      toast.error(message);
      setErrorAnnouncement(message);
      // Keep dialog open on 5xx/network errors (data preserved)
    }
    setActionLoading(false);
  }

  async function handleAssign(jobOpeningId: string) {
    setActionLoading(true);
    try {
      if (currentJobOpeningId) {
        await reassignCandidate(id, jobOpeningId);
        await handleActionSuccess("Đã chuyển vị trí tuyển dụng thành công");
      } else {
        await assignCandidate(id, jobOpeningId);
        await handleActionSuccess("Đã gán vị trí tuyển dụng thành công");
      }
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleUnassign() {
    setActionLoading(true);
    try {
      await unassignCandidate(id);
      await handleActionSuccess("Đã bỏ gán vị trí tuyển dụng thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleReject(reason: string) {
    setActionLoading(true);
    try {
      const data: RejectRequest = { reason };
      await rejectCandidate(id, data);
      await handleActionSuccess("Đã từ chối ứng viên thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleAccept() {
    setActionLoading(true);
    try {
      await acceptCandidate(id);
      await handleActionSuccess("Đã chấp nhận ứng viên thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleArchive() {
    setActionLoading(true);
    try {
      await archiveCandidate(id);
      await handleActionSuccess("Đã lưu trữ ứng viên thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleCreateInterview(data: InterviewFormData) {
    setActionLoading(true);
    try {
      await createInterview(id, data);
      await handleActionSuccess("Đã lên lịch phỏng vấn thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleReplacementInterview(
    cancelledInterviewId: string,
    data: InterviewFormData,
  ) {
    setActionLoading(true);
    try {
      await createReplacementInterview(id, cancelledInterviewId, data);
      await handleActionSuccess("Đã tạo lịch phỏng vấn thay thế thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleCompleteInterview(interviewId: string) {
    setActionLoading(true);
    try {
      await completeInterview(id, interviewId);
      await handleActionSuccess("Đã hoàn thành buổi phỏng vấn");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleCancelInterview(interviewId: string) {
    setActionLoading(true);
    try {
      await cancelInterview(id, interviewId);
      await handleActionSuccess("Đã hủy buổi phỏng vấn");
    } catch (err) {
      handleActionError(err);
    }
  }

  async function handleSendEmail(data: { subject: string; body: string }) {
    setActionLoading(true);
    try {
      const request: SendEmailRequest = {
        subject: data.subject,
        body_html: data.body,
      };
      await sendEmail(id, request);
      await handleActionSuccess("Đã gửi email thành công");
    } catch (err) {
      handleActionError(err);
    }
  }

  // -------------------------------------------------------------------------
  // Render: Loading State
  // -------------------------------------------------------------------------

  if (pageState.kind === "loading") {
    return (
      <div className="p-6 space-y-6">
        {/* Breadcrumb skeleton */}
        <Skeleton className="h-4 w-48" />

        {/* Header skeleton */}
        <div className="space-y-3">
          <Skeleton className="h-8 w-64" />
          <div className="flex gap-4">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-5 w-28" />
          </div>
        </div>

        {/* Status and confidence skeleton */}
        <div className="flex gap-4">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-6 w-32" />
        </div>

        {/* Actions skeleton */}
        <div className="flex gap-2">
          <Skeleton className="h-9 w-28" />
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
        </div>

        {/* CV sections skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <Skeleton className="h-5 w-20" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-5 w-20" />
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-20" />
              <Skeleton className="h-6 w-14" />
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Not Found State
  // -------------------------------------------------------------------------

  if (pageState.kind === "not_found") {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <p className="text-lg text-muted-foreground">Không tìm thấy ứng viên</p>
        <Link href="/recruitment">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Quay lại danh sách
          </Button>
        </Link>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Error State
  // -------------------------------------------------------------------------

  if (pageState.kind === "error") {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <p className="text-lg text-destructive">{pageState.message}</p>
        <Button variant="outline" onClick={fetchCandidate}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Thử lại
        </Button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Render: Loaded State
  // -------------------------------------------------------------------------

  const { candidate } = pageState;

  return (
    <div className="p-6 space-y-6">
      {/* aria-live regions for announcements */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {actionAnnouncement}
      </div>
      <div aria-live="assertive" aria-atomic="true" className="sr-only">
        {errorAnnouncement}
      </div>

      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-2 text-sm text-muted-foreground">
          <li>
            <Link
              href="/recruitment"
              className="hover:text-foreground transition-colors"
            >
              Tuyển dụng
            </Link>
          </li>
          <li aria-hidden="true">&gt;</li>
          <li className="text-foreground font-medium">{candidate.name}</li>
        </ol>
      </nav>

      {/* Header: Name + basic info */}
      <div className="space-y-3">
        <h1 className="text-2xl font-bold text-foreground">{candidate.name}</h1>
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span>{candidate.email}</span>
          <span>{candidate.phone}</span>
          <span>Ngày tạo: {formatDate(candidate.created_at)}</span>
        </div>
      </div>

      {/* Status + Confidence */}
      <div className="flex flex-wrap items-center gap-4">
        <CandidateStatusBadge status={candidate.status as CandidateStatus} />
        <ConfidenceScore score={candidate.confidence_score} />
      </div>

      {/* Action Buttons */}
      <div className="border-b pb-4">
        <CandidateActions
          status={candidate.status as CandidateStatus}
          onScheduleInterview={() => setActiveDialog("schedule")}
          onSendEmail={() => setActiveDialog("email")}
          onReject={() => setActiveDialog("reject")}
          onAccept={() => setActiveDialog("accept")}
          onArchive={() => setActiveDialog("archive")}
          disabled={actionLoading}
        />
      </div>

      {/* Job Opening Assignment */}
      <div className="flex flex-wrap items-center gap-3 rounded-md border bg-muted/30 px-4 py-3">
        <div className="flex min-w-0 flex-1 items-center gap-2 text-sm">
          <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="shrink-0 text-muted-foreground">Vị trí tuyển dụng:</span>
          {candidate.job_opening_id ? (
            <span className="truncate font-medium">{candidate.job_opening_title || "Đã gán"}</span>
          ) : (
            <span className="italic text-muted-foreground">Chưa gán</span>
          )}
        </div>
        {!isTerminalStatus(candidate.status) && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveDialog("assign")}
              disabled={actionLoading}
            >
              {candidate.job_opening_id ? "Chuyển vị trí" : "Gán vị trí"}
            </Button>
            {candidate.job_opening_id && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveDialog("unassign")}
                disabled={actionLoading}
                className="text-destructive hover:text-destructive"
              >
                Bỏ gán
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Calendar Conflicts */}
      <ConflictManager
        conflicts={conflicts}
        onConflictResolved={() => {
          void fetchConflicts();
        }}
      />

      {/* Interview List (new Interview API) */}
      <InterviewList
        interviews={candidate.interviews ?? []}
        candidateId={id}
        onReplacement={(interview) => {
          setReplacementSourceId(interview.id);
          setActiveDialog("replacement");
        }}
        onComplete={(interview) => {
          void handleCompleteInterview(interview.id);
        }}
        onCancel={(interview) => {
          void handleCancelInterview(interview.id);
        }}
        actionLoading={actionLoading}
      />

      {/* CV Sections + Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CV Parsed Data */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Thông tin CV</h2>
          <CVSections
            summary={candidate.summary}
            skills={candidate.skills}
            experience={candidate.experience}
            education={candidate.education}
          />
        </div>

        {/* Documents */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Tài liệu</h2>
          <DocumentList
            documents={candidate.cv_documents}
            candidateId={candidate.id}
          />
        </div>
      </div>

      {/* Action Dialogs */}
      <RejectDialog
        open={activeDialog === "reject"}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        onConfirm={handleReject}
        loading={actionLoading}
      />

      <AcceptDialog
        open={activeDialog === "accept"}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        onConfirm={handleAccept}
        loading={actionLoading}
      />

      <ArchiveDialog
        open={activeDialog === "archive"}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        onConfirm={handleArchive}
        loading={actionLoading}
      />

      <InterviewFormDialog
        open={activeDialog === "schedule"}
        onOpenChange={(open) => {
          if (!open) {
            setActiveDialog(null);
          }
        }}
        onConfirm={(data) => {
          void handleCreateInterview(data);
        }}
        loading={actionLoading}
        interviewers={interviewers}
        mode="create"
      />

      <InterviewFormDialog
        open={activeDialog === "replacement"}
        onOpenChange={(open) => {
          if (!open) {
            setReplacementSourceId(null);
            setActiveDialog(null);
          }
        }}
        onConfirm={(data) => {
          if (replacementSourceId) {
            void handleReplacementInterview(replacementSourceId, data);
          }
        }}
        loading={actionLoading}
        interviewers={interviewers}
        mode="replacement"
      />

      <SendEmailDialog
        open={activeDialog === "email"}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        onConfirm={handleSendEmail}
        loading={actionLoading}
      />

      <AssignJobOpeningDialog
        open={activeDialog === "assign"}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        onConfirm={handleAssign}
        currentAssignment={currentJobOpeningTitle || undefined}
        loading={actionLoading}
      />

      <UnassignDialog
        open={activeDialog === "unassign"}
        onOpenChange={(open) => {
          if (!open) setActiveDialog(null);
        }}
        onConfirm={handleUnassign}
        jobOpeningTitle={currentJobOpeningTitle || undefined}
        loading={actionLoading}
      />
    </div>
  );
}
