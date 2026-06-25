"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, AlertCircle } from "lucide-react";

const formSchema = z.object({
  google_client_id: z.string().min(1, "Client ID is required"),
  google_client_secret: z.string().min(1, "Client Secret is required"),
});

export default function OAuthStep({ onNext, onBack }: { onNext: () => void, onBack: () => void }) {
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      google_client_id: "",
      google_client_secret: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setError(null);
    try {
      const response = await fetch("/api/setup/oauth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: values.google_client_id.trim(),
          client_secret: values.google_client_secret.trim(),
          redirect_uri: `${window.location.origin}/api/auth/callback`,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || "Failed to save OAuth configuration");
      }

      onNext();
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 flex flex-col flex-1">
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      <div className="space-y-4 flex-1">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Google Client ID</label>
          <input 
            type="text"
            {...form.register("google_client_id")}
            placeholder="Enter your Google Client ID"
            className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
          />
          {form.formState.errors.google_client_id && (
            <p className="text-xs text-destructive">{form.formState.errors.google_client_id.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Google Client Secret</label>
          <input 
            type="password"
            {...form.register("google_client_secret")}
            placeholder="Enter your Google Client Secret"
            className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
          />
          {form.formState.errors.google_client_secret && (
            <p className="text-xs text-destructive">{form.formState.errors.google_client_secret.message}</p>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            These credentials are required to enable "Sign in with Google" for your organization.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border pt-4 mt-8">
        <button
          type="button"
          onClick={onBack}
          disabled={form.formState.isSubmitting}
          className="px-4 py-2 text-sm font-medium border border-border rounded-md hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={form.formState.isSubmitting}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {form.formState.isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
          Continue to Test
        </button>
      </div>
    </form>
  );
}
