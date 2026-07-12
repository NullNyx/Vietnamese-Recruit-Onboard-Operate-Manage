"use client";

import { FormEvent, useState } from "react";
import {
  getOrganizationAIConfiguration,
  testOrganizationAIConfiguration,
  updateOrganizationAIConfiguration,
  type OrganizationAIConfiguration,
} from "@/lib/api/admin";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function OrganizationAIConfigForm({
  config,
  onUpdated,
}: {
  config: OrganizationAIConfiguration;
  onUpdated: (config: OrganizationAIConfiguration) => void;
}) {
  const [provider, setProvider] = useState(config.provider ?? "openai");
  const [baseUrl, setBaseUrl] = useState(config.base_url ?? "https://api.openai.com/v1");
  const [model, setModel] = useState(config.model ?? "");
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const data = { provider, base_url: baseUrl, model, api_key: apiKey };
      const result = await testOrganizationAIConfiguration(data);
      if (!result.success) throw new Error(result.message);
      const updated = await updateOrganizationAIConfiguration(data);
      onUpdated(updated);
      setApiKey("");
      setMessage("Đã kiểm tra và lưu cấu hình AI.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể cập nhật cấu hình AI");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="max-w-2xl space-y-6 rounded-lg border bg-card p-6">
      <div className="grid gap-2">
        <Label htmlFor="ai-provider">Provider</Label>
        <Input id="ai-provider" value={provider} onChange={(e) => setProvider(e.target.value)} required />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="ai-base-url">OpenAI-compatible Base URL</Label>
        <Input id="ai-base-url" type="url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} required />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="ai-model">Model</Label>
        <Input id="ai-model" value={model} onChange={(e) => setModel(e.target.value)} placeholder="gpt-4o-mini hoặc custom-model" required />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="ai-api-key">Organization API key</Label>
        <Input id="ai-api-key" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder={config.api_key_masked ?? "Nhập API key"} required />
        {config.configured && <p className="text-xs text-muted-foreground">Key hiện tại: {config.api_key_masked}. Nhập key mới để thay đổi.</p>}
      </div>
      <Button type="submit" disabled={busy}>{busy ? "Đang kiểm tra..." : "Kiểm tra và lưu"}</Button>
      {message && <p role="status" className={success ? "text-sm text-green-600" : "text-sm text-destructive"}>{message}</p>}
    </form>
  );
}
