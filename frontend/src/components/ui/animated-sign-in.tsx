"use client";

import React, { useState, useEffect } from "react";
import { Loader2, Moon, Sun } from "lucide-react";

// Google Icon
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

const AnimatedSignIn: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setIsDarkMode(prefersDark);
    if (prefersDark) {
      document.documentElement.classList.add("dark");
    }
  }, []);

  const handleLogin = () => {
    setLoading(true);
    window.location.href = "/api/auth/login";
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle("dark");
  };

  // Create particles
  useEffect(() => {
    if (!mounted) return;
    const canvas = document.getElementById("particles") as HTMLCanvasElement;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const setCanvasSize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    setCanvasSize();
    window.addEventListener("resize", setCanvasSize);

    class Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      color: string;

      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 3 + 1;
        this.speedX = (Math.random() - 0.5) * 0.5;
        this.speedY = (Math.random() - 0.5) * 0.5;
        this.color = isDarkMode
          ? `rgba(255, 255, 255, ${Math.random() * 0.3})`
          : `rgba(184, 66, 46, ${Math.random() * 0.3})`;
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;

        if (this.x > canvas.width) this.x = 0;
        if (this.x < 0) this.x = canvas.width;
        if (this.y > canvas.height) this.y = 0;
        if (this.y < 0) this.y = canvas.height;
      }

      draw() {
        if (!ctx) return;
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    const particles: Particle[] = [];
    const particleCount = Math.min(
      100,
      Math.floor((canvas.width * canvas.height) / 15000)
    );

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }

    let animationId: number;
    const animate = () => {
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const particle of particles) {
        particle.update();
        particle.draw();
      }

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", setCanvasSize);
      cancelAnimationFrame(animationId);
    };
  }, [isDarkMode, mounted]);

  if (!mounted) return null;

  return (
    <div
      className={`relative min-h-screen w-full flex items-center justify-center overflow-hidden transition-colors duration-500 ${
        isDarkMode ? "bg-slate-950 text-slate-50" : "bg-[#F7F5F2] text-slate-900"
      }`}
    >
      <canvas
        id="particles"
        className="absolute inset-0 z-0 pointer-events-none"
      ></canvas>

      <button
        onClick={toggleDarkMode}
        className="absolute top-6 right-6 z-20 p-2.5 rounded-full bg-slate-200/50 dark:bg-slate-800/50 hover:bg-slate-300/50 dark:hover:bg-slate-700/50 backdrop-blur-md transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-[#B8422E]/50"
        aria-label="Toggle dark mode"
      >
        {isDarkMode ? (
          <Sun size={20} className="text-yellow-400" />
        ) : (
          <Moon size={20} className="text-slate-700" />
        )}
      </button>

      <div
        className={`relative z-10 w-full max-w-[420px] p-8 m-4 rounded-2xl backdrop-blur-xl border shadow-2xl transition-all duration-700 ${
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        } ${
          isDarkMode
            ? "bg-slate-900/80 border-slate-800"
            : "bg-white/80 border-slate-200 shadow-slate-200/50"
        }`}
      >
        {/* Header with Logo */}
        <div className="flex flex-col items-center justify-center gap-3 mb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#B8422E] shadow-lg shadow-[#B8422E]/30">
              <span className="text-[18px] font-bold text-white">V</span>
            </div>
            <span className="text-2xl font-bold tracking-tight">Vroom HR</span>
          </div>
          <div className="text-center mt-3">
            <h2 className="text-xl font-semibold">Đăng nhập Workspace</h2>
            <p
              className={`text-[13px] mt-1.5 ${
                isDarkMode ? "text-slate-400" : "text-slate-500"
              }`}
            >
              Truy cập hệ thống quản lý nhân sự của tổ chức
            </p>
          </div>
        </div>

        <div className="space-y-7">
          {/* Main Action: Google Auth */}
          <button
            onClick={handleLogin}
            disabled={loading}
            className="flex w-full items-center justify-center gap-3 rounded-xl bg-[#B8422E] px-4 py-3.5 text-[15px] font-semibold text-white transition-all hover:bg-[#9C3726] hover:shadow-lg hover:shadow-[#B8422E]/30 focus:outline-none focus:ring-2 focus:ring-[#B8422E]/50 focus:ring-offset-2 disabled:opacity-70 disabled:cursor-not-allowed transform active:scale-[0.98]"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <GoogleIcon />}
            <span>{loading ? "Đang kết nối..." : "Đăng nhập bằng Google"}</span>
          </button>

          {/* Divider */}
          <div className="relative flex items-center py-2">
            <div
              className={`flex-grow border-t ${
                isDarkMode ? "border-slate-800" : "border-slate-200"
              }`}
            ></div>
            <span
              className={`flex-shrink-0 mx-4 text-[11px] uppercase tracking-wider font-medium ${
                isDarkMode ? "text-slate-500" : "text-slate-400"
              }`}
            >
              Hoặc đăng nhập với Email
            </span>
            <div
              className={`flex-grow border-t ${
                isDarkMode ? "border-slate-800" : "border-slate-200"
              }`}
            ></div>
          </div>

          {/* Email/Password Form (Disabled) */}
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            <div className="relative group">
              <input
                type="email"
                id="email"
                className={`peer w-full bg-transparent border-b-2 px-1 py-2 text-[14px] outline-none transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                  isDarkMode
                    ? "border-slate-700 focus:border-[#B8422E] text-slate-300"
                    : "border-slate-300 focus:border-[#B8422E] text-slate-700"
                }`}
                placeholder=" "
                disabled
              />
              <label
                htmlFor="email"
                className={`absolute left-1 top-2.5 cursor-text transition-all duration-300 peer-focus:-top-4 peer-focus:text-[11px] peer-focus:font-medium peer-focus:text-[#B8422E] peer-not-placeholder-shown:-top-4 peer-not-placeholder-shown:text-[11px] peer-not-placeholder-shown:font-medium ${
                  isDarkMode ? "text-slate-500" : "text-slate-400"
                }`}
              >
                Địa chỉ Email
              </label>
            </div>

            <div className="relative group">
              <input
                type="password"
                id="password"
                className={`peer w-full bg-transparent border-b-2 px-1 py-2 text-[14px] outline-none transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                  isDarkMode
                    ? "border-slate-700 focus:border-[#B8422E] text-slate-300"
                    : "border-slate-300 focus:border-[#B8422E] text-slate-700"
                }`}
                placeholder=" "
                disabled
              />
              <label
                htmlFor="password"
                className={`absolute left-1 top-2.5 cursor-text transition-all duration-300 peer-focus:-top-4 peer-focus:text-[11px] peer-focus:font-medium peer-focus:text-[#B8422E] peer-not-placeholder-shown:-top-4 peer-not-placeholder-shown:text-[11px] peer-not-placeholder-shown:font-medium ${
                  isDarkMode ? "text-slate-500" : "text-slate-400"
                }`}
              >
                Mật khẩu
              </label>
            </div>

            <button
              type="submit"
              disabled
              className={`w-full rounded-xl px-4 py-3.5 text-[14px] font-medium transition-colors cursor-not-allowed ${
                isDarkMode
                  ? "bg-slate-800/50 text-slate-500 border border-slate-800"
                  : "bg-slate-100 text-slate-400 border border-slate-200"
              }`}
            >
              Đăng nhập bằng Email (Sắp ra mắt)
            </button>
          </form>

          <p
            className={`text-center text-[12px] leading-relaxed mt-4 ${
              isDarkMode ? "text-slate-500" : "text-slate-400"
            }`}
          >
            Bằng việc đăng nhập, bạn đồng ý với{" "}
            <a href="#" className="hover:text-[#B8422E] transition-colors">
              Điều khoản
            </a>{" "}
            và{" "}
            <a href="#" className="hover:text-[#B8422E] transition-colors">
              Chính sách
            </a>{" "}
            của chúng tôi.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AnimatedSignIn;
