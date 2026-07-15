"use client";

import { useEffect, useState } from "react";
import { Loader2, ShieldAlert } from "lucide-react";

import { getOAuthConfig, type OAuthConfig } from "@/lib/api/admin";
import { OAuthConfigForm } from "@/components/admin/oauth-config-form";
import { Button } from "@/components/ui/button";

export default function OAuthConfigPage() {
  const [config, setConfig] = useState<OAuthConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchConfig(); }, []);

  async function fetchConfig() {
    setLoading(true);
    setError(null);
    try {
      setConfig(await getOAuthConfig());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải cấu hình OAuth");
    } finally {
      setLoading(false);
    }
  }

      return (
        <div className="animate-fade-in space-y-6">
          <div className="fade-in-section">
            <h1 className="font-heading text-2xl font-bold tracking-tight">Cấu hình OAuth</h1>
            <p className="text-sm text-muted-foreground mt-1">Quản lý thông tin xác thực Google OAuth cho đăng nhập</p>
          </div>
          <div aria-live="polite" className="fade-in-section">
            {loading && <div className="flex items-center justify-center py-16"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" /><span className="sr-only">Đang tải cấu hình OAuth...</span></div>}
            {!loading && error && <div className="flex flex-col items-center justify-center gap-4 py-16 rounded-xl border border-destructive/20 bg-destructive/5"><ShieldAlert className="h-12 w-12 text-destructive" aria-hidden="true" /><p className="text-sm text-muted-foreground">{error}</p><Button variant="link" onClick={fetchConfig}>Thử lại</Button></div>}
            {!loading && !error && config && <OAuthConfigForm config={config} onUpdated={setConfig} />}
          </div>
        </div>
  );
}
