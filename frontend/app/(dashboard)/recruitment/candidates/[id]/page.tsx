'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  UserCheck, ArrowLeft, CheckCircle2, XCircle, Archive, Link2, Unlink,
  FileText, Calendar, Briefcase, ExternalLink, AlertTriangle, Plus,
} from 'lucide-react';
    import {
      getCandidate, acceptCandidate, rejectCandidate, archiveCandidate,
      assignCandidate, reassignCandidate, unassignCandidate,
      createInterview, completeInterview, cancelInterview, createReplacementInterview,
      getCVPresignedUrl,
      listJobOpenings,
      type CandidateDetail, type JobOpeningListItem, type InterviewResponse,
      type CreateInterviewRequest,
    } from '@/lib/api/recruitment';
    import { getCalendars, type CalendarListResponse } from '@/lib/api/gmail';
    import { useAuthGuard } from '@/lib/auth/session';
    import {
      ErrorBanner, Loading, StatusPill,
      CANDIDATE_STATUS_META, confidencePct,
    } from '@/components/shared-ui';

export default function CandidateDetailPage() {
  useAuthGuard({ requireAuth: true, requireAdmin: true });
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [rejectReason, setRejectReason] = useState('');
  const [rejectOpen, setRejectOpen] = useState(false);
  const [assJob, setAssJob] = useState('');
  const [actionError, setActionError] = useState<unknown>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [assignOpen, setAssignOpen] = useState(false);
  const [interviewOpen, setInterviewOpen] = useState(false);

  const { data: candidate, isLoading, error } = useQuery<CandidateDetail>({
    queryKey: ['recruitment-candidate', params.id],
    queryFn: () => getCandidate(params.id),
    enabled: !!params.id,
    staleTime: 30 * 1000,
  });

      const { data: calendars } = useQuery<CalendarListResponse>({
        queryKey: ['google-calendars'],
        queryFn: () => getCalendars(),
        staleTime: 5 * 60 * 1000,
      });
      const selectedCalendarId = calendars?.selected_calendar_id ?? null;

      const { data: openJobsData } = useQuery({
        queryKey: ['recruitment-job-openings', 'open'],
        queryFn: () => listJobOpenings({ status: ['open'], page_size: 100 }),
        staleTime: 60 * 1000,
      });
      const openJobs: JobOpeningListItem[] = openJobsData?.job_openings ?? [];

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['recruitment-candidate', params.id] });
    qc.invalidateQueries({ queryKey: ['recruitment-candidates'] });
    qc.invalidateQueries({ queryKey: ['recruitment-job-openings'] });
    qc.invalidateQueries({ queryKey: ['recruitment-interviews'] });
    qc.invalidateQueries({ queryKey: ['onboarding'] });
  };
  const wrapErr = (_label: string) => (e: unknown) => setActionError(e);

  const acceptM = useMutation({
    mutationFn: () => acceptCandidate(params.id),
    onSuccess: () => {
      invalidate();
      setActionError(null);
      setActionSuccess('Ứng viên đã được chấp nhận. Onboarding process đã được tạo tự động.');
    },
    onError: wrapErr('Lỗi accept'),
  });
  const rejectM = useMutation({ mutationFn: (reason: string) => rejectCandidate(params.id, { reason }), onSuccess: () => { invalidate(); setRejectOpen(false); setActionError(''); }, onError: wrapErr('Lỗi reject') });
  const archiveM = useMutation({ mutationFn: () => archiveCandidate(params.id), onSuccess: () => { invalidate(); setActionError(''); }, onError: wrapErr('Lỗi archive') });
  const assignM = useMutation({
    mutationFn: (jobOpeningId: string) =>
      candidate?.job_opening_id ? reassignCandidate(params.id, jobOpeningId) : assignCandidate(params.id, jobOpeningId),
    onSuccess: () => { invalidate(); setAssignOpen(false); setActionError(''); setAssJob(''); },
    onError: wrapErr('Lỗi gán vị trí'),
  });
  const unassignM = useMutation({ mutationFn: () => unassignCandidate(params.id), onSuccess: () => { invalidate(); setActionError(''); }, onError: wrapErr('Lỗi hủy gán') });
  const createIntM = useMutation({
    mutationFn: (data: CreateInterviewRequest) => createInterview(params.id, data),
    onSuccess: () => { invalidate(); setInterviewOpen(false); setActionError(''); },
    onError: wrapErr('Lỗi tạo phỏng vấn'),
  });
      const completeIntM = useMutation({
        mutationFn: (ivId: string) => {
          if (!window.confirm('Xác nhận hoàn tất buổi phỏng vấn này?')) return Promise.reject(new Error('Cancelled'));
          return completeInterview(params.id, ivId);
        },
        onSuccess: () => { invalidate(); setActionError(''); },
        onError: (e: any) => { if (e?.message !== 'Cancelled') setActionError(e); },
      });
      const cancelIntM = useMutation({
        mutationFn: (ivId: string) => {
          if (!window.confirm('Xác nhận hủy buổi phỏng vấn này? Hành động không thể hoàn tác.')) return Promise.reject(new Error('Cancelled'));
          return cancelInterview(params.id, ivId);
        },
        onSuccess: () => { invalidate(); setActionError(''); },
        onError: (e: any) => { if (e?.message !== 'Cancelled') setActionError(e); },
      });
  const [replaceFor, setReplaceFor] = useState<string | null>(null);
  const replaceIntM = useMutation({
    mutationFn: ({ ivId, data }: { ivId: string; data: CreateInterviewRequest }) => createReplacementInterview(params.id, ivId, data),
    onSuccess: () => { invalidate(); setReplaceFor(null); setActionError(''); },
    onError: wrapErr('Lỗi tạo replacement PV'),
  });

  if (isLoading) return <Loading label="Đang tải hồ sơ ứng viên..." />;
  if (error) return <ErrorBanner error={error} />;
  if (!candidate) return <ErrorBanner error={new Error('Không tìm thấy ứng viên')} />;

  const meta = CANDIDATE_STATUS_META[candidate.status] ?? { label: candidate.status, tone: 'slate' as const };
  const isTerminal = candidate.status === 'accepted' || candidate.status === 'rejected' || candidate.status === 'archived';
  const interviews: InterviewResponse[] = candidate.interviews ?? [];

  return (
    <div className="space-y-5">
      <button onClick={() => router.push('/recruitment/candidates')} className="flex items-center gap-1 text-xs text-slate-500 hover:text-indigo-600">
        <ArrowLeft className="w-3.5 h-3.5" /> Quay lại danh sách
      </button>

      {/* Header */}
      <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <StatusPill status={candidate.status} label={meta.label} tone={meta.tone} />
              <span className="text-[11px] font-mono text-slate-400">confidence {confidencePct(candidate.confidence_score)}</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">{candidate.name}</h1>
            <p className="text-sm text-slate-500">{candidate.email} {candidate.phone && `· ${candidate.phone}`}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {!isTerminal && candidate.status !== 'accepted' && (
              <button onClick={() => acceptM.mutate()} disabled={acceptM.isPending} className="px-3 py-2 text-xs font-medium bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-1.5 disabled:opacity-50">
                <CheckCircle2 className="w-4 h-4" /> Accept → Onboarding
              </button>
            )}
            {!isTerminal && candidate.status !== 'rejected' && (
              <button onClick={() => setRejectOpen((v) => !v)} disabled={rejectM.isPending} className="px-3 py-2 text-xs font-medium bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 rounded-lg flex items-center gap-1.5">
                <XCircle className="w-4 h-4" /> Reject
              </button>
            )}
            {!isTerminal && candidate.status !== 'archived' && (
              <button onClick={() => archiveM.mutate()} disabled={archiveM.isPending} className="px-3 py-2 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg flex items-center gap-1.5 disabled:opacity-50">
                <Archive className="w-4 h-4" /> Archive
              </button>
            )}
          </div>
        </div>

        {rejectOpen && (
          <div className="mt-3 p-3 bg-rose-50/50 rounded-xl border border-rose-200 flex items-end gap-2">
            <div className="flex-1">
              <label className="text-[10px] font-mono uppercase text-slate-500 block mb-1">Lý do từ chối (bắt buộc)</label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={2}
                className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg"
                placeholder="VD: Không khớp yêu cầu vị trí..."
              />
            </div>
            <button onClick={() => rejectReason.trim() && rejectM.mutate(rejectReason.trim())} disabled={rejectM.isPending || !rejectReason.trim()} className="px-3 py-1.5 text-xs bg-rose-600 text-white rounded-lg disabled:opacity-50">
              Xác nhận reject
            </button>
          </div>
        )}

        <div className="mt-3 text-[11px] text-slate-400 font-mono">
          Tạo: {new Date(candidate.created_at).toLocaleString('vi-VN')} · Cập nhật: {new Date(candidate.updated_at).toLocaleString('vi-VN')}
        </div>
      </div>

      {!!actionError && <ErrorBanner error={actionError} />}

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-700 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{actionSuccess}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/onboarding"
              className="px-3 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-full transition-all flex items-center gap-1"
            >
              <ExternalLink className="w-3 h-3" /> Xem Onboarding
            </Link>
            <button
              onClick={() => setActionSuccess(null)}
              className="text-emerald-500 hover:text-emerald-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: CV + parsed */}
        <div className="lg:col-span-2 space-y-4">
          {candidate.summary && (
            <Section icon={FileText} title="Tóm tắt">
              <p className="text-sm text-slate-600 leading-relaxed">{candidate.summary}</p>
            </Section>
          )}
    {/* Interviews */}
              <Section icon={Calendar} title="Lịch phỏng vấn (Interview — entity riêng, không tự đổi pipeline)">
            {interviews.length === 0 ? (
              <p className="text-xs text-slate-400 mb-2">Chưa có lịch phỏng vấn.</p>
            ) : (
              <ul className="space-y-2 mb-2">
                {interviews.map((iv) => (
                  <li key={iv.id} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="flex items-center justify-between flex-wrap gap-1">
                      <span className="text-xs font-medium text-slate-800">{iv.round_name}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${iv.status === 'scheduled' ? 'bg-indigo-50 text-indigo-600' : iv.status === 'completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>{iv.status}</span>
                    </div>
                    <p className="text-[10px] font-mono text-slate-500 mt-0.5">
                      {new Date(iv.start_at).toLocaleString('vi-VN', { timeZone: iv.timezone })} ({iv.timezone})
                    </p>
                    {iv.needs_relink && <p className="text-[10px] text-amber-600 mt-0.5">⚠ Cần relink calendar event</p>}
                    {iv.status === 'scheduled' && (
                          <div className="flex gap-1.5 mt-2 flex-wrap">
                            <button onClick={() => completeIntM.mutate(iv.id)} disabled={completeIntM.isPending} className="text-[10px] px-2 py-1 bg-emerald-50 text-emerald-600 rounded hover:bg-emerald-100">Hoàn tất</button>
                            <button onClick={() => cancelIntM.mutate(iv.id)} disabled={cancelIntM.isPending} className="text-[10px] px-2 py-1 bg-rose-50 text-rose-600 rounded hover:bg-rose-100">Hủy</button>
                            <button onClick={() => { setReplaceFor(iv.id); setInterviewOpen(true); }} className="text-[10px] px-2 py-1 bg-amber-50 text-amber-600 rounded hover:bg-amber-100">Đổi lịch</button>
                          </div>
                        )}
                        {iv.status === 'cancelled' && !isTerminal && (
                          <div className="flex gap-1.5 mt-2">
                            <button onClick={() => { setReplaceFor(iv.id); setInterviewOpen(true); }} className="text-[10px] px-2 py-1 bg-indigo-50 text-indigo-600 rounded hover:bg-indigo-100">Tạo lịch thay thế</button>
                          </div>
                        )}
                  </li>
                ))}
                            </ul>
                              )}
                              {!isTerminal && (
                                <>
                                  <button onClick={() => { setReplaceFor(null); setInterviewOpen((v) => !v); }} disabled={createIntM.isPending || replaceIntM.isPending} className="text-xs px-3 py-1.5 bg-indigo-600 text-white rounded-lg flex items-center gap-1.5 disabled:opacity-50">
                                    <Plus className="w-3.5 h-3.5" /> {replaceFor ? 'Tạo lịch thay thế' : 'Tạo lịch phỏng vấn'}
                                  </button>
                                  {interviewOpen && (
                                    <InterviewForm
                                      onSubmit={(d) => replaceFor ? replaceIntM.mutate({ ivId: replaceFor, data: d }) : createIntM.mutate(d)}
                                      pending={replaceFor ? replaceIntM.isPending : createIntM.isPending}
                                      onCancel={() => { setInterviewOpen(false); setReplaceFor(null); }}
                                      hasCalendar={!!selectedCalendarId}
                                      isReplacement={!!replaceFor}
                                    />
                                  )}
                                </>
                              )}

                                </Section>

              {candidate.skills.length > 0 && (
                <Section icon={Briefcase} title="Kỹ năng (Field Provenance: AI trích xuất)">
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills.map((s) => (
                      <span key={s} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded font-mono border border-emerald-100">{s}</span>
                    ))}
                  </div>
                </Section>
              )}
              {candidate.experience.length > 0 && (
                <Section icon={Briefcase} title="Kinh nghiệm">
                  <ul className="space-y-1.5">
                    {candidate.experience.map((e, i) => (
                      <li key={i} className="text-xs">
                        <span className="font-medium text-slate-800">{e.role}</span> · <span className="text-slate-500">{e.company}</span>
                        <span className="text-slate-400 font-mono block">{e.duration}</span>
                      </li>
                    ))}
                  </ul>
                </Section>
              )}
              {candidate.education.length > 0 && (
                <Section icon={FileText} title="Học vấn">
                  <ul className="space-y-1.5">
                    {candidate.education.map((e, i) => (
                      <li key={i} className="text-xs">
                        <span className="font-medium text-slate-800">{e.degree}</span> · <span className="text-slate-500">{e.institution}</span>
                        <span className="text-slate-400 font-mono block">{e.year}</span>
                      </li>
                    ))}
                  </ul>
                </Section>
              )}

              {/* CV documents + provenance */}
              <Section icon={FileText} title="Tài liệu CV (provenance từ email/attachment)">
                {candidate.cv_documents.length === 0 ? (
                  <p className="text-xs text-slate-400">Chưa có CV.</p>
                ) : (
                  <ul className="space-y-1.5">
                    {candidate.cv_documents.map((doc) => (
                      <li key={doc.id} className="flex items-center justify-between gap-2 p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-slate-800 truncate">{doc.original_filename}</p>
                          <p className="text-[10px] font-mono text-slate-400">
                            {doc.processing_status} · {(doc.size_bytes / 1024).toFixed(0)}KB · {doc.mime_type}
                          </p>
                        </div>
                        <button
                          onClick={() => viewCV(candidate.id, doc.id, setActionError)}
                          disabled={!doc.presigned_url}
                          className="text-xs px-2.5 py-1 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 disabled:opacity-40 flex items-center gap-1"
                        >
                          <ExternalLink className="w-3 h-3" /> Xem
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {candidate.source_email_message_id && (
                  <p className="text-[10px] font-mono text-slate-400 mt-2">Nguồn: email {candidate.source_email_message_id.slice(0, 12)}…</p>
                )}
              </Section>
            </div>

            {/* Right: assignment */}
        <div className="space-y-4">
          <Section icon={Link2} title="Gán Job Opening (tối đa 1, chỉ 'open')">
            {candidate.job_opening_id ? (
              <div className="p-3 bg-emerald-50/60 border border-emerald-100 rounded-xl">
                <p className="text-xs font-medium text-emerald-700">Đã gán:</p>
                <p className="text-sm text-slate-800">{candidate.job_opening_title || candidate.job_opening_id}</p>
                {!isTerminal && (
                  <div className="flex gap-1.5 mt-2">
                    <button onClick={() => setAssignOpen((v) => !v)} className="text-[10px] px-2 py-1 bg-white border border-slate-200 rounded text-slate-600 hover:bg-slate-50">Đổi</button>
                    <button onClick={() => unassignM.mutate()} disabled={unassignM.isPending} className="text-[10px] px-2 py-1 bg-rose-50 text-rose-600 rounded flex items-center gap-1 disabled:opacity-50">
                      <Unlink className="w-3 h-3" /> Hủy gán
                    </button>
                  </div>
                )}
              </div>
            ) : (
              !isTerminal ? (
                <>
                  <button onClick={() => setAssignOpen((v) => !v)} className="text-xs px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 flex items-center gap-1.5">
                    <Link2 className="w-3.5 h-3.5" /> Gán vị trí tuyển
                  </button>
                  {assignOpen && (
                    <div className="mt-2 space-y-2">
                      <select value={assJob} onChange={(e) => setAssJob(e.target.value)} className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg">
                        <option value="">Chọn vị trí đang tuyển...</option>
                        {openJobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
                      </select>
                      {openJobs.length === 0 && <p className="text-[10px] text-amber-600">Không có Job Opening nào đang <code>open</code>.</p>}
                      <button onClick={() => assJob && assignM.mutate(assJob)} disabled={!assJob || assignM.isPending} className="w-full px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg disabled:opacity-50">
                        Xác nhận gán
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-xs text-slate-400">Ứng viên ở trạng thái terminal — không gán lại được.</p>
              )
            )}
          </Section>

          {candidate.rejection_reason && (
            <Section icon={AlertTriangle} title="Lý do từ chối">
              <p className="text-xs text-slate-600">{candidate.rejection_reason}</p>
              {candidate.rejected_at && <p className="text-[10px] font-mono text-slate-400 mt-1">{new Date(candidate.rejected_at).toLocaleString('vi-VN')}</p>}
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm shadow-slate-100">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-indigo-600" />
        <h3 className="text-sm font-bold text-slate-900">{title}</h3>
      </div>
      {children}
    </div>
  );
}

async function viewCV(candidateId: string, docId: string, setErr: (m: string) => void) {
  try {
    const r = await getCVPresignedUrl(candidateId, docId);
    if (r.presigned_url) window.open(r.presigned_url, '_blank');
  } catch (e) {
    setErr(e instanceof Error ? e.message : 'Lỗi lấy CV');
  }
}

    function InterviewForm({ onSubmit, pending, onCancel, hasCalendar, isReplacement }: { onSubmit: (d: CreateInterviewRequest) => void; pending: boolean; onCancel: () => void; hasCalendar: boolean; isReplacement?: boolean }) {
  const [roundName, setRoundName] = useState('Vòng 1');
  // Use datetime-local → ISO. tz default Asia/Ho_Chi_Minh
  const [start, setStart] = useState('');
  const [duration, setDuration] = useState(60);
  const [mode, setMode] = useState<'google_meet' | 'in_person' | 'custom_link'>('google_meet');
  const [notes, setNotes] = useState('');

  const submit = () => {
    if (!start) return;
    const startDate = new Date(start);
    const endDate = new Date(startDate.getTime() + duration * 60000);
    onSubmit({
      round_name: roundName,
      start: startDate.toISOString(),
      end: endDate.toISOString(),
      timezone: 'Asia/Ho_Chi_Minh',
      mode,
      interviewer_ids: [],
      external_participant_emails: [],
      notes: notes || null,
    });
  };

  return (
    <div className="mt-3 p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-[10px] font-mono uppercase text-slate-500 block mb-1">Vòng</label>
          <input value={roundName} onChange={(e) => setRoundName(e.target.value)} className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg" />
        </div>
        <div>
          <label className="text-[10px] font-mono uppercase text-slate-500 block mb-1">Thời gian bắt đầu</label>
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg" />
        </div>
        <div>
          <label className="text-[10px] font-mono uppercase text-slate-500 block mb-1">Thời lượng (phút)</label>
          <input type="number" value={duration} onChange={(e) => setDuration(Number(e.target.value) || 60)} className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg" />
        </div>
        <div>
          <label className="text-[10px] font-mono uppercase text-slate-500 block mb-1">Hình thức</label>
          <select value={mode} onChange={(e) => setMode(e.target.value as 'google_meet' | 'in_person' | 'custom_link')} className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg">
            <option value="google_meet">Google Meet</option>
            <option value="in_person">Trực tiếp</option>
            <option value="custom_link">Link tùy chỉnh</option>
          </select>
        </div>
      </div>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Ghi chú..." rows={2} className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg" />
                <div className="flex items-center justify-between gap-2">
                  {hasCalendar ? (
                    <p className="text-[10px] text-emerald-600">✅ Calendar đã chọn — sẵn sàng tạo lịch.</p>
                  ) : (
                    <p className="text-[10px] text-amber-600">⚠ Bắt buộc đã chọn Calendar ở Settings/Gmail (GH #214).</p>
                  )}
                  <div className="flex gap-2">
                                        <button onClick={onCancel} className="px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg">Hủy</button>
                                        <button onClick={submit} disabled={pending || !start} className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg disabled:opacity-50">{isReplacement ? 'Tạo thay thế' : 'Tạo'}</button>
                  </div>
                </div>
      </div>
  );
}