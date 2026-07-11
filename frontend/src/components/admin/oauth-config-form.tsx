"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

import { updateOAuthConfig, type OAuthConfig } from "@/lib/api/admin";
import {
  oauthConfigUpdateSchema,
  type OAuthConfigUpdateFormData,
} from "@/lib/api/admin-schemas";

export interface OAuthConfigFormProps {
  config: OAuthConfig;
  onUpdated: (config: OAuthConfig) => void;
}

export function OAuthConfigForm({ config, onUpdated }: OAuthConfigFormProps) {
  const [backendError, setBackendError] = useState<string | null>(null);
  const [connection, setConnection] = useState<{ status: "disconnected" | "connected" | "reauthorization_required"; email: string | null; redirect_url: string | null } | null>(null);

  const form = useForm<OAuthConfigUpdateFormData>({
    resolver: zodResolver(oauthConfigUpdateSchema),
    mode: "onBlur",
    defaultValues: {
      client_id: "",
      client_secret: "",
      redirect_uri: "",
    },
  });

  const loadConnection = async () => {
    try {
      const res = await fetch("/api/auth/organization-google-connection");
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail?.message ?? "Không thể tải trạng thái kết nối");
      setConnection(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể tải trạng thái kết nối";
      toast.error(message);
    }
  };

  useEffect(() => {
    void loadConnection();
  }, []);

  const handleSubmit = async (values: OAuthConfigUpdateFormData) => {
    setBackendError(null);
    try {
      const updated = await updateOAuthConfig(values);
      onUpdated(updated);
      await loadConnection();
      form.reset({ client_id: "", client_secret: "", redirect_uri: "" });
      toast.success("Đã cập nhật cấu hình OAuth");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể cập nhật cấu hình OAuth";
      setBackendError(message);
      toast.error(message);
    }
  };

  const handleReconnect = async () => {
    if (!window.confirm("Kết nối lại Google Workspace?")) return;
    try {
      const res = await fetch("/api/auth/organization-google-connection/reconnect", { method: "POST" });
      const next = await res.json();
      if (!res.ok) throw new Error(next?.detail?.message ?? "Không thể tạo URL kết nối");
      setConnection(next);
      if (next.redirect_url) {
        window.location.assign(next.redirect_url);
        return;
      }
      toast.success("Đã tạo lại kết nối");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể tạo lại kết nối";
      toast.error(message);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Ngắt kết nối Google Workspace?")) return;
    try {
      const res = await fetch("/api/auth/organization-google-connection", { method: "DELETE" });
      const next = await res.json();
      if (!res.ok) throw new Error(next?.detail?.message ?? "Không thể ngắt kết nối");
      setConnection(next);
      toast.success("Đã ngắt kết nối Google Workspace");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể ngắt kết nối";
      toast.error(message);
    }
  };

  const statusLabel = connection?.status ?? "unknown";
  const connectedEmail = connection?.email ?? null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Cấu hình hiện tại</CardTitle>
              <CardDescription>
                Thông tin xác thực Google OAuth đang sử dụng
              </CardDescription>
            </div>
            <Badge variant={config.source === "database" ? "default" : "secondary"}>
              {config.source === "database" ? "Database" : "Environment"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Client ID</dt>
              <dd className="mt-1 text-sm font-mono break-all">
                {config.client_id || <span className="text-muted-foreground italic">Chưa cấu hình</span>}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Client Secret</dt>
              <dd className="mt-1 text-sm font-mono">
                {config.client_secret_masked || <span className="text-muted-foreground italic">Chưa cấu hình</span>}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm font-medium text-muted-foreground">Redirect URI</dt>
              <dd className="mt-1 text-sm font-mono break-all">
                {config.redirect_uri || <span className="text-muted-foreground italic">Chưa cấu hình</span>}
              </dd>
            </div>
            {config.updated_at && (
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-muted-foreground">Cập nhật lần cuối</dt>
                <dd className="mt-1 text-sm">
                  {new Date(config.updated_at).toLocaleString("vi-VN")}
                </dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Kết nối Google Workspace</CardTitle>
          <CardDescription>
            HR giữ kết nối dùng chung cho Gmail và Calendar.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={statusLabel === "connected" ? "default" : statusLabel === "reauthorization_required" ? "destructive" : "secondary"}>
              {statusLabel}
            </Badge>
            <span className="text-sm text-muted-foreground">{connectedEmail ?? "Chưa kết nối"}</span>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="outline" onClick={() => void loadConnection()}>
              Tải trạng thái
            </Button>
            <Button type="button" onClick={() => void handleReconnect()}>
              Kết nối lại
            </Button>
            <Button type="button" variant="destructive" onClick={() => void handleDisconnect()}>
              Ngắt kết nối
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cập nhật thông tin</CardTitle>
          <CardDescription>
            Gửi thông tin xác thực mới. Chúng sẽ được xác minh với Google trước khi áp dụng.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {backendError && (
            <div
              className="mb-4 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
              role="alert"
            >
              {backendError}
            </div>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="client_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Client ID <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="your-client-id.apps.googleusercontent.com"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      OAuth 2.0 Client ID từ Google Cloud Console
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="client_secret"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Client Secret <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="Nhập client secret mới"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      OAuth 2.0 Client Secret. Sẽ được mã hóa khi lưu trữ.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="redirect_uri"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Redirect URI <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="url"
                        placeholder="https://your-domain.com/api/auth/callback"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      URI chuyển hướng được cấu hình trong Google Cloud Console
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex items-center gap-3 pt-2">
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                  )}
                  Cập nhật cấu hình
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    form.reset();
                    setBackendError(null);
                  }}
                  disabled={form.formState.isSubmitting}
                >
                  Đặt lại
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}

export default OAuthConfigForm;
