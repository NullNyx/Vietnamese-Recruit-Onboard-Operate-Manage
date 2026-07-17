"use client";

import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  assignJobApplication,
  listJobOpenings,
  promoteJobApplication,
} from "@/lib/api/recruitment";
import type {
  JobApplicationInboxResult,
  JobOpeningListItem,
} from "@/lib/api/recruitment";
import { ApiError } from "@/lib/api/types";

interface Props {
  applications: JobApplicationInboxResult[];
}

export function JobApplicationActions({ applications }: Props) {
  const [items, setItems] = React.useState(applications);
  const [openings, setOpenings] = React.useState<JobOpeningListItem[]>([]);
  const [busyId, setBusyId] = React.useState<string | null>(null);

  React.useEffect(() => {
    listJobOpenings({ status: ["open"], page_size: 100 })
      .then((result) => setOpenings(result.job_openings))
      .catch(() => toast.error("Không thể tải Job Opening đang mở"));
  }, []);

  const update = (id: string, patch: Partial<JobApplicationInboxResult>) => {
    setItems((current) =>
      current.map((application) =>
        application.id === id ? { ...application, ...patch } : application,
      ),
    );
  };

  const assign = async (application: JobApplicationInboxResult, openingId: string) => {
    setBusyId(application.id);
    try {
      const result = await assignJobApplication(application.id, openingId || null);
      update(application.id, { job_opening_id: result.job_opening_id });
      toast.success("Đã cập nhật Job Opening");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Không thể gán Job Opening");
    } finally {
      setBusyId(null);
    }
  };

  const promote = async (application: JobApplicationInboxResult) => {
    if (!application.applicant_name?.trim() || !application.applicant_email?.trim()) return;
    setBusyId(application.id);
    try {
      const result = await promoteJobApplication(application.id, {
        applicant_name: application.applicant_name.trim(),
        applicant_email: application.applicant_email.trim(),
        job_opening_id: application.job_opening_id,
      });
      update(application.id, {
        status: result.status,
        job_opening_id: result.job_opening_id,
      });
      toast.success("Đã promote thành Candidate");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Không thể promote Candidate");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="space-y-3 rounded-lg border p-4" aria-label="Job Application vừa tạo">
      <h4 className="font-medium text-sm">Job Application vừa tạo</h4>
      {items.map((application, index) => {
        const promoted = application.status === "promoted";
        return (
          <div key={application.id} className="space-y-3 rounded-md border p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Application {index + 1}</span>
              {promoted && <Badge variant="outline">Đã promote</Badge>}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor={`applicant-name-${application.id}`}>Tên ứng viên</Label>
                <Input
                  id={`applicant-name-${application.id}`}
                  value={application.applicant_name ?? ""}
                  disabled={promoted}
                  onChange={(event) =>
                    update(application.id, { applicant_name: event.target.value })
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor={`applicant-email-${application.id}`}>Email ứng viên</Label>
                <Input
                  id={`applicant-email-${application.id}`}
                  type="email"
                  value={application.applicant_email ?? ""}
                  disabled={promoted}
                  onChange={(event) =>
                    update(application.id, { applicant_email: event.target.value })
                  }
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label htmlFor={`job-opening-${application.id}`}>Job Opening</Label>
              <select
                id={`job-opening-${application.id}`}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={application.job_opening_id ?? ""}
                disabled={promoted || busyId === application.id}
                onChange={(event) => assign(application, event.target.value)}
              >
                <option value="">Chưa xác định</option>
                {openings.map((opening) => (
                  <option key={opening.id} value={opening.id}>
                    {opening.title}
                  </option>
                ))}
              </select>
            </div>
            {!promoted && (
              <Button
                type="button"
                onClick={() => promote(application)}
                disabled={
                  busyId === application.id ||
                  !application.applicant_name?.trim() ||
                  !application.applicant_email?.trim()
                }
              >
                Promote thành Candidate
              </Button>
            )}
          </div>
        );
      })}
    </section>
  );
}
