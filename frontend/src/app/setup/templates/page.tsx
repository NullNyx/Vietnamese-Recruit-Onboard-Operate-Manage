'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { completeSetup } from '@/lib/api/setup';

export default function SetupTemplatesPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFinish = async () => {
    setLoading(true);
    setError(null);
    try {
      await completeSetup();
      router.push('/setup/complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lỗi hoàn tất setup');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[520px] rounded-2xl border border-[#E4E4E7] bg-white p-10 shadow-sm">
      <div className="space-y-6">
          <div className="space-y-1 text-center">
            <h1 className="text-lg font-bold text-[#09090B]">Import template</h1>
            <p className="text-sm text-[#71717A]">
              Template mặc định được nạp sẵn. Có thể chỉnh lại trong dashboard sau setup.
            </p>
          </div>

          <div className="rounded-lg border border-[#E4E4E7] bg-[#F8FAFC] p-4 text-sm text-[#71717A]">
            Hệ thống đã có bộ template mặc định cho task, document, và contract.
          </div>

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3">
            <p className="text-xs text-destructive">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <Button type="button" variant="outline" className="flex-1" onClick={() => router.push('/setup/ai-config')}>
            Quay lại
          </Button>
          <Button className="flex-1" onClick={handleFinish} disabled={loading}>
            {loading ? 'Đang xử lý…' : 'Hoàn tất setup'}
          </Button>
        </div>
      </div>
    </div>
  );
}
