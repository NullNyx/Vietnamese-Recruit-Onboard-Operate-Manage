import type { OnboardingProcess, OnboardingTask } from '@/lib/api/onboarding';

/**
 * Return visual metadata for a given onboarding process status.
 */
export function getProcessStatusMeta(status: OnboardingProcess['status']) {
  switch (status) {
    case 'in_progress':
      return { label: 'Đang thực hiện', badgeClassName: 'bg-blue-100 text-blue-700 border-blue-200', tone: 'blue' as const };
    case 'ready_for_completion':
      return { label: 'Sẵn sàng hoàn thành', badgeClassName: 'bg-amber-50 text-amber-700 border-amber-200', tone: 'amber' as const };
    case 'complete':
      return { label: 'Đã kích hoạt', badgeClassName: 'bg-emerald-100 text-emerald-700 border-emerald-200', tone: 'green' as const };
  }
}

/**
 * Return readiness note for a task before it can be marked done.
 * Certain tasks require setup fields before they can be completed.
 */
export function getTaskReadinessNote(
  process: Pick<OnboardingProcess, 'missing_setup_fields'>,
  task: Pick<OnboardingTask, 'order_index' | 'name' | 'status'>,
): { isReady: boolean; note: string } {
  if (task.order_index === 2) {
    const missing = process.missing_setup_fields?.filter((f: string) =>
      ['department_id', 'position_id', 'manager_id'].includes(f),
    );
    if (missing && missing.length > 0) {
      return { isReady: false, note: 'Vui lòng hoàn thiện thông tin phòng ban, vị trí và quản lý trực tiếp trong phần Setup trước khi hoàn thành task này.' };
    }
  }
  if (task.order_index === 3) {
    if (process.missing_setup_fields?.includes('start_date')) {
      return { isReady: false, note: 'Vui lòng chọn Ngày bắt đầu làm việc trong phần Setup trước khi hoàn thành task này.' };
    }
  }
  if (task.order_index === 0) {
    return { isReady: true, note: 'Hãy đảm bảo nhân viên đã ký hợp đồng hợp lệ trước khi xác nhận.' };
  }
  if (task.order_index === 1) {
    return { isReady: true, note: 'Hãy kiểm tra và đảm bảo nhân viên đã nộp đủ hồ sơ cá nhân theo yêu cầu.' };
  }
  return { isReady: true, note: 'Xác nhận hoàn thành task này?' };
}
