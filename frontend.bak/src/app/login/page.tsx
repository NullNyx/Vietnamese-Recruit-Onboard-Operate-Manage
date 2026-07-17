"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { motion } from "motion/react";
import { AlertCircle, Loader2, Moon, Sun } from "lucide-react";

import { login, getSetupStatus } from "@/lib/api/auth";
import { useCurrentUser } from "@/hooks/use-current-user";

// ── Shared ──────────────────────────────────────────────────────────────────

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button
      type="button"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="fixed right-5 top-5 z-50 flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      aria-label="Chuyển đổi giao diện"
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </button>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const router = useRouter();
  const { user, loading: userLoading, refetch } = useCurrentUser();
  const [checkingSetup, setCheckingSetup] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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
        if (!result.setup_complete) {
          router.replace("/setup");
          return;
        }
      } catch {
        if (!active) return;
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
    setSubmitting(true);
    setError(null);
    try {
      const result = await login(email, password);
      await refetch();
      if (result.must_change_password) {
        router.replace("/change-password");
        return;
      }
      router.replace(result.user.role === "admin" ? "/" : "/employee/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  // ── Loading ──

  if (checkingSetup || userLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <ThemeToggle />
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // ── Render ──

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4 sm:p-6">
      <ThemeToggle />

      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full max-w-sm"
      >
        {/* Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-warm">
            <span className="text-lg font-bold text-primary-foreground">V</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Vroom HR
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Đăng nhập vào hệ thống
          </p>
        </div>

        {/* Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-warm sm:p-8">
          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-5 flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
              role="alert"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="text-xs font-medium text-muted-foreground"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none ring-offset-background transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="name@company.com"
                autoComplete="email"
                required
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label
                htmlFor="password"
                className="text-xs font-medium text-muted-foreground"
              >
                Mật khẩu
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none ring-offset-background transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
                autoComplete="current-password"
                required
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Đăng nhập"
              )}
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
