"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

function GoogleIcon() {
  return (
    <svg
      className="mr-2 h-5 w-5"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
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

export default function LoginPage() {
  const handleLogin = () => {
    window.location.href = "/api/auth/login";
  };

  return (
    <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden px-4">
      {/* Atmospheric gradient mesh background */}
      <div
        className="absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: `
            radial-gradient(ellipse at 20% 50%, hsl(168 65% 28% / 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, hsl(168 50% 40% / 0.12) 0%, transparent 40%),
            radial-gradient(ellipse at 60% 80%, hsl(35 90% 52% / 0.08) 0%, transparent 45%),
            radial-gradient(ellipse at 40% 30%, hsl(180 30% 60% / 0.1) 0%, transparent 35%),
            linear-gradient(to bottom, hsl(0 0% 99%), hsl(180 10% 96%))
          `,
        }}
      />
      {/* Dark mode background overlay */}
      <div
        className="absolute inset-0 -z-10 hidden dark:block"
        aria-hidden="true"
        style={{
          background: `
            radial-gradient(ellipse at 30% 50%, hsl(168 55% 45% / 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 30%, hsl(200 60% 30% / 0.06) 0%, transparent 40%),
            radial-gradient(ellipse at 50% 70%, hsl(168 40% 35% / 0.05) 0%, transparent 45%),
            linear-gradient(to bottom, hsl(210 20% 8%), hsl(210 22% 6%))
          `,
        }}
      />

      {/* Centered login card */}
      <Card className="w-full max-w-sm border-border/50 shadow-lg backdrop-blur-sm">
        <CardContent className="flex flex-col items-center space-y-6 p-8">
          {/* Logo */}
          <div
            className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground opacity-0 animate-fade-in"
            style={{ animationDelay: "0ms", animationDuration: "400ms" }}
          >
            <span className="text-2xl font-bold">V</span>
          </div>

          {/* Heading */}
          <h1
            className="font-heading text-2xl font-bold tracking-tight text-foreground opacity-0 animate-fade-in"
            style={{ animationDelay: "100ms", animationDuration: "400ms" }}
          >
            Vroom HR
          </h1>

          {/* Tagline */}
          <p
            className="text-center text-sm text-muted-foreground opacity-0 animate-fade-in"
            style={{ animationDelay: "200ms", animationDuration: "400ms" }}
          >
            Hệ thống quản lý nhân sự thông minh
          </p>

          {/* Google OAuth Button */}
          <Button
            onClick={handleLogin}
            size="lg"
            className="w-full bg-[#4285F4] text-white hover:bg-[#3367D6] opacity-0 animate-fade-in"
            style={{ animationDelay: "300ms", animationDuration: "400ms" }}
            aria-label="Đăng nhập bằng Google"
          >
            <GoogleIcon />
            Đăng nhập bằng Google
          </Button>

          {/* Consent Notice */}
          <p
            className="text-center text-xs text-muted-foreground opacity-0 animate-fade-in"
            style={{ animationDelay: "400ms", animationDuration: "400ms" }}
          >
            Đăng nhập đồng nghĩa bạn cho phép truy cập Gmail và Google
            Calendar.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
