"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { motion } from "motion/react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  AlertCircle,
  Check,
  ChevronLeft,
  Loader2,
  Moon,
  RefreshCw,
  ShieldCheck,
  Sun,
} from "lucide-react";

import { AuthApiError, getSetupStatus, setupFirstRun } from "@/lib/api/auth";
import { useCurrentUser } from "@/hooks/use-current-user";

// ── Shared ──────────────────────────────────────────────────────────────────

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button
      type="button"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="fixed right-5 top-5 z-50 flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      aria-label="Chuyển đổi giao diện"
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </button>
  );
}

// ── Form schema ─────────────────────────────────────────────────────────────

const setupSchema = z
  .object({
    organizationName: z.string().trim().min(1, "Vui lòng nhập tên Organization"),
    name: z.string().trim().min(1, "Vui lòng nhập họ tên"),
    email: z.string().trim().email("Email không hợp lệ"),
    password: z.string().min(12, "Mật khẩu phải có ít nhất 12 ký tự"),
    passwordConfirmation: z.string(),
  })
  .refine((values) => values.password === values.passwordConfirmation, {
    path: ["passwordConfirmation"],
    message: "Mật khẩu xác nhận không khớp",
  });

type SetupValues = z.infer<typeof setupSchema>;
type SetupState = "checking" | "ready" | "unavailable" | "success";

const inputClass =
  "w-full rounded-lg border border-border bg-background px-3.5 py-3 text-sm text-foreground outline-none ring-offset-background transition-all placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/20";

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? (
    <p id={id} role="alert" className="text-sm text-destructive">
      {message}
    </p>
  ) : null;
}

// ── Status screen ───────────────────────────────────────────────────────────

function StatusScreen({
  message,
  error,
  success,
  headingRef,
  action,
}: {
  message?: string;
  error?: string;
  success?: boolean;
  headingRef?: React.Ref<HTMLHeadingElement>;
  action?: React.ReactNode;
}) {
  return (
    <main className="relative flex min-h-screen items-center justify-center bg-background p-6">
      <ThemeToggle />
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="w-full max-w-md"
      >
        <div className="rounded-xl border border-border bg-card p-8 text-center shadow-warm">
          {success ? (
            <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-success/15 text-success">
              <Check className="h-6 w-6" />
            </div>
          ) : !error ? (
            <Loader2 className="mx-auto mb-5 h-8 w-8 animate-spin text-primary" />
          ) : (
            <AlertCircle className="mx-auto mb-5 h-8 w-8 text-destructive" />
          )}

          {success ? (
            <h1
              ref={headingRef}
              tabIndex={-1}
              className="text-3xl font-semibold tracking-tight text-foreground"
            >
              Thiết lập thành công
            </h1>
          ) : (
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              {error ? "Không khả dụng" : "Vroom HR"}
            </h1>
          )}

          <p
            role={error ? "alert" : undefined}
            className="mt-3 text-sm text-muted-foreground"
          >
            {error ?? message ?? "Organization và tài khoản HR đã sẵn sàng."}
          </p>

          {action && <div className="mt-6">{action}</div>}
        </div>
      </motion.div>
    </main>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function SetupPage() {
  const { replace } = useRouter();
  const { user, loading: userLoading, refetch } = useCurrentUser();
  const [state, setState] = useState<SetupState>("checking");
  const [step, setStep] = useState(1);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const successHeading = useRef<HTMLHeadingElement>(null!);
  const setupSucceeded = useRef(false);

  const announcement =
    state === "checking"
      ? "Đang kiểm tra trạng thái thiết lập"
      : formError ?? undefined;

  const form = useForm<SetupValues>({
    resolver: zodResolver(setupSchema),
    mode: "onBlur",
    defaultValues: {
      organizationName: "",
      name: "",
      email: "",
      password: "",
      passwordConfirmation: "",
    },
  });
  const {
    register,
    handleSubmit,
    trigger,
    getValues,
    setError,
    setFocus,
    formState: { errors },
  } = form;

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

  useEffect(() => {
    void checkSetup();
  }, [checkSetup]);

  useEffect(() => {
    if (!setupSucceeded.current && !userLoading && user) {
      if (user.must_change_password) replace("/change-password");
      else replace(user.role === "admin" ? "/" : "/employee/dashboard");
    }
  }, [replace, user, userLoading]);

  useEffect(() => {
    if (state === "success") successHeading.current?.focus();
  }, [state]);

  useEffect(() => {
    const firstField = Object.keys(errors)[0] as keyof SetupValues | undefined;
    if (firstField) setFocus(firstField);
  }, [errors, setFocus]);

  async function nextStep() {
    const valid = await trigger(
      step === 1
        ? ["organizationName"]
        : ["name", "email", "password", "passwordConfirmation"],
    );
    if (!valid) return;
    setFormError(null);
    setStep(step + 1);
  }

  async function submit(values: SetupValues) {
    setSubmitting(true);
    setFormError(null);
    try {
      const result = await setupFirstRun(
        values.organizationName.trim(),
        values.name.trim(),
        values.email.trim(),
        values.password,
        values.passwordConfirmation,
      );
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
        const fieldNames: Record<string, keyof SetupValues> = {
          organization_name: "organizationName",
          name: "name",
          email: "email",
          password: "password",
          password_confirmation: "passwordConfirmation",
        };
        for (const [field, message] of Object.entries(err.fields)) {
          const name = fieldNames[field];
          if (name) setError(name, { message });
        }
        setFormError(
          err.message || "Thiết lập chưa hoàn tất. Vui lòng thử lại.",
        );
      } else {
        setFormError("Thiết lập tạm thời không thành công. Vui lòng thử lại.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  // ── Status screens ──

  if (state === "checking" || userLoading)
    return <StatusScreen message="Đang kiểm tra trạng thái thiết lập…" />;

  if (state === "unavailable")
    return (
      <StatusScreen
        error={formError ?? undefined}
        action={
          <button
            type="button"
            onClick={() => void checkSetup()}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <RefreshCw className="h-4 w-4" />
            Thử lại
          </button>
        }
      />
    );

  if (state === "success")
    return (
      <StatusScreen
        success
        headingRef={successHeading}
        action={
          <button
            type="button"
            onClick={() => replace("/")}
            className="rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Mở dashboard
          </button>
        }
      />
    );

  // ── Form ──

  const values = getValues();

  const steps = [
    { label: "Organization" },
    { label: "Tài khoản HR" },
    { label: "Xem lại" },
  ];

  return (
    <main className="relative min-h-screen bg-background lg:grid lg:grid-cols-[minmax(280px,0.8fr)_minmax(480px,1.2fr)]">
      <ThemeToggle />

      {/* ── Hero sidebar ── */}
      <aside className="hidden flex-col justify-between bg-foreground p-10 text-background lg:flex xl:p-16">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        >
          {/* Logo */}
          <div className="mb-16 flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary font-bold shadow-warm">
              V
            </span>
            <span className="font-semibold tracking-wide">Vroom HR</span>
          </div>

          {/* Label */}
          <p className="mb-4 font-mono text-xs uppercase tracking-[0.2em] text-background/60">
            First-Run Setup
          </p>

          {/* Headline */}
          <h1 className="max-w-md text-5xl leading-tight">
            Bắt đầu một cách rõ ràng.
          </h1>
          <p className="mt-6 max-w-sm text-sm leading-6 text-background/70">
            Xác lập Organization và tạo tài khoản HR đầu tiên cho deployment của
            bạn.
          </p>
        </motion.div>

        {/* Trust markers */}
        <motion.ul
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="space-y-4 text-sm text-background/75"
        >
          <li className="flex gap-3">
            <ShieldCheck className="h-5 w-5 shrink-0 text-primary" />
            Dữ liệu khởi tạo được lưu nguyên tử.
          </li>
          <li className="flex gap-3">
            <ShieldCheck className="h-5 w-5 shrink-0 text-primary" />
            Chỉ HR của Organization có quyền quản trị.
          </li>
          <li className="flex gap-3">
            <ShieldCheck className="h-5 w-5 shrink-0 text-primary" />
            Bạn có thể cấu hình chi tiết sau.
          </li>
        </motion.ul>
      </aside>

      {/* ── Form panel ── */}
      <section className="flex min-h-screen items-center justify-center p-5 sm:p-10">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="w-full max-w-xl"
        >
          {/* Mobile logo */}
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary font-bold text-primary-foreground">
                V
              </span>
              <span className="font-semibold text-foreground">Vroom HR</span>
            </div>
          </div>

          {/* Header */}
          <div className="mb-8">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted-foreground">
              Thiết lập lần đầu
            </p>
            <h2 className="mt-2 text-4xl leading-tight text-foreground">
              Thiết lập Organization
            </h2>
            <p className="mt-3 text-sm text-muted-foreground">
              Tạo không gian làm việc và tài khoản HR đầu tiên.
            </p>
          </div>

          {/* Stepper */}
          <div className="mb-8 flex items-center" aria-label={`Bước ${step} trên 3`}>
            <div className="flex w-full items-center">
              {steps.map((s, index) => {
                const current = index + 1;
                const isActive = current <= step;
                const isCurrent = current === step;
                return (
                  <div
                    key={s.label}
                    className="flex flex-1 items-center last:flex-none"
                  >
                    {/* Step circle */}
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold transition-colors ${
                        isActive
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border text-muted-foreground"
                      }`}
                    >
                      {current < step ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        current
                      )}
                    </div>
                    {/* Label */}
                    <span
                      className={`ml-2 hidden text-xs sm:block ${
                        isCurrent
                          ? "font-semibold text-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      {s.label}
                    </span>
                    {/* Connector line */}
                    {current < 3 && (
                      <div
                        className={`mx-3 h-px flex-1 transition-colors ${
                          current < step ? "bg-primary" : "bg-border"
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Screen reader announcement */}
          <div aria-live="polite" className="sr-only">
            {announcement}
          </div>

          {/* Form error */}
          {formError && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              role="alert"
              className="mb-5 flex gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
            >
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{formError}</span>
            </motion.div>
          )}

          {/* ── Form card ── */}
          <form
            onSubmit={handleSubmit(submit)}
            className="rounded-xl border border-border bg-card p-5 shadow-warm sm:p-8"
          >
            {/* Step 1 — Organization */}
            {step === 1 && (
              <motion.div
                initial={{ opacity: 0, x: 4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-5"
              >
                <div>
                  <label
                    htmlFor="organizationName"
                    className="mb-2 block font-mono text-xs uppercase tracking-wide text-muted-foreground"
                  >
                    Tên Organization
                  </label>
                  <input
                    id="organizationName"
                    autoFocus
                    {...register("organizationName")}
                    aria-invalid={!!errors.organizationName}
                    aria-describedby="organizationName-error"
                    className={inputClass}
                    placeholder="Ví dụ: Công ty ABC"
                  />
                  <FieldError
                    id="organizationName-error"
                    message={errors.organizationName?.message}
                  />
                </div>

                <p className="text-sm leading-6 text-muted-foreground">
                  Tên này sẽ xuất hiện trong các giao diện quản trị và email của
                  Organization.
                </p>

                <button
                  type="button"
                  onClick={() => void nextStep()}
                  disabled={!form.watch("organizationName")?.trim()}
                  className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Tiếp tục
                </button>
              </motion.div>
            )}

            {/* Step 2 — HR Account */}
            {step === 2 && (
              <motion.div
                initial={{ opacity: 0, x: 4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-5"
              >
                <div>
                  <label
                    htmlFor="name"
                    className="mb-2 block font-mono text-xs uppercase tracking-wide text-muted-foreground"
                  >
                    Họ tên HR
                  </label>
                  <input
                    id="name"
                    autoFocus
                    {...register("name")}
                    aria-invalid={!!errors.name}
                    aria-describedby="name-error"
                    className={inputClass}
                    placeholder="Nguyễn Văn A"
                  />
                  <FieldError
                    id="name-error"
                    message={errors.name?.message}
                  />
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="mb-2 block font-mono text-xs uppercase tracking-wide text-muted-foreground"
                  >
                    Email HR
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    {...register("email")}
                    aria-invalid={!!errors.email}
                    aria-describedby="email-error"
                    className={inputClass}
                    placeholder="hr@abc.vn"
                  />
                  <FieldError
                    id="email-error"
                    message={errors.email?.message}
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="mb-2 block font-mono text-xs uppercase tracking-wide text-muted-foreground"
                  >
                    Mật khẩu
                  </label>
                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    {...register("password")}
                    aria-invalid={!!errors.password}
                    aria-describedby="password-hint password-error"
                    className={inputClass}
                  />
                  <p
                    id="password-hint"
                    className="mt-2 text-xs text-muted-foreground"
                  >
                    Ít nhất 12 ký tự
                  </p>
                  <FieldError
                    id="password-error"
                    message={errors.password?.message}
                  />
                </div>

                <div>
                  <label
                    htmlFor="passwordConfirmation"
                    className="mb-2 block font-mono text-xs uppercase tracking-wide text-muted-foreground"
                  >
                    Xác nhận mật khẩu
                  </label>
                  <input
                    id="passwordConfirmation"
                    type="password"
                    autoComplete="new-password"
                    {...register("passwordConfirmation")}
                    aria-invalid={!!errors.passwordConfirmation}
                    aria-describedby="passwordConfirmation-error"
                    className={inputClass}
                  />
                  <FieldError
                    id="passwordConfirmation-error"
                    message={errors.passwordConfirmation?.message}
                  />
                </div>

                <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-3 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Quay lại
                  </button>
                  <button
                    type="button"
                    onClick={() => void nextStep()}
                    className="rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    Xem lại thiết lập
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 3 — Review */}
            {step === 3 && (
              <motion.div
                initial={{ opacity: 0, x: 4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-5"
              >
                <div>
                  <p className="text-sm text-muted-foreground">
                    Kiểm tra lại thông tin trước khi hoàn tất.
                  </p>
                  <dl className="mt-4 divide-y divide-border rounded-lg border border-border">
                    <div className="flex justify-between gap-4 p-4">
                      <dt className="text-sm text-muted-foreground">
                        Organization
                      </dt>
                      <dd className="text-right text-sm font-semibold text-foreground">
                        {values.organizationName}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-4 p-4">
                      <dt className="text-sm text-muted-foreground">HR</dt>
                      <dd className="text-right text-sm font-semibold text-foreground">
                        {values.name}
                        <br />
                        <span className="font-normal text-muted-foreground">
                          {values.email}
                        </span>
                      </dd>
                    </div>
                  </dl>
                </div>

                <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    disabled={submitting}
                    className="inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-3 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Quay lại
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {submitting && (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    )}
                    {submitting ? "Đang thiết lập…" : "Hoàn tất thiết lập"}
                  </button>
                </div>
              </motion.div>
            )}
          </form>
        </motion.div>
      </section>
    </main>
  );
}
