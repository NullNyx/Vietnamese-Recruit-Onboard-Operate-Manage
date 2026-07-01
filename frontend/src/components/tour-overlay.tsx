"use client";

import { useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

const steps = [
  {
    title: "🎉 Workspace đã sẵn sàng!",
    desc: "Chào mừng bạn đến với Vroom HR. Hãy cùng dành khoảng 30 giây để xem qua giao diện vận hành cốt lõi giúp bạn làm quen nhanh nhất.",
    mode: "dialog" as const,
  },
  {
    title: "1. Tổng quan vận hành",
    desc: "Đây là khu vực trung tâm giúp HR theo dõi toàn bộ tình trạng nhân sự, các công việc đang trễ hạn và tài liệu cần xác minh.",
    mode: "tooltip" as const,
    x: 300, y: 120, w: 320,
  },
  {
    title: "2. Cập nhật từ Trợ lý AI",
    desc: "Khi bật AI, hệ thống tự động tóm tắt công việc dưới dạng hội thoại tự nhiên. Nếu không có AI, hệ thống hiển thị dựa trên rule dữ liệu.",
    mode: "tooltip" as const,
    x: 450, y: 330, w: 320,
  },
  {
    title: "3. Chỉ số vận hành",
    desc: "Các chỉ số tổng quan: tổng nhân sự, onboarding đang thực hiện, hoàn tất và hồ sơ cần chú ý.",
    mode: "tooltip" as const,
    x: 450, y: 510, w: 320,
  },
  {
    title: "4. Hồ sơ cần chú ý",
    desc: "Danh sách nhân viên cần bổ sung thông tin giấy tờ, chứng từ hoặc thông tin nhân sự.",
    mode: "tooltip" as const,
    x: 400, y: 320, w: 320,
  },
  {
    title: "5. Timeline nhân sự",
    desc: "Dòng thời gian hiển thị lịch sử thay đổi nhân sự, giúp HR nắm bắt mọi biến động trong tổ chức.",
    mode: "tooltip" as const,
    x: 650, y: 320, w: 320,
  },
  {
    title: "6. Menu điều hướng",
    desc: "Sidebar chứa tất cả tính năng: quản lý hồ sơ, tuyển dụng, onboarding, Gmail, và bảng điều khiển.",
    mode: "tooltip" as const,
    x: 280, y: 200, w: 320,
  },
];

function TourOverlayInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const stepParam = searchParams.get("tour");
  const current = stepParam ? parseInt(stepParam, 10) - 1 : -1;

  const isOpen = current >= 0 && current < steps.length;
  const step = isOpen ? steps[current] : null;

  const go = useCallback(
    (s: number) => {
      if (s >= steps.length) {
        router.replace("/", { scroll: false });
      } else {
        router.replace(`/?tour=${s + 1}`, { scroll: false });
      }
    },
    [router],
  );

  if (!isOpen || !step) return null;

  return (
    <>
      {/* Full scrim on first step, partial on others */}
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={() => go(current + 1)}
      />

      {step.mode === "dialog" ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="w-[480px] rounded-xl border border-[#E4E4E7] bg-white p-8 shadow-lg">
            <div className="space-y-6 text-center">
              <div className="space-y-1">
                <p className="text-lg font-bold text-[#09090B]">{step.title}</p>
                <p className="text-sm text-[#71717A]">{step.desc}</p>
              </div>
              <div className="flex gap-3">
                <Button className="flex-1" onClick={() => go(current + 1)}>
                  Khám phá ngay
                </Button>
                <Button variant="outline" className="flex-1" onClick={() => go(steps.length)}>
                  Bỏ qua
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div
          className="fixed z-50 rounded-lg border border-primary bg-white p-4 shadow-lg"
          style={{ left: step.x, top: step.y, width: step.w }}
        >
          <div className="space-y-2">
            <p className="text-sm font-bold text-primary">{step.title}</p>
            <p className="text-sm text-[#09090B]">{step.desc}</p>
            <div className="flex items-center justify-between pt-1">
              <p className="text-[10px] text-[#71717A]">
                {current + 1} / {steps.length}
              </p>
              <div className="flex gap-2">
                <button
                  className="text-xs text-[#71717A] hover:text-[#09090B]"
                  onClick={() => go(steps.length)}
                >
                  Bỏ qua
                </button>
                <button
                  className="text-xs font-medium text-primary hover:text-primary/80"
                  onClick={() => go(current + 1)}
                >
                  {current < steps.length - 1 ? "Tiếp →" : "Kết thúc"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export function TourOverlay() {
  return (
    <Suspense fallback={null}>
      <TourOverlayInner />
    </Suspense>
  );
}
