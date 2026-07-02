"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Save, Send, FileSignature, RefreshCw, XCircle, Ban, Download, Plus } from "lucide-react";
import type { Contract, Employee, ContractAmendment } from "@/lib/api/types";
import {
  getContract,
  getEmployee,
  updateContract,
  sendContractForSigning,
  signContract,
  renewContract,
  terminateContract,
  cancelContract,
  listContractAmendments,
  createContractAmendment,
} from "@/lib/api/employees";

const CONTRACT_TYPE_LABELS: Record<string, string> = {
  labor: "Labor Contract",
  offer: "Offer Letter",
  nda: "NDA",
  other: "Other",
};

const STATUS_META: Record<string, { label: string; className: string }> = {
  draft: { label: "Draft", className: "border-muted bg-muted text-muted-foreground" },
  pending_signature: { label: "Pending Signature", className: "border-amber-200 bg-amber-50 text-amber-700" },
  active: { label: "Active", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
  expired: { label: "Expired", className: "border-slate-200 bg-slate-50 text-slate-700" },
  terminated: { label: "Terminated", className: "border-rose-200 bg-rose-50 text-rose-700" },
  cancelled: { label: "Cancelled", className: "border-red-200 bg-red-50 text-red-700" },
};

function StatusBadge({ status }: { status: string }) {
  const m = STATUS_META[status] ?? { label: status, className: "border-muted bg-muted text-muted-foreground" };
  return <Badge variant="outline" className={m.className}>{m.label}</Badge>;
}

export default function ContractDetailPage() {
  const params = useParams();
  const contractId = params.id as string;

  const [contract, setContract] = useState<Contract | null>(null);
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Inline edit state
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [editNumber, setEditNumber] = useState("");
  const [editStarted, setEditStarted] = useState("");
  const [editEnded, setEditEnded] = useState("");
  const [saving, setSaving] = useState(false);

  // Sign dialog state
  const [showSign, setShowSign] = useState(false);
  const [signDate, setSignDate] = useState("");

  // Renew dialog state
  const [showRenew, setShowRenew] = useState(false);
  const [renewStarted, setRenewStarted] = useState("");
  const [renewEnded, setRenewEnded] = useState("");
  const [renewContent, setRenewContent] = useState("");
  const [amendContent, setAmendContent] = useState("");
  const [amendments, setAmendments] = useState<ContractAmendment[]>([]);
  const [showAmendForm, setShowAmendForm] = useState(false);
  const [amendName, setAmendName] = useState("");
  const [amendSaving, setAmendSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const c = await getContract(contractId);
        setContract(c);
        setEditContent(c.content ?? "");
        setEditNumber(c.contract_number ?? "");
        setEditStarted(c.started_on ?? "");
        setEditEnded(c.ended_on ?? "");
        try {
          const emp = await getEmployee(c.employee_id);
          setEmployee(emp);
        } catch {
          // employee fetch optional
        }
        listContractAmendments(c.id).then(setAmendments).catch(() => {});
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load contract");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [contractId]);

  const handleCreateAmendment = async () => {
    if (!amendName || !amendContent) return;
    setAmendSaving(true);
    try {
      const a = await createContractAmendment(contractId, { name: amendName, content: amendContent });
      setAmendments((prev) => [...prev, a]);
      setAmendName("");
      setAmendContent("");
      setShowAmendForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create amendment failed");
    } finally {
      setAmendSaving(false);
    }
  };

  const handleExport = () => {
    if (!contract?.content) return;
    const blob = new Blob([contract.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${contract.contract_number || "contract"}_${contract.contract_type}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSaveDraft = async () => {
    if (!contract) return;
    setSaving(true);
    try {
      const updated = await updateContract(contractId, {
        contract_number: editNumber || undefined,
        content: editContent || undefined,
        started_on: editStarted || undefined,
        ended_on: editEnded || undefined,
      });
      setContract(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleAction = async (action: string, fn: () => Promise<Contract>) => {
    setActionLoading(action);
    try {
      const updated = await fn();
      setContract(updated);
      setShowSign(false);
      setShowRenew(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : `${action} failed`);
    } finally {
      setActionLoading(null);
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Loading contract...</p>
      </div>
    );
  }

  if (error || !contract) {
    return (
      <div className="p-6">
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">{error || "Contract not found"}</div>
      </div>
    );
  }

  const backLink = employee ? `/employees/${employee.id}` : "/employees";
  const isDraft = contract.status === "draft";
  const isPending = contract.status === "pending_signature";
  const isActive = contract.status === "active";
  const isTerminal = ["expired", "terminated", "cancelled"].includes(contract.status);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href={backLink}><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">
                {contract.contract_number || CONTRACT_TYPE_LABELS[contract.contract_type] || contract.contract_type}
              </h1>
              <StatusBadge status={contract.status} />
            </div>
            <p className="text-sm text-muted-foreground">
              {employee?.full_name ?? "Employee"} &middot;{" "}
              {CONTRACT_TYPE_LABELS[contract.contract_type] ?? contract.contract_type}
              {contract.signed_on && <> &middot; Signed {contract.signed_on}</>}
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={handleExport}>
          <Download className="mr-1.5 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      {/* Main content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Details card */}
        <div className="lg:col-span-2 rounded-md border bg-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Contract Details</h2>

          {isDraft && editing ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="contract_number">Contract Number</Label>
                  <Input id="contract_number" value={editNumber} onChange={(e) => setEditNumber(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="contract_type">Type</Label>
                  <Input id="contract_type" value={CONTRACT_TYPE_LABELS[contract.contract_type] ?? contract.contract_type} disabled />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="started_on">Start Date</Label>
                  <Input id="started_on" type="date" value={editStarted} onChange={(e) => setEditStarted(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ended_on">End Date</Label>
                  <Input id="ended_on" type="date" value={editEnded} onChange={(e) => setEditEnded(e.target.value)} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="content">Content</Label>
                <Textarea id="content" rows={8} value={editContent} onChange={(e) => setEditContent(e.target.value)} />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSaveDraft} disabled={saving}>
                  <Save className="mr-1.5 h-4 w-4" />
                  {saving ? "Saving..." : "Save"}
                </Button>
                <Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <DetailItem label="Contract Number" value={contract.contract_number ?? "—"} />
                <DetailItem label="Type" value={CONTRACT_TYPE_LABELS[contract.contract_type] ?? contract.contract_type} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <DetailItem label="Start Date" value={contract.started_on ?? "—"} />
                <DetailItem label="End Date" value={contract.ended_on ?? "—"} />
              </div>
              <DetailItem label="Signed On" value={contract.signed_on ?? "—"} />
              <div>
                <p className="text-sm text-muted-foreground mb-1">Content</p>
                <div className="rounded-md bg-muted/50 p-3 text-sm whitespace-pre-wrap">
                  {contract.content || "No content"}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Actions card */}
        <div className="rounded-md border bg-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Actions</h2>

          {isDraft && (
            <div className="space-y-2">
              {editing ? null : (
                <>
                  <Button className="w-full" variant="outline" onClick={handleExport} disabled={!contract?.content}>
                    <Download className="mr-1.5 h-4 w-4" /> Export
                  </Button>
                  <Button className="w-full" variant="outline" onClick={() => setEditing(true)}>
                    <Save className="mr-1.5 h-4 w-4" /> Edit Draft
                  </Button>
                </>
              )}
              <Button className="w-full" onClick={() => handleAction("send", () => sendContractForSigning(contractId))} disabled={actionLoading === "send"}>
                <Send className="mr-1.5 h-4 w-4" />
                {actionLoading === "send" ? "Sending..." : "Send for Signing"}
              </Button>
            </div>
          )}

          {isPending && (
            <div className="space-y-2">
              {showSign ? (
                <div className="space-y-3 border rounded-md p-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="sign_date">Signed Date</Label>
                    <Input id="sign_date" type="date" value={signDate} onChange={(e) => setSignDate(e.target.value)} />
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleAction("sign", () => signContract(contractId, { signed_on: signDate || undefined }))} disabled={actionLoading === "sign"}>
                      {actionLoading === "sign" ? "Signing..." : "Confirm Sign"}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setShowSign(false)}>Cancel</Button>
                  </div>
                </div>
              ) : (
                <>
                  <Button className="w-full" onClick={() => setShowSign(true)}>
                    <FileSignature className="mr-1.5 h-4 w-4" /> Sign Contract
                  </Button>
                  <Button className="w-full" variant="outline" onClick={() => handleAction("cancel", () => cancelContract(contractId))} disabled={actionLoading === "cancel"}>
                    <Ban className="mr-1.5 h-4 w-4" /> Cancel
                  </Button>
                </>
              )}
            </div>
          )}

          {isActive && (
            <div className="space-y-2">
              {showRenew ? (
                <div className="space-y-3 border rounded-md p-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="renew_start">New Start Date</Label>
                    <Input id="renew_start" type="date" value={renewStarted} onChange={(e) => setRenewStarted(e.target.value)} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="renew_end">New End Date</Label>
                    <Input id="renew_end" type="date" value={renewEnded} onChange={(e) => setRenewEnded(e.target.value)} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="renew_content">Content (optional)</Label>
                    <Textarea id="renew_content" rows={4} value={renewContent} onChange={(e) => setRenewContent(e.target.value)} />
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleAction("renew", () => renewContract(contractId, { new_started_on: renewStarted || undefined, new_ended_on: renewEnded || undefined, new_content: renewContent || undefined }))} disabled={actionLoading === "renew"}>
                      {actionLoading === "renew" ? "Renewing..." : "Confirm Renew"}
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setShowRenew(false)}>Cancel</Button>
                  </div>
                </div>
              ) : (
                <>
                  <Button className="w-full" onClick={() => setShowRenew(true)}>
                    <RefreshCw className="mr-1.5 h-4 w-4" /> Renew Contract
                  </Button>
                  <Button className="w-full" variant="outline" onClick={() => handleAction("terminate", () => terminateContract(contractId))} disabled={actionLoading === "terminate"}>
                    <XCircle className="mr-1.5 h-4 w-4" /> Terminate
                  </Button>
                </>
              )}
            </div>
          )}

          {isTerminal && (
            <p className="text-sm text-muted-foreground">No actions available for {contract.status} contracts.</p>
          )}
        </div>
      </div>

      <div className="rounded-md border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Amendments</h2>
          <Badge variant="outline">{amendments.length}</Badge>
        </div>

        {amendments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No amendments yet.</p>
        ) : (
          <div className="space-y-2">
            {amendments.map((amendment) => (
              <div key={amendment.id} className="rounded-md border border-border p-3">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium">{amendment.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {amendment.status} &bull; {new Date(amendment.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge variant="outline">{amendment.status}</Badge>
                </div>
                {amendment.content && (
                  <p className="mt-2 text-sm whitespace-pre-wrap text-muted-foreground">
                    {amendment.content}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5 md:col-span-1">
            <Label htmlFor="amendment_name">Name</Label>
            <Input id="amendment_name" value={amendmentName} onChange={(e) => setAmendmentName(e.target.value)} />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="amendment_file">File path</Label>
            <Input id="amendment_file" value={amendmentFilePath} onChange={(e) => setAmendmentFilePath(e.target.value)} />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="amendment_content">Content</Label>
          <Textarea id="amendment_content" rows={4} value={amendmentContent} onChange={(e) => setAmendmentContent(e.target.value)} />
        </div>
        <Button onClick={handleCreateAmendment} disabled={amendmentSaving || !amendmentName || !amendmentContent}>
          <Plus className="mr-1.5 h-4 w-4" />
          {amendmentSaving ? "Creating..." : "Create Amendment"}
        </Button>
      </div>
          {/* Amendments section */}
      <div className="rounded-md border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Amendments</h2>
          <Button size="sm" variant="outline" onClick={() => setShowAmendForm(!showAmendForm)}>
            {showAmendForm ? "Cancel" : "Add Amendment"}
          </Button>
        </div>

        {showAmendForm && (
          <div className="space-y-3 border rounded-md p-4">
            <div className="space-y-1.5">
              <Label htmlFor="amend_name">Name</Label>
              <Input id="amend_name" value={amendName} onChange={(e) => setAmendName(e.target.value)} placeholder="e.g. Salary adjustment" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="amend_content">Content</Label>
              <Textarea id="amend_content" rows={6} value={amendContent} onChange={(e) => setAmendContent(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateAmendment} disabled={amendSaving || !amendName || !amendContent}>
                {amendSaving ? "Saving..." : "Create"}
              </Button>
              <Button size="sm" variant="outline" onClick={() => setShowAmendForm(false)}>Cancel</Button>
            </div>
          </div>
        )}

        {amendments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No amendments yet.</p>
        ) : (
          <div className="space-y-2">
            {amendments.map((a) => (
              <div key={a.id} className="flex items-start justify-between rounded-md border border-border p-3">
                <div>
                  <p className="text-sm font-medium">{a.name}</p>
                  <div className="text-xs text-muted-foreground whitespace-pre-wrap mt-1">{a.content}</div>
                </div>
                <p className="shrink-0 text-xs text-muted-foreground">
                  {new Date(a.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
</div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}
