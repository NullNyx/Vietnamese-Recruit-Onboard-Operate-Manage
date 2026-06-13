"use client";

import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export interface UnassignDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  jobOpeningTitle?: string;
  loading?: boolean;
}

export function UnassignDialog({
  open,
  onOpenChange,
  onConfirm,
  jobOpeningTitle,
  loading = false,
}: UnassignDialogProps) {
  function handleOpenChange(nextOpen: boolean) {
    if (!loading) {
      onOpenChange(nextOpen);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Bỏ gán vị trí tuyển dụng</DialogTitle>
          <DialogDescription>
            {jobOpeningTitle
              ? `Bạn có chắc chắn muốn bỏ gán ứng viên khỏi "${jobOpeningTitle}"?`
              : "Bạn có chắc chắn muốn bỏ gán vị trí tuyển dụng khỏi ứng viên này?"}
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Hủy
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={loading}>
            {loading && <Loader2 className="animate-spin" />}
            Bỏ gán
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
