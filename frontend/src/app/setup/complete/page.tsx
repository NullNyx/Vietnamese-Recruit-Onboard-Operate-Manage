'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function SetupCompletePage() {
  const router = useRouter();

  return (
    <div className="w-full max-w-[520px] rounded-2xl border border-[#E4E4E7] bg-white p-10 shadow-sm">
      <div className="space-y-6 text-center">
        <div className="space-y-1">
          <p className="text-sm font-medium text-primary">Setup complete</p>
          <h1 className="text-lg font-bold text-[#09090B]">Workspace đã sẵn sàng</h1>
          <p className="text-sm text-[#71717A]">
            Hệ thống đã được khởi tạo. Bây giờ có thể vào dashboard để tiếp tục vận hành.
          </p>
        </div>

        <Button className="w-full" size="lg" onClick={() => router.push('/')}>
          Đi tới dashboard
        </Button>
      </div>
    </div>
  );
}
