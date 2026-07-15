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
        <div className="animate-fade-in space-y-6">
          <div className="fade-in-section">
            <h1 className="font-heading text-2xl font-bold tracking-tight">Cấu hình AI</h1>
            <p className="text-sm text-muted-foreground mt-1">Cấu hình provider và model AI dùng chung cho Organization.</p>
          </div>
          {error && <div className="fade-in-section flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 p-4"><ShieldAlert className="h-5 w-5 text-destructive" aria-hidden="true" /><p className="text-destructive">{error}</p><Button variant="link" onClick={load}>Thử lại</Button></div>}
          {!error && !config && <div className="flex items-center justify-center py-16"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Đang tải cấu hình AI" /></div>}
          {config && <div className="fade-in-section"><OrganizationAIConfigForm config={config} onUpdated={setConfig} /></div>}
        </div>
  );
}
