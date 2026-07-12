"use client";

import { useEffect, useState } from "react";
import { Loader2, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { OrganizationAIConfigForm } from "@/components/admin/organization-ai-config-form";
import { getOrganizationAIConfiguration, type OrganizationAIConfiguration } from "@/lib/api/admin";

export default function OrganizationAISettingsPage() {
  const [config, setConfig] = useState<OrganizationAIConfiguration | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try { setConfig(await getOrganizationAIConfiguration()); }
    catch (err) { setError(err instanceof Error ? err.message : "Không thể tải cấu hình AI"); }
  }

  useEffect(() => { void load(); }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Organization AI Settings</h1>
        <p className="text-sm text-muted-foreground">Cấu hình provider và model AI dùng chung cho Organization.</p>
      </div>
      {error && <div className="flex items-center gap-3 text-destructive"><ShieldAlert className="h-5 w-5" aria-hidden="true" /><p>{error}</p><Button variant="link" onClick={load}>Thử lại</Button></div>}
      {!error && !config && <Loader2 className="h-8 w-8 animate-spin" aria-label="Đang tải cấu hình AI" />}
      {config && <OrganizationAIConfigForm config={config} onUpdated={setConfig} />}
    </div>
  );
}
