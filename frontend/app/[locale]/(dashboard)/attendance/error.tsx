'use client';
import { useTranslations } from 'next-intl';

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
    console.error('Attendance admin page error:', error);
  }, [error]);
      const t = useTranslations('employee');

  return (
    <div className="space-y-6">
      <PageHeader icon={Clock} title={t('attendance')} subtitle={t('attendanceErrorDesc')} />
      <Card>
        <div className="text-center py-8 space-y-3">
          <p className="text-sm text-slate-600">{t('attendanceRetryDesc')}</p>
          <p className="text-[10px] text-slate-400 font-mono">{error.message}</p>
          <ButtonPrimary onClick={reset}>{t('retry')}</ButtonPrimary>
        </div>
      </Card>
    </div>
  );
}
