"use client";

import { FormEvent, useState } from "react";
import {
  testOrganizationAIConfiguration,
  updateOrganizationAIConfiguration,
  setCredentialSource,
  activateOrgApiKey,
  revokeOrgApiKey,
  testDeploymentKey,
  updateProviderConfig,
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
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [credentialSource, setCredentialSourceState] = useState(
    config.credential_source ?? "org_api_key"
  );
  const [revokeConfirm, setRevokeConfirm] = useState(false);

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
      setCredentialSourceState(updated.credential_source ?? "org_api_key");
      setTestResult(null);
      setMessage("Đã kiểm tra và lưu cấu hình AI.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể cập nhật cấu hình AI");
    } finally {
      setBusy(false);
    }
  }

  async function handleTestOnly(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setTestResult(null);
    setMessage(null);
    try {
      const data = { provider, base_url: baseUrl, model, api_key: apiKey };
      const result = await testOrganizationAIConfiguration(data);
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : "Test failed",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleActivate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    setTestResult(null);
    try {
      const updated = await activateOrgApiKey(apiKey);
      onUpdated(updated);
      setApiKey("");
      setCredentialSourceState(updated.credential_source ?? "org_api_key");
      setMessage("API key mới đã được kích hoạt.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể kích hoạt API key");
    } finally {
      setBusy(false);
    }
  }

  async function handleSourceChange(source: string) {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const updated = await setCredentialSource(source);
      onUpdated(updated);
      setCredentialSourceState(source);
      setMessage(
        source === "deployment_key"
          ? "Đã chuyển sang Deployment key."
          : "Đã chuyển sang Organization API key."
      );
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể thay đổi credential source");
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke() {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    setRevokeConfirm(false);
    try {
      const updated = await revokeOrgApiKey();
      onUpdated(updated);
      setCredentialSourceState(updated.credential_source ?? "org_api_key");
      setMessage("Organization API key đã bị thu hồi.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể thu hồi API key");
    } finally {
      setBusy(false);
    }
  }

  async function handleTestDeploymentKey() {
    setBusy(true);
    setMessage(null);
    setTestResult(null);
    try {
      const result = await testDeploymentKey();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : "Test failed",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveProvider() {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const updated = await updateProviderConfig({
        provider,
        base_url: baseUrl,
        model,
      });
      onUpdated(updated);
      setMessage("Đã lưu cấu hình provider.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể lưu cấu hình provider");
    } finally {
      setBusy(false);
    }
  }

  const isOrgKeySource = credentialSource === "org_api_key";
  const isDeploymentKeySource = credentialSource === "deployment_key";
  const hasConfigured = config.configured;
  const hasOrgApiKey = config.configured && isOrgKeySource && config.api_key_masked != null;
  const hasDeploymentKey = config.deployment_key_available;

  return (
    <div className="max-w-2xl space-y-6">
      {/* Credential source selection */}
      <section className="rounded-lg border bg-card p-6 space-y-4">
        <h2 className="font-heading text-lg font-semibold">Credential source</h2>
        <p className="text-sm text-muted-foreground">
          Chọn nguồn credential cho Organization AI. Deployment key được cung cấp bởi deployment
          operator ngoài UI.
        </p>

        <div className="flex gap-4">
          <Button
            type="button"
            variant={isOrgKeySource ? "default" : "outline"}
            onClick={() => handleSourceChange("org_api_key")}
            disabled={busy}
          >
            Organization API key
          </Button>
          <Button
            type="button"
            variant={isDeploymentKeySource ? "default" : "outline"}
            onClick={() => handleSourceChange("deployment_key")}
            disabled={busy || !hasDeploymentKey}
            title={
              !hasDeploymentKey
                ? "Deployment key chưa được cấu hình (AI_DEPLOYMENT_KEY)"
                : undefined
            }
          >
            Deployment key
            {hasDeploymentKey ? " ✓" : " (chưa có)"}
          </Button>
        </div>

        {isDeploymentKeySource && hasDeploymentKey && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Deployment key có sẵn</span>
            <Button type="button" variant="outline" size="sm" onClick={handleTestDeploymentKey} disabled={busy}>
              {busy ? "Đang test..." : "Test deployment key"}
            </Button>
          </div>
        )}
        {!hasDeploymentKey && (
          <p className="text-xs text-muted-foreground">
            Deployment key chưa được cấu hình. Đặt biến môi trường AI_DEPLOYMENT_KEY để bật.
          </p>
        )}
      </section>

      {/* Provider configuration */}
      <section className="rounded-lg border bg-card p-6 space-y-4">
        <h2 className="font-heading text-lg font-semibold">Provider & Model</h2>
        <div className="grid gap-2">
          <Label htmlFor="ai-provider">Provider</Label>
          <Input
            id="ai-provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            required
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="ai-base-url">OpenAI-compatible Base URL</Label>
          <Input
            id="ai-base-url"
            type="url"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            required
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="ai-model">Model</Label>
          <Input
            id="ai-model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="gpt-4o-mini hoặc custom-model"
            required
          />
        </div>
        <Button type="button" variant="outline" onClick={handleSaveProvider} disabled={busy}>
          {busy ? "Đang lưu..." : "Lưu cấu hình provider"}
        </Button>
      </section>

      {/* Organization API key section */}
      {isOrgKeySource && (
        <section className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="font-heading text-lg font-semibold">Organization API key</h2>

          {hasOrgApiKey && (
            <p className="text-xs text-muted-foreground">
              Key hiện tại: {config.api_key_masked}
            </p>
          )}

          <div className="grid gap-2">
            <Label htmlFor="ai-api-key">
              {hasOrgApiKey ? "API key mới (để rotate)" : "Organization API key"}
            </Label>
            <Input
              id="ai-api-key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={hasOrgApiKey ? "Nhập key mới để thay đổi" : "Nhập API key"}
            />
          </div>

          <div className="flex gap-3 flex-wrap">
            <Button type="button" onClick={handleTestOnly} disabled={busy || !apiKey}>
              {busy ? "Đang test..." : "Test key"}
            </Button>
            {testResult?.success && (
              <Button type="button" variant="default" onClick={handleActivate} disabled={busy}>
                {busy ? "Đang kích hoạt..." : "Kích hoạt key này"}
              </Button>
            )}
            <Button
              type="button"
              onClick={submit}
              disabled={busy || !apiKey}
              variant="secondary"
            >
              {busy ? "Đang xử lý..." : "Test và lưu (một bước)"}
            </Button>
          </div>

          {testResult && (
            <p
              role="status"
              className={testResult.success ? "text-sm text-green-600" : "text-sm text-destructive"}
            >
              {testResult.success ? "✓ Test kết nối thành công. Nhấn 'Kích hoạt' để lưu." : `✗ ${testResult.message}`}
            </p>
          )}
        </section>
      )}

      {/* Revoke section */}
      {hasOrgApiKey && (
        <section className="rounded-lg border border-destructive/20 bg-card p-6 space-y-4">
          <h2 className="font-heading text-lg font-semibold text-destructive">Revoke API key</h2>
          <p className="text-sm text-muted-foreground">
            Thu hồi Organization API key hiện tại. Provider và model sẽ được giữ nguyên.
          </p>
          {!revokeConfirm ? (
            <Button
              type="button"
              variant="destructive"
              onClick={() => setRevokeConfirm(true)}
              disabled={busy}
            >
              Thu hồi API key
            </Button>
          ) : (
            <div className="flex gap-3 items-center">
              <span className="text-sm text-destructive">Xác nhận thu hồi?</span>
              <Button type="button" variant="destructive" onClick={handleRevoke} disabled={busy}>
                {busy ? "Đang xử lý..." : "Xác nhận thu hồi"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setRevokeConfirm(false)}
                disabled={busy}
              >
                Hủy
              </Button>
            </div>
          )}
        </section>
      )}

      {/* Global message */}
      {message && (
        <p role="status" className={success ? "text-sm text-green-600" : "text-sm text-destructive"}>
          {message}
        </p>
      )}
    </div>
  );
}
