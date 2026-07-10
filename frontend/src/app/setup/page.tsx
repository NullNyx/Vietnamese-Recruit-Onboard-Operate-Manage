"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, Loader2 } from "lucide-react";

import { AuthApiError, getSetupStatus, setupFirstRun } from "@/lib/api/auth";
import { useCurrentUser } from "@/hooks/use-current-user";

export default function SetupPage() {
  const router = useRouter();
  const { user, loading: userLoading, refetch } = useCurrentUser();
  const [checkingSetup, setCheckingSetup] = useState(true);
  const [organizationName, setOrganizationName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [statusUnavailable, setStatusUnavailable] = useState(false);

  useEffect(() => {
    if (userLoading) return;
    if (user) {
      if (user.must_change_password) {
        router.replace("/change-password");
        return;
      }
      router.replace(user.role === "admin" ? "/" : "/employee/dashboard");
    }
  }, [router, user, userLoading]);

  useEffect(() => {
    let active = true;
    async function checkSetup() {
      try {
        const result = await getSetupStatus();
        if (!active) return;
        if (result.setup_complete) {
          router.replace("/login");
          return;
        }
      } catch {
        if (!active) return;
          setStatusUnavailable(true);
          setError("Không thể kiểm tra trạng thái khởi tạo");
      } finally {
        if (active) setCheckingSetup(false);
      }
    }
    checkSetup();
    return () => {
      active = false;
    };
  }, [router]);

    async function handleSubmit(e: React.FormEvent) {
      e.preventDefault();
      if (submitting) return;
      const nextErrors: Record<string, string> = {};
      if (!organizationName.trim()) nextErrors.organization_name = "Vui lòng nhập tên Organization";
      if (!name.trim()) nextErrors.name = "Vui lòng nhập họ tên";
      if (!/^\S+@\S+\.\S+$/.test(email.trim())) nextErrors.email = "Email không hợp lệ";
      if (password.length < 12) nextErrors.password = "Mật khẩu phải có ít nhất 12 ký tự";
      if (password !== passwordConfirmation) nextErrors.password_confirmation = "Mật khẩu xác nhận không khớp";
      if (Object.keys(nextErrors).length) {
        setFieldErrors(nextErrors);
        setError("Vui lòng kiểm tra lại thông tin");
        return;
      }
      setSubmitting(true);
      setError(null);
      setFieldErrors({});
    try {
      const result = await setupFirstRun(
        organizationName,
        name,
        email,
        password,
        passwordConfirmation,
      );
      await refetch();
      router.replace(result.user.role === "admin" ? "/" : "/employee/dashboard");
      } catch (err) {
        if (err instanceof AuthApiError) {
          if (err.code === "AUTH_SETUP_ALREADY_COMPLETED") {
            router.replace("/login?setup=completed");
            return;
          }
          setFieldErrors(err.fields);
          setError(err.message);
        } else {
          setError(err instanceof Error ? err.message : "Khởi tạo thất bại");
        }
    } finally {
      setSubmitting(false);
    }
  }

    if (statusUnavailable) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p role="alert" className="text-sm text-muted-foreground">{error}</p>
          <button type="button" onClick={() => window.location.reload()} className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white">Thử lại</button>
        </div>
      );
    }

    if (checkingSetup || userLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm space-y-6">
        <div className="space-y-2 text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-white">V</span>
          </div>
          <h1 className="text-2xl font-semibold text-foreground">First-Run Setup</h1>
          <p className="text-sm text-muted-foreground">Tạo HR account đầu tiên</p>
        </div>

          {error && (
            <div role="alert" className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p>{error}</p>
                {Object.entries(fieldErrors).map(([field, message]) => (
                  <p key={field} className="mt-1">{message}</p>
                ))}
              </div>
            </div>
          )}

        <form className="space-y-4 rounded-lg border border-border bg-card p-6" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label htmlFor="organizationName" className="text-xs font-medium text-muted-foreground">
              Tên Organization
            </label>
            <input
              id="organizationName"
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
              required
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="name" className="text-xs font-medium text-muted-foreground">
              Họ tên
            </label>
            <input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
              required
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="email" className="text-xs font-medium text-muted-foreground">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
              required
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="password" className="text-xs font-medium text-muted-foreground">
              Mật khẩu
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
              autoComplete="new-password"
              required
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="passwordConfirmation" className="text-xs font-medium text-muted-foreground">
              Xác nhận mật khẩu
            </label>
            <input
              id="passwordConfirmation"
              type="password"
              value={passwordConfirmation}
              onChange={(e) => setPasswordConfirmation(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-primary/50 focus:ring-1 focus:ring-primary/20"
              autoComplete="new-password"
              required
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Tạo HR account"}
          </button>
        </form>
      </div>
    </div>
  );
}
