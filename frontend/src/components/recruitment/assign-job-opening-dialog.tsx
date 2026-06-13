"use client";

import * as React from "react";
import { Loader2, Search, Building2 } from "lucide-react";

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
import { listOpenJobOpenings, type JobOpeningListItem } from "@/lib/api/recruitment";

export interface AssignJobOpeningDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (jobOpeningId: string) => void;
  /** Title of the currently assigned Job Opening, if any. */
  currentAssignment?: string;
  loading?: boolean;
}

export function AssignJobOpeningDialog({
  open,
  onOpenChange,
  onConfirm,
  currentAssignment,
  loading = false,
}: AssignJobOpeningDialogProps) {
  const [jobOpenings, setJobOpenings] = React.useState<JobOpeningListItem[]>([]);
  const [search, setSearch] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [fetching, setFetching] = React.useState(false);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  // Fetch open Job Openings when dialog opens or search changes
  React.useEffect(() => {
    if (!open) return;
    setFetching(true);
    setFetchError(null);

    listOpenJobOpenings({ page_size: 100, search: search || undefined })
      .then((res) => setJobOpenings(res.job_openings))
      .catch((err) => {
        setFetchError(err instanceof Error ? err.message : "Không thể tải danh sách vị trí");
      })
      .finally(() => setFetching(false));
  }, [open, search]);



  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen && !loading) {
      setSelectedId(null);
      setSearch("");
    }
    onOpenChange(nextOpen);
  }

  function handleConfirm() {
    if (selectedId && !loading) {
      onConfirm(selectedId);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {currentAssignment ? "Chuyển vị trí tuyển dụng" : "Gán vị trí tuyển dụng"}
          </DialogTitle>
          <DialogDescription>
            {currentAssignment
              ? `Ứng viên hiện thuộc: ${currentAssignment}. Chọn vị trí mới.`
              : "Chọn vị trí tuyển dụng cho ứng viên."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Tìm vị trí tuyển dụng..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Job Opening list */}
          <div className="max-h-60 overflow-y-auto rounded-md border">
            {fetching ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : fetchError ? (
              <p className="py-4 text-center text-sm text-destructive">{fetchError}</p>
            ) : jobOpenings.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                {"Không có vị trí tuyển dụng đang mở"}
              </p>
            ) : (
              <div className="divide-y">
                {jobOpenings.map((jo) => {
                  const isSelected = selectedId === jo.id;
                  return (
                    <button
                      key={jo.id}
                      type="button"
                      onClick={() => setSelectedId(jo.id)}
                      className={`flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-accent ${
                        isSelected ? "bg-primary/10 font-medium" : ""
                      }`}
                      aria-pressed={isSelected}
                    >
                      <Building2
                        className={`h-4 w-4 shrink-0 ${
                          isSelected ? "text-primary" : "text-muted-foreground"
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="truncate">{jo.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {jo.position_name} &middot; {jo.total_candidates} ứng viên
                        </div>
                      </div>
                      {isSelected && (
                        <span className="text-xs font-medium text-primary">Đã chọn</span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={loading}>
            Hủy
          </Button>
          <Button onClick={handleConfirm} disabled={loading || !selectedId}>
            {loading && <Loader2 className="animate-spin" />}
            {currentAssignment ? "Chuyển đổi" : "Gán"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
