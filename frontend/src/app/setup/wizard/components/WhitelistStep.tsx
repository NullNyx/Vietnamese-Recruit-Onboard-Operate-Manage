"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, AlertCircle } from "lucide-react";

const formSchema = z.object({
  emails_text: z.string().min(1, "At least one email is required"),
});

export default function WhitelistStep({ onNext, onBack }: { onNext: () => void, onBack: () => void }) {
  const [error, setError] = useState<string | null>(null);
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      emails_text: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setError(null);
    try {
      const emailsArray = values.emails_text
        .split(/[\n,]+/)
        .map(e => e.trim().toLowerCase())
        .filter(e => e.length > 0);

      if (emailsArray.length === 0) {
        throw new Error("Please enter at least one valid email address");
      }

      const response = await fetch("/api/setup/whitelist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emails: emailsArray }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || "Failed to save whitelist");
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
          <label className="text-sm font-medium text-foreground">Whitelist Emails</label>
          <textarea 
            {...form.register("emails_text")}
            placeholder={"admin@company.com\nuser@company.com"}
            rows={4}
            className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/60 transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20"
          />
          {form.formState.errors.emails_text && (
            <p className="text-xs text-destructive">{form.formState.errors.emails_text.message}</p>
          )}

          {(() => {
            const currentText = form.watch("emails_text");
            const firstEmail = currentText
              ? currentText.split(/[\n,]+/).map(e => e.trim()).filter(e => e.length > 0)[0]
              : null;
            
            if (firstEmail) {
              return (
                <div className="mt-3 flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3 text-sm text-primary">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <p>
                    <strong>Important Note:</strong> If the account <strong className="bg-primary/10 px-1 py-0.5 rounded">{firstEmail}</strong> is the first to successfully sign in, it will automatically be promoted to <strong>Super Admin</strong>. Subsequent accounts will be regular Users.
                  </p>
                </div>
              );
            }
            return (
              <p className="text-xs text-muted-foreground">
                Enter the email addresses (one per line) allowed to access the system.
              </p>
            );
          })()}
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
