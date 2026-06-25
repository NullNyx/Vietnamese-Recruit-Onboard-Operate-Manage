"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, AlertCircle } from "lucide-react";

const formSchema = z.object({
  timezone: z.string().min(1, "Timezone is required"),
});

export default function OrganizationStep({ onNext, onBack }: { onNext: () => void, onBack: () => void }) {
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      timezone: "Asia/Ho_Chi_Minh",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setError(null);
    try {
      const response = await fetch("/api/setup/organization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || "Failed to save organization settings");
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
          <label className="text-sm font-medium text-foreground">Default Timezone</label>
          <select 
            {...form.register("timezone")}
            className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
          >
            <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (Vietnam Time)</option>
            <option value="UTC">UTC</option>
            <option value="America/New_York">America/New_York (Eastern Time)</option>
            <option value="America/Los_Angeles">America/Los_Angeles (Pacific Time)</option>
          </select>
          {form.formState.errors.timezone && (
            <p className="text-xs text-destructive">{form.formState.errors.timezone.message}</p>
          )}
          <p className="text-xs text-muted-foreground">This timezone will be used as the default for the entire organization (e.g. for attendances).</p>
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
          Save & Continue
        </button>
      </div>
    </form>
  );
}
