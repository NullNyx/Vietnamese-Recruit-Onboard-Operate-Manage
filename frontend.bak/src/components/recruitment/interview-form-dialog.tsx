"use client";

import * as React from "react";
import { Loader2, X, Plus, ExternalLink, MapPin, Video } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Interviewer {
  id: string;
  name: string;
}

export type InterviewMode = "google_meet" | "in_person" | "custom_link";

/**
 * Payload emitted on confirm — matches the CreateInterviewRequest contract.
 */
export interface InterviewFormData {
  round_name: string;
  start: string; // ISO 8601 datetime with timezone offset
  end: string; // ISO 8601 datetime with timezone offset
  timezone: string; // IANA timezone
  mode: InterviewMode;
  meeting_link?: string | null;
  interviewer_ids: string[];
  external_participant_emails?: string[];
  notes?: string | null;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const NOTES_MAX = 1000;
const MAX_INTERVIEWERS = 20;
const MAX_EXTERNAL_EMAILS = 20;

const MODE_OPTIONS: { value: InterviewMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: "google_meet", label: "Google Meet", icon: Video },
  { value: "in_person", label: "Trực tiếp", icon: MapPin },
  { value: "custom_link", label: "Link tùy chỉnh", icon: ExternalLink },
];

const TIMEZONES = [
  "Asia/Ho_Chi_Minh",
  "Asia/Hanoi",
  "Asia/Saigon",
  "Asia/Bangkok",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Asia/Seoul",
  "Asia/Taipei",
  "Asia/Hong_Kong",
  "Asia/Shanghai",
  "Asia/Kuala_Lumpur",
  "Asia/Jakarta",
  "Asia/Manila",
  "Asia/Yangon",
  "Asia/Phnom_Penh",
  "Asia/Vientiane",
  "Australia/Sydney",
  "Pacific/Auckland",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Moscow",
  "UTC",
];

function toLocalDatetimeValue(isoString?: string | null): string {
  if (!isoString) return "";
  const d = new Date(isoString);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface InterviewFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (data: InterviewFormData) => void;
  loading?: boolean;
  interviewers?: Interviewer[];
  /** Initial values for editing/replacement. */
  initialValues?: Partial<InterviewFormData>;
  /** "create" (default) creates a new interview; "replacement" creates a replacement for a cancelled interview. */
  mode?: "create" | "replacement";
  /** Error message to display (e.g. CALENDAR_GRANT_MISSING). Preserves form data. */
  serverError?: string | null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function InterviewFormDialog({
  open,
  onOpenChange,
  onConfirm,
  loading = false,
  interviewers = [],
  initialValues,
  mode = "create",
  serverError,
}: InterviewFormDialogProps) {
  const [roundName, setRoundName] = React.useState(initialValues?.round_name ?? "");
  const [start, setStart] = React.useState(toLocalDatetimeValue(initialValues?.start));
  const [end, setEnd] = React.useState(toLocalDatetimeValue(initialValues?.end));
  const [timezone, setTimezone] = React.useState(initialValues?.timezone ?? "Asia/Ho_Chi_Minh");
  const [interviewMode, setInterviewMode] = React.useState<InterviewMode>(
    (initialValues?.mode as InterviewMode) ?? "google_meet",
  );
  const [meetingLink, setMeetingLink] = React.useState(initialValues?.meeting_link ?? "");
  const [selectedInterviewers, setSelectedInterviewers] = React.useState<string[]>(
    initialValues?.interviewer_ids ?? [],
  );
  const [externalEmails, setExternalEmails] = React.useState<string[]>(
    initialValues?.external_participant_emails ?? [],
  );
  const [externalEmailInput, setExternalEmailInput] = React.useState("");
  const [notes, setNotes] = React.useState(initialValues?.notes ?? "");
  const [touched, setTouched] = React.useState(false);

  const isReplacement = mode === "replacement";
  const title = isReplacement ? "Tạo lịch phỏng vấn thay thế" : "Lên lịch phỏng vấn";
  const description = isReplacement
    ? "Tạo buổi phỏng vấn mới thay thế cho buổi đã hủy."
    : "Chọn thông tin cho buổi phỏng vấn của ứng viên.";
  const confirmLabel = isReplacement ? "Tạo lịch thay thế" : "Lên lịch phỏng vấn";

  // Reset form when opening
  React.useEffect(() => {
    if (open) {
      setRoundName(initialValues?.round_name ?? "");
      setStart(toLocalDatetimeValue(initialValues?.start));
      setEnd(toLocalDatetimeValue(initialValues?.end));
      setTimezone(initialValues?.timezone ?? "Asia/Ho_Chi_Minh");
      setInterviewMode((initialValues?.mode as InterviewMode) ?? "google_meet");
      setMeetingLink(initialValues?.meeting_link ?? "");
      setSelectedInterviewers(initialValues?.interviewer_ids ?? []);
      setExternalEmails(initialValues?.external_participant_emails ?? []);
      setExternalEmailInput("");
      setNotes(initialValues?.notes ?? "");
      setTouched(false);
    }
  }, [open, initialValues]);

  // Validation
  const roundNameError = React.useMemo(() => {
    if (!roundName.trim()) return "Vui lòng nhập tên vòng phỏng vấn";
    if (roundName.length > 255) return "Tên vòng tối đa 255 ký tự";
    return null;
  }, [roundName]);

  const startError = React.useMemo(() => {
    if (!start) return "Vui lòng chọn thời gian bắt đầu";
    const selected = new Date(start);
    if (Number.isNaN(selected.getTime())) return "Thời gian bắt đầu không hợp lệ";
    if (selected.getTime() <= Date.now()) return "Thời gian phỏng vấn phải ở tương lai";
    return null;
  }, [start]);

  const endError = React.useMemo(() => {
    if (!end) return "Vui lòng chọn thời gian kết thúc";
    const endDate = new Date(end);
    if (Number.isNaN(endDate.getTime())) return "Thời gian kết thúc không hợp lệ";
    if (start) {
      const startDate = new Date(start);
      if (endDate <= startDate) return "Thời gian kết thúc phải sau thời gian bắt đầu";
    }
    return null;
  }, [end, start]);

  const interviewerError = React.useMemo(() => {
    if (selectedInterviewers.length > MAX_INTERVIEWERS) {
      return `Tối đa ${MAX_INTERVIEWERS} người phỏng vấn`;
    }
    return null;
  }, [selectedInterviewers]);

  const externalEmailError = React.useMemo(() => {
    if (externalEmails.length > MAX_EXTERNAL_EMAILS) {
      return `Tối đa ${MAX_EXTERNAL_EMAILS} email người ngoài`;
    }
    // Validate any invalid email
    const invalid = externalEmails.find((e) => !e.includes("@"));
    if (invalid) return `Email không hợp lệ: ${invalid}`;
    return null;
  }, [externalEmails]);

  const meetingLinkError = React.useMemo(() => {
    if (interviewMode === "custom_link" && !meetingLink.trim()) {
      return "Vui lòng nhập link cuộc họp khi chọn chế độ Link tùy chỉnh";
    }
    return null;
  }, [interviewMode, meetingLink]);

  const notesError = React.useMemo(() => {
    if (notes.length > NOTES_MAX) return `Ghi chú tối đa ${NOTES_MAX} ký tự`;
    return null;
  }, [notes]);

  const isValid =
    roundName.trim() !== "" &&
    !roundNameError &&
    start !== "" &&
    !startError &&
    end !== "" &&
    !endError &&
    !interviewerError &&
    !externalEmailError &&
    !meetingLinkError &&
    !notesError;

  function toIsoWithTimezone(localValue: string): string {
    return new Date(localValue).toISOString();
  }

  function handleConfirm() {
    setTouched(true);
    if (!isValid || loading) return;
    onConfirm({
      round_name: roundName.trim(),
      start: toIsoWithTimezone(start),
      end: toIsoWithTimezone(end),
      timezone,
      mode: interviewMode,
      meeting_link: interviewMode === "custom_link" ? meetingLink.trim() : null,
      interviewer_ids: selectedInterviewers,
      external_participant_emails: externalEmails.length > 0 ? externalEmails : undefined,
      notes: notes.trim() || null,
    });
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && !loading) {
      // Let parent handle full reset via useEffect on open
    }
    onOpenChange(nextOpen);
  }

  function toggleInterviewer(id: string) {
    setSelectedInterviewers((prev) => {
      if (prev.includes(id)) return prev.filter((i) => i !== id);
      if (prev.length >= MAX_INTERVIEWERS) return prev;
      return [...prev, id];
    });
  }

  function removeInterviewer(id: string) {
    setSelectedInterviewers((prev) => prev.filter((i) => i !== id));
  }

  function addExternalEmail() {
    const email = externalEmailInput.trim();
    if (!email || !email.includes("@")) return;
    if (externalEmails.includes(email)) return;
    if (externalEmails.length >= MAX_EXTERNAL_EMAILS) return;
    setExternalEmails((prev) => [...prev, email]);
    setExternalEmailInput("");
  }

  function removeExternalEmail(email: string) {
    setExternalEmails((prev) => prev.filter((e) => e !== email));
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Server error banner */}
          {serverError && (
            <div
              className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
            >
              {serverError}
            </div>
          )}

          {/* Round name */}
          <div className="space-y-2">
            <Label htmlFor="round-name">Tên vòng phỏng vấn</Label>
            <Input
              id="round-name"
              placeholder="VD: Vòng kỹ thuật 1"
              value={roundName}
              onChange={(e) => setRoundName(e.target.value)}
              aria-invalid={touched && !!roundNameError}
            />
            {touched && roundNameError && (
              <p className="text-xs text-destructive" role="alert">
                {roundNameError}
              </p>
            )}
          </div>

          {/* Start datetime */}
          <div className="space-y-2">
            <Label htmlFor="interview-start">Thời gian bắt đầu</Label>
            <Input
              id="interview-start"
              type="datetime-local"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              aria-invalid={touched && (!start || !!startError)}
            />
            {touched && !start && (
              <p className="text-xs text-destructive" role="alert">
                Vui lòng chọn thời gian bắt đầu
              </p>
            )}
            {touched && startError && (
              <p className="text-xs text-destructive" role="alert">
                {startError}
              </p>
            )}
          </div>

          {/* End datetime */}
          <div className="space-y-2">
            <Label htmlFor="interview-end">Thời gian kết thúc</Label>
            <Input
              id="interview-end"
              type="datetime-local"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              aria-invalid={touched && (!end || !!endError)}
            />
            {touched && !end && (
              <p className="text-xs text-destructive" role="alert">
                Vui lòng chọn thời gian kết thúc
              </p>
            )}
            {touched && endError && (
              <p className="text-xs text-destructive" role="alert">
                {endError}
              </p>
            )}
          </div>

          {/* Timezone */}
          <div className="space-y-2">
            <Label htmlFor="interview-timezone">Múi giờ</Label>
            <Select value={timezone} onValueChange={setTimezone}>
              <SelectTrigger id="interview-timezone">
                <SelectValue placeholder="Chọn múi giờ" />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz} value={tz}>
                    {tz}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Meeting mode */}
          <div className="space-y-2">
            <Label>Hình thức phỏng vấn</Label>
            <div className="flex flex-wrap gap-2">
              {MODE_OPTIONS.map((opt) => {
                const Icon = opt.icon;
                const selected = interviewMode === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setInterviewMode(opt.value)}
                    className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-2 text-sm transition-colors ${
                      selected
                        ? "border-primary bg-primary/10 text-primary font-medium"
                        : "border-input hover:bg-accent"
                    }`}
                    aria-pressed={selected}
                  >
                    <Icon className="h-4 w-4" />
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Meeting link (shown only for custom_link mode) */}
          {interviewMode === "custom_link" && (
            <div className="space-y-2">
              <Label htmlFor="meeting-link">Link cuộc họp</Label>
              <Input
                id="meeting-link"
                placeholder="https://meet.example.com/..."
                value={meetingLink}
                onChange={(e) => setMeetingLink(e.target.value)}
                aria-invalid={touched && !!meetingLinkError}
              />
              {touched && meetingLinkError && (
                <p className="text-xs text-destructive" role="alert">
                  {meetingLinkError}
                </p>
              )}
            </div>
          )}

          {/* Interviewer multi-select */}
          <div className="space-y-2">
            <Label>Người phỏng vấn (tối đa {MAX_INTERVIEWERS})</Label>

            {/* Selected interviewers */}
            {selectedInterviewers.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedInterviewers.map((id) => {
                  const interviewer = interviewers.find((i) => i.id === id);
                  return (
                    <span
                      key={id}
                      className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                    >
                      {interviewer?.name ?? id}
                      <button
                        type="button"
                        onClick={() => removeInterviewer(id)}
                        className="rounded-sm hover:bg-primary/20"
                        aria-label={`Xóa ${interviewer?.name ?? id}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  );
                })}
              </div>
            )}

            {/* Interviewer list */}
            <div className="max-h-40 overflow-y-auto rounded-md border p-2">
              {interviewers.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Không có người phỏng vấn khả dụng
                </p>
              ) : (
                <div className="space-y-1">
                  {interviewers.map((interviewer) => {
                    const isSelected = selectedInterviewers.includes(interviewer.id);
                    return (
                      <button
                        key={interviewer.id}
                        type="button"
                        onClick={() => toggleInterviewer(interviewer.id)}
                        className={`w-full rounded-sm px-2 py-1.5 text-left text-sm transition-colors hover:bg-accent ${
                          isSelected
                            ? "bg-primary/10 font-medium text-primary"
                            : ""
                        }`}
                        aria-pressed={isSelected}
                      >
                        {interviewer.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {touched && interviewerError && (
              <p className="text-xs text-destructive" role="alert">
                {interviewerError}
              </p>
            )}
          </div>

          {/* External participant emails */}
          <div className="space-y-2">
            <Label>Email người tham gia ngoài (tùy chọn, tối đa {MAX_EXTERNAL_EMAILS})</Label>

            {externalEmails.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {externalEmails.map((email) => (
                  <span
                    key={email}
                    className="inline-flex items-center gap-1 rounded-md bg-secondary/50 px-2 py-1 text-xs font-medium"
                  >
                    {email}
                    <button
                      type="button"
                      onClick={() => removeExternalEmail(email)}
                      className="rounded-sm hover:bg-secondary"
                      aria-label={`Xóa ${email}`}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <Input
                placeholder="email@example.com"
                value={externalEmailInput}
                onChange={(e) => setExternalEmailInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addExternalEmail();
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={addExternalEmail}
                disabled={!externalEmailInput.trim() || !externalEmailInput.includes("@")}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {touched && externalEmailError && (
              <p className="text-xs text-destructive" role="alert">
                {externalEmailError}
              </p>
            )}
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="interview-notes">Ghi chú (tùy chọn)</Label>
            <Textarea
              id="interview-notes"
              placeholder="Ghi chú thêm cho buổi phỏng vấn..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              aria-invalid={touched && !!notesError}
            />
            {touched && notesError && (
              <p className="text-xs text-destructive" role="alert">
                {notesError}
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={loading}
          >
            Hủy
          </Button>
          <Button onClick={handleConfirm} disabled={loading || !isValid}>
            {loading && <Loader2 className="animate-spin" />}
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
