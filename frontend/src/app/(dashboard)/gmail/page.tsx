"use client";

import * as React from "react";
import { PenSquare, RotateCw, Sparkles } from "lucide-react";

import type { ConnectionStatus, EmailMessage, CapabilityHealth } from "@/lib/api/types";
import { ApiError } from "@/lib/api/types";
import * as gmailApi from "@/lib/api/gmail";

import { ToastProvider, useToast } from "@/components/gmail/toast-provider";
import { ConnectionPanel } from "@/components/gmail/connection-panel";
import { ConfirmDialog } from "@/components/gmail/confirm-dialog";
import { EmailList } from "@/components/gmail/email-list";
import { HistoricalImportPanel } from "@/components/gmail/historical-import-panel";
import { SyncIndicator } from "@/components/gmail/sync-indicator";
import { EmailDetail } from "@/components/gmail/email-detail";
import { ComposeDialog } from "@/components/gmail/compose-dialog";
import { AIClassificationBanner } from "@/components/gmail/ai-classification-banner";
import { EmailEmptyState } from "@/components/gmail/email-empty-state";

// ---------------------------------------------------------------------------
// Inner page component (needs ToastProvider context)
// ---------------------------------------------------------------------------

function GmailPageContent() {
  const { addToast } = useToast();

  // --- Connection state ---
  const [connectionStatus, setConnectionStatus] =
    React.useState<ConnectionStatus | null>(null);
  const [connectedEmail, setConnectedEmail] = React.useState<string | null>(
    null,
  );
  const [statusLoading, setStatusLoading] = React.useState(true);
  const [statusError, setStatusError] = React.useState<string | null>(null);
  const [connectLoading, setConnectLoading] = React.useState(false);
  const [disconnectLoading, setDisconnectLoading] = React.useState(false);
  const [disconnectDialogOpen, setDisconnectDialogOpen] = React.useState(false);

  // --- Capability health state ---
  const [capabilities, setCapabilities] = React.useState<CapabilityHealth[]>([]);

  // --- Email list state ---
  const [emails, setEmails] = React.useState<EmailMessage[]>([]);
  const [emailsLoading, setEmailsLoading] = React.useState(false);

  // --- Selected email state ---
  const [selectedEmailId, setSelectedEmailId] = React.useState<string | null>(
    null,
  );

  // --- Compose state ---
  const [composeOpen, setComposeOpen] = React.useState(false);
  const [replyToEmail, setReplyToEmail] = React.useState<EmailMessage | null>(
    null,
  );

  // --- Category filter state ---
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(
    null,
  );

  // --- Review mode state ---
  const [reviewMode, setReviewMode] = React.useState(false);
  const [reviewEmails, setReviewEmails] = React.useState<EmailMessage[]>([]);
  const [reclassifying, setReclassifying] = React.useState<string | null>(null);
  const [processingAttachments, setProcessingAttachments] = React.useState<string | null>(null);

  // --- Classification state ---
  const [classifying, setClassifying] = React.useState(false);
  const [classifyProgress, setClassifyProgress] = React.useState<string | null>(
    null,
  );

  // Derived: filtered emails by category
  const filteredEmails = React.useMemo(() => {
    const source = reviewMode ? reviewEmails : emails;
    if (selectedCategory === null) return source;
    return source.filter(
      (e) => (e.category || "uncategorized") === selectedCategory,
    );
  }, [emails, reviewEmails, reviewMode, selectedCategory]);

  // Derived: selected email object
  const selectedEmail = React.useMemo(
    () => (reviewMode ? reviewEmails : emails).find((e) => e.id === selectedEmailId) ?? null,
    [emails, reviewEmails, reviewMode, selectedEmailId],
  );

  // --- Error handler (stable ref to avoid re-render loops) ---
  const handleApiErrorRef = React.useRef<(err: unknown) => void>(() => {});
  handleApiErrorRef.current = React.useCallback(
    (err: unknown) => {
      if (err instanceof ApiError) {
        if (err.statusCode === 401) {
          window.location.href = "/login";
          return;
        }
        addToast(err.message, "error");
      } else {
        addToast("Không thể kết nối server. Vui lòng thử lại.", "error");
      }
    },
    [addToast],
  );

  const handleApiError = React.useCallback((err: unknown) => {
    handleApiErrorRef.current(err);
  }, []);

  // --- Fetch review emails ---
  const fetchReviewEmails = React.useCallback(async () => {
    try {
      const res = await gmailApi.listEmailsNeedingReview();
      setReviewEmails(res.messages);
    } catch (err) {
      handleApiError(err);
    }
  }, [handleApiError]);

  // --- Fetch connection status from identity router ---
  const fetchStatus = React.useCallback(async () => {
    setStatusLoading(true);
    setStatusError(null);
    try {
      const res = await gmailApi.getConnectionStatus();
      setConnectionStatus(res.status);
      setConnectedEmail(res.email);
    } catch (err) {
      if (err instanceof ApiError && err.statusCode === 401) {
        window.location.href = "/login";
        return;
      }
      setStatusError(
        err instanceof Error ? err.message : "Không thể kiểm tra trạng thái",
      );
    } finally {
      setStatusLoading(false);
    }
  }, []);

  // --- Update capability health when connection status changes ---
  React.useEffect(() => {
    setCapabilities(gmailApi.getCapabilityHealth(connectionStatus === "connected"));
  }, [connectionStatus]);

  // --- Fetch emails from backend ---
  const fetchEmails = React.useCallback(async () => {
    setEmailsLoading(true);
    try {
      const res = await fetch("/api/gmail/messages");
      if (!res.ok) {
        if (res.status === 401) {
          window.location.href = "/login";
          return;
        }
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new ApiError(
          res.status,
          "FETCH_ERROR",
          body?.detail || "Không thể tải danh sách email",
        );
      }
      const data = await res.json();
      // Support both { items: [...] } and direct array response
      const emailList: EmailMessage[] = Array.isArray(data)
        ? data
        : (data.items ?? data.messages ?? []);
      setEmails(emailList);
    } catch (err) {
      handleApiError(err);
    } finally {
      setEmailsLoading(false);
    }
  }, [handleApiError]);

  // --- On mount: fetch status ---
  React.useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // --- When connected: fetch emails + review count ---
  React.useEffect(() => {
    if (connectionStatus === "connected") {
      fetchEmails();
      fetchReviewEmails();
    } else {
      setEmails([]);
      setSelectedEmailId(null);
    }
  }, [connectionStatus, fetchEmails, fetchReviewEmails]);

  // --- Connect handler: get authorize URL from identity router ---
  const handleConnect = React.useCallback(async () => {
    setConnectLoading(true);
    try {
      const res = await gmailApi.getAuthorizeUrl();
      if (res.redirect_url) {
        window.location.href = res.redirect_url;
      } else {
        // Already connected
        await fetchStatus();
      }
    } catch (err) {
      handleApiError(err);
    } finally {
      setConnectLoading(false);
    }
  }, [fetchStatus, handleApiError]);

  // --- Reconnect handler: for reauthorization_required case ---
  const handleReconnect = React.useCallback(async () => {
    setConnectLoading(true);
    try {
      const res = await gmailApi.reconnectConnection();
      if (res.redirect_url) {
        window.location.href = res.redirect_url;
      } else {
        await fetchStatus();
      }
    } catch (err) {
      handleApiError(err);
    } finally {
      setConnectLoading(false);
    }
  }, [fetchStatus, handleApiError]);

  // --- Disconnect handlers ---
  const handleDisconnectClick = React.useCallback(() => {
    setDisconnectDialogOpen(true);
  }, []);

  const handleDisconnectConfirm = React.useCallback(async () => {
    setDisconnectDialogOpen(false);
    setDisconnectLoading(true);
    try {
      const res = await gmailApi.disconnectConnection();
      setConnectionStatus(res.status);
      setConnectedEmail(res.email);
      addToast("Đã ngắt kết nối Gmail thành công.", "success");
    } catch (err) {
      handleApiError(err);
    } finally {
      setDisconnectLoading(false);
    }
  }, [addToast, handleApiError]);

  const handleDisconnectCancel = React.useCallback(() => {
    setDisconnectDialogOpen(false);
  }, []);

  // --- Sync complete handler ---
  const handleSyncComplete = React.useCallback(() => {
    fetchEmails();
  }, [fetchEmails]);

  // --- Connection lost handler (from SyncIndicator 409) ---
  const handleConnectionLost = React.useCallback(() => {
    fetchStatus();
  }, [fetchStatus]);

  // --- Email selection ---
  const handleEmailSelect = React.useCallback((id: string) => {
    setSelectedEmailId(id);
  }, []);

  // --- Back button (mobile) ---
  const handleBack = React.useCallback(() => {
    setSelectedEmailId(null);
  }, []);

  // --- Reply handler ---
  const handleReply = React.useCallback((email: EmailMessage) => {
    setReplyToEmail(email);
    setComposeOpen(true);
  }, []);

  // --- Reclassify handler ---
  const handleReclassify = React.useCallback(async (emailId: string) => {
    setReclassifying(emailId);
    try {
      const result = await gmailApi.reclassifyEmail(emailId);
      // Update the email in the review list
      setReviewEmails((prev) =>
        prev.map((e) => (e.id === emailId ? result : e)),
      );
      // Also update in main emails list if present
      setEmails((prev) => prev.map((e) => (e.id === emailId ? result : e)));
      addToast("Đã phân loại lại email", "success");
      // If email is no longer needs_review, remove from review list
      if (result.processing_status !== "needs_review") {
        setReviewEmails((prev) => prev.filter((e) => e.id !== emailId));
      }
    } catch (err) {
      handleApiError(err);
    } finally {
      setReclassifying(null);
    }
  }, [addToast, handleApiError]);

  // --- Process attachments handler ---
  const handleProcessAttachments = React.useCallback(async (messageId: string) => {
    setProcessingAttachments(messageId);
    try {
      const result = await gmailApi.processAttachments(messageId);
      if (result.processed_count > 0) {
        addToast(`Đã xử lý ${result.processed_count} CV`, "success");
      } else {
        addToast(result.message || "Không có CV nào để xử lý", "success");
      }
      // Refetch emails to update processing status + attachment badges
      await fetchEmails();
      if (reviewMode) await fetchReviewEmails();
    } catch (err) {
      handleApiError(err);
    } finally {
      setProcessingAttachments(null);
    }
  }, [addToast, handleApiError, fetchEmails, fetchReviewEmails, reviewMode]);

  // --- Compose handlers ---
  const handleComposeOpen = React.useCallback(() => {
    setReplyToEmail(null);
    setComposeOpen(true);
  }, []);

  const handleComposeClose = React.useCallback(() => {
    setComposeOpen(false);
    setReplyToEmail(null);
  }, []);

  // --- Classify handler ---
  const handleClassify = React.useCallback(async () => {
    setClassifying(true);
    setClassifyProgress("Đang chuẩn bị phân loại...");

    let totalClassified = 0;
    let totalToClassify: number | null = null;
      let totalCvProcessed = 0;

    try {
      // Process in batches of 5 to avoid proxy timeout
      let remaining = 1; // Start with non-zero to enter loop
      while (remaining > 0) {
        const result = await gmailApi.classifyBatch(5);

        // On first batch, capture the real total from backend
        if (totalToClassify === null) {
          totalToClassify = result.remaining + result.classified_count;
        }

        totalClassified += result.classified_count;
          totalCvProcessed += result.cv_processed_count ?? 0;
        remaining = result.remaining;

        // Update progress with accurate numbers
        setClassifyProgress(
          `AI đang phân loại... (${totalClassified}/${totalToClassify})`,
        );

        // If nothing was classified in this batch, stop
        if (result.classified_count === 0) break;
      }

      setClassifyProgress(null);
      addToast(`AI đã phân loại ${totalClassified} email${totalCvProcessed > 0 ? `, xử lý ${totalCvProcessed} CV` : ""}`, "success");
      await fetchEmails();
    } catch (err) {
      setClassifyProgress(null);
      if (totalClassified > 0) {
        addToast(
          `Đã phân loại ${totalClassified}/${totalToClassify ?? "?"} email (có lỗi)`,
          "error",
        );
        await fetchEmails();
      } else {
        handleApiError(err);
      }
    } finally {
      setClassifying(false);
    }
  }, [addToast, fetchEmails, handleApiError]);

  // --- Determine if connected ---
  const isConnected = connectionStatus === "connected";

  // --- Handle connect or reconnect based on status ---
  const handleConnectOrReconnect = React.useCallback(() => {
    if (connectionStatus === "reauthorization_required") {
      return handleReconnect();
    }
    return handleConnect();
  }, [connectionStatus, handleConnect, handleReconnect]);

  return (
    <div className="gmail-fullbleed flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold text-foreground">Hộp thư</h1>
        </div>
        {isConnected && (
          <div className="flex items-center gap-2">
            {/* Review button — shows count of needs_review emails */}
            <button
              type="button"
              onClick={() => {
                const newMode = !reviewMode;
                setReviewMode(newMode);
                setSelectedEmailId(null);
                if (newMode) fetchReviewEmails();
              }}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                reviewMode
                  ? "bg-orange-100 text-orange-700 ring-1 ring-orange-200"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
            >
              <RotateCw className="h-3.5 w-3.5" />
              Cần review
              {reviewEmails.length > 0 && (
                <span className="rounded-full bg-orange-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-orange-700">
                  {reviewEmails.length}
                </span>
              )}
            </button>

            {/* Classify button in header — always visible when there are unclassified emails */}
            {emails.length > 0 &&
              emails.some(
                (e) => !e.category || e.category === "uncategorized",
              ) && (
                <button
                  type="button"
                  onClick={handleClassify}
                  disabled={classifying}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {classifying
                    ? "Đang phân loại..."
                    : `Phân loại (${emails.filter((e) => !e.category || e.category === "uncategorized").length})`}
                </button>
              )}
                <SyncIndicator
                  onSyncComplete={handleSyncComplete}
                  onConnectionLost={handleConnectionLost}
                />

                {/* Historical Import Panel */}
                <HistoricalImportPanel />
          </div>
        )}
      </div>

      {/* Connection Panel - always visible when not connected */}
      {!isConnected && (
        <div className="p-4 sm:p-6">
          <ConnectionPanel
            status={connectionStatus}
            email={connectedEmail}
            loading={statusLoading}
            error={statusError}
            onConnect={handleConnectOrReconnect}
            onDisconnect={handleDisconnectClick}
            onRetry={fetchStatus}
            connectLoading={connectLoading}
            disconnectLoading={disconnectLoading}
            capabilities={capabilities}
          />
        </div>
      )}

      {/* Main content area - only when connected */}
      {isConnected && (
        <div className="flex flex-1 flex-col overflow-hidden relative min-h-0">
          {/* Classification progress overlay */}
          {classifying && classifyProgress && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/80">
              <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-card px-8 py-6 shadow-md">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                  <Sparkles className="h-6 w-6 text-primary animate-pulse" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-foreground">
                    AI đang phân loại email
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {classifyProgress}
                  </p>
                </div>
                <div className="w-48 h-1.5 rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-primary rounded-full animate-pulse w-2/3" />
                </div>
              </div>
            </div>
          )}
          {/* AI Classification Banner — always visible when connected */}
          <AIClassificationBanner
            emails={emails}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            onClassify={handleClassify}
            classifying={classifying}
          />

          {/* Two-panel layout */}
          <div className="flex flex-1 min-h-0 overflow-hidden">
            {/* Left panel: Connection + Email List */}
            <div
              className={`flex flex-col border-r border-border ${
                selectedEmailId ? "hidden lg:flex" : "flex"
              } w-full lg:w-[380px] lg:shrink-0 h-full`}
            >
              {/* Connection status bar (compact) with capability health */}
              <div className="border-b border-border px-3 py-2 space-y-2">
                <ConnectionPanel
                  status={connectionStatus}
                  email={connectedEmail}
                  loading={statusLoading}
                  error={statusError}
                  onConnect={handleConnectOrReconnect}
                  onDisconnect={handleDisconnectClick}
                  onRetry={fetchStatus}
                  connectLoading={connectLoading}
                  disconnectLoading={disconnectLoading}
                  compact
                />
                {/* Capability health cards shown separately from connection status */}
                {connectionStatus === "connected" && capabilities.length > 0 && (
                  <div className="pt-1">
                    {/* Using CapabilityHealthCards inline */}
                    {capabilities.map((cap) => (
                      <div
                        key={cap.capability}
                        className="flex items-center gap-1.5 py-0.5"
                      >
                        <span className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-400" />
                        <span className="text-[10px] text-muted-foreground">
                          {cap.label}:{" "}
                          {cap.health === "unknown"
                            ? "Chưa xác thực"
                            : cap.health === "unavailable"
                              ? "Không khả dụng"
                              : cap.health === "healthy"
                                ? "Hoạt động"
                                : "Lỗi"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Email list or empty state */}
              <div className="flex-1 overflow-y-auto">
                {!emailsLoading && filteredEmails.length === 0 ? (
                  <EmailEmptyState
                    isFirstSync={emails.length === 0}
                    onSync={() => {
                      const syncBtn = document.querySelector(
                        '[aria-label="Đồng bộ email"]',
                      ) as HTMLButtonElement | null;
                      syncBtn?.click();
                    }}
                  />
                ) : (
                  <EmailList
                    emails={filteredEmails}
                    selectedId={selectedEmailId}
                    loading={emailsLoading}
                    onSelect={handleEmailSelect}
                    connected={isConnected}
                  />
                )}
              </div>
            </div>

            {/* Right panel: Email Detail */}
            <div
              className={`flex flex-1 flex-col overflow-hidden h-full ${
                selectedEmailId ? "flex" : "hidden lg:flex"
              }`}
            >
              {selectedEmail ? (
                <div className="flex h-full flex-col overflow-hidden">
                  <EmailDetail
                    email={selectedEmail}
                    onBack={handleBack}
                    onReply={handleReply}
                    onReclassify={handleReclassify}
                    reclassifying={reclassifying}
                    onProcessAttachments={handleProcessAttachments}
                    processingAttachments={processingAttachments}
                  />
                </div>
              ) : (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">
                      Chọn một email để xem nội dung
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Email được AI phân loại tự động sau khi đồng bộ
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Floating Compose Button */}
      {isConnected && (
        <button
          type="button"
          onClick={handleComposeOpen}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-lg transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
          aria-label="Soạn email mới"
        >
          <PenSquare className="h-5 w-5" />
          <span className="hidden sm:inline">Soạn email</span>
        </button>
      )}

      {/* Compose Dialog */}
      <ComposeDialog
        open={composeOpen}
        onClose={handleComposeClose}
        replyTo={replyToEmail}
      />

      {/* Disconnect Confirmation Dialog */}
      <ConfirmDialog
        open={disconnectDialogOpen}
        onConfirm={handleDisconnectConfirm}
        onCancel={handleDisconnectCancel}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page export (wrapped with ToastProvider)
// ---------------------------------------------------------------------------

export default function GmailPage() {
  return (
    <ToastProvider>
      <GmailPageContent />
    </ToastProvider>
  );
}
