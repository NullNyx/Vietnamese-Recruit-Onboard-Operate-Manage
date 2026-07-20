# 04 — Recruitment (Tuyển dụng)

> **Nhóm:** Recruitment | **Tổng:** 9 chức năng | **Deployed:** 9 | **Pending Review:** 9
> **Backend module:** `backend/src/modules/recruitment/`
> **Frontend:** `frontend/app/(dashboard)/recruitment/`

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| RC-01 | Recruitment Inbox | Workspace hợp nhất: cần xác nhận, cần bổ sung, sẵn sàng review, đã xử lý | `/api/recruitment/inbox*` | `/recruitment/inbox` | ✅ Deployed | ⬜ |
| RC-02 | Job Application | AI tạo từ email; HR promote → Candidate | `/api/recruitment/job-applications*` | Promote/Dismiss/Link từ Inbox | ✅ Deployed | ⬜ |
| RC-03 | Candidate Pipeline | `new → reviewing → interview_scheduled → accepted/rejected/archived` | `/api/recruitment/candidates*` | `/recruitment/candidates`, `/recruitment/interviews` | ✅ Deployed | ⬜ |
| RC-04 | Job Opening | CRUD, open/close/cancel; headcount metrics | `/api/recruitment/job-openings*` | Job Openings UI | ✅ Deployed | ⬜ |
| RC-05 | Candidate Assignment | Gán tối đa 1 Job Opening; chặn ở status terminal | `/api/recruitment/candidates/*/assign` | Assign/Reassign dialog (Candidate detail) | ✅ Deployed | ⬜ |
| RC-06 | Review Queue | CV review queue, confidence/provenance, correction | `/api/recruitment/cv-review` | `/recruitment/review` | ✅ Deployed | ⬜ |
| RC-07 | Metrics Dashboard | Pipeline & Job Opening metrics từ dữ liệu live | `/api/recruitment/metrics` | `/recruitment/metrics` | ✅ Deployed | ⬜ |
| RC-08 | Calendar Conflicts | Liệt kê & resolve conflict Google Calendar vs Vroom | `/api/recruitment/calendar-conflicts*` | Conflict management UI | ✅ Deployed | ⬜ |
| RC-09 | Evaluation Management | Quản lý evaluation sets, samples, correction records | `/api/recruitment/evaluation*` | Evaluation UI | ✅ Deployed | ⬜ |

---

## ADR & Docs liên quan

- `docs/adr/0004-job-application-classification-boundary.md`
- `docs/runbooks/job-application-classification-rollout.md`

---

## Tiêu chí Review

- [ ] Router đã wired trong `backend/src/main.py`
- [ ] Backbone flow: email → inbox → candidate → interview → accepted → onboarding
- [ ] Invariant: AI không tự tạo Candidate; chỉ HR promote
- [ ] Invariant: Candidate gán tối đa 1 Job Opening; Job Opening phải `open`
- [ ] Job Application contract (migr `068`)
- [ ] Error handling + error handler đã đăng ký
- [ ] Integration test coverage (`backend/tests/modules/recruitment/`)
- [ ] AuthZ: role phù hợp cho từng endpoint (HR vs Admin)

---

## Kết quả Review từng chức năng

### RC-01 — Recruitment Inbox
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-02 — Job Application
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-03 — Candidate Pipeline
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-04 — Job Opening
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-05 — Candidate Assignment
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-06 — Review Queue
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-07 — Metrics Dashboard
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-08 — Calendar Conflicts
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### RC-09 — Evaluation Management
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —


