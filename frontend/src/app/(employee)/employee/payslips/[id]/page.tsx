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
  const num = parseFloat(amount);
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(num);
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("vi-VN", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function formatPeriod(start: string, end: string): string {
  try {
    const s = new Date(start);
    const e = new Date(end);
    return `${s.toLocaleDateString("vi-VN", { day: "numeric", month: "long" })} - ${e.toLocaleDateString("vi-VN", { day: "numeric", month: "long", year: "numeric" })}`;
  } catch {
    return `${start} - ${end}`;
  }
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
      <span className="text-[13px] text-[#8a8f98]">{label}</span>
      <span
        className={`text-[14px] font-medium ${
          highlight ? "text-[#e4f222]" : "text-[#f7f8f8]"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function Divider() {
  return <div className="border-t border-white/[0.06]" />;
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
      if (!payslipId) return;
      try {
        const data = await fetchMyPayslip(payslipId);
        if (!cancelled) {
          setPayslip(data);
          setError(null);
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
    <div className="space-y-6 max-w-[700px]">
      {/* Back button */}
      <Button variant="ghost" size="sm" onClick={handleBack} className="text-[#8a8f98]">
        <ArrowLeft className="mr-1 h-4 w-4" />
        Quay lại
      </Button>

      {/* Loading */}
      {loading && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-36" />
          <Divider />
          <Skeleton className="h-5 w-full" />
          <Skeleton className="h-5 w-full" />
          <Skeleton className="h-5 w-3/4" />
          <Divider />
          <Skeleton className="h-5 w-32" />
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 text-red-400" />
          <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
            Không thể tải phiếu lương
          </h3>
          <p className="mt-1 text-[12px] text-[#8a8f98]">{error}</p>
        </div>
      )}

      {/* NotFound fallback */}
      {!loading && !error && !payslip && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
          <DollarSign className="mx-auto h-10 w-10 text-[#8a8f98]" />
          <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
            Không tìm thấy phiếu lương
          </h3>
          <p className="mt-1 text-[12px] text-[#8a8f98]">
            Phiếu lương không tồn tại hoặc chưa được phát hành.
          </p>
        </div>
      )}

      {/* Detail */}
      {!loading && !error && payslip && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
          {/* Header */}
          <div className="space-y-1 pb-4">
            <h2 className="text-[18px] font-semibold text-[#f7f8f8]">
              Phiếu lương
            </h2>
            <p className="text-[13px] text-[#8a8f98]">
              {formatPeriod(payslip.pay_period_start, payslip.pay_period_end)}
            </p>
          </div>

          <Divider />

          {/* Amounts */}
          <div className="py-2 space-y-0">
            <DetailRow
              label="Lương gross"
              value={formatCurrency(payslip.gross_amount)}
            />
            <DetailRow
              label="Tổng khấu trừ"
              value={formatCurrency(payslip.total_deductions)}
            />
            <Divider />
            <DetailRow
              label="Lương net (thực nhận)"
              value={formatCurrency(payslip.net_amount)}
              highlight
            />
          </div>

          <Divider />

          {/* Details breakdown (if available) */}
          {payslip.details && Object.keys(payslip.details).length > 0 && (
            <>
              <div className="py-3">
                <h3 className="text-[13px] font-medium text-[#8a8f98] mb-2">
                  Chi tiết
                </h3>
                <div className="space-y-1">
                  {Object.entries(payslip.details).map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between text-[13px]"
                    >
                      <span className="text-[#8a8f98] capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="text-[#f7f8f8]">
                        {typeof value === "number"
                          ? formatCurrency(String(value))
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <Divider />
            </>
          )}

          {/* PDF link */}
          {payslip.pdf_url && (
            <div className="pt-4">
              <Link
                href={payslip.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[13px] text-[#e4f222] hover:underline"
              >
                Tải PDF
              </Link>
            </div>
          )}

          {/* Footer - metadata */}
          <div className="pt-4 flex items-center justify-between text-[11px] text-[#585c63]">
            <span>Ngày phát hành: {formatDate(payslip.created_at)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
