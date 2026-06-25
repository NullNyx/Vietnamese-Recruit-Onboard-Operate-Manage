"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, AlertCircle } from "lucide-react";

const formSchema = z.object({
  domains_text: z.string().min(1, "At least one domain is required"),
});

export default function DomainsStep({ onNext, onBack }: { onNext: () => void, onBack: () => void }) {
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      domains_text: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setError(null);
    try {
      const domainsArray = values.domains_text
        .split(/[\n,]+/)
        .map(d => d.trim().toLowerCase())
        .filter(d => d.length > 0);

      if (domainsArray.length === 0) {
        throw new Error("Please enter at least one valid domain");
      }

      const response = await fetch("/api/setup/domains", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domains: domainsArray }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || "Failed to save domains");
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
          <label className="text-sm font-medium text-foreground">Allowed Email Domains</label>
          <textarea 
            {...form.register("domains_text")}
            placeholder={"company.com\nsubsidiary.com"}
            rows={4}
            className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/60 transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
          />
          {form.formState.errors.domains_text && (
            <p className="text-xs text-destructive">{form.formState.errors.domains_text.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Enter one domain per line or separate with commas. Users with these email domains will be allowed to log into the platform.
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
          Save & Continue
        </button>
      </div>
    </form>
  );
}
