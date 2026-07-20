'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  CheckSquare, ChevronDown, ChevronRight, Circle, CheckCircle2,
  UserCheck, AlertTriangle, Search, ChevronLeft, ChevronLast,
  Loader2, ExternalLink, Save,
} from 'lucide-react';
import {
  getOnboardingCounts, listOnboardingProcesses, getOnboardingProcess,
  updateTaskStatus, updateEmployeeSetup,
  type OnboardingProcess, type OnboardingCounts,
  type OnboardingTaskStatus, type ProcessFilter,
} from '@/lib/api/onboarding';
import { listDepartments } from '@/lib/api/departments';
import { listPositions } from '@/lib/api/positions';
import { listEmployees } from '@/lib/api/employees';
import { useAuthGuard } from '@/lib/auth/session';
import { ErrorBanner, Loading, EmptyState, StatusPill, Modal, ButtonPrimary, ButtonGhost } from '@/components/shared-ui';
import type { Department, Position, Employee } from '@/lib/api/types';

const FILTERS: { key: ProcessFilter; label: string }[] = [
  { key: 'all', label: 'Tất cả' },
  { key: 'in_progress', label: 'Đang tiến hành' },
  { key: 'complete', label: 'Hoàn tất' },
];

const PAGE_SIZE = 10;

export default function OnboardingPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const qc = useQueryClient();
  const [filter, setFilter] = useState<ProcessFilter>('all');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [actionError, setActionError] = useState<unknown>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loadingTaskId, setLoadingTaskId] = useState<string | null>(null);
  const [detailProcessId, setDetailProcessId] = useState<string | null>(null);

  // Fetch full process detail when a row is expanded
  const { data: processDetail } = useQuery({
    queryKey: ['onboarding', 'detail', detailProcessId],
    queryFn: () => detailProcessId ? getOnboardingProcess(detailProcessId) : null,
    enabled: !!detailProcessId,
    staleTime: 30 * 1000,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['onboarding'] });
    qc.invalidateQueries({ queryKey: ['recruitment-candidates'] });
  };

  const { data: counts } = useQuery<OnboardingCounts>({
    queryKey: ['onboarding', 'counts'],
    queryFn: getOnboardingCounts,
    staleTime: 30 * 1000,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['onboarding', 'list', filter],
    queryFn: () => listOnboardingProcesses(filter),
    staleTime: 30 * 1000,
  });

  // Refs for setup form
  const { data: departments } = useQuery<Department[]>({
    queryKey: ['onboarding', 'departments'],
    queryFn: listDepartments,
    staleTime: 0,
    refetchOnMount: true,
  });
  const { data: positions } = useQuery<Position[]>({
    queryKey: ['onboarding', 'positions'],
    queryFn: listPositions,
    staleTime: 0,
    refetchOnMount: true,
  });
  const { data: activeEmployees } = useQuery<Employee[]>({
    queryKey: ['employees', 'active'],
    queryFn: async () => {
      const res = await listEmployees({ is_active: true, page_size: 100 });
      return res.items;
    },
    staleTime: 2 * 60 * 1000,
  });

  const tasksM = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: OnboardingTaskStatus }) =>
      updateTaskStatus(taskId, status),
    onMutate: ({ taskId }) => setLoadingTaskId(taskId),
    onSuccess: () => { invalidate(); setActionError(null); setLoadingTaskId(null); },
    onError: (e: unknown) => { setActionError(e); setLoadingTaskId(null); },
  });

  const setupM = useMutation({
    mutationFn: ({ processId, data }: { processId: string; data: Record<string, unknown> }) =>
      updateEmployeeSetup(processId, data as { department_id?: string | null; position_id?: string | null; manager_id?: string | null; start_date?: string | null }),
    onSuccess: () => { invalidate(); setActionError(null); },
    onError: (e: unknown) => setActionError(e),
  });

  const allProcesses = data?.items ?? [];


  // Client-side search filter
  const lowerSearch = search.toLowerCase().trim();
  const filtered = lowerSearch
    ? allProcesses.filter((p) =>
        p.employee_full_name.toLowerCase().includes(lowerSearch) ||
        p.employee_email.toLowerCase().includes(lowerSearch) ||
        (p.employee_code ?? '').toLowerCase().includes(lowerSearch)
      )
    : allProcesses;

  // Reset page when filter or search changes
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pagedProcesses = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);


  // Merge process detail data into list when a detail is loaded
  const processesWithDetail = pagedProcesses.map((proc) => {
    if (processDetail && proc.id === processDetail.id) {
      return { ...proc, ...processDetail, tasks: processDetail.tasks ?? proc.tasks };
    }
    return proc;
  });

  // Reset page on filter/search change
  React.useEffect(() => { setPage(1); }, [filter, search]);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-indigo-600">
        <CheckSquare className="w-5 h-5" />
        <h1 className="text-xl font-bold text-slate-900">Onboarding Processes</h1>
      </div>
      <p className="text-sm text-slate-500 -mt-3">
        Candidate <em>accepted</em> → event <code>candidate_accepted</code> (idempotent) → Employee <strong>inactive</strong> + checklist. HR hoàn tất từng task + setup; task cuối done + đủ setup → process complete + Employee <strong>active</strong> trong 1 transaction.
      </p>

      {/* Counts */}
      {counts && (
        <div className="grid grid-cols-3 gap-2">
          <Count label="Tổng" value={counts.total} />
          <Count label="Đang tiến hành" value={counts.in_progress} tone="indigo" />
          <Count label="Hoàn tất" value={counts.complete} tone="emerald" />
        </div>
      )}

      {/* Search + Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo tên, email, mã NV..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-2 rounded-lg border border-slate-200 bg-white text-sm text-slate-900 placeholder-slate-300 focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
          />
        </div>
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
              filter === f.key
                ? 'bg-indigo-600 text-white'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {f.label}{' '}
            {counts && f.key !== 'all' && (
              <span className="opacity-70 font-mono">
                {f.key === 'in_progress' ? counts.in_progress : counts.complete}
              </span>
            )}
          </button>
        ))}
      </div>

      {actionError && <ErrorBanner error={actionError} />}

      {isLoading ? (
        <Loading label="Đang tải onboarding..." />
      ) : error ? (
        <ErrorBanner error={error} />
      ) : filtered.length === 0 ? (
        <EmptyState
          filtered={filter !== 'all' || search !== ''}
          onReset={() => { setFilter('all'); setSearch(''); }}
          emptyFiltered={search ? 'Không tìm thấy process khớp với tìm kiếm.' : 'Không có bản ghi khớp với bộ lọc hiện tại.'}
          hintFiltered={search ? 'Thử từ khóa khác.' : 'Thử thay đổi bộ lọc.'}
        />
      ) : (
        <>
          <div className="space-y-2">
            {processesWithDetail.map((proc) => (
              <ProcessRow
                key={proc.id}
                proc={proc}
                expanded={!!expanded[proc.id]}
                onToggle={() => {
                  const willExpand = !expanded[proc.id];
                  setExpanded((p) => ({ ...p, [proc.id]: willExpand }));
                  if (willExpand) setDetailProcessId(proc.id);
                }}
                onToggleTask={(taskId, status) => tasksM.mutate({ taskId, status })}
                pending={tasksM.isPending}
                loadingTaskId={loadingTaskId}
                departments={departments ?? []}
                positions={positions ?? []}
                activeEmployees={activeEmployees ?? []}
                onSaveSetup={(processId, data) => setupM.mutate({ processId, data })}
                setupPending={setupM.isPending}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500">
                Trang {safePage}/{totalPages} · {filtered.length} process
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={safePage <= 1}
                  className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 transition-all flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Trước
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage >= totalPages}
                  className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 transition-all flex items-center gap-1"
                >
                  Sau <ChevronLast className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Count({
  label,
  value,
  tone = 'slate',
}: {
  label: string;
  value: number;
  tone?: 'slate' | 'indigo' | 'emerald';
}) {
  const tones: Record<string, string> = {
    slate: 'text-slate-800',
    indigo: 'text-indigo-600',
    emerald: 'text-emerald-600',
  };
  return (
    <div className="p-3 bg-white rounded-xl border border-slate-200">
      <div className={`text-2xl font-bold ${tones[tone]}`}>{value}</div>
      <p className="text-[10px] font-mono uppercase text-slate-400">{label}</p>
    </div>
  );
}

function ProcessRow({
  proc,
  expanded,
  onToggle,
  onToggleTask,
  pending,
  loadingTaskId,
  departments,
  positions,
  activeEmployees,
  onSaveSetup,
  setupPending,
}: {
  proc: OnboardingProcess;
  expanded: boolean;
  onToggle: () => void;
  onToggleTask: (taskId: string, status: OnboardingTaskStatus) => void;
  pending: boolean;
  loadingTaskId: string | null;
  departments: Department[];
  positions: Position[];
  activeEmployees: Employee[];
  onSaveSetup: (processId: string, data: Record<string, unknown>) => void;
  setupPending: boolean;
}) {
  const isComplete = proc.status === 'complete';
  const missing = proc.missing_setup_fields ?? [];
  const tasks = proc.tasks ?? [];
  const allTasksDone = tasks.length > 0 && tasks.every((t) => t.status === 'done');
  const setupComplete = missing.length === 0;
  const readyToActivate = allTasksDone && setupComplete && !isComplete;
  const canActivate = allTasksDone && setupComplete && isComplete;

  // Setup form state - sync from proc when detail data loads
  const [setupForm, setSetupForm] = useState<{
    department_id: string;
    position_id: string;
    manager_id: string;
    start_date: string;
  }>({
    department_id: proc.department_id ?? '',
    position_id: proc.position_id ?? '',
    manager_id: proc.manager_id ?? '',
    start_date: proc.start_date ?? '',
  });
  const [setupDirty, setSetupDirty] = useState(false);

  // Sync setup form when proc data changes (e.g., detail loaded)
  React.useEffect(() => {
    setSetupForm({
      department_id: proc.department_id ?? '',
      position_id: proc.position_id ?? '',
      manager_id: proc.manager_id ?? '',
      start_date: proc.start_date ?? '',
    });
    setSetupDirty(false);
  }, [proc.department_id, proc.position_id, proc.manager_id, proc.start_date]);

  // Confirm dialog for critical task
  const [confirmTask, setConfirmTask] = useState<{
    taskId: string;
    taskName: string;
    isLast: boolean;
  } | null>(null);

  const pendingTasks = tasks.filter((t) => t.status !== 'done');
  const isLastPendingTask = pendingTasks.length === 1;

  const handleTaskClick = (taskId: string, currentStatus: string, taskName: string) => {
    const newStatus = currentStatus === 'done' ? 'pending' : 'done';
    // Confirm when marking the last pending task done
    if (newStatus === 'done' && isLastPendingTask && currentStatus !== 'done') {
      setConfirmTask({ taskId, taskName, isLast: true });
    } else if (newStatus === 'pending' && currentStatus === 'done') {
      // Confirm when undoing a completed task
      setConfirmTask({ taskId, taskName, isLast: false });
    } else {
      onToggleTask(taskId, newStatus);
    }
  };

  const handleSaveSetup = () => {
    const data: Record<string, unknown> = {};
    if (setupForm.department_id !== (proc.department_id ?? ''))
      data.department_id = setupForm.department_id || null;
    if (setupForm.position_id !== (proc.position_id ?? ''))
      data.position_id = setupForm.position_id || null;
    if (setupForm.manager_id !== (proc.manager_id ?? ''))
      data.manager_id = setupForm.manager_id || null;
    if (setupForm.start_date !== (proc.start_date ?? ''))
      data.start_date = setupForm.start_date || null;
    if (Object.keys(data).length > 0) {
      onSaveSetup(proc.id, data);
      setSetupDirty(false);
    }
  };

  // Filter positions by selected department
  const filteredPositions = setupForm.department_id
    ? positions.filter(
        (p) => !p.department_id || p.department_id === setupForm.department_id
      )
    : positions;

  const inputCls =
    'w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-900 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-100 transition-all';

  return (
    <>
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100 overflow-hidden">
        <button
          onClick={onToggle}
          className="w-full flex items-start gap-3 p-4 text-left"
        >
          <div className="mt-0.5 text-slate-400">
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <StatusPill
                status={proc.status}
                label={
                  isComplete
                    ? 'Hoàn tất — Employee active'
                    : readyToActivate
                      ? 'Sẵn sàng kích hoạt'
                      : 'Đang onboarding'
                }
                tone={isComplete ? 'emerald' : readyToActivate ? 'amber' : 'indigo'}
              />
              <span className="text-[11px] font-mono text-slate-400">
                {proc.completed_count}/{proc.total_count} task
              </span>
              {proc.employee_code && (
                <span className="text-xs font-mono font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                  {proc.employee_code}
                </span>
              )}
              {/* Completed-by summary in collapsed view */}
              {tasks.filter((t) => t.completed_by_name).length > 0 && (
                <span className="text-[10px] text-slate-400 truncate max-w-[120px]">
                  {[
                    ...new Set(
                      tasks
                        .filter((t) => t.completed_by_name)
                        .map((t) => t.completed_by_name)
                    ),
                  ].join(', ')}
                </span>
              )}
            </div>
            <p className="font-semibold text-sm text-slate-900 truncate">
              {proc.employee_full_name}
            </p>
            <p className="text-xs text-slate-500 truncate">
              {proc.employee_email}
              {proc.job_opening ? ` · ${proc.job_opening}` : ''}
            </p>
          </div>
        </button>

        {expanded && (
          <div className="px-4 pb-4 border-t border-slate-100 pt-3 space-y-3">
            {/* Setup warning */}
            {missing.length > 0 && !isComplete && (
              <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 flex items-start gap-2">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <div>
                  <span>
                    Thiếu thông tin:{' '}
                    <code className="font-mono">{missing.join(', ')}</code>.
                  </span>{' '}
                  <span>Cập nhật bên dưới để có thể kích hoạt Employee.</span>
                </div>
              </div>
            )}

            {/* Ready-to-activate info */}
            {readyToActivate && (
              <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span>
                  Tất cả task đã hoàn tất và đủ thông tin setup. Hoàn tất task
                  cuối cùng để kích hoạt Employee.
                </span>
              </div>
            )}

            {/* Task checklist */}
            {tasks.length === 0 ? (
              <p className="text-xs text-slate-400">Chưa có task checklist.</p>
            ) : (
              <ul className="space-y-1.5">
                {tasks
                  .sort((a, b) => a.order_index - b.order_index)
                  .map((task) => {
                    const isThisLoading = loadingTaskId === task.id;
                    const isDone = task.status === 'done';
                    return (
                      <li key={task.id} className="flex items-center gap-2.5">
                        <button
                          onClick={() =>
                            handleTaskClick(task.id, task.status, task.name)
                          }
                          disabled={pending || isComplete}
                          className={`shrink-0 ${
                            isDone
                              ? 'text-emerald-600'
                              : 'text-slate-300 hover:text-indigo-500'
                          } disabled:opacity-50`}
                          title={
                            isDone
                              ? 'Click để đánh dấu chưa hoàn tất'
                              : 'Click để đánh dấu hoàn tất'
                          }
                        >
                          {isThisLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
                          ) : isDone ? (
                            <CheckCircle2 className="w-5 h-5" />
                          ) : (
                            <Circle className="w-5 h-5" />
                          )}
                        </button>
                        <span
                          className={`text-sm ${
                            isDone
                              ? 'line-through text-slate-400'
                              : 'text-slate-700'
                          }`}
                        >
                          {task.name}
                          {isLastPendingTask && !isDone && (
                            <span className="ml-1 text-[10px] text-amber-500 font-medium">
                              (bước cuối)
                            </span>
                          )}
                        </span>
                        {task.completed_by_name && (
                          <span className="text-[10px] font-mono text-slate-400 ml-auto">
                            {task.completed_by_name} ·{' '}
                            {task.completed_at &&
                              new Date(task.completed_at).toLocaleDateString(
                                'vi-VN'
                              )}
                          </span>
                        )}
                      </li>
                    );
                  })}
              </ul>
            )}

            {/* Employee Setup Form */}
            {!isComplete && (
              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs font-semibold text-slate-700 mb-2">
                  ⚙️ Thông tin Employee Setup
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {/* Department */}
                  <label className="block">
                    <span className="text-[10px] font-semibold text-slate-500">
                      Phòng ban
                    </span>
                    <select
                      value={setupForm.department_id}
                      onChange={(e) => {
                        setSetupForm((f) => ({
                          ...f,
                          department_id: e.target.value,
                          position_id: '',
                        }));
                        setSetupDirty(true);
                      }}
                      className={inputCls}
                    >
                      <option value="">-- Chọn --</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  {/* Position */}
                  <label className="block">
                    <span className="text-[10px] font-semibold text-slate-500">
                      Chức vụ
                    </span>
                    <select
                      value={setupForm.position_id}
                      onChange={(e) => {
                        setSetupForm((f) => ({
                          ...f,
                          position_id: e.target.value,
                        }));
                        setSetupDirty(true);
                      }}
                      className={inputCls}
                    >
                      <option value="">-- Chọn --</option>
                      {filteredPositions.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  {/* Manager */}
                  <label className="block">
                    <span className="text-[10px] font-semibold text-slate-500">
                      Quản lý
                    </span>
                    <select
                      value={setupForm.manager_id}
                      onChange={(e) => {
                        setSetupForm((f) => ({
                          ...f,
                          manager_id: e.target.value,
                        }));
                        setSetupDirty(true);
                      }}
                      className={inputCls}
                    >
                      <option value="">-- Chọn --</option>
                      {activeEmployees.map((emp) => (
                        <option key={emp.id} value={emp.id}>
                          {emp.full_name} ({emp.employee_code})
                        </option>
                      ))}
                    </select>
                  </label>

                  {/* Start Date */}
                  <label className="block">
                    <span className="text-[10px] font-semibold text-slate-500">
                      Ngày bắt đầu
                    </span>
                    <input
                      type="date"
                      value={setupForm.start_date}
                      onChange={(e) => {
                        setSetupForm((f) => ({
                          ...f,
                          start_date: e.target.value,
                        }));
                        setSetupDirty(true);
                      }}
                      className={inputCls}
                    />
                  </label>
                </div>
                {setupDirty && (
                  <button
                    onClick={handleSaveSetup}
                    disabled={setupPending}
                    className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50 transition-all"
                  >
                    {setupPending ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Save className="w-3.5 h-3.5" />
                    )}
                    Lưu setup
                  </button>
                )}
              </div>
            )}

            {/* Activation status footer */}
            <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
              <UserCheck
                className={`w-4 h-4 ${
                  canActivate || readyToActivate
                    ? 'text-emerald-600'
                    : 'text-slate-300'
                }`}
              />
              <span className="text-xs text-slate-500">
                {canActivate
                  ? '✓ Process hoàn tất — Employee đã chuyển active.'
                  : readyToActivate
                    ? '⏳ Sẵn sàng kích hoạt — hoàn tất task cuối để activate Employee.'
                    : isComplete
                      ? '✓ Employee active.'
                      : 'Hoàn tất toàn bộ task và Employee setup để kích hoạt.'}
              </span>
            </div>

            {/* Employee link after activation */}
            {isComplete && (
              <div className="pt-1">
                <Link
                  href={`/employees/${proc.employee_id}`}
                  className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  <ExternalLink className="w-3 h-3" /> Xem hồ sơ Nhân viên
                </Link>
              </div>
            )}

            {proc.accepted_at && (
              <p className="text-[10px] font-mono text-slate-400">
                Accepted:{' '}
                {new Date(proc.accepted_at).toLocaleString('vi-VN')}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Confirm dialog for critical task actions */}
      {confirmTask && (
        <Modal
          open={true}
          onClose={() => setConfirmTask(null)}
          title={confirmTask.isLast ? 'Xác nhận hoàn tất' : 'Xác nhận thay đổi'}
        >
          <p className="text-sm text-slate-600 mb-4">
            {confirmTask.isLast
              ? `Bạn sắp hoàn tất task cuối cùng "${confirmTask.taskName}". Sau khi hoàn tất, Employee sẽ được kích hoạt (active) nếu đã đủ thông tin setup. Bạn có chắc chắn?`
              : `Bạn có chắc muốn đánh dấu "${confirmTask.taskName}" là chưa hoàn tất? Hành động này có thể ảnh hưởng đến trạng thái activation.`}
          </p>
          <div className="flex justify-end gap-2">
            <ButtonGhost onClick={() => setConfirmTask(null)}>Hủy</ButtonGhost>
            <ButtonPrimary
              onClick={() => {
                const task = tasks.find((t) => t.id === confirmTask.taskId);
                if (task) {
                  const newStatus =
                    task.status === 'done' ? 'pending' : 'done';
                  onToggleTask(task.id, newStatus);
                }
                setConfirmTask(null);
              }}
            >
              Xác nhận
            </ButtonPrimary>
          </div>
        </Modal>
      )}
    </>
  );
}
