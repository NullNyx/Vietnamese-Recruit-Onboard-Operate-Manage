"use client";

import * as React from "react";
import { Loader2, X } from "lucide-react";

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

export interface Interviewer {
  id: string;
  name: string;
}

/** Payload emitted on confirm — matches the ADR-0008 schedule contract. */
export interface ScheduleInterviewFormData {
  /** ISO 8601 datetime string for the interview start. */
  start: string;
  durationMinutes: number;
  interviewerIds: string[];
  notes?: string;
}

const DURATION_MIN = 15;
const DURATION_MAX = 180;
const DEFAULT_DURATION = 60;
const NOTES_MAX = 1000;
const MAX_INTERVIEWERS = 10;

export interface ScheduleInterviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (data: ScheduleInterviewFormData) => void;
  loading?: boolean;
  interviewers?: Interviewer[];
  /** "schedule" (default) creates a new interview; "reschedule" updates it. */
  mode?: "schedule" | "reschedule";
}

/** Convert a `datetime-local` value (local time) to an ISO 8601 string. */
function toIsoStart(localValue: string): string {
  return new Date(localValue).toISOString();
}

export function ScheduleInterviewDialog({
  open,
  onOpenChange,
  onConfirm,
  loading = false,
  interviewers = [],
  mode = "schedule",
}: ScheduleInterviewDialogProps) {
  const [start, setStart] = React.useState("");
  const [duration, setDuration] = React.useState(String(DEFAULT_DURATION));
  const [selectedInterviewers, setSelectedInterviewers] = React.useState<
    string[]
  >([]);
  const [notes, setNotes] = React.useState("");
  const [touched, setTouched] = React.useState(false);

  const isReschedule = mode === "reschedule";
  const title = isReschedule ? "Đổi lịch phỏng vấn" : "Lên lịch phỏng vấn";
  const description = isReschedule
    ? "Chọn thời gian mới cho buổi phỏng vấn của ứng viên."
    : "Chọn thời gian và người phỏng vấn cho ứng viên.";
  const confirmLabel = isReschedule
    ? "Đổi lịch phỏng vấn"
    : "Lên lịch phỏng vấn";

  const startError = React.useMemo(() => {
    if (!start) return null;
    const selected = new Date(start);
    if (Number.isNaN(selected.getTime())) {
      return "Thời gian phỏng vấn không hợp lệ";
    }
    if (selected.getTime() <= Date.now()) {
      return "Thời gian phỏng vấn phải ở tương lai";
    }
    return null;
  }, [start]);

  const durationError = React.useMemo(() => {
    const value = Number(duration);
    if (!duration || Number.isNaN(value)) {
      return "Vui lòng nhập thời lượng phỏng vấn";
    }
    if (!Number.isInteger(value)) {
      return "Thời lượng phải là số nguyên (phút)";
    }
    if (value < DURATION_MIN || value > DURATION_MAX) {
      return `Thời lượng phải từ ${DURATION_MIN} đến ${DURATION_MAX} phút`;
    }
    return null;
  }, [duration]);

  const interviewerError = React.useMemo(() => {
    if (selectedInterviewers.length < 1) {
      return "Vui lòng chọn ít nhất 1 người phỏng vấn";
    }
    if (selectedInterviewers.length > MAX_INTERVIEWERS) {
      return `Tối đa ${MAX_INTERVIEWERS} người phỏng vấn`;
    }
    return null;
  }, [selectedInterviewers]);

  const notesError = React.useMemo(() => {
    if (notes.length > NOTES_MAX) {
      return `Ghi chú tối đa ${NOTES_MAX} ký tự`;
    }
    return null;
  }, [notes]);

  const isValid =
    start !== "" &&
    !startError &&
    !durationError &&
    !interviewerError &&
    !notesError &&
    selectedInterviewers.length >= 1;

  function handleConfirm() {
    setTouched(true);
    if (isValid) {
      onConfirm({
        start: toIsoStart(start),
        durationMinutes: Number(duration),
        interviewerIds: selectedInterviewers,
        notes: notes || undefined,
      });
    }
  }

  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && !loading) {
      setStart("");
      setDuration(String(DEFAULT_DURATION));
      setSelectedInterviewers([]);
      setNotes("");
      setTouched(false);
    }
    onOpenChange(nextOpen);
  }

  function toggleInterviewer(id: string) {
    setSelectedInterviewers((prev) => {
      if (prev.includes(id)) {
        return prev.filter((i) => i !== id);
      }
      if (prev.length >= MAX_INTERVIEWERS) return prev;
      return [...prev, id];
    });
  }

  function removeInterviewer(id: string) {
    setSelectedInterviewers((prev) => prev.filter((i) => i !== id));
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Start datetime input */}
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
                Vui lòng chọn thời gian phỏng vấn
              </p>
            )}
            {touched && startError && (
              <p className="text-xs text-destructive" role="alert">
                {startError}
              </p>
            )}
          </div>

          {/* Duration input */}
          <div className="space-y-2">
            <Label htmlFor="interview-duration">Thời lượng (phút)</Label>
            <Input
              id="interview-duration"
              type="number"
              min={DURATION_MIN}
              max={DURATION_MAX}
              step={5}
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              aria-invalid={touched && !!durationError}
            />
            {touched && durationError && (
              <p className="text-xs text-destructive" role="alert">
                {durationError}
              </p>
            )}
          </div>

          {/* Interviewer multi-select */}
          <div className="space-y-2">
            <Label>Người phỏng vấn (1–10)</Label>

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
                    const isSelected = selectedInterviewers.includes(
                      interviewer.id,
                    );
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

          {/* Notes (optional) */}
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
