'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function SetupWelcomePage() {
  const router = useRouter();

  return (
    <div className="w-full max-w-[520px] rounded-2xl border border-[#E4E4E7] bg-white p-10 shadow-sm">
      <div className="flex flex-col items-center gap-6 text-center">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-sm font-bold text-white">V</span>
          </div>
          <span className="text-lg font-bold text-primary">VROOM HR</span>
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold text-[#09090B]">
            Khởi tạo HR Workspace
          </h1>
          <p className="mx-auto max-w-[440px] text-sm text-[#71717A]">
            Chào mừng bạn đến với nền tảng hỗ trợ vận hành nhân sự
            cho doanh nghiệp Việt Nam. Hãy khởi tạo không gian làm việc
            của bạn chỉ trong 3-5 phút.
          </p>
        </div>

        {/* Time estimate box */}
        <div className="w-full rounded-lg bg-[#F4F4F5] p-3 text-center">
          <p className="text-xs text-[#71717A]">
            ⏱ Thời gian ước lượng: <strong>3-5 phút</strong>
          </p>
        </div>

        <Button
          className="w-full"
          size="lg"
          onClick={() => router.push('/setup/administrator')}
        >
          Bắt đầu thiết lập →
        </Button>
      </div>
    </div>
  );
}
