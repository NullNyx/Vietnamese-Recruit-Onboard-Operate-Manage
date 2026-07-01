"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, AlertCircle } from "lucide-react";

// ─── Google Icon ────────────────────────────────────────────────────────────
function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

// ─── Login Content (uses useSearchParams, must be in Suspense) ──────────────
function LoginContent() {
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogin = () => {
    setLoading(true);
    window.location.href = "/api/auth/login";
  };

  return (
    <div
      className={`flex w-full items-center justify-center p-6 sm:p-8 transition-all duration-700 ${
        mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
    >
      <div className="w-full max-w-[400px] space-y-8">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-white">V</span>
          </div>
          <span className="text-sm font-semibold text-foreground">
            Vroom HR
          </span>
        </div>

        {/* Error Alert */}
        {error === "DOMAIN_NOT_ALLOWED" && (
          <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <AlertCircle className="mt-0.5 h-4 w-4 text-destructive shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-destructive">Tên miền chưa được ủy quyền</p>
              <p className="mt-1 text-destructive/80">
                Email domain của bạn chưa được phép đăng nhập. Liên hệ quản trị viên HR để được hỗ trợ.
              </p>
            </div>
          </div>
        )}
        {error === "AUTH_ACCESS_DENIED" && (
          <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <AlertCircle className="mt-0.5 h-4 w-4 text-destructive shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-destructive">Truy cập bị từ chối</p>
              <p className="mt-1 text-destructive/80">
                Tài khoản của bạn chưa được phép đăng nhập. Liên hệ quản trị viên HR.
              </p>
            </div>
          </div>
        )}

        {/* Login header */}
        <div className="space-y-2 text-center">
          <h2 className="text-2xl font-semibold tracking-[-0.3px] text-foreground">
            Đăng nhập vào Workspace
          </h2>
          <p className="text-sm text-muted-foreground">
            Truy cập hệ thống quản lý nhân sự của tổ chức
          </p>
        </div>

        {/* Login card */}
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="space-y-6">
            {/* Google OAuth Button — Primary */}
            <button
              onClick={handleLogin}
              disabled={loading}
              className="flex w-full items-center justify-center gap-3 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-60 disabled:cursor-not-allowed"
              aria-label="Đăng nhập bằng Google"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <GoogleIcon />
              )}
              <span>
                {loading ? "Đang kết nối..." : "Đăng nhập bằng Google"}
              </span>
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-[10px] text-muted-foreground">hoặc</span>
              <div className="h-px flex-1 bg-border" />
            </div>

            {/* Email/Password form */}
            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
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
                  placeholder="name@company.com"
                  className="w-full rounded-lg border border-border bg-card px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/60 transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
                  disabled
                />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="password"
                    className="text-xs font-medium text-muted-foreground"
                  >
                    Mật khẩu
                  </label>
                  <button
                    type="button"
                    className="text-[10px] text-muted-foreground hover:text-primary transition-colors"
                    disabled
                  >
                    Quên mật khẩu?
                  </button>
                </div>
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-border bg-card px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/60 transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
                  disabled
                />
              </div>

              {/* Remember me */}
              <div className="flex items-center gap-2">
                <input
                  id="remember"
                  type="checkbox"
                  className="h-3.5 w-3.5 rounded border-border bg-card"
                  disabled
                />
                <label
                  htmlFor="remember"
                  className="text-xs text-muted-foreground"
                >
                  Ghi nhớ phiên đăng nhập
                </label>
              </div>

              {/* Email login button */}
              <button
                type="submit"
                disabled
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm font-medium text-muted-foreground cursor-not-allowed transition-colors"
              >
                Đăng nhập bằng Email
              </button>
            </form>

            {/* Note */}
            <p className="text-center text-[10px] text-muted-foreground leading-relaxed">
              Hiện tại hỗ trợ Google Workspace. Email/Password sẽ available
              trong phiên bản tiếp theo.
            </p>
          </div>
        </div>

        {/* Bottom trust */}
        <p className="text-center text-[10px] text-muted-foreground leading-relaxed">
          Đăng nhập đồng nghĩa bạn đồng ý với{" "}
          <span className="text-foreground hover:text-primary cursor-pointer transition-colors">
            Điều khoản sử dụng
          </span>{" "}
          và{" "}
          <span className="text-foreground hover:text-primary cursor-pointer transition-colors">
            Chính sách bảo mật
          </span>
        </p>
      </div>
    </div>
  );
}

// ─── Setup check ────────────────────────────────────────────────────────────

async function checkSetupRequired(): Promise<boolean> {
  try {
    const res = await fetch("/api/setup/status");
    if (!res.ok) return false;
    const status = await res.json();
    return !status.is_locked;
  } catch {
    return false;
  }
}

// ─── Main Login Page ────────────────────────────────────────────────────────
export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background overflow-hidden">
      <Suspense
        fallback={
          <div className="flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        }
      >
        <LoginContentWithCheck />
      </Suspense>
    </div>
  );
}

function LoginContentWithCheck() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function check() {
      const needsSetup = await checkSetupRequired();
      if (needsSetup) {
        router.replace("/setup");
        return;
      }
      setChecking(false);
    }
    check();
  }, [router]);

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return <LoginContent />;
}
