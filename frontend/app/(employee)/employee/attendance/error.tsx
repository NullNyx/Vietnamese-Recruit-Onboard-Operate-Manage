'use client';

import { useEffect } from 'react';
import { Clock } from 'lucide-react';
import { PageHeader, Card, ButtonPrimary } from '@/components/shared-ui';

export default function AttendanceError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Attendance page error:', error);
  }, [error]);

  return (
    <div className="space-y-6">
      <PageHeader icon={Clock} title="Chấm công" subtitle="Đã xảy ra lỗi khi tải trang chấm công." />
      <Card>
        <div className="text-center py-8 space-y-3">
          <p className="text-sm text-slate-600">Không thể hiển thị trang chấm công. Vui lòng thử lại.</p>
          <p className="text-[10px] text-slate-400 font-mono">{error.message}</p>
          <ButtonPrimary onClick={reset}>Thử lại</ButtonPrimary>
        </div>
      </Card>
    </div>
  );
}
