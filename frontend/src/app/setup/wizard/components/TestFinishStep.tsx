"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function TestFinishStep({ onBack }: { onBack: () => void }) {
  const [testState, setTestState] = useState<"idle" | "polling" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [locking, setLocking] = useState(false);
  const popupRef = useRef<Window | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const router = useRouter();

  const handleTestLogin = () => {
    setTestState("polling");
    setError(null);
    
    // Open a popup for the login flow
    const width = 500;
    const height = 600;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;
    
    popupRef.current = window.open(
      "/api/auth/login",
      "TestGoogleLogin",
      `width=${width},height=${height},left=${left},top=${top},status=yes,scrollbars=yes`
    );

    // Start polling to check if user got the auth cookie
    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch("/api/auth/me");
        if (res.ok) {
          // Success!
          setTestState("success");
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          if (popupRef.current) popupRef.current.close();
        } else if (popupRef.current && popupRef.current.closed) {
          // User closed popup without finishing login
          if (testState !== "success") {
            setTestState("error");
            setError("Login window was closed before completion.");
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          }
        }
      } catch (err) {
        // Just keep polling
      }
    }, 2000);
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const handleLockSetup = async () => {
    setLocking(true);
    setError(null);
    try {
      const response = await fetch("/api/setup/lock", {
        method: "POST",
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || "Failed to lock setup");
      }

      // Setup is finished! Redirect to dashboard or home
      router.push("/");
    } catch (err: any) {
      setError(err.message);
      setLocking(false);
    }
  };

  return (
    <div className="space-y-6 flex flex-col flex-1">
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      <div className="space-y-4 flex-1">
        <p className="text-sm text-foreground">
          You have configured all necessary parameters. To ensure the system is usable, please perform a test login using the newly configured Google OAuth credentials. 
          This will also verify that your email is correctly whitelisted.
        </p>

        {testState === "idle" && (
          <div className="pt-4 flex justify-center">
            <button
              type="button"
              onClick={handleTestLogin}
              className="px-6 py-3 text-sm font-medium bg-secondary text-secondary-foreground border border-border rounded-md hover:bg-secondary/80 transition-colors"
            >
              Test Login with Google
            </button>
          </div>
        )}

        {testState === "polling" && (
          <div className="pt-4 flex flex-col items-center gap-3 text-sm text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p>Waiting for login completion in popup window...</p>
          </div>
        )}

        {testState === "success" && (
          <div className="pt-4 flex flex-col items-center gap-3 text-sm text-green-600 dark:text-green-500">
            <CheckCircle2 className="h-8 w-8" />
            <p className="font-medium text-base">Test Login Successful!</p>
            <p className="text-muted-foreground text-center">
              Your OAuth configuration and whitelist are working perfectly. You can now finalize the setup. 
              Once finalized, the system will be locked and ready for use.
            </p>
          </div>
        )}
        
        {testState === "error" && (
           <div className="pt-4 flex justify-center">
             <button
               type="button"
               onClick={handleTestLogin}
               className="px-6 py-3 text-sm font-medium bg-secondary text-secondary-foreground border border-border rounded-md hover:bg-secondary/80 transition-colors"
             >
               Retry Test Login
             </button>
           </div>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-border pt-4 mt-8">
        <button
          type="button"
          onClick={onBack}
          disabled={locking || testState === "polling"}
          className="px-4 py-2 text-sm font-medium border border-border rounded-md hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleLockSetup}
          disabled={locking || testState !== "success"}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {locking && <Loader2 className="h-4 w-4 animate-spin" />}
          Lock & Finish Setup
        </button>
      </div>
    </div>
  );
}
