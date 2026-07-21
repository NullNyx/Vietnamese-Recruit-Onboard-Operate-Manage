# Knowledge Base RAG — Playwright Test Report

**Date:** 2026-07-21  
**Tester:** AI Agent (Playwright)  
**App URL:** http://localhost:3000  
**Account:** admin@vroomhr.com / VroomAdmin!2026

---

## Summary

| # | Test Case | Result | Notes |
|---|-----------|--------|-------|
| 1 | Login & Navigate to "Tài liệu nội bộ" | ✅ PASS | Sidebar navigation works |
| 2 | HR Tab: Upload PDF + verify status badge | ✅ PASS | Status transitions: pending → ready ("Sẵn sàng") |
| 3 | Nhân viên Tab: Upload PDF + verify | ✅ PASS | Employee KB docs isolated from HR KB |
| 4 | AI Assistant RAG citation | ❌ FAIL | `/api/assistant/chat/stream` endpoint returns 404 |
| 5 | PATCH metadata | ✅ PASS | Display name, category, description updated successfully |
| 6 | DELETE document | ✅ PASS | Document + chunks removed, empty state shown |
| 7 | Filter category/status | ✅ PASS | Both category and status filters work correctly |
| 8 | Empty states | ✅ PASS | Both non-filtered and filtered empty states display properly |

**Overall: 7/8 PASS, 1 FAIL**

---

## Detailed Results

### 1. Login & Navigation — ✅ PASS

- Navigated to `http://localhost:3000` → redirected to `/login`
- Filled `admin@vroomhr.com` / `VroomAdmin!2026`
- Landed on Dashboard after successful login
- Clicked "Tài liệu nội bộ" in sidebar → navigated to `/knowledge-base`

### 2. HR Tab Upload — ✅ PASS

- Clicked "Tải lên tài liệu" on HR tab
- Uploaded `noi-quy-cong-ty.pdf` (2.5 KB) with:
  - Display name: "Nội quy công ty Vroom HR 2025"
  - Category: "Chính sách"
- Document appeared with "Chờ xử lý" badge
- After ~3 seconds: status changed to "Sẵn sàng" (ready)
- Confirmed in database: `status = 'ready'`, chunks created with embeddings

### 3. Nhân viên Tab Upload — ✅ PASS

- Switched to "Nhân viên" tab → saw empty state
- Uploaded `so-tay-nhan-vien.pdf` with:
  - Display name: "Sổ tay nhân viên Vroom HR 2025"
  - Category: "Đào tạo"
- Document processed successfully, status → "ready"
- Confirmed in `employee_knowledge_base_documents` table

### 4. AI Assistant RAG Citation — ❌ FAIL

- Navigated to `/assistant` → AI Assistant chat UI loaded
- Asked: "Quy định về giờ làm việc và nghỉ phép trong công ty như thế nào?"
- Response: "Không tìm thấy tài nguyên — vui lòng thử lại."
- **Root cause:** Backend endpoint `POST /api/assistant/chat/stream` returns **404 Not Found**
- The `chat_stream` method on `AssistantService` is not implemented
- Frontend calls `/api/assistant/chat/stream` but router only has `/chat` (non-streaming)
- This blocks the entire RAG citation flow through the AI Assistant UI

### 5. PATCH Metadata — ✅ PASS

- Clicked "Sửa thông tin" on the document row
- Updated:
  - Display name: "Nội quy công ty Vroom HR 2025" → "Nội quy công ty Vroom HR 2025 (đã cập nhật)"
  - Category: "Chung" → "Chính sách"
  - Description: added "Tài liệu nội quy công ty..."
- Clicked "Lưu thay đổi"
- Verified in DB: `display_name`, `category`, `description` all updated
- UI confirmed the updated display name after page refresh

### 6. DELETE Document — ✅ PASS

- Clicked "Xóa tài liệu" → confirmation dialog appeared
- Clicked "Xóa vĩnh viễn"
- Document removed from DB (`hr_knowledge_base_documents` count = 0)
- Chunks also removed (`hr_knowledge_base_chunks` count = 0)
- UI showed empty state: "Chưa có tài liệu nào trong Knowledge Base HR."

### 7. Filter Category/Status — ✅ PASS

- **Status filter "Sẵn sàng":** showed 1 document ✅
- **Status filter "Đang xử lý":** showed filtered empty state: "Không có tài liệu nào khớp với bộ lọc hiện tại." ✅
- **Category filter "Chính sách":** showed filtered empty state ✅
- **Category filter "Chung":** showed 1 document ✅
- "Xóa bộ lọc" button visible and functional ✅
- Document count label updates correctly ✅

### 8. Empty States — ✅ PASS

- **Non-filtered empty state:** "Chưa có tài liệu nào trong Knowledge Base HR/Nhân viên." + hint "Tải lên tài liệu PDF, DOCX để bắt đầu xây dựng kho kiến thức." ✅
- **Filtered empty state:** "Không có tài liệu nào khớp với bộ lọc hiện tại." + "Thử thay đổi danh mục hoặc trạng thái." + "Xóa bộ lọc" button ✅

---

## Bugs Found & Fixed During Testing

### Bug 1: ARQ Job Queue Collision (Workaround Applied)

**Symptom:** `ingest_document` ARQ job failed with `function 'ingest_document' not found`

**Root Cause:** Multiple ARQ workers (kb-worker, gmail-worker, onboarding-worker) share the same Redis database (`redis://redis:6379/0`) and default queue name. When `ingest_document` was enqueued, the gmail-worker or onboarding-worker would sometimes dequeue it and fail because they don't have that function registered. Similarly, the kb-worker was receiving gmail cron jobs and failing them.

**Workaround:** Stopped gmail-worker and onboarding-worker during testing to allow kb-worker to process jobs exclusively.

**Proper Fix (not yet implemented):** Each worker should use a unique `queue_name` in their ARQ WorkerSettings to isolate job queues. Alternatively, separate Redis databases per worker.

### Bug 2: Embedding Vector Dimension Mismatch — ✅ FIXED

**Symptom:** `asyncpg.exceptions.DataError: expected 768 dimensions, not 1024`

**Root Cause:** The pgvector columns were defined as `Vector(768)` in:
- `backend/alembic/versions/078_create_knowledge_base_tables.py`
- `backend/alembic/versions/079_create_employee_knowledge_base_tables.py`
- `backend/src/modules/knowledge_base/domain/entities.py`

But the embedding model (AITeamVN/Vietnamese_Embedding_v2 or similar) produces **1024-dimensional** vectors.

**Fix Applied:**
1. Altered database columns: `ALTER TABLE ... ALTER COLUMN embedding TYPE vector(1024)`
2. Updated migration files: `Vector(768)` → `Vector(1024)`
3. Updated entity models: `Vector(768)` → `Vector(1024)`
4. Updated docstrings referencing "768-dimensional"

**Files changed:**
- `backend/alembic/versions/078_create_knowledge_base_tables.py:76`
- `backend/alembic/versions/079_create_employee_knowledge_base_tables.py:78`
- `backend/src/modules/knowledge_base/domain/entities.py:54,68,118,132`

### Bug 3: Missing `/chat/stream` Endpoint — ❌ NOT FIXED

**Symptom:** AI Assistant returns "Không tìm thấy tài nguyên" for any query.

**Root Cause:** The frontend `sendStreamMessage()` in `frontend/lib/api/assistant.ts` calls `POST /api/assistant/chat/stream` which does not exist. The backend router at `backend/src/modules/assistant/api/router.py` only has:
- `POST /api/assistant/chat` (non-streaming)
- `POST /api/assistant/feedback`
- `POST /api/assistant/draft-decision`
- `POST /api/assistant/session/start`
- `POST /api/assistant/session/end`

The `chat_stream` method on `AssistantService` is also missing.

**Required Fix:**
1. Add `chat_stream` method to `AssistantService` (similar to `chat` but SSE streaming)
2. Add `POST /api/assistant/chat/stream` endpoint to the router
3. This feature was previously documented in `docs/feature-review/13-employee-assistant/README.md` as a known gap

---

## Test Assets

- PDF 1 (HR): `/tmp/kb-test-files/noi-quy-cong-ty.pdf` — Company regulations (2.6 KB)
- PDF 2 (Employee): `/tmp/kb-test-files/so-tay-nhan-vien.pdf` — Employee handbook (2.6 KB)

---

## Recommendations

1. **Implement `/chat/stream` endpoint** — This is critical for the AI Assistant to function. Without it, the entire RAG chat experience is broken.
2. **Fix ARQ queue isolation** — Add `queue_name` to each worker's settings to prevent job stealing between workers.
3. **Add retry/fallback for ingestion failures** — Currently if ingestion fails, the document stays "pending" forever with no UI indication of the error.
