"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AlertCircle, Check, ChevronLeft, Loader2, RefreshCw, ShieldCheck } from "lucide-react";

import { AuthApiError, getSetupStatus, setupFirstRun } from "@/lib/api/auth";
import { useCurrentUser } from "@/hooks/use-current-user";

const setupSchema = z.object({
  organizationName: z.string().trim().min(1, "Vui lòng nhập tên Organization"),
  name: z.string().trim().min(1, "Vui lòng nhập họ tên"),
  email: z.string().trim().email("Email không hợp lệ"),
  password: z.string().min(12, "Mật khẩu phải có ít nhất 12 ký tự"),
  passwordConfirmation: z.string(),
}).refine((values) => values.password === values.passwordConfirmation, {
  path: ["passwordConfirmation"],
  message: "Mật khẩu xác nhận không khớp",
});

type SetupValues = z.infer<typeof setupSchema>;
type SetupState = "checking" | "ready" | "unavailable" | "success";

const inputClass = "w-full rounded-lg border border-border bg-background px-3.5 py-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20";

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? <p id={id} role="alert" className="text-sm text-destructive">{message}</p> : null;
}

export default function SetupPage() {
  const { replace } = useRouter();
  const { user, loading: userLoading, refetch } = useCurrentUser();
  const [state, setState] = useState<SetupState>("checking");
  const [step, setStep] = useState(1);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const successHeading = useRef<HTMLHeadingElement>(null!);
  const setupSucceeded = useRef(false);

  const announcement = state === "checking" ? "Đang kiểm tra trạng thái thiết lập" : formError ?? undefined;

  const form = useForm<SetupValues>({
    resolver: zodResolver(setupSchema),
    mode: "onBlur",
    defaultValues: { organizationName: "", name: "", email: "", password: "", passwordConfirmation: "" },
  });
  const { register, handleSubmit, trigger, getValues, setError, setFocus, formState: { errors } } = form;

  const checkSetup = useCallback(async () => {
    setState("checking");
    setFormError(null);
    try {
      const result = await getSetupStatus();
      if (result.setup_complete) {
        replace("/login");
        return;
      }
      setState("ready");
    } catch {
      setState("unavailable");
      setFormError("Không thể kiểm tra trạng thái thiết lập. Vui lòng thử lại.");
    }
  }, [replace]);

  useEffect(() => { void checkSetup(); }, [checkSetup]);
  useEffect(() => {
    if (!setupSucceeded.current && !userLoading && user) {
      if (user.must_change_password) replace("/change-password");
      else replace(user.role === "admin" ? "/" : "/employee/dashboard");
    }
  }, [replace, user, userLoading]);
  useEffect(() => { if (state === "success") successHeading.current?.focus(); }, [state]);
  useEffect(() => {
    const firstField = Object.keys(errors)[0] as keyof SetupValues | undefined;
    if (firstField) setFocus(firstField);
  }, [errors, setFocus]);

  async function nextStep() {
    const valid = await trigger(step === 1 ? ["organizationName"] : ["name", "email", "password", "passwordConfirmation"]);
    if (!valid) return;
    setFormError(null);
    setStep(step + 1);
  }

  async function submit(values: SetupValues) {
    setSubmitting(true);
    setFormError(null);
    try {
      const result = await setupFirstRun(values.organizationName.trim(), values.name.trim(), values.email.trim(), values.password, values.passwordConfirmation);
      setupSucceeded.current = true;
      await refetch();
      setState("success");
      // Keep the authenticated session from the atomic setup response; dashboard navigation is explicit.
      void result;
    } catch (err) {
      if (err instanceof AuthApiError) {
        if (err.code === "AUTH_SETUP_ALREADY_COMPLETED") {
          replace("/login?setup=completed");
          return;
        }
        for (const [field, message] of Object.entries(err.fields)) {
          const name = field as keyof SetupValues;
          if (name in getValues()) setError(name, { message });
        }
        setFormError(err.message || "Thiết lập chưa hoàn tất. Vui lòng thử lại.");
      } else {
        setFormError("Thiết lập tạm thời không thành công. Vui lòng thử lại.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (state === "checking" || userLoading) return <StatusScreen message="Đang kiểm tra trạng thái thiết lập…" />;
  if (state === "unavailable") return <StatusScreen error={formError ?? undefined} action={<button type="button" onClick={() => void checkSetup()} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground"><RefreshCw className="h-4 w-4" /> Thử lại</button>} />;
  if (state === "success") return <StatusScreen success headingRef={successHeading} action={<button type="button" onClick={() => replace("/")} className="rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground">Mở dashboard</button>} />;

  const values = getValues();
  return (
    <main className="min-h-screen bg-background lg:grid lg:grid-cols-[minmax(280px,0.8fr)_minmax(480px,1.2fr)]">
      <aside className="hidden flex-col justify-between bg-foreground p-10 text-background lg:flex xl:p-16">
        <div><div className="mb-16 flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary font-semibold">V</span><span className="font-semibold tracking-wide">Vroom HR</span></div><p className="mb-4 font-mono text-xs uppercase tracking-[0.2em] text-background/60">First-Run Setup</p><h1 className="max-w-md font-serif text-5xl leading-tight">Bắt đầu một cách rõ ràng.</h1><p className="mt-6 max-w-sm text-sm leading-6 text-background/70">Xác lập Organization và tạo tài khoản HR đầu tiên cho deployment của bạn.</p></div>
        <ul className="space-y-4 text-sm text-background/75"><li className="flex gap-3"><ShieldCheck className="h-5 w-5 shrink-0 text-primary" />Dữ liệu khởi tạo được lưu nguyên tử.</li><li className="flex gap-3"><ShieldCheck className="h-5 w-5 shrink-0 text-primary" />Chỉ HR của Organization có quyền quản trị.</li><li className="flex gap-3"><ShieldCheck className="h-5 w-5 shrink-0 text-primary" />Bạn có thể cấu hình chi tiết sau.</li></ul>
      </aside>
      <section className="flex min-h-screen items-center justify-center p-5 sm:p-10"><div className="w-full max-w-xl">
        <div className="mb-8 lg:hidden"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary font-semibold text-primary-foreground">V</span><span className="font-semibold">Vroom HR</span></div></div>
        <div className="mb-8"><p className="font-mono text-xs uppercase tracking-[0.18em] text-muted-foreground">Thiết lập lần đầu</p><h2 className="mt-2 font-serif text-4xl leading-tight">Thiết lập Organization</h2><p className="mt-3 text-sm text-muted-foreground">Tạo không gian làm việc và tài khoản HR đầu tiên.</p></div>
        <div className="mb-8 flex items-center" aria-label={`Bước ${step} trên 3`}><div className="flex w-full items-center">{["Organization", "Tài khoản HR", "Xem lại"].map((label, index) => { const current = index + 1; return <div key={label} className="flex flex-1 items-center last:flex-none"><div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold ${current <= step ? "border-primary bg-primary text-primary-foreground" : "border-border text-muted-foreground"}`}>{current < step ? <Check className="h-4 w-4" /> : current}</div><span className={`ml-2 hidden text-xs sm:block ${current === step ? "font-semibold text-foreground" : "text-muted-foreground"}`}>{label}</span>{current < 3 && <div className={`mx-3 h-px flex-1 ${current < step ? "bg-primary" : "bg-border"}`} />}</div>; })}</div></div>
        <div aria-live="polite" className="sr-only">{announcement}</div>
        {formError && <div role="alert" className="mb-5 flex gap-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive"><AlertCircle className="h-5 w-5 shrink-0" /><span>{formError}</span></div>}
        <form onSubmit={handleSubmit(submit)} className="rounded-xl border border-border bg-card p-5 shadow-sm sm:p-8">
          {step === 1 && <div className="space-y-5"><div><label htmlFor="organizationName" className="mb-2 block font-mono text-xs uppercase tracking-wide">Tên Organization</label><input id="organizationName" autoFocus {...register("organizationName")} aria-invalid={!!errors.organizationName} aria-describedby="organizationName-error" className={inputClass} placeholder="Ví dụ: Công ty ABC" /><FieldError id="organizationName-error" message={errors.organizationName?.message} /></div><p className="text-sm leading-6 text-muted-foreground">Tên này sẽ xuất hiện trong các giao diện quản trị và email của Organization.</p><button type="button" onClick={() => void nextStep()} disabled={!form.watch("organizationName")?.trim()} className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50">Tiếp tục</button></div>}
          {step === 2 && <div className="space-y-5"><div><label htmlFor="name" className="mb-2 block font-mono text-xs uppercase tracking-wide">Họ tên HR</label><input id="name" autoFocus {...register("name")} aria-invalid={!!errors.name} aria-describedby="name-error" className={inputClass} placeholder="Nguyễn Văn A" /><FieldError id="name-error" message={errors.name?.message} /></div><div><label htmlFor="email" className="mb-2 block font-mono text-xs uppercase tracking-wide">Email HR</label><input id="email" type="email" autoComplete="email" {...register("email")} aria-invalid={!!errors.email} aria-describedby="email-error" className={inputClass} placeholder="hr@abc.vn" /><FieldError id="email-error" message={errors.email?.message} /></div><div><label htmlFor="password" className="mb-2 block font-mono text-xs uppercase tracking-wide">Mật khẩu</label><input id="password" type="password" autoComplete="new-password" {...register("password")} aria-invalid={!!errors.password} aria-describedby="password-hint password-error" className={inputClass} /><p id="password-hint" className="mt-2 text-xs text-muted-foreground">Ít nhất 12 ký tự</p><FieldError id="password-error" message={errors.password?.message} /></div><div><label htmlFor="passwordConfirmation" className="mb-2 block font-mono text-xs uppercase tracking-wide">Xác nhận mật khẩu</label><input id="passwordConfirmation" type="password" autoComplete="new-password" {...register("passwordConfirmation")} aria-invalid={!!errors.passwordConfirmation} aria-describedby="passwordConfirmation-error" className={inputClass} /><FieldError id="passwordConfirmation-error" message={errors.passwordConfirmation?.message} /></div><div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between"><button type="button" onClick={() => setStep(1)} className="inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-3 text-sm font-semibold hover:bg-muted"><ChevronLeft className="h-4 w-4" />Quay lại</button><button type="button" onClick={() => void nextStep()} className="rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90">Xem lại thiết lập</button></div></div>}
          {step === 3 && <div className="space-y-5"><div><p className="text-sm text-muted-foreground">Kiểm tra lại thông tin trước khi hoàn tất.</p><dl className="mt-4 divide-y divide-border rounded-lg border border-border"><div className="flex justify-between gap-4 p-4"><dt className="text-sm text-muted-foreground">Organization</dt><dd className="text-right text-sm font-semibold">{values.organizationName}</dd></div><div className="flex justify-between gap-4 p-4"><dt className="text-sm text-muted-foreground">HR</dt><dd className="text-right text-sm font-semibold">{values.name}<br /><span className="font-normal text-muted-foreground">{values.email}</span></dd></div></dl></div><div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between"><button type="button" onClick={() => setStep(2)} disabled={submitting} className="inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-3 text-sm font-semibold hover:bg-muted"><ChevronLeft className="h-4 w-4" />Quay lại</button><button type="submit" disabled={submitting} className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60">{submitting && <Loader2 className="h-4 w-4 animate-spin" />} {submitting ? "Đang thiết lập…" : "Hoàn tất thiết lập"}</button></div></div>}
        </form>
      </div></section>
    </main>
  );
}

function StatusScreen({ message, error, success, headingRef, action }: { message?: string; error?: string; success?: boolean; headingRef?: React.RefObject<HTMLHeadingElement>; action?: React.ReactNode }) {
  return <main className="flex min-h-screen items-center justify-center bg-background p-6"><div className="w-full max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-sm">{success ? <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-green-500/15 text-green-600"><Check className="h-6 w-6" /></div> : !error ? <Loader2 className="mx-auto mb-5 h-8 w-8 animate-spin text-primary" /> : <AlertCircle className="mx-auto mb-5 h-8 w-8 text-destructive" />}{success ? <h1 ref={headingRef} tabIndex={-1} className="font-serif text-3xl">Thiết lập thành công</h1> : <h1 className="font-serif text-2xl">{error ? "Không khả dụng" : "Vroom HR"}</h1>}<p role={error ? "alert" : undefined} className="mt-3 text-sm text-muted-foreground">{error ?? message ?? "Organization và tài khoản HR đã sẵn sàng."}</p>{action && <div className="mt-6">{action}</div>}</div></main>;
}
