# 05 — Interview & Calendar

> **Nhóm:** Interview & Calendar | **Tổng:** 3 chức năng | **Deployed:** 3 | **Pending Review:** 3
> **Backend module:** `backend/src/modules/recruitment/` (interview, conflict routes)
> **Frontend:** `frontend/app/(dashboard)/recruitment/interviews/` + Candidate detail dialogs

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| IV-01 | Tạo Interview | Entity riêng: round, time, timezone, mode, participants, calendar event; bắt buộc selected Calendar | `POST /api/recruitment/candidates/{id}/schedule-interview`, `POST .../create-interview` | Candidate detail dialogs (`/recruitment/candidates/[id]`) | ✅ Deployed | ⬜ |
| IV-02 | Interview Lifecycle | `scheduled → completed/cancelled`; reschedule giữ entity; replacement tạo mới | `POST .../interviews/{id}/complete`, `.../cancel`, `.../replacement`, `.../reschedule-interview` | `/recruitment/interviews` | ✅ Deployed | ⬜ |
| IV-03 | Calendar Sync & Conflict | Selected calendar, sync cursor, ETag/conflict, xử lý 410/412 | `/api/recruitment/calendar-conflicts/*` | `/recruitment/interviews` (conflict section) | ✅ Deployed | ⬜ |

---

## ADR & Docs liên quan

- `CONTEXT.md` — Interview entity lifecycle, Calendar domain definition
- Cross-ref: `docs/feature-review/04-recruitment/README.md` RC-08 (cùng conflict router)

---

## Migration liên quan

- `046` — Create `interviews` + `interview_participants` tables (tách entity khỏi Candidate)
- `049` — Add `calendar_etag`, `meeting_mode`, `meeting_link`, `response_status`
- `050` — Create `calendar_sync_cursors` table
- `052` — Create `calendar_conflicts` table (410/412 resolution)
- `054` — Drop legacy Candidate calendar fields (sau backfill 046)
- `072` — Add `interview_calendar_id`
- `073` — Add `calendar_id` to sync cursors
- `074` — Backfill Candidate calendar fields → Interview, drop legacy columns (GH #215)

---

## Tiêu chí Review

- [ ] Router đã wired trong `backend/src/main.py`
- [ ] Interview không tự đổi Candidate pipeline
- [ ] Reschedule giữ entity; replacement tạo mới + lịch sử cancelled
- [ ] Calendar conflict xử lý đúng (410/412)
- [ ] Bắt buộc selected Calendar khi tạo Interview (GH #214)
- [ ] Backfill migration hoàn tất (GH #215)
- [ ] Integration test coverage (`backend/tests/modules/recruitment/test_interview_*.py`, `test_calendar_*.py`)
- [ ] AuthZ: Admin cho conflict resolve; HR cho interview CRUD

---

## Kết quả Review từng chức năng

### IV-01 — Tạo Interview
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### IV-02 — Interview Lifecycle
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### IV-03 — Calendar Sync & Conflict
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —
