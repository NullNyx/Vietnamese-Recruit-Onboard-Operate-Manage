"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import { AlertCircle, Loader2, LockKeyhole } from "lucide-react";

import { changePassword } from "@/lib/api/auth";
import { useCurrentUser } from "@/hooks/use-current-user";

export default function ChangePasswordPage() {
  const router = useRouter();
  const { user, loading, refetch } = useCurrentUser();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (!user.must_change_password) {
      router.replace(user.role === "admin" ? "/" : "/employee/dashboard");
    }
  }, [router, user, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Mật khẩu mới không khớp");
      return;
    }
    setSubmitting(true);
    try {
      const result = await changePassword(currentPassword, newPassword);
      await refetch();
      router.replace(result.user.role === "admin" ? "/" : "/employee/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đổi mật khẩu thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4 sm:p-6">
      {/* Decorative top-right gradient */}
      <div
        className="pointer-events-none absolute -right-40 -top-40 h-80 w-80 rounded-full bg-primary/5 blur-3xl"
        aria-hidden="true"
      />

      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full max-w-sm"
      >
        {/* Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-warm">
            <LockKeyhole className="h-5 w-5 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Đổi mật khẩu
          </h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Bắt buộc đổi mật khẩu trước khi vào hệ thống
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
            {/* Current password */}
            <div className="space-y-1.5">
              <label
                htmlFor="current"
                className="text-xs font-medium text-muted-foreground"
              >
                Mật khẩu hiện tại
              </label>
              <input
                id="current"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none ring-offset-background transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
                autoComplete="current-password"
                required
              />
            </div>

            {/* New password */}
            <div className="space-y-1.5">
              <label
                htmlFor="new"
                className="text-xs font-medium text-muted-foreground"
              >
                Mật khẩu mới
              </label>
              <input
                id="new"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none ring-offset-background transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
                autoComplete="new-password"
                required
              />
            </div>

            {/* Confirm new password */}
            <div className="space-y-1.5">
              <label
                htmlFor="confirm"
                className="text-xs font-medium text-muted-foreground"
              >
                Xác nhận mật khẩu mới
              </label>
              <input
                id="confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground outline-none ring-offset-background transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
                autoComplete="new-password"
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
                "Lưu mật khẩu mới"
              )}
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
