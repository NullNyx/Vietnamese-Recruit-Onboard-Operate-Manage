"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, AlertCircle } from "lucide-react";

export default function SetupPage() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/setup/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: token.trim() }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || "Invalid setup token");
      }

      // Success, move to the wizard
      router.push("/setup/wizard");
    } catch (error) {
      const err = error as Error;
      setError(err.message || "Failed to verify token");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background overflow-hidden">
      <div className="flex w-full items-center justify-center p-6 sm:p-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="w-full max-w-[400px] space-y-8">
          <div className="flex items-center justify-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <span className="text-sm font-bold text-white">V</span>
            </div>
            <span className="text-sm font-semibold text-foreground">
              Vroom HR Setup
            </span>
          </div>

          <div className="space-y-2 text-center">
            <h2 className="text-2xl font-semibold tracking-[-0.3px] text-foreground">
              First-Run Setup
            </h2>
            <p className="text-sm text-muted-foreground">
              Enter the setup token from your server console to begin initialization.
            </p>
          </div>

          {error && (
            <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
              <AlertCircle className="mt-0.5 h-4 w-4 text-destructive shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-destructive">Verification Failed</p>
                <p className="mt-1 text-destructive/80">{error}</p>
              </div>
            </div>
          )}

          <div className="rounded-lg border border-border bg-card p-6">
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="space-y-1.5">
                <label
                  htmlFor="token"
                  className="text-xs font-medium text-muted-foreground"
                >
                  Setup Token
                </label>
                <input
                  id="token"
                  type="password"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste your token here"
                  className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/60 transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
                  required
                  autoFocus
                />
              </div>

              <button
                type="submit"
                disabled={loading || !token.trim()}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "Verifying..." : "Verify Token"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
