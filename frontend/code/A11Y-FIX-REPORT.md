# A11y Fix Report — BUG-7 + BUG-8

> Worker a11y. Mục tiêu: sửa 2 bug accessibility chặn cascade ESS (T3/T4/T5-T7) và
> AI test (T9) phát hiện ở `code/E2E-RERUN-REPORT.md` §4. **CHỈ thêm a11y attrs**, không
> đụng feature logic, không refactor Modal API, không sửa backend. KHÔNG commit.

Ngày fix: 2026-07-17. Repo HEAD chưa commit (vroom-hr/components chưa tracked).

---

## 1. BUG-7 (P1) — shared `Modal` thiếu `role="dialog"`

### File
`vroom-hr/components/operate.tsx` — hàm `Modal` (~line 260).

### Root cause
`Modal` render `<div className="fixed inset-0…">` bọc một `<div>` panel nhưng **không
set** `role="dialog"` / `aria-modal` / `aria-label`. Accessibility tree không nhận diện
node là dialog → Playwright `page.getByRole("dialog")` trả 0 element → T3 timeout 20s dù
modal render thị giác + BE `POST …/account` tạo account 200 thành công (có
`temporary_password`). Cascade: T3 không ghi `EMP_CREDS` → T4 skip → T5/T6/T7 không có ESS
session → fail.

### Fix
Giữ `<div>` (KHÔNG nâng lên native `<dialog>` để tránh regress styling/focus của toàn bộ
các trang dùng Modal). Thêm 3 a11y attrs lên panel `<div>` (node đóng vai trò dialog
window), dùng prop `title` hiện có làm `aria-label`:

```diff
   return (
     <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm" onClick={onClose}>
       <div
+        role="dialog"
+        aria-modal="true"
+        aria-label={title}
         className="w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-xl p-5 max-h-[90vh] overflow-y-auto"
         onClick={(e) => e.stopPropagation()}
       >
         <div className="flex items-center justify-between mb-4">
           <h3 className="font-bold text-slate-900 text-sm">{title}</h3>
-          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg leading-none">×</button>
+          <button onClick={onClose} aria-label="Đóng" className="text-slate-400 hover:text-slate-600 text-lg leading-none">×</button>
         </div>
         {children}
       </div>
     </div>
   );
```

Ghi chú:
- `role="dialog"` + `aria-modal="true"` đặt trên panel `<div>` ( KHÔNG phải backdrop) để
  `getByRole("dialog")` match đúng node dialog window.
- `aria-label={title}` dùng trực tiếp prop `title` đã có → mọi caller tự có tên dialog
  ("Tài khoản đã được tạo", "Chi tiết phiếu lương", "Hiệu chỉnh bản ghi chấm công"…).
- `aria-label="Đóng"` trên nút close (`×`) để nút không còn là icon-only vô tên — chuẩn a11y.
- Focus trap / Esc-onClose KHÔNG thêm (theo ràng buộc: tránh regress, ưu tiên `getByRole`
  match). Backdrop click close + nút × close vẫn giữ nguyên behavior cũ.
- Modal API (`{open, onClose, title, children}`) KHÔNG đổi → mọi caller compile không cần sửa.

### Grep usage ảnh hưởng
`rg -n "Modal" vroom-hr/app vroom-hr/components` — tất cả caller dùng prop `{open,
onClose, title, children}` y hệt, không ai truyền `role`/`aria-label` riêng nên không xung
đột prop):

```
components/operate.tsx:260                export function Modal({
app/(employee)/employee/payslips/page.tsx:75    <Modal open={!!viewId} … title="Chi tiết phiếu lương">
app/(employee)/employee/requests/page.tsx:162   <Modal … title="Hủy yêu cầu">
app/(employee)/employee/documents/page.tsx:101  <Modal … title="Tải lên tài liệu">
app/(dashboard)/requests/page.tsx:166          <Modal … title="Từ chối yêu cầu">
app/(dashboard)/attendance/page.tsx:242         <Modal … title="Hiệu chỉnh bản ghi chấm công">
app/(dashboard)/attendance/page.tsx:353        <Modal … title="Thay thế allowlist">
app/(dashboard)/payroll/payslips/page.tsx:237  <Modal … title="Tạo payslip draft">
app/(dashboard)/payroll/payslips/page.tsx:268  <Modal … title={editMode ? 'Sửa payslip draft' : 'Chi tiết payslip'}>
app/(dashboard)/employees/[id]/page.tsx:251   <Modal … title="Tải lên tài liệu">
app/(dashboard)/employees/[id]/page.tsx:302   <Modal … title="Tài khoản đã được tạo">   ← T3 provisioning modal
```

Tất cả caller compile pass (xác nhận bằng `next build` exit 0, §3).

### Opcascade unlock
- T3: `getByRole("dialog")` giờ match → modal "Tài khoản đã được tạo" lộ → test ghi
  `EMP_CREDS` (temporary_password).
- T4: có `EMP_CREDS` → nhánh ESS onboarding login + change-pw chạy.
- T5/T6/T7: có ESS session (`employee.json`) → `/employee/{attendance,requests,payslips}`
  không còn redirect `/login`.

---

## 2. BUG-8 (P2) — AI Assistant send button thiếu accessible name

### File
`vroom-hr/components/AiChat.tsx` — composer send button (~line 566, trong `<form>`
của HR/ESS assistant).

### Root cause
Send button icon-only (`<Send className="w-4 h-4" />` lucide), KHÔNG có `aria-label` /
text → accessibility tree báo button không tên → Playwright
`getByRole("button", { name: /gửi|send/i })` = 0 → T9 skip ở nhánh "composer/send not
found" dù UI + chat API hoạt động (verify thủ công: click → BE trả `502 LLM timeout`
đúng BUG-3, UI surface error + nút "Thử lại").

### Fix
Thêm `aria-label="Gửi"` + `<span className="sr-only">Gửi</span>` (belt-and-suspenders: cả
attribute lẫn sr-only text, để khớp cả `name:/gửi|send/i`无视 rendering):

```diff
             <textarea … disabled={loading} />
             <button
-              type="submit"
+              type="submit"
+              aria-label="Gửi"
               disabled={loading || !input.trim()}
               className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-100 text-white disabled:text-slate-400 rounded-xl transition-all shrink-0 shadow-md shadow-indigo-50"
             >
+              <span className="sr-only">Gửi</span>
               <Send className="w-4 h-4" />
             </button>
```

### Verify selector match
- `aria-label="Gửi"` → accessible name = "Gửi" → `getByRole("button", { name: /gửi/i })`
  match.
- sr-only text "Gửi" là fallback nếu Tailwind purge/`sr-only` class chưa build.
- KHÔNG đụng `handleSend`, `onSubmit`, `loading`, `disabled`, `api.sendMessage` — feature
  logic nguyên vẹn.

### Unlock
- T9: send button match → test gửi câu hỏi → BE trả LLM error (BUG-3, LLM chưa cấu hình)
  → UI surface `replyOrError` → assertion PASS (test đã handle fallback error).

---

## 3. Build

```bash
cd /home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage/vroom-hr
node_modules/.bin/next build
```

Tail pass:

```
✓ Compiled successfully in 3.0s
…
Route (app)                                         Size      First Load JS
…
├ ○ /employee/assistant                  1.32 kB         161 kB
├ ƒ /employees/[id]                      6.67 kB         123 kB
├ ○ /payroll/payslips                    6.82 kB         123 kB
…
ƒ Middleware                             32.3 kB
○  (Static)   prerendered as static content
ƒ (Dynamic)  server-rendered on demand
```

`EXIT_CODE=0`. Không có error/warning mới. 32 routes build OK, bao gồm tất cả trang dùng
`Modal` (`/employees/[id]`, `/payroll/payslips`, `/attendance`, `/requests`,
`/employee/payslips`, `/employee/requests`, `/employee/documents`) và trang AI Assistant
(`/employee/assistant`, `/(dashboard)/assistant`).

---

## 4. Ràng buộc tuân thủ

- ✅ Tiếng Việt.
- ✅ KHÔNG sửa backend (chỉ `vroom-hr/components/operate.tsx` + `vroom-hr/components/AiChat.tsx`).
- ✅ KHÔNG refactor Modal API — chỉ thêm `role`/`aria-modal`/`aria-label` (+ `aria-label`
  cho nút close).
- ✅ KHÔNG đụng feature logic (chỉ a11y attrs).
- ✅ Build PASS rồi dừng.
- ✅ KHÔNG commit.

---

## 5. Việc tiếp theo cho orchestrator

1. Re-run e2e smoke 9 test (`pnpm exec playwright test --reporter=list`) để xác nhận:
   - T3 ❌→✅ (modal match, ghi `EMP_CREDS`).
   - T4 ❌SKIP→✅ (cascade unlock).
   - T5/T6/T7 ❌→✅ (có ESS session).
   - T9 ❌SKIP→✅ (send button match → LLM-error assertion pass).
2. Bug còn lại không thuộc scope a11y: BUG-2 (CORS), BUG-3 (LLM env), BUG-4 (Google
   Workspace connect) — đã note trong `E2E-RERUN-REPORT.md` §4, không chặn smoke.