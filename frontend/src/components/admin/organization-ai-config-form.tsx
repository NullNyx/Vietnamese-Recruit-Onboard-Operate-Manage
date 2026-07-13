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
      getDataPolicy,
      acceptDataPolicy,
      enableAutomation,
      disableAutomation,
      enableAssistant,
      disableAssistant,
      configureClassificationRollout,
      rollbackClassificationRollout,
      type OrganizationAIConfiguration,
      type DataPolicyResponse,
} from "@/lib/api/admin";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function StateBadge({ state }: { state: string }) {
  const colorMap: Record<string, string> = {
    not_configured: "bg-gray-100 text-gray-700",
    disabled: "bg-yellow-100 text-yellow-700",
    ready: "bg-green-100 text-green-700",
    unavailable: "bg-red-100 text-red-700",
  };
  const labelMap: Record<string, string> = {
    not_configured: "Chưa cấu hình",
    disabled: "Đã tắt",
    ready: "Sẵn sàng",
    unavailable: "Không khả dụng",
  };
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${colorMap[state] || "bg-gray-100 text-gray-700"}`}>
      {labelMap[state] || state}
    </span>
  );
}


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
  const [policyExpanded, setPolicyExpanded] = useState(false);
  const [policy, setPolicy] = useState<DataPolicyResponse | null>(null);
  const [classifierVersion, setClassifierVersion] = useState(
    config.candidate_classifier_version ?? config.stable_classifier_version
  );
  const [classificationPolicyVersion, setClassificationPolicyVersion] = useState(
    config.candidate_classification_policy_version ?? config.classification_policy_version
  );

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

  async function handleLoadPolicy() {
    setBusy(true);
    setMessage(null);
    try {
      const data = await getDataPolicy();
      setPolicy(data);
      setPolicyExpanded(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể tải data policy");
    } finally {
      setBusy(false);
    }
  }

  async function handleAcceptPolicy() {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const updated = await acceptDataPolicy();
      onUpdated(updated);
      setMessage("Đã chấp nhận data policy.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể chấp nhận data policy");
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleAutomation(enable: boolean) {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const updated = enable ? await enableAutomation() : await disableAutomation();
      onUpdated(updated);
      setMessage(enable ? "AI Automation đã được bật." : "AI Automation đã được tắt.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể thay đổi AI Automation");
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleAssistant(enable: boolean) {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const updated = enable ? await enableAssistant() : await disableAssistant();
      onUpdated(updated);
      setMessage(enable ? "AI Assistant đã được bật." : "AI Assistant đã được tắt.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể thay đổi AI Assistant");
    } finally {
      setBusy(false);
    }
  }

  async function handleClassificationRollout(mode: "shadow" | "canary") {
    setBusy(true);
    setMessage(null);
    setSuccess(false);
    try {
      const updated = await configureClassificationRollout({
        mode,
        business_policy: "recall_first",
        policy_version: classificationPolicyVersion,
        classifier_version: classifierVersion,
        canary_percentage: mode === "canary" ? 10 : 0,
      });
      onUpdated(updated);
      setMessage(
        mode === "shadow"
          ? "Đã bật shadow; kết quả candidate không thay đổi workflow."
          : "Đã bật canary ổn định 10% theo email."
      );
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể cập nhật rollout");
    } finally {
      setBusy(false);
    }
  }

  async function handleClassificationRollback() {
    setBusy(true);
    setMessage(null);
    try {
      const updated = await rollbackClassificationRollout();
      onUpdated(updated);
      setMessage("Đã rollback về classifier và policy stable.");
      setSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Không thể rollback");
    } finally {
      setBusy(false);
    }
  }


  const isOrgKeySource = credentialSource === "org_api_key";
  const isDeploymentKeySource = credentialSource === "deployment_key";
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


          {/* Job Application classification rollout */}
          {config.configured && (
            <section className="rounded-lg border bg-card p-6 space-y-4">
              <h2 className="font-heading text-lg font-semibold">Job Application classification</h2>
              <p className="text-sm text-muted-foreground">
                Organization chọn policy nghiệp vụ; confidence threshold do hệ thống quản lý.
              </p>
              <div className="rounded border p-3 text-sm">
                <p><strong>Policy:</strong> Ưu tiên không bỏ sót</p>
                <p><strong>Stable:</strong> {config.stable_classifier_version} / {config.classification_policy_version}</p>
                <p><strong>Rollout:</strong> {config.rollout_mode}{config.rollout_mode === "canary" ? ` (${config.canary_percentage}%)` : ""}</p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="classifier-version">Candidate classifier version</Label>
                <Input
                  id="classifier-version"
                  value={classifierVersion}
                  onChange={(event) => setClassifierVersion(event.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="classification-policy-version">Policy version</Label>
                <Input
                  id="classification-policy-version"
                  value={classificationPolicyVersion}
                  onChange={(event) => setClassificationPolicyVersion(event.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="outline" disabled={busy} onClick={() => handleClassificationRollout("shadow")}>
                  Bật shadow
                </Button>
                <Button type="button" variant="outline" disabled={busy} onClick={() => handleClassificationRollout("canary")}>
                  Bật canary 10%
                </Button>
                {config.rollout_mode !== "stable" && (
                  <Button type="button" variant="destructive" disabled={busy} onClick={handleClassificationRollback}>
                    Rollback stable
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Full rollout chỉ mở qua operational release gate sau khi có báo cáo no-CV riêng.
              </p>
            </section>
          )}


          {/* Data Policy & Consent */}
          {config.configured && (
            <section className="rounded-lg border bg-card p-6 space-y-4">
              <h2 className="font-heading text-lg font-semibold">Data Policy & Consent</h2>
              <p className="text-sm text-muted-foreground">
                Trước khi bật AI, bạn cần xem và chấp nhận data policy mô tả loại dữ liệu
                được gửi tới provider.
              </p>

              {!policy && !policyExpanded && (
                <Button type="button" variant="outline" onClick={handleLoadPolicy} disabled={busy}>
                  {busy ? "Đang tải..." : "Xem Data Policy"}
                </Button>
              )}

              {policyExpanded && policy && (
                <div className="space-y-3">
                  <p className="text-xs text-muted-foreground">
                    Phiên bản: {policy.version}
                  </p>
                  {policy.items.map((item, idx) => (
                    <div key={idx} className="rounded border p-3 text-sm">
                      <p className="font-medium">{item.category}</p>
                      <p className="text-muted-foreground">Dữ liệu: {item.data_types}</p>
                      <p className="text-muted-foreground">Mục đích: {item.purpose}</p>
                      <p className="text-muted-foreground">Lưu trữ: {item.retention}</p>
                    </div>
                  ))}

                  {!config.data_policy_accepted && (
                    <Button type="button" variant="default" onClick={handleAcceptPolicy} disabled={busy}>
                      {busy ? "Đang xử lý..." : "Tôi đồng ý và chấp nhận Data Policy"}
                    </Button>
                  )}

                  {config.data_policy_accepted && (
                    <p className="text-sm text-green-600">
                      ✓ Data policy đã được chấp nhận
                      {config.data_policy_accepted_at && ` (${new Date(config.data_policy_accepted_at).toLocaleString()})`}
                      {config.data_policy_version && ` — phiên bản ${config.data_policy_version}`}
                    </p>
                  )}
                </div>
              )}
            </section>
          )}

          {/* Capability Toggles */}
          {config.configured && (
            <section className="rounded-lg border bg-card p-6 space-y-4">
              <h2 className="font-heading text-lg font-semibold">AI Capabilities</h2>
              <p className="text-sm text-muted-foreground">
                Bật/tắt độc lập AI Automation và AI Assistant. Cả hai dùng chung provider/model.
              </p>

              {/* AI Automation toggle */}
              <div className="flex items-center justify-between rounded border p-4">
                <div>
                  <p className="font-medium">AI Automation</p>
                  <p className="text-xs text-muted-foreground">
                    Phân loại email và parse CV tự động
                  </p>
                  <StateBadge state={config.automation_state} />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={config.automation_enabled ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleToggleAutomation(!config.automation_enabled)}
                    disabled={busy || (!config.automation_enabled && !config.data_policy_accepted)}
                  >
                    {config.automation_enabled ? "Đang bật" : "Đang tắt"}
                  </Button>
                </div>
              </div>

              {/* AI Assistant toggle */}
              <div className="flex items-center justify-between rounded border p-4">
                <div>
                  <p className="font-medium">AI Assistant</p>
                  <p className="text-xs text-muted-foreground">
                    Trợ lý hội thoại cho HR
                  </p>
                  <StateBadge state={config.assistant_state} />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={config.assistant_enabled ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleToggleAssistant(!config.assistant_enabled)}
                    disabled={busy || (!config.assistant_enabled && !config.data_policy_accepted)}
                  >
                    {config.assistant_enabled ? "Đang bật" : "Đang tắt"}
                  </Button>
                </div>
              </div>
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
