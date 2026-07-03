"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Archive, Eye, Plus, RotateCcw, Save, Sparkles, Tags, Trash2 } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  archiveOnboardingTemplate,
  createOnboardingTemplate,
  listOnboardingTemplates,
  previewOnboardingTemplate,
  updateOnboardingTemplate,
  type OnboardingTemplate,
  type OnboardingTemplateCreateInput,
  type OnboardingTemplateType,
  type OnboardingTemplateUpdateInput,
} from "@/lib/api/onboarding";

type TemplateFormState = {
  template_type: OnboardingTemplateType;
  key: string;
  display_name: string;
  description: string;
  template_body: string;
  is_required: boolean;
  order_index: string;
};

const EMPTY_FORM: TemplateFormState = {
  template_type: "task",
  key: "",
  display_name: "",
  description: "",
  template_body: "",
  is_required: true,
  order_index: "0",
};

const TYPE_LABELS: Record<OnboardingTemplateType, string> = {
  task: "Task",
  document: "Document",
  contract: "Contract",
};

function toForm(template: OnboardingTemplate, overrideType?: OnboardingTemplateType): TemplateFormState {
  return {
    template_type: overrideType ?? template.template_type,
    key: template.key,
    display_name: template.display_name,
    description: template.description ?? "",
    template_body: template.template_body ?? "",
    is_required: template.is_required,
    order_index: String(template.order_index),
  };
}

export default function TemplateSettingsPage() {
  const [selectedType, setSelectedType] = useState<OnboardingTemplateType>("task");
  const [templates, setTemplates] = useState<OnboardingTemplate[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<TemplateFormState>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const filteredTemplates = useMemo(
    () => templates.filter((template) => template.template_type === selectedType),
    [templates, selectedType],
  );

  const loadTemplates = useCallback(
    async (type: OnboardingTemplateType) => {
      try {
        setLoading(true);
        const data = await listOnboardingTemplates(type);
      setTemplates(data.items);
      if (data.items.length > 0 && editingId === null) {
        const first = data.items[0];
        setEditingId(first.id);
        setForm(toForm(first));
      }
      setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Không tải được template");
      } finally {
        setLoading(false);
      }
    },
    [editingId],
  );

  useEffect(() => {
    void loadTemplates(selectedType);
  }, [loadTemplates, selectedType]);

  function startCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM, template_type: selectedType });
    setPreview(null);
  }

  function startEdit(template: OnboardingTemplate) {
    setEditingId(template.id);
    setForm(toForm(template, selectedType));
    setPreview(null);
  }

  async function handleSave() {
    const payloadBase = {
      template_type: form.template_type,
      key: form.key.trim(),
      display_name: form.display_name.trim(),
      description: form.description.trim() || null,
      template_body: form.template_body.trim() || null,
      is_required: form.is_required,
      order_index: Number(form.order_index || "0"),
    };
    if (!payloadBase.key || !payloadBase.display_name) {
      setError("Key và tên template bắt buộc.");
      return;
    }
    try {
      setSaving(true);
      setError(null);
      if (editingId) {
        const payload: OnboardingTemplateUpdateInput = {
          display_name: payloadBase.display_name,
          description: payloadBase.description,
          template_body: payloadBase.template_body,
          is_required: payloadBase.is_required,
          order_index: payloadBase.order_index,
        };
        const updated = await updateOnboardingTemplate(editingId, payload);
        setTemplates((current) =>
          current.map((item) => (item.id === updated.id ? updated : item)),
        );
        setSuccess("Đã cập nhật template.");
      } else {
        const payload: OnboardingTemplateCreateInput = {
          ...payloadBase,
          version: 1,
          is_system: false,
          is_archived: false,
        };
        const created = await createOnboardingTemplate(payload);
        setTemplates((current) => [created, ...current]);
        setEditingId(created.id);
        setSuccess("Đã tạo template.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không lưu được template");
    } finally {
      setSaving(false);
    }
  }

  async function handleArchive(template: OnboardingTemplate) {
    const confirmed = window.confirm(`Archive template "${template.display_name}"?`);
    if (!confirmed) return;
    try {
      setSaving(true);
      setError(null);
      const updated = await archiveOnboardingTemplate(template.id);
      setTemplates((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      if (editingId === updated.id) {
        setForm(toForm(updated, selectedType));
      }
      setSuccess("Đã archive template.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không archive được template");
    } finally {
      setSaving(false);
    }
  }

  async function handlePreview(template: OnboardingTemplate) {
    try {
      setError(null);
      const data = await previewOnboardingTemplate(template.id);
      setPreview(data.preview);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không xem được preview");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-foreground">Template management</h1>
          <p className="text-sm text-muted-foreground">
            Quản lý template dùng cho onboarding case generation.
          </p>
        </div>
        <Button onClick={startCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Tạo mới
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <Trash2 className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert className="border-green-200 bg-green-50 text-green-800">
          <Sparkles className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader className="space-y-4">
            <div>
              <CardTitle>Template list</CardTitle>
              <CardDescription>Task, document, và contract template.</CardDescription>
            </div>
            <div className="flex gap-2">
              {(Object.keys(TYPE_LABELS) as OnboardingTemplateType[]).map((type) => (
                <Button
                  key={type}
                  variant={selectedType === type ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setSelectedType(type);
                    setEditingId(null);
                    setPreview(null);
                  }}
                >
                  {TYPE_LABELS[type]}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="text-sm text-muted-foreground">Đang tải...</div>
            ) : filteredTemplates.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
                Chưa có template trong nhóm này.
              </div>
            ) : (
              <div className="space-y-3">
                {filteredTemplates.map((template) => (
                  <div
                    key={template.id}
                    className="rounded-lg border border-border bg-background p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-medium text-foreground">{template.display_name}</h3>
                          <Badge variant="outline">{template.key}</Badge>
                          <Badge variant="secondary">{TYPE_LABELS[template.template_type]}</Badge>
                          {template.is_system && <Badge>System</Badge>}
                          {template.is_archived && <Badge variant="destructive">Archived</Badge>}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {template.description || "Không có mô tả."}
                        </p>
                        <div className="text-xs text-muted-foreground">
                          v{template.version} • order {template.order_index}
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <Button variant="outline" size="sm" onClick={() => handlePreview(template)}>
                          <Eye className="mr-2 h-4 w-4" />
                          Preview
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => startEdit(template)}>
                          <RotateCcw className="mr-2 h-4 w-4" />
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={template.is_archived || saving}
                          onClick={() => handleArchive(template)}
                        >
                          <Archive className="mr-2 h-4 w-4" />
                          Archive
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{editingId ? "Edit template" : "Create template"}</CardTitle>
            <CardDescription>Chỉnh metadata, nội dung preview, và version.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="template_type">Type</Label>
                <Select
                  value={form.template_type}
                  disabled={editingId !== null}
                  onValueChange={(value) =>
                    setForm((current) => ({ ...current, template_type: value as OnboardingTemplateType }))
                  }
                >
                  <SelectTrigger id="template_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="task">Task</SelectItem>
                    <SelectItem value="document">Document</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="template_order">Order</Label>
                <Input
                  id="template_order"
                  type="number"
                  value={form.order_index}
                  onChange={(event) => setForm((current) => ({ ...current, order_index: event.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="template_key">Key</Label>
              <Input
                id="template_key"
                value={form.key}
                disabled={editingId !== null}
                onChange={(event) => setForm((current) => ({ ...current, key: event.target.value }))}
                placeholder="sign_contract"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="template_name">Display name</Label>
              <Input
                id="template_name"
                value={form.display_name}
                onChange={(event) =>
                  setForm((current) => ({ ...current, display_name: event.target.value }))
                }
                placeholder="Sign Contract"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="template_description">Description</Label>
              <Textarea
                id="template_description"
                value={form.description}
                onChange={(event) =>
                  setForm((current) => ({ ...current, description: event.target.value }))
                }
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="template_body">Template body</Label>
              <Textarea
                id="template_body"
                value={form.template_body}
                onChange={(event) =>
                  setForm((current) => ({ ...current, template_body: event.target.value }))
                }
                rows={8}
                placeholder="Used for contract preview."
              />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                id="template_required"
                type="checkbox"
                checked={form.is_required}
                onChange={(event) =>
                  setForm((current) => ({ ...current, is_required: event.target.checked }))
                }
              />
              <Label htmlFor="template_required" className="font-normal">
                Required
              </Label>
            </div>
            <Separator />
            {preview && (
              <div className="max-h-72 overflow-auto rounded-lg border bg-muted/30 p-3 text-sm">
                <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
                  <Tags className="h-3.5 w-3.5" />
                  Preview
                </div>
                <pre className="whitespace-pre-wrap break-words text-xs leading-5">{preview}</pre>
              </div>
            )}
            <Button className="w-full" onClick={handleSave} disabled={saving}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Đang lưu..." : "Lưu template"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
