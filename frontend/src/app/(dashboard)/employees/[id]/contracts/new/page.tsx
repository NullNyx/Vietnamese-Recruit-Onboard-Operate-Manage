"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { createEmployeeContract, getEmployee, listContractTemplates } from "@/lib/api/employees";
import type { ContractTemplate, Employee } from "@/lib/api/types";

const CONTRACT_TYPES = [
  { value: "labor", label: "Labor Contract" },
  { value: "offer", label: "Offer Letter" },
  { value: "nda", label: "NDA" },
  { value: "other", label: "Other" },
];

export default function NewContractPage() {
  const params = useParams();
  const router = useRouter();
  const employeeId = params.id as string;

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [templates, setTemplates] = useState<ContractTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    contract_type: "labor",
    contract_number: "",
    template_id: "",
    started_on: "",
    ended_on: "",
    content: "",
  });

  useEffect(() => {
    async function load() {
      try {
        const [emp, tpl] = await Promise.all([getEmployee(employeeId), listContractTemplates()]);
        setEmployee(emp);
        setTemplates(tpl);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load contract form");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [employeeId]);

  const chooseTemplate = (templateId: string) => {
    const template = templates.find((item) => item.id === templateId);
    setForm((prev) => ({
      ...prev,
      template_id: templateId,
      content: template?.content ?? prev.content,
    }));
  };

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const contract = await createEmployeeContract(employeeId, {
        contract_type: form.contract_type,
        contract_number: form.contract_number || undefined,
        template_id: form.template_id || undefined,
        started_on: form.started_on || undefined,
        ended_on: form.ended_on || undefined,
        content: form.content || undefined,
      });
      router.push(`/employees/${employeeId}/contracts/${contract.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading contract form...</div>;
  }

  if (error || !employee) {
    return <div className="p-6 text-sm text-destructive">{error || "Employee not found"}</div>;
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href={`/employees/${employeeId}`}><ArrowLeft className="h-4 w-4" /></Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">New Contract</h1>
          <p className="text-sm text-muted-foreground">{employee.full_name}</p>
        </div>
      </div>

      <div className="max-w-3xl rounded-md border bg-card p-6 space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Contract type">
            <Select value={form.contract_type} onValueChange={(value) => setForm((prev) => ({ ...prev, contract_type: value }))}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                {CONTRACT_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="Contract number">
            <Input value={form.contract_number} onChange={(e) => setForm((prev) => ({ ...prev, contract_number: e.target.value }))} />
          </Field>
          <Field label="Template">
            <Select value={form.template_id} onValueChange={chooseTemplate}>
              <SelectTrigger><SelectValue placeholder="Blank" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">Blank</SelectItem>
                {templates.map((template) => (
                  <SelectItem key={template.id} value={template.id}>{template.name} v{template.version}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="Started on">
            <Input type="date" value={form.started_on} onChange={(e) => setForm((prev) => ({ ...prev, started_on: e.target.value }))} />
          </Field>
          <Field label="Ended on">
            <Input type="date" value={form.ended_on} onChange={(e) => setForm((prev) => ({ ...prev, ended_on: e.target.value }))} />
          </Field>
        </div>
        <Field label="Content">
          <Textarea className="min-h-64" value={form.content} onChange={(e) => setForm((prev) => ({ ...prev, content: e.target.value }))} />
        </Field>
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        <div className="flex gap-2">
          <Button onClick={submit} disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? "Creating..." : "Create"}
          </Button>
          <Link href={`/employees/${employeeId}`}>
            <Button variant="outline">Cancel</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
