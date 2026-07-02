import { describe, expect, it } from 'vitest';
import { getProcessStatusMeta, getTaskReadinessNote } from './onboarding-detail-utils';

const process = {
  missing_setup_fields: ['start_date'],
};

describe('onboarding detail helpers', () => {
  it('maps ready_for_completion into the right badge metadata', () => {
    expect(getProcessStatusMeta('ready_for_completion')).toEqual({
      label: 'Sẵn sàng hoàn thành',
      badgeClassName: 'bg-amber-50 text-amber-700 border-amber-200',
      tone: 'amber',
    });
  });

  it('blocks start date task until setup is complete', () => {
    const note = getTaskReadinessNote(
      process,
      { name: 'Set Start Date', status: 'pending', order_index: 3 },
    );

    expect(note).toEqual({
      isReady: false,
      note: 'Vui lòng chọn Ngày bắt đầu làm việc trong phần Setup trước khi hoàn thành task này.',
    });
  });
});
