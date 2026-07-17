"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, DollarSign, Loader2 } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { fetchMyPayslip } from "@/lib/api/payslips";
import type { Payslip } from "@/lib/api/payslips";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(amount: string): string {
  const num = Number(amount);
  if (!Number.isFinite(num)) return amount;
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(num);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString("vi-VN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatPeriodMonth(periodMonth: string | null | undefined): string {
  if (!periodMonth) return "-";
  const parts = periodMonth.split("-");
  const year = Number(parts[0]);
  const month = Number(parts[1]);
  if (!Number.isFinite(year) || !Number.isFinite(month) || month < 1 || month > 12) {
    return periodMonth;
  }
  const date = new Date(year, month - 1);
  if (Number.isNaN(date.getTime())) return periodMonth;
  return date.toLocaleDateString("vi-VN", {
    month: "long",
    year: "numeric",
  });
}

// ---------------------------------------------------------------------------
// Detail row component
// ---------------------------------------------------------------------------

    function DetailRow({
      label,
      value,
      highlight,
    }: {
      label: string;
      value: string;
      highlight?: boolean;
    }) {
      return (
        <div className="flex items-center justify-between py-2">
          <span className="text-[13px] text-muted-foreground">{label}</span>
          <span
            className={`text-[14px] font-medium ${
              highlight ? "text-primary" : "text-foreground"
            }`}
          >
            {value}
          </span>
        </div>
      );
    }
    
    function Divider() {
      return <div className="border-t border-border" />;
    }

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function EmployeePayslipDetailPage() {
  const params = useParams();
  const router = useRouter();
  const payslipId = params.id as string;

  const [payslip, setPayslip] = useState<Payslip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!payslipId) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      setPayslip(null);
      try {
        const data = await fetchMyPayslip(payslipId);
        if (!cancelled) {
          setPayslip(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Không thể tải phiếu lương");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [payslipId]);

  // -- Back navigation --
  function handleBack() {
    router.push("/employee/payslips");
  }

      return (
        <div className="animate-fade-in space-y-6 max-w-[700px]">
          {/* Back button */}
          <div className="fade-in-section">
            <Button variant="ghost" size="sm" onClick={handleBack} className="text-muted-foreground">
              <ArrowLeft className="mr-1 h-4 w-4" />
              Quay lại
            </Button>
          </div>

          {/* Loading */}
          {loading && (
            <div className="fade-in-section rounded-xl border border-border/40 bg-card p-6 space-y-4">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-36" />
              <Divider />
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-5 w-full" />
              <Skeleton className="h-5 w-3/4" />
              <Divider />
              <Skeleton className="h-5 w-32" />
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div className="fade-in-section rounded-xl border border-destructive/20 bg-destructive/10 p-12 text-center">
              <Loader2 className="mx-auto h-10 w-10 text-destructive" />
              <h3 className="mt-4 text-[14px] font-medium text-foreground">
                Không thể tải phiếu lương
              </h3>
              <p className="mt-1 text-[12px] text-muted-foreground">{error}</p>
            </div>
          )}

          {/* NotFound fallback */}
          {!loading && !error && !payslip && (
            <div className="fade-in-section rounded-xl border border-border/40 bg-card p-12 text-center">
              <DollarSign className="mx-auto h-10 w-10 text-muted-foreground" />
              <h3 className="mt-4 text-[14px] font-medium text-foreground">
                Không tìm thấy phiếu lương
              </h3>
              <p className="mt-1 text-[12px] text-muted-foreground">
                Phiếu lương không tồn tại hoặc chưa được phát hành.
              </p>
            </div>
          )}

          {/* Detail */}
          {!loading && !error && payslip && (
            <div className="fade-in-section rounded-xl border border-border/40 bg-card p-6 card-hover">
              {/* Header */}
              <div className="space-y-1 pb-4">
                <h2 className="text-[18px] font-semibold text-foreground">
                  Phiếu lương
                </h2>
                <p className="text-[13px] text-muted-foreground">
                  {formatPeriodMonth(payslip.period_month)}
                </p>
              </div>

              <Divider />

              {/* Gross & Deductions */}
              <div className="py-2 space-y-0">
                <DetailRow
                  label="Lương gộp"
                  value={formatCurrency(payslip.gross_salary)}
                />
                <DetailRow
                  label="BHXH + BHYT + BHTN (người lao động)"
                  value={formatCurrency(payslip.insurance_employee)}
                />
                <DetailRow
                  label="Các khoản khấu trừ"
                  value={formatCurrency(payslip.deductions)}
                />
                <Divider />
                <DetailRow
                  label="Thu nhập chịu thuế"
                  value={formatCurrency(payslip.taxable_income)}
                />
                <DetailRow
                  label="Thuế TNCN"
                  value={formatCurrency(payslip.pit_amount)}
                />
                <Divider />
                <DetailRow
                  label="Lương thực nhận"
                  value={formatCurrency(payslip.net_salary)}
                  highlight
                />
              </div>

              <Divider />

              {/* PDF link */}
              {payslip.pdf_url && (
                <div className="pt-4">
                  <Link
                    href={payslip.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[13px] text-primary hover:underline"
                  >
                    Tải PDF
                  </Link>
                </div>
              )}

              {/* Footer - metadata */}
              <div className="pt-4 flex items-center justify-between text-[11px] text-muted-foreground/70">
                <span>Ngày phát hành: {formatDate(payslip.published_at)}</span>
              </div>
            </div>
          )}
        </div>
  );
}
