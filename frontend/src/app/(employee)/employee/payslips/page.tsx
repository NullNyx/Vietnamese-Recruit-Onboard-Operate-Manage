"use client";

import { useState, useEffect } from "react";
import { DollarSign, Loader2 } from "lucide-react";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

import { fetchMyPayslips } from "@/lib/api/payslips";
import type { Payslip } from "@/lib/api/payslips";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(amount: string): string {
  const num = parseFloat(amount);
  if (!Number.isFinite(num)) return amount;
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(num);
}

function formatPeriodMonth(periodMonth: string): string {
  const [year, month] = periodMonth.split("-").map(Number);
  const date = new Date(year, month - 1);
  return date.toLocaleDateString("vi-VN", {
    month: "long",
    year: "numeric",
  });
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function PayslipSkeleton() {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-28" />
        <div className="flex items-center justify-between pt-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-5 w-28" />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Payslip card
// ---------------------------------------------------------------------------

function PayslipCard({ payslip }: { payslip: Payslip }) {
  return (
    <Link
      href={`/employee/payslips/${payslip.id}`}
      className="block rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 transition-all hover:border-white/[0.1] hover:bg-white/[0.04]"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <p className="text-[14px] font-medium text-[#f7f8f8]">
            {formatPeriodMonth(payslip.period_month)}
          </p>
          <p className="text-[12px] text-[#8a8f98]">
            Gross: {formatCurrency(payslip.gross_salary)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[16px] font-semibold text-[#f7f8f8]">
            {formatCurrency(payslip.net_salary)}
          </p>
          <p className="text-[11px] text-[#8a8f98]">Net</p>
        </div>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function EmployeePayslipsPage() {
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchMyPayslips();
        if (!cancelled) {
          setPayslips(data.payslips);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Không thể tải bảng lương");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-6 max-w-[900px]">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-[24px] font-semibold tracking-[-0.3px] text-[#f7f8f8]">
          Bảng lương
        </h1>
        <p className="text-[14px] text-[#8a8f98]">
          Các phiếu lương đã được phát hành
        </p>
      </div>

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          <PayslipSkeleton />
          <PayslipSkeleton />
          <PayslipSkeleton />
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 text-red-400" />
          <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
            Không thể tải dữ liệu
          </h3>
          <p className="mt-1 text-[12px] text-[#8a8f98]">{error}</p>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && payslips.length === 0 && (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-12 text-center">
          <DollarSign className="mx-auto h-10 w-10 text-[#8a8f98]" />
          <h3 className="mt-4 text-[14px] font-medium text-[#f7f8f8]">
            Chưa có bảng lương
          </h3>
          <p className="mt-1 text-[12px] text-[#8a8f98]">
            Các phiếu lương đã phát hành sẽ xuất hiện ở đây.
          </p>
        </div>
      )}

      {/* List */}
      {!loading && !error && payslips.length > 0 && (
        <div className="space-y-3">
          {payslips.map((p) => (
            <PayslipCard key={p.id} payslip={p} />
          ))}
        </div>
      )}
    </div>
  );
}
