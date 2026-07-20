# 12 — AI Assistant (HR)

> **Nhóm:** AI Assistant (HR) | **Tổng:** 3 chức năng | **Deployed:** 3 | **Reviewed:** 3 (UX Review ✅)
> **Backend module:** `backend/src/modules/assistant/`
> **Frontend:** Admin Assistant

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| HA-01 | Hội thoại HR | Chat; 8 Read-Tools + 2 Draft-Tools; **không write-tool** cho LLM | `/api/assistant` | Admin Assistant | ✅ Deployed | 🔴 |
| HA-02 | Human-in-the-loop | Draft Action → preview/provenance → HR confirm → write endpoint thật | Assistant service + DraftActionCard | Confirmation UI | ✅ Deployed | 🟡 |
| HA-03 | Context & Quality | Context Block Builder, quality metrics, safe config | `assistant/application/context_builder.py` | — | ✅ Deployed | 🔴 |

---

## Read-Tools & Draft-Tools hiện có

**Read-Tools (8):**
- `count_candidates_by_status`
- `list_interviews_for_candidate`
- `get_onboarding_task_details`
- `list_in_progress_onboarding`
- `search_candidates`
- `get_candidate_parsed_cv`
- `list_job_openings`
- `get_department_info`

**Draft-Tools (2):**
- `draft_interview_invitation`
- `draft_congratulations_email`

---

## Migration liên quan

- `075` — Tạo 3 bảng assistant quality

---

## UX Review — Góc độ người dùng (Ngày review: 2025-07-15)

Review toàn diện từ góc độ người dùng HR và Employee, bao gồm luồng thao tác,
phản hồi UI, error handling, và tính liền mạch của trải nghiệm.

### 🔴 Critical — Lỗi chặn người dùng

**1. Endpoint `/feedback` bị nest sai indent — thumbs up/down không bao giờ được ghi nhận**

Cả `router.py:139` và `employee_router.py:186` định nghĩa route `/feedback` bên trong
hàm `chat`/`employee_chat` (indent 4 spaces = function body), thay vì ở module level.
FastAPI sẽ không register route con của một function. Hậu quả: khi user click 👍/👎,
frontend gọi `POST /api/assistant/feedback` hoặc `POST /api/ess/assistant/feedback`
và nhận **404 Not Found**. Frontend nuốt lỗi (`.catch(() => {})`), nên user không thấy
thông báo lỗi nào — nhưng feedback không được lưu.

*File:* `backend/src/modules/assistant/api/router.py:139-170`
*File:* `backend/src/modules/assistant/api/employee_router.py:186-204`

**Fix:** Đưa `@router.post("/feedback", ...)` ra module level (0 indent) như các route
`/draft-decision`, `/session/start`, `/session/end`.

**2. Không có confirmation dialog trước khi gửi email thật**

Khi HR click "Xác nhận & Ghi dữ liệu" trên DraftActionCard, hệ thống gọi luôn
endpoint gửi email (`POST /api/recruitment/candidates/{id}/send-email`)
mà không có bước confirm trung gian. Dù DraftActionCard đã hiển thị preview,
một cú click nhầm vẫn gửi email thật ngay lập tức.

*File:* `frontend/components/AiChat.tsx:362-390` (`handleDraftConfirm`)

**Fix:** Thêm một dialog/confirm nhỏ: "Bạn có chắc muốn gửi email này?" trước khi gọi
`api.confirmAction`.

---

### 🟠 High — Ảnh hưởng nghiêm trọng đến UX

**3. Không có nút "Cuộc trò chuyện mới" / "Xóa lịch sử"**

User phải reload trang (F5) để bắt đầu cuộc trò chuyện mới. Với hội thoại dài,
context bị phình to (dù backend trim 20 messages), các câu hỏi cũ vẫn hiển thị
trong chat. Điều này gây rối khi HR muốn hỏi một chủ đề hoàn toàn khác.

*File:* `frontend/components/AiChat.tsx:255-580` (không có nút reset)

**Fix:** Thêm nút "➕ Cuộc trò chuyện mới" ở header. Khi click: reset `messages` về `[]`,
gọi `endSession` + `startSession` mới, xoá `draftAction`.

**4. Textarea chỉ 1 dòng, không expand theo nội dung**

Textarea có `rows={1}` với `resize-none max-h-32`. User gõ câu hỏi dài (VD: mô tả
ngữ cảnh phức tạp) bị giới hạn trong 1 dòng. `max-h-32` cho phép scroll nhẹ nhưng
textarea không tự động grow khi user gõ nhiều dòng.

*File:* `frontend/components/AiChat.tsx:556-565`

**Fix:** Dùng `auto-resize` textarea (set `style.height = 'auto'` rồi
`style.height = scrollHeight + 'px'` trong `onChange`) hoặc tăng `rows={2-3}`.

**5. Không có indicator tiến trình khi LLM gọi nhiều tool**

Khi user hỏi câu phức tạp, LLM có thể gọi 2-3 tools tuần tự (VD: search_candidates
→ get_candidate_parsed_cv → draft_interview_invitation). User chỉ thấy 1 spinner
"Trợ lý đang truy vấn dữ liệu và phân tích..." suốt 5-15 giây, không biết hệ thống
đang làm gì.

*File:* `frontend/components/AiChat.tsx:490-500` (loading indicator)

**Fix:** Hiển thị step indicator: "Đang tìm ứng viên..." → "Đang đọc CV..." →
"Đang soạn email..." dựa trên tool_calls trong streaming response.

**6. Không có streaming — user phải đợi toàn bộ response**

Response được gửi về nguyên khối sau khi tool-calling loop hoàn tất. Với câu hỏi
cần 3 tool calls, user đợi 10-15 giây không thấy gì. Nếu timeout, user thấy lỗi
chung chung "Yêu cầu đã hết thời gian chờ".

*File:* `backend/src/modules/assistant/api/router.py:100-137` (trả về 1 lần)

**Fix:** Cân nhắc Server-Sent Events (SSE) để stream từng bước: tool call →
tool result → text response.

---

### 🟡 Medium — Gây bất tiện nhưng không chặn

**7. Click suggestion chip không tự send**

Khi click chip gợi ý (VD: "Có bao nhiêu candidate đang reviewing?"), text được điền
vào textarea nhưng không tự gửi. User phải làm thêm 1 bước: nhấn Enter hoặc click
nút Gửi. Điều này làm giảm tính "trợ lý nhanh".

*File:* `frontend/components/AiChat.tsx:439-452`

**Fix:** Click suggestion chip → auto-send luôn (gọi `handleSend(suggestionText)`).

**8. Không hiển thị thông báo xác nhận sau khi feedback được gửi**

Khi user click 👍/👎, icon đổi màu nhưng không có toast/thông báo. User không
biết feedback đã được ghi nhận chưa (đặc biệt nếu endpoint 404 như bug #1).

*File:* `frontend/components/AiChat.tsx:214-249` (FeedbackRow)

**Fix:** Thêm toast nhỏ "Cảm ơn phản hồi của bạn" hoặc ít nhất giữ trạng thái
đã chọn rõ ràng hơn.

**9. Thiếu thông tin lỗi thân thiện khi confirm email thất bại**

Nếu `confirmDraftAction` thất bại, error hiển thị là `e.message` từ network layer:
VD: "Confirm API 500: Internal Server Error". Không có message tiếng Việt dễ hiểu.

*File:* `frontend/components/AiChat.tsx:105-108`

**Fix:** Map error codes sang message tiếng Việt: "Gửi email thất bại — vui lòng
thử lại hoặc gửi thủ công từ trang Ứng viên."

**10. Không có hậu kiểm sau confirm — mất conversational continuity**

Sau khi HR confirm gửi email, DraftActionCard hiển thị "Đã xác nhận và ghi thành
công" nhưng trợ lý AI không được thông báo. Không có follow-up message kiểu
"Email đã được gửi thành công đến Nguyễn Văn A." Cuộc hội thoại kết thúc đột ngột.

*File:* `frontend/components/AiChat.tsx:362-390`

**Fix:** Sau khi confirm thành công, append một system/assistant message xác nhận
vào chat: "✅ Đã gửi thư mời phỏng vấn đến ..."

**11. Confirm rồi recordDecision lỗi → mất audit trail**

`handleDraftConfirm` gọi `api.confirmAction` (gửi email) TRƯỚC rồi mới gọi
`api.recordDecision` (ghi audit). Nếu `recordDecision` fail (network error),
email đã được gửi nhưng không có audit trail. Thứ tự này nên đảo ngược:
ghi audit trước, hoặc dùng transaction/saga pattern.

*File:* `frontend/components/AiChat.tsx:387-388`
  `await api.confirmAction(draftAction);`
  `await api.recordDecision?.(draftAction, 'confirm');`

**Fix:** Gọi `recordDecision` trước (best-effort audit), rồi mới confirm.
Hoặc backend nên tự audit khi confirm endpoint được gọi.

---

### 🟢 Low — Cải tiến nhỏ

**12. Session startup chậm — welcome message xuất hiện trước khi session sẵn sàng**

`startSession` là async trong `useEffect`, welcome message hiển thị ngay lập tức.
Tin nhắn đầu tiên có thể được gửi trước khi session_id được gán → message đó
không có tool_call_event record. Tác động thấp vì chỉ ảnh hưởng analytics.

*File:* `frontend/components/AiChat.tsx:300-318`

**13. Không hỗ trợ keyboard shortcut để focus textarea**

Không có shortcut như `Ctrl+Shift+A` để jump focus vào textarea assistant.
HR phải dùng chuột để click vào textarea mỗi lần muốn hỏi.

**14. Timestamp không hiển thị trên mỗi message**

Hàm `nowTime()` được định nghĩa nhưng không dùng. Không có timestamp trên từng
message, user không biết message được gửi lúc nào.

*File:* `frontend/components/AiChat.tsx:51-53` (unused function)

---

## Tổng kết UX Review

| Mức độ | Số lượng | Hành động |
|--------|----------|-----------|
| 🔴 Critical | 2 | Phải fix trước khi release cho user thật |
| 🟠 High | 4 | Nên fix trong sprint tiếp theo |
| 🟡 Medium | 5 | Cần fix nhưng không gấp |
| 🟢 Low | 3 | Nice-to-have, có thể defer |

**Điểm mạnh UX:**
- Human-in-the-loop được thiết kế tốt: preview → provenance → confirm rõ ràng
- DraftActionCard UI đẹp, thông tin rõ ràng, có expand/collapse provenance
- Error state có nút "Thử lại" tiện lợi
- Giao diện chat quen thuộc, responsive, dark header tương phản tốt
- Defensive: frontend strip tool messages, backend validate endpoint /api/,
  confirm_endpoint có validator chặn URL ngoài

**Điểm yếu UX chính:**
- Feedback endpoint broken → mất toàn bộ quality metrics
- Thiếu streaming → user đợi lâu không phản hồi
- Không có nút New Chat → phải F5
- Thiếu confirmation dialog trước write

## Tiêu chí Review

- [x] Router đã wired trong `backend/src/main.py`
- [x] **Không write-tool** nào được cấp cho LLM (ranh giới an toàn cấu trúc)
- [x] Draft Action: preview, provenance, confirm → frontend gọi write endpoint thật
- [x] Context Block Builder inject context động
- [ ] Quality metrics + safe config — 🔴 `/feedback` endpoint 404 do indent bug
- [ ] Tool config seed (enabled/disabled) hoạt động — 🟡 chưa thấy auto-seeder

---

## Kết quả Review từng chức năng

### HA-01 — Hội thoại HR
- **Ngày review:** 2025-07-15
- **Người review:** AI UX Review
- **Kết quả:** 🔴 Có lỗi
- **Ghi chú:**
  - ✅ Read-Tools (8) + Draft-Tools (2) hoạt động đúng, không có write-tool
  - ✅ Router wired, `/chat` hoạt động
  - ✅ Frontend sanitize tool messages trước khi gửi
  - 🔴 **Critical:** `/feedback` endpoint bị nest sai indent trong `router.py:139` → 404
  - 🟠 Textarea 1 dòng, không auto-resize
  - 🟠 Không có nút "Cuộc trò chuyện mới"
  - 🟠 Thiếu streaming/progress indicator khi multi-tool
  - 🟡 Suggestion chips không auto-send
  - 🟡 Thiếu timestamp trên message

### HA-02 — Human-in-the-loop
- **Ngày review:** 2025-07-15
- **Người review:** AI UX Review
- **Kết quả:** 🟡 Có vấn đề
- **Ghi chú:**
  - ✅ DraftActionCard UI đẹp, preview + provenance rõ ràng
  - ✅ Confirm gọi write endpoint thật, không qua LLM
  - ✅ Defensive: confirm_endpoint validator chặn URL ngoài
  - ✅ Employee assistant có scoped guard riêng
  - 🔴 **Critical:** Không có confirm dialog trước khi gửi email thật
  - 🟡 Sau confirm không có follow-up message → mất conversational continuity
  - 🟡 recordDecision gọi sau confirm → có thể mất audit trail nếu network lỗi
  - 🟡 DraftActionCard error message là raw network error, không có i18n

### HA-03 — Context & Quality
- **Ngày review:** 2025-07-15
- **Người review:** AI UX Review
- **Kết quả:** 🔴 Có lỗi
- **Ghi chú:**
  - ✅ Context Block Builder inject context động (org name, pipeline, openings)
  - ✅ Quality metrics models đầy đủ (sessions, feedback, tool_call_events)
  - ✅ Safe config: tool toggle per DB row
  - 🔴 **Critical:** `/feedback` endpoint broken ở cả 2 router → quality metrics không thu thập được
  - 🟡 Tool config seed: không thấy seeder tự động, chỉ có repo upsert
