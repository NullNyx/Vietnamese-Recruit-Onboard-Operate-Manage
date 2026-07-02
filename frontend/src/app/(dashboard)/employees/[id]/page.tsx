"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  CheckCircle2,
  XCircle,
  CalendarX,
  ArrowLeft,
  Trash2,
  Download,
  FileText,
  Upload,
  Plus,
} from "lucide-react";
import type {
  Employee,
  EmployeeDocument,
  Contract,
  EmploymentEvent,
  Department,
  Position,
} from "@/lib/api/types";
import {
  getEmployee,
  listDocuments,
  uploadDocument,
  downloadDocument,
  deleteDocument,
  listEmployeeContracts,
  listEmployeeEvents,
  changeEmployeeStatus,
  verifyDocument,
  rejectDocument,
  markDocumentExpired,
} from "@/lib/api/employees";
import { listDepartments } from "@/lib/api/departments";
import { listPositions } from "@/lib/api/positions";

export default function EmployeeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [documents, setDocuments] = useState<EmployeeDocument[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [events, setEvents] = useState<EmploymentEvent[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("profile");

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadType, setUploadType] = useState("contract");
  const [uploadDescription, setUploadDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [statusDraft, setStatusDraft] = useState("");
  const [statusSaving, setStatusSaving] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [emp, docs, depts, pos] = await Promise.all([
          getEmployee(id),
          listDocuments(id),
          listDepartments(),
          listPositions(),
        ]);
        setEmployee(emp);
        setDocuments(docs);
        setDepartments(depts);
        setPositions(pos);
        setStatusDraft(emp.employment_status);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load employee",
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  useEffect(() => {
    if (activeTab === "contracts") {
      listEmployeeContracts(id).then(setContracts).catch(() => {});
    }
    if (activeTab === "events") {
      listEmployeeEvents(id).then(setEvents).catch(() => {});
    }
  }, [activeTab, id]);

  const getDepartmentName = (deptId: string | null) => {
    if (!deptId) return "—";
    return departments.find((d) => d.id === deptId)?.name || "—";
  };

  const getPositionName = (posId: string | null) => {
    if (!posId) return "—";
    return positions.find((p) => p.id === posId)?.name || "—";
  };

  const formatContractType = (type: string | null) => {
    if (!type) return "—";
    return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadError(null);
    try {
      const doc = await uploadDocument(
        id,
        uploadFile,
        uploadType,
        uploadDescription || undefined,
      );
      setDocuments((prev) => [...prev, doc]);
      setUploadFile(null);
      setUploadDescription("");
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleChangeStatus = async () => {
    if (!employee || !statusDraft || statusDraft === employee.employment_status) return;
    setStatusSaving(true);
    setStatusError(null);
    try {
      const updated = await changeEmployeeStatus(id, {
        status: statusDraft,
        termination_date:
          statusDraft === "terminated" ? new Date().toISOString().slice(0, 10) : undefined,
      });
      setEmployee(updated);
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : "Status update failed");
    } finally {
      setStatusSaving(false);
    }
  };

  const handleDownload = async (doc: EmployeeDocument) => {
    try {
      const blob = await downloadDocument(doc.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.file_name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      alert("Failed to download document");
    }
  };


  const handleVerifyDocument = async (docId: string) => {
    try {
      const doc = await verifyDocument(docId);
      setDocuments((prev) => prev.map((d) => (d.id === docId ? doc : d)));
    } catch {
      alert("Failed to verify document");
    }
  };

  const handleRejectDocument = async (docId: string) => {
    try {
      const doc = await rejectDocument(docId);
      setDocuments((prev) => prev.map((d) => (d.id === docId ? doc : d)));
    } catch {
      alert("Failed to reject document");
    }
  };

  const handleExpireDocument = async (docId: string) => {
    try {
      const doc = await markDocumentExpired(docId);
      setDocuments((prev) => prev.map((d) => (d.id === docId ? doc : d)));
    } catch {
      alert("Failed to expire document");
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!window.confirm("Are you sure you want to delete this document?"))
      return;
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch {
      alert("Failed to delete document");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Loading employee...</p>
      </div>
    );
  }

  if (error || !employee) {
    return (
      <div className="p-6">
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {error || "Employee not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/employees")}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {employee.full_name}
            </h1>
            <p className="text-sm text-muted-foreground">
              {employee.employee_code}
            </p>
          </div>
        </div>
        <Link href={`/employees/${id}/edit`}>
          <Button>Edit Employee</Button>
        </Link>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="documents">
            Documents
            {documents.length > 0 && (
              <span className="ml-1.5 rounded-full bg-muted px-1.5 text-xs">
                {documents.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="contracts">Contracts</TabsTrigger>
          <TabsTrigger value="events">Events &amp; Audit</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="mt-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Personal Info Card */}
            <div className="rounded-md border border-border bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold text-foreground">
                Personal Information
              </h2>
              <dl className="space-y-3">
                <DetailRow label="Full Name" value={employee.full_name} />
                <DetailRow label="Email" value={employee.email} />
                <DetailRow label="Phone" value={employee.phone || "—"} />
                <DetailRow
                  label="Date of Birth"
                  value={employee.date_of_birth || "—"}
                />
                <DetailRow
                  label="Gender"
                  value={
                    employee.gender
                      ? employee.gender.charAt(0).toUpperCase() +
                        employee.gender.slice(1)
                      : "—"
                  }
                />
                <DetailRow label="ID Number" value={employee.id_number || "—"} />
                <DetailRow label="Address" value={employee.address || "—"} />
              </dl>
            </div>

            {/* Employment Info Card */}
            <div className="rounded-md border border-border bg-card p-6">
              <h2 className="mb-4 text-lg font-semibold text-foreground">
                Employment Information
              </h2>
              <dl className="space-y-3">
                <DetailRow
                  label="Department"
                  value={getDepartmentName(employee.department_id)}
                />
                <DetailRow
                  label="Position"
                  value={getPositionName(employee.position_id)}
                />
                <DetailRow label="Start Date" value={employee.start_date || "—"} />
                <DetailRow
                  label="Contract Type"
                  value={formatContractType(employee.contract_type)}
                />
                <DetailRow label="Tax Code" value={employee.tax_code || "—"} />
                <DetailRow
                  label="Status"
                  value={<EmploymentStatusBadge status={employee.employment_status} />}
                />
                {employee.termination_date && (
                  <DetailRow
                    label="Termination Date"
                    value={employee.termination_date}
                  />
                )}
                <div className="pt-2">
                  <Label className="mb-1 block text-xs font-medium text-muted-foreground">
                    Change Status
                  </Label>
                  <div className="flex gap-2">
                    <Select value={statusDraft} onValueChange={setStatusDraft}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="resigned">Resigned</SelectItem>
                        <SelectItem value="terminated">Terminated</SelectItem>
                        <SelectItem value="suspended">Suspended</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleChangeStatus}
                      disabled={statusSaving || statusDraft === employee.employment_status}
                    >
                      {statusSaving ? "Saving..." : "Update"}
                    </Button>
                  </div>
                  {statusError && (
                    <p className="mt-2 text-xs text-destructive">{statusError}</p>
                  )}
                </div>
              </dl>
            </div>
          </div>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="mt-6">
          <div className="rounded-md border border-border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Documents
            </h2>

            {documents.length === 0 ? (
              <p className="mb-4 text-sm text-muted-foreground">
                No documents uploaded yet.
              </p>
            ) : (
              <div className="mb-6 space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between rounded-md border border-border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{doc.file_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {doc.document_type} &bull;{" "}
                          {formatFileSize(doc.file_size)} &bull;{" "}
                          {new Date(doc.uploaded_at).toLocaleDateString()}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <DocumentStatusBadge status={doc.status} />
                          {doc.description && (
                            <span className="text-xs text-muted-foreground">{doc.description}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDownload(doc)}
                        title="Download"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      {(doc.status === "uploaded" || doc.status === "rejected") && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleVerifyDocument(doc.id)}
                          title="Verify"
                        >
                          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        </Button>
                      )}
                      {doc.status === "uploaded" && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRejectDocument(doc.id)}
                          title="Reject"
                        >
                          <XCircle className="h-4 w-4 text-red-500" />
                        </Button>
                      )}
                      {(doc.status === "uploaded" || doc.status === "verified") && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleExpireDocument(doc.id)}
                          title="Mark expired"
                        >
                          <CalendarX className="h-4 w-4 text-muted-foreground" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteDocument(doc.id)}
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Upload Form */}
            <form
              onSubmit={handleUpload}
              className="rounded-md border border-dashed border-border p-4"
            >
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
                <Upload className="h-4 w-4" />
                Upload Document
              </h3>
              {uploadError && (
                <div className="mb-3 rounded-md bg-destructive/10 p-2 text-xs text-destructive">
                  {uploadError}
                </div>
              )}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div>
                  <label
                    htmlFor="doc_file"
                    className="mb-1 block text-xs font-medium text-muted-foreground"
                  >
                    File
                  </label>
                  <input
                    id="doc_file"
                    type="file"
                    onChange={(e) =>
                      setUploadFile(e.target.files?.[0] || null)
                    }
                    className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:border-0 file:bg-transparent file:text-sm file:font-medium"
                  />
                </div>
                <div>
                  <label
                    htmlFor="doc_type"
                    className="mb-1 block text-xs font-medium text-muted-foreground"
                  >
                    Document Type
                  </label>
                  <select
                    id="doc_type"
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="contract">Contract</option>
                    <option value="id_card">ID Card</option>
                    <option value="cv">CV / Resume</option>
                    <option value="certificate">Certificate</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label
                    htmlFor="doc_desc"
                    className="mb-1 block text-xs font-medium text-muted-foreground"
                  >
                    Description (optional)
                  </label>
                  <input
                    id="doc_desc"
                    type="text"
                    value={uploadDescription}
                    onChange={(e) => setUploadDescription(e.target.value)}
                    placeholder="Brief description"
                    className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              </div>
              <div className="mt-3">
                <Button
                  type="submit"
                  size="sm"
                  disabled={!uploadFile || uploading}
                >
                  <Upload className="mr-2 h-3 w-3" />
                  {uploading ? "Uploading..." : "Upload"}
                </Button>
              </div>
            </form>
          </div>
        </TabsContent>

        {/* Contracts Tab */}
        <TabsContent value="contracts" className="mt-6">
          <div className="rounded-md border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-foreground">
                Contracts
              </h2>
              <Link href={`/employees/${id}/contracts/new`}>
                <Button size="sm">
                  <Plus className="mr-1.5 h-4 w-4" />
                  Create Contract
                </Button>
              </Link>
            </div>

            {contracts.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No contracts yet.
              </p>
            ) : (
              <div className="space-y-2">
                {contracts.map((c) => (
                  <Link key={c.id} href={`/employees/${id}/contracts/${c.id}`}>
                    <div className="flex cursor-pointer items-center justify-between rounded-md border border-border p-3 transition-colors hover:bg-muted/50">
                      <div>
                        <p className="text-sm font-medium">
                          {c.contract_number || formatContractType(c.contract_type)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatContractType(c.contract_type)}
                          {c.started_on && (
                            <>
                              {" "}
                              &bull; {c.started_on}
                              {c.ended_on ? ` → ${c.ended_on}` : " → ∞"}
                            </>
                          )}
                        </p>
                      </div>
                      <ContractStatusBadge status={c.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events" className="mt-6">
          <div className="rounded-md border border-border bg-card p-6">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Employment Events
            </h2>

            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No events recorded yet.
              </p>
            ) : (
              <div className="space-y-2">
                {events.map((evt) => (
                  <div
                    key={evt.id}
                    className="flex items-start justify-between rounded-md border border-border p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        {evt.event_type.replace(/_/g, " ")}
                      </p>
                      {evt.note && (
                        <p className="text-xs text-muted-foreground">
                          {evt.note}
                        </p>
                      )}
                    </div>
                    <p className="shrink-0 text-xs text-muted-foreground">
                      {new Date(evt.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}



function DocumentStatusBadge({ status }: { status: string }) {
  const meta: Record<string, { label: string; className: string }> = {
    uploaded: { label: "Uploaded", className: "border-blue-200 bg-blue-50 text-blue-700" },
    verified: { label: "Verified", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
    rejected: { label: "Rejected", className: "border-red-200 bg-red-50 text-red-700" },
    expired: { label: "Expired", className: "border-slate-200 bg-slate-50 text-slate-700" },
  };
  const m = meta[status] ?? { label: status || "—", className: "border-muted bg-muted text-muted-foreground" };
  return <Badge variant="outline" className={m.className}>{m.label}</Badge>;
}

function EmploymentStatusBadge({ status }: { status: string }) {
  const meta: Record<string, { label: string; className: string }> = {
    active: {
      label: "Đang làm",
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    },
    resigned: {
      label: "Đã nghỉ",
      className: "border-amber-200 bg-amber-50 text-amber-700",
    },
    terminated: {
      label: "Chấm dứt",
      className: "border-rose-200 bg-rose-50 text-rose-700",
    },
    suspended: {
      label: "Tạm ngưng",
      className: "border-slate-200 bg-slate-50 text-slate-700",
    },
  };
  const m = meta[status] ?? {
    label: status || "—",
    className: "border-muted bg-muted text-muted-foreground",
  };
  return (
    <Badge variant="outline" className={m.className}>
      {m.label}
    </Badge>
  );
}

function ContractStatusBadge({ status }: { status: string }) {
  const meta: Record<string, { label: string; className: string }> = {
    draft: {
      label: "Draft",
      className: "border-muted bg-muted text-muted-foreground",
    },
    pending_signature: {
      label: "Pending Signature",
      className: "border-amber-200 bg-amber-50 text-amber-700",
    },
    active: {
      label: "Active",
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    },
    expired: {
      label: "Expired",
      className: "border-slate-200 bg-slate-50 text-slate-700",
    },
    terminated: {
      label: "Terminated",
      className: "border-rose-200 bg-rose-50 text-rose-700",
    },
    cancelled: {
      label: "Cancelled",
      className: "border-red-200 bg-red-50 text-red-700",
    },
  };
  const m = meta[status] ?? {
    label: status || "—",
    className: "border-muted bg-muted text-muted-foreground",
  };
  return (
    <Badge variant="outline" className={m.className}>
      {m.label}
    </Badge>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-right text-sm font-medium text-foreground">
        {value}
      </dd>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
