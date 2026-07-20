# 13 — Employee Assistant

> **Nhóm:** Employee Assistant | **Tổng:** 2 chức năng | **Deployed:** 2 | **Pending Review:** 2
> **Backend module:** `backend/src/modules/assistant/` (employee router)
> **Frontend:** ESS Assistant

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| EA-01 | Hội thoại Employee | Scope theo session; đọc dữ liệu cá nhân; draft request thuộc chính Employee | `/api/ess/assistant/*` | ESS Assistant | ✅ Deployed | ⬜ |
| EA-02 | Chat/Session/Feedback | Chat, feedback, session-start, session-end | `/api/ess/assistant/*` | ESS Assistant | ✅ Deployed | ⬜ |

---

## Tiêu chí Review (Backend Security)

- [x] Router đã wired trong `backend/src/main.py`
- [x] Chỉ Employee active truy cập
- [x] employee_id lấy từ session, không nhận từ LLM
- [x] Chỉ đọc dữ liệu của chính Employee đó
- [x] Chỉ draft action thuộc Employee (request nghỉ, làm thêm...)
- [x] Không tự ghi database

## Tiêu chí Review (UX / Người dùng)

- [x] SSE streaming hoạt động cho Employee Assistant
- [x] Tool labels/icon hiển thị tiếng Việt cho employee tools
- [x] Draft Action confirm dùng UI dialog thay vì window.confirm()
- [x] Session management nhất quán giữa frontend và backend
- [x] Error message thân thiện, có fallback khi streaming fail
- [ ] Conversation history không mất khi refresh trang (cân nhắc)

---

## Kết quả Review từng chức năng

### EA-01 — Hội thoại Employee
- **Ngày review:** 2025-07-14
- **Người review:** AI Agent (UX perspective)
- **Kết quả:** ✅ Đã fix — Backend logic + security OK. SSE streaming đã thêm. Tool labels đã thêm tiếng Việt.
- **Ghi chú:** Fixes: `chat_stream` method + `/chat/stream` endpoint + `sendEmployeeStreamMessage` + `AiChat` routing fix.

### EA-02 — Chat/Session/Feedback
- **Ngày review:** 2025-07-14
- **Người review:** AI Agent (UX perspective)
- **Kết quả:** ✅ Đã fix — Session/feedback flow OK. window.confirm đã remove. `startEmployeeSession` đã simplify.
- **Ghi chú:** Fixes: Remove `window.confirm()`, simplify `startEmployeeSession()`, add `sendStreamMessage` to `AiChatApi`.

---

## Phân tích chi tiết từ góc độ người dùng (UX)

### 🔴 CRITICAL — SSE Streaming bị broken cho Employee Assistant

**Mô tả:** Khi Employee gõ tin nhắn, `AiChat` component gọi `sendStreamMessage()` imported trực tiếp từ `@/lib/api/assistant`. Hàm này hardcode `BASE = /api/assistant` (HR endpoint), không phải `/api/ess/assistant` (Employee endpoint).

**File liên quan:**
- `frontend/components/AiChat.tsx:134` — `fetch(\`${BASE}/chat/stream\`, ...)` với BASE từ `@/lib/api/assistant`
- `frontend/components/AiChat.tsx:14` — `import { sendStreamMessage } from '@/lib/api/assistant'`
- `frontend/lib/api/assistant.ts:11` — `const BASE = \`${API_BASE_URL}/api/assistant\``

**Hậu quả:**
1. Request bị gửi đến `/api/assistant/chat/stream` (HR router) — endpoint này yêu cầu `require_admin` → luôn trả về **403 Forbidden** cho Employee.
2. Backend `employee_assistant_router` **không có** `/chat/stream` endpoint — chỉ có `/chat` (non-streaming).
3. `EmployeeAssistantService` **không có** method `chat_stream` — chỉ có `chat`.
4. `frontend/lib/api/employee-assistant.ts` **không export** `sendStreamMessage` — chỉ có `sendEmployeeChatMessage`.
5. `AiChat` component **không bao giờ gọi** `api.sendMessage` — luôn dùng `sendStreamMessage` import trực tiếp.
6. Error bar hiện "Bạn không có quyền thực hiện thao tác này" → người dùng bấm "Thử lại" → lặp vô hạn.

**Impact:** **Toàn bộ tính năng chat của Employee Assistant không hoạt động.** Đây là bug P0.

**Cách khắc phục đề xuất:**
1. Thêm `chat_stream` method vào `EmployeeAssistantService` (hiện tại chỉ HR `AssistantService` có).
2. Thêm `POST /api/ess/assistant/chat/stream` endpoint vào `employee_router.py`.
3. Export `sendEmployeeStreamMessage` từ `employee-assistant.ts` trỏ đến `/api/ess/assistant/chat/stream`.
4. Sửa `AiChat` component để dùng `api.sendStreamMessage` qua prop thay vì import trực tiếp, hoặc ít nhất detect `assistantType === 'employee'` để chọn đúng endpoint.

---

### 🟡 HIGH — Tool execution labels hiển thị raw name cho Employee

**Mô tả:** Khi SSE streaming chạy tool, component hiển thị chip trạng thái tool với label tiếng Việt và icon. Nhưng `TOOL_LABELS` và `TOOL_ICONS` trong `AiChat.tsx` **chỉ map HR tools**. Các employee tool như `get_my_profile`, `list_my_attendance_records`, `draft_leave_request`... không có entry → hiển thị raw technical name.

**File:** `frontend/components/AiChat.tsx:85-109`

**Ví dụ:**
- `get_my_profile` → hiển thị "get_my_profile" thay vì "Hồ sơ của tôi"
- `draft_leave_request` → hiển thị "draft_leave_request" thay vì "Soạn đơn nghỉ phép"
- `list_my_payslips` → hiển thị "list_my_payslips" thay vì "Bảng lương của tôi"

**Cần thêm vào `TOOL_LABELS` và `TOOL_ICONS`:**
```typescript
get_my_profile: 'Hồ sơ của tôi',
list_my_documents: 'Tài liệu của tôi',
get_today_attendance: 'Chấm công hôm nay',
list_my_attendance_records: 'Lịch sử chấm công',
list_my_employee_requests: 'Yêu cầu của tôi',
get_my_leave_balance: 'Số dư nghỉ phép',
list_my_payslips: 'Bảng lương của tôi',
draft_leave_request: 'Soạn đơn nghỉ phép',
draft_overtime_request: 'Soạn đơn tăng ca',
```

---

### 🟡 MEDIUM — Draft Action confirmation dùng `window.confirm()` thô

**Mô tả:** Employee Assistant page (`employee/assistant/page.tsx`) không truyền `onOpenRequestDialog` prop cho `AiChat`. Khi employee nhận được Draft Action (đơn nghỉ phép / tăng ca), component fallback xuống `window.confirm()` — một dialog trình duyệt thô sơ, không thể custom style, không hỗ trợ tiếng Việt tốt trên một số trình duyệt.

**File:** `frontend/components/AiChat.tsx:557`

**So sánh:** HR Assistant page cũng không truyền `onOpenRequestDialog`, nhưng HR assistant dùng chung `DraftActionCard` với nút "Xác nhận & Ghi dữ liệu" đẹp hơn. Sự khác biệt là HR Draft Action không trigger `window.confirm` mà gọi `handleDraftConfirm` trực tiếp. Employee flow cũng gọi `handleDraftConfirm` nhưng logic bên trong check `onOpenRequestDialog`:

```typescript
if (onOpenRequestDialog && (draftAction.action_type === 'submit_leave_request' || ...)) {
  // dùng custom dialog
} else {
  const confirmed = window.confirm(...)  // ← Employee rơi vào đây
}
```

**Đề xuất:** Implement một modal dialog đẹp cho Employee xác nhận đơn nghỉ/tăng ca, hoặc ít nhất thay `window.confirm` bằng custom confirm component.

---

### 🟡 MEDIUM — Không có fallback khi SSE streaming thất bại

**Mô tả:** `AiChat.handleSend` chỉ gọi `sendStreamMessage`. Nếu streaming thất bại (network, timeout, endpoint không hỗ trợ), component hiển thị lỗi nhưng **không tự fallback** sang non-streaming `api.sendMessage`. Người dùng phải bấm "Thử lại" và lặp fail.

**File:** `frontend/components/AiChat.tsx:449-519`

**Lưu ý:** `api.sendMessage` (tức `sendEmployeeChatMessage`) đã được implement đầy đủ trong `employee-assistant.ts` và backend `/api/ess/assistant/chat` hoạt động tốt. Chỉ cần thêm fallback logic.

---

### 🟢 LOW — SessionStartRequest body bị ignore bởi employee router

**Mô tả:** `startEmployeeSession` gửi `{ assistant_type: assistantType }` lên `/api/ess/assistant/session/start`. Nhưng backend `start_employee_assistant_session` **bỏ qua** `body.assistant_type` và hardcode `assistant_type="employee"`. Điều này an toàn về mặt security, nhưng:
- `assistantType` parameter trong `startEmployeeSession` vô nghĩa — luôn nhận `"employee"` từ caller.
- Nếu ai đó vô tình gọi `startEmployeeSession("hr")`, session vẫn được tạo với type "employee" mà không có warning.

**File:** `backend/src/modules/assistant/api/employee_router.py:217-227`

**Đề xuất:** Bỏ `assistant_type` khỏi `SessionStartRequest` khi dùng cho employee router, hoặc validate `assistant_type === "employee"` và reject nếu khác.

---

### 🟢 LOW — Không có audit logging cho Employee Assistant

**Mô tả:** HR Assistant log audit event cho mọi Draft Action và feedback. Employee Assistant **không có** audit logging nào. Điều này có thể chấp nhận được nếu employee action vốn đã được audit ở tầng request write (`/api/employee-requests/me/*`), nhưng việc **ai đã dùng assistant**, **tool nào được gọi**, và **feedback nào được gửi** nên được track để đo lường chất lượng.

**File:** So sánh `router.py:127-134` (có audit) vs `employee_router.py` (không có audit).

---

### 🟢 LOW — Suggestion chip "Lịch chấm công tuần này" không khớp tool capability

**Mô tả:** Default suggestion cho Employee Assistant:
```typescript
['Số dư phép của tôi?', 'Soạn đơn nghỉ phép 2 ngày', 'Lịch chấm công tuần này']
```
Nhưng tool `list_my_attendance_records` nhận `month` và `year`, không hỗ trợ filter theo tuần. LLM vẫn có thể xử lý (gọi tool với tháng hiện tại rồi tự lọc), nhưng suggestion nên khớp với capability thực tế.

**Đề xuất:** Đổi thành `'Lịch sử chấm công tháng này'`.

---

### ✅ ĐIỂM TỐT — Những thứ làm đúng từ góc nhìn UX

1. **Security model đúng**: `employee_id` không bao giờ expose cho LLM, luôn inject từ session. Mỗi handler tool đều có `args.pop("employee_id", None)` phòng thủ.
2. **Human-in-the-loop**: Draft Action chỉ tạo preview, không tự ghi DB. Người dùng xác nhận → frontend gọi endpoint thực. ADR-0006 được tuân thủ.
3. **Scope cô lập**: `EmployeeToolRegistry` block HR tool names, trả về `scope_denied` nếu LLM cố gọi HR tool.
4. **Context injection**: `ContextBuilder.build_employee_context` cung cấp thông tin cá nhân (tên, phòng ban, số dư phép, pending requests) vào system prompt → LLM trả lời chính xác hơn.
5. **Session lifecycle**: Mount → `startSession`, Unmount → `endSession`. Có tracking message_count.
6. **Error message tiếng Việt**: `toUserError()` map HTTP status code sang thông báo tiếng Việt dễ hiểu.
7. **Feedback (thumbs up/down)**: Có UI feedback row sau mỗi assistant message, lưu vào DB.
8. **Keyboard shortcut Ctrl+J**: Focus nhanh vào textarea.
9. **Loading steps animation**: Các bước "Đang phân tích câu hỏi..." → "Đang soạn câu trả lời..." giúp người dùng biết hệ thống đang làm việc.
10. **Tool status chips**: Hiển thị real-time tool đang chạy (dù label còn thiếu cho employee tools — xem mục HIGH ở trên).

---

## Tổng kết

| Hạng mục | Trạng thái |
|----------|------------|
| Backend security (6 tiêu chí) | ✅ Pass |
| SSE Streaming hoạt động | ✅ **Đã fix** |
| Tool labels tiếng Việt | ✅ **Đã fix** |
| Draft confirm UX | ✅ **Đã fix** |
| Streaming fallback | ✅ **Đã fix** (fallback to `api.sendMessage`) |
| Session consistency | ✅ **Đã fix** (`startEmployeeSession` simplified) |
| Audit logging | 🟢 Missing (nice-to-have) |
| Suggestion accuracy | ✅ **Đã fix** |
