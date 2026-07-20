# 15 — Frontend UI

> **Nhóm:** Frontend UI | **Tổng:** 8 chức năng | **Deployed:** 8 | **Reviewed:** 8
> **Frontend:** `frontend/app/`, `frontend/components/`
> **Design System:** AI Studio — Inter font + Warm Professional palette + Motion animations

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Trang/Component | Status | Review |
|----|-----------|------------|-----------------|--------|--------|
| UI-01 | Shell & Navigation | HR dashboard, ESS layout, nav nhóm (Nhân sự/Tuyển dụng/Chấm công/Lương/Hệ thống), responsive/mobile, dark mode + breadcrumb + hover | `layout.tsx`, nav components | ✅ Deployed | ⚠️ |
| UI-02 | Design System | Inter + Warm Professional palette (đỏ+amber+xanh, radius 6px) + Motion LazyMotion/AutoAnimate; 9 Playwright visual snapshot test | `globals.css`, `layout.tsx` | ✅ Deployed | ⚠️ |
| UI-03 | Auth Pages | `/setup` (3-step wizard), `/login`, `/change-password` | `setup/`, `login/`, `change-password/` | ✅ Deployed | ✅ |
| UI-04 | Recruitment UI | Pipeline, inbox, detail, review, job openings, metrics, interview dialogs, conflict manager | `(dashboard)/recruitment/` | ✅ Deployed | 🔴 |
| UI-05 | Gmail UI | Connection, sync, historical import, list/detail, attachment, classification, compose | `(dashboard)/gmail/` | ✅ Deployed | ✅ |
| UI-06 | Admin UI | AI settings, OAuth, users, whitelist, domains, audit, assistant, assistant-tools, runtime health | `(dashboard)/admin/` | ✅ Deployed | ⚠️ |
| UI-07 | Onboarding UI | Process list, counts, detail, checklist update | `(dashboard)/onboarding/` | ✅ Deployed | ✅ |
| UI-08 | Payslip UI | HR list/detail/new/publish; ESS list/detail | `(dashboard)/payroll/`, ESS | ✅ Deployed | ⚠️ |

---

## Tiêu chí Review

- [x] Tất cả trang khớp với backend route
- [⚠️] Design system nhất quán: Inter, Warm Professional palette (thiếu dark mode, grouping nav)
- [⚠️] Responsive/mobile hoạt động (thiếu hamburger menu, sidebar luôn hiển thị)
- [❌] Dark mode hoạt động (chưa implement)
- [ ] Playwright visual snapshot tests pass (chưa verify)
- [✅] Trạng thái rỗng (empty data / empty filter) đúng
- [✅] Tiếng Việt mặc định, nhất quán
- [⚠️] Accessibility (a11y) - chưa audit đầy đủ

---

## Kết quả Review từng chức năng

### UI-01 — Shell & Navigation
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ⚠️ — Cần cải thiện

**Điểm tốt:**
- AppShell component dùng chung cho cả Dashboard (HR) và Employee (ESS) layout — DRY, maintainable
- Active state trên nav item rõ ràng (indigo background + border + shadow)
- Breadcrumb hiển thị role label (`/ Quản trị`) ở top bar
- Hover state trên nav button mượt (slate → indigo)
- Border-top ngăn cách AI Assistant button với phần nav chính
- Middleware redirect auth hợp lý (protect route, force change-password)

**Vấn đề cần sửa:**
1. **Thiếu nav grouping** — Spec nói nav nhóm (Nhân sự/Tuyển dụng/Chấm công/Lương/Hệ thống) nhưng sidebar hiện tại là flat list, không có visual grouping. Người dùng HR mới sẽ khó định hướng 15 mục không phân nhóm.
2. **Thiếu hamburger menu trên mobile** — Ở 375px width, sidebar vẫn full width (`w-full lg:w-56`). Không có collapse/toggle. Người dùng mobile phải scroll qua sidebar mới thấy nội dung chính.
3. **Không có dark mode toggle** — Spec nói hỗ trợ dark mode nhưng không có UI toggle nào và không có CSS dark mode.
4. **Icon "Cấu hình" ở top bar dùng `Sparkles`** — `Sparkles` thường biểu thị AI/magic, không phải Settings. Nên dùng `Settings` hoặc `Gear`. Gây confusion: người dùng nghĩ đó là nút AI.
5. **Logout không có visual feedback** — Khi click Đăng xuất, `handleLogout` gọi POST `/api/auth/logout` rồi `router.replace('/login')`. Nếu API call fail (catch ignore), middleware redirect về dashboard — người dùng không biết logout thành công hay thất bại.
6. **Breadcrumb chỉ là text tĩnh** — Không có breadcrumb động theo page hiện tại (VD: `VR Vroom HR / Quản trị / Tuyển dụng / Ứng viên`), chỉ hiện role label cố định `/ Quản trị`.

**Khuyến nghị:**
- Thêm section header/collapsible group cho nav items (theo spec: Nhân sự, Tuyển dụng, Chấm công, Lương, Hệ thống)
- Thêm hamburger button + slide-over drawer cho mobile (< 1024px)
- Thêm dark mode toggle ở top bar
- Đổi icon Cấu hình từ `Sparkles` → `Settings`
- Thêm loading/error state cho logout
- Breadcrumb động theo pathname

---

### UI-02 — Design System
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ⚠️ — Một phần, thiếu dark mode

**Điểm tốt:**
- Palette indigo/slate/emerald/amber/rose nhất quán trên toàn bộ app
- Radius 6px (`rounded-xl` = 12px, `rounded-2xl` = 16px) — hơi lớn hơn spec (6px) nhưng tạo visual identity riêng
- Font Inter + JetBrains Mono (mono) dùng nhất quán
- Tailwind v4 với `@import "tailwindcss"` — modern setup
- Print styles cho payslip — ẩn chrome UI khi in
- `selection:bg-indigo-500` tạo branded text selection

**Vấn đề cần sửa:**
1. **Không có dark mode** — Không có `@media (prefers-color-scheme: dark)` hay class-based dark mode. Toàn bộ app dùng `bg-white`, `text-slate-900` cố định.
2. **Không thấy Motion/LazyMotion/AutoAnimate** — Spec nói có animation nhưng khi browse app không thấy transition/animation rõ rệt. App-shell dùng `transition-all` cơ bản trên nav items.
3. **Radius không đúng spec** — Spec nói radius 6px nhưng component dùng `rounded-xl` (12px) và `rounded-2xl` (16px).
4. **globals.css quá mỏng** — Chỉ có Tailwind import + print styles. Không có CSS custom properties, design tokens, hay theme configuration tập trung.

**Khuyến nghị:**
- Implement dark mode với Tailwind `dark:` prefix hoặc CSS custom properties
- Thêm animation library (Framer Motion/LazyMotion) nếu spec yêu cầu
- Chuẩn hóa radius về 6px (`rounded-lg`) hoặc cập nhật spec
- Tạo `design-tokens.css` với CSS custom properties cho màu sắc, spacing, radius

---

### UI-03 — Auth Pages
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ✅ — Tốt

**Điểm tốt:**
- Login page dùng `react-hook-form` + `zodResolver` — validation chặt chẽ
- Show/hide password toggle (`Eye`/`EyeOff` icon)
- Error handling phân biệt: field-level errors (BE validation) vs server errors (generic)
- Loading spinner khi check session (`isLoading`)
- Redirect thông minh: `must_change_password` → `/change-password`, admin → `/dashboard`, employee → `/employee`
- Change-password page: success state với 2s delay rồi redirect (kèm `CheckCircle` icon)
- BUG-10 fix documented: sync React Query cache ngay sau login/change-password để tránh race condition
- Schema validation (`loginSchema`, `changePasswordSchema`) tách riêng trong `auth-schemas.ts`
- Middleware force redirect khi `must_change_password=true`

**Vấn đề cần sửa:**
1. **Không test được `/setup` page** — Setup page redirect về dashboard khi đã authenticated. Không verify được 3-step wizard UI.
2. **Không có "Quên mật khẩu" link** — Login page không có forgot password flow. Đây là self-hosted nên có thể không cần, nhưng là UX gap cho user thật.
3. **Không có rate limiting feedback** — Nếu user nhập sai nhiều lần, không có thông báo "quá nhiều lần thử".

**Khuyến nghị:**
- (Minor) Thêm rate limit error message rõ ràng hơn
- (Optional) Thêm forgot password flow nếu cần cho production

---

### UI-04 — Recruitment UI
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** 🔴 — Có bug blocking

**Điểm tốt:**
- **Inbox:** Filter tabs (Tất cả/Cần xác nhận/Cần bổ sung/Sẵn sàng review/Đã xử lý) + count badges rõ ràng. Empty state "Chưa có bản ghi nào" chuẩn.
- **Candidates:** Pipeline tabs (Mới/Đang review/Đã lên lịch PV/Đã nhận/Từ chối/Lưu trữ) + search box + empty state. Flow lifecycle rõ ràng.
- **Job Openings:** Summary cards (Tổng/Bản nháp/Đang tuyển/Đã đóng/Đã hủy) + filter tabs + "Tạo vị trí" button. Lifecycle doc ngay trong description.
- **Interviews:** Conflict manager (410/412 handling) + calendar selection + candidate list. "Điều kiện tạo Interview" precondition box rất hữu ích.
- **CV Review (Parse):** Correction form (HR sửa AI output → evaluation set) + retry/dismiss actions + confidence score display + provenance preview.

**Vấn đề cần sửa:**
1. **🔴 CRITICAL: CORS error trên CV Review page** — API `http://localhost:8000/api/recruitment/cv-review` không trả về `Access-Control-Allow-Origin` header. Toàn bộ page không load được data. Đây là bug blocking — người dùng không thể dùng tính năng này.
2. **🔴 Google Calendar 403 treo UI** — `getCalendars()` trả về 403, React Query retry 3 lần → `calLoading` = `true` trong thời gian dài. UI hiện "Đang kiểm tra kết nối Google Calendar..." mãi không resolve. Cần `isError` state để hiện thông báo lỗi thay vì loading vĩnh viễn.
3. **Không có Metrics Tuyển dụng page** — Menu item "Metrics Tuyển dụng" tồn tại nhưng chưa test được (có thể empty page).
4. **Không test được "Tạo vị trí" flow** — Chưa verify dialog/form tạo job opening mới.

**Khuyến nghị:**
- **Gấp:** Fix CORS trên backend (`localhost:8000`) — thêm `Access-Control-Allow-Origin: http://localhost:3000`
- **Gấp:** Xử lý `isError` state cho Google Calendar query — hiện fallback message thay vì loading forever
- Verify Metrics page có nội dung
- Test "Tạo vị trí" + "Tạo interview" flow với data thật

---

### UI-05 — Gmail UI
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ✅ — Tốt (với dữ liệu hạn chế)

**Điểm tốt:**
- Trạng thái "Chưa kết nối" hiển thị rõ ràng: "Organization Google Connection — Chưa kết nối"
- Button "Kết nối Gmail" CTA rõ ràng
- UI đơn giản, không gây confusion cho người dùng chưa connect

**Vấn đề cần sửa:**
1. **Chưa test được full flow** — Không có Gmail kết nối nên không verify được: list email, detail, attachment, classification, compose.
2. **Heading "Organization Google Connection"** — Tiếng Anh trong app tiếng Việt, không nhất quán.

**Khuyến nghị:**
- Đổi heading thành tiếng Việt: "Kết nối Google Workspace"
- Test với Gmail đã kết nối khi có môi trường staging

---

### UI-06 — Admin UI
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ⚠️ — Cần cải thiện UX

**Điểm tốt:**
- Tab navigation: Cấu hình AI / Công cụ AI / Tình trạng hệ thống / Nhật ký hoạt động / Người dùng & Vai trò / Danh sách truy cập / Tên miền email — đầy đủ theo spec
- AI Settings: provider/model/API URL/key form + status indicators (Đã kết nối) + "Kiểm tra kết nối" button
- Automation levels: 3 mức (Thận trọng/Cân bằng/Bao phủ) với description rõ ràng → user không cần đọc docs để hiểu
- Feature toggles: Phân loại email & Trích xuất CV / Trợ lý AI hỏi đáp — mỗi cái có description chi tiết
- Hướng dẫn kết nối: step-by-step (①②③) với URL phổ biến (OpenAI/Gemini/Cline)
- Audit trail: "Nguồn xác thực: Khóa API | Trạng thái: Đã kết nối | Cập nhật: 22:46 19/07/2026"

**Vấn đề cần sửa:**
1. **AI Tool names bị concatenate** — Tool name và identifier dính vào nhau: `"Đếm ứng viên theo trạng tháicount_candidates_by_status"`. Không có separator giữa label và function name. Rất khó đọc.
2. **Chưa test các tab còn lại** — Tình trạng hệ thống, Người dùng & Vai trò, Danh sách truy cập, Tên miền email chưa được click-through test.
3. **Feature toggle dùng custom switch** — Button `[ref=e975]` không có label rõ ràng, chỉ là empty button. User có thể không biết đó là toggle.

**Khuyến nghị:**
- Sửa tool name display: format `label — function_name` hoặc tách 2 dòng
- Test tất cả admin sub-tab
- Thêm accessible label cho toggle switches
- Verify OAuth settings page (nếu có)

---

### UI-07 — Onboarding UI
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ✅ — Tốt

**Điểm tốt:**
- Summary cards: Tổng / Đang tiến hành / Hoàn tất — với count numbers
- Filter: search + tabs (Tất cả/Đang tiến hành/Hoàn tất)
- Empty state chuẩn: "Chưa có bản ghi nào. Dữ liệu sẽ xuất hiện khi có bản ghi."
- Flow documentation rõ ràng: `Candidate accepted → event candidate_accepted (idempotent) → Employee inactive + checklist → HR hoàn tất task → process complete + Employee active trong 1 transaction`
- Technical transparency: mention "idempotent", "transaction" → HR tech-savvy có thể hiểu được behavior

**Vấn đề cần sửa:**
1. **Chưa test được flow với data** — Không có onboarding process nào đang chạy nên không verify được: checklist update, detail page, task completion flow.
2. **Description dùng nhiều technical term** — `idempotent`, `transaction`, `event candidate_accepted` có thể confusing cho HR không technical.

**Khuyến nghị:**
- Test với onboarding data thật (tạo candidate → accept → verify process created)
- Cân nhắc giản lược technical term trong description, hoặc thêm tooltip giải thích

---

### UI-08 — Payslip UI
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (user-centric review)
- **Kết quả:** ⚠️ — Cần cải thiện UX

**Điểm tốt:**
- Filter: Nhân viên (textbox) + Trạng thái (combobox: Tất cả/Bản nháp/Đã phát hành) + Kỳ lương (Năm/Tháng dropdowns)
- Table columns: checkbox, Nhân viên, Kỳ, Lương gross, Net, Trạng thái, Thao tác
- Vietnamese currency format: `15.000.000 ₫`
- "Tạo draft" button rõ ràng
- Print styles trong `globals.css` — ẩn chrome khi in phiếu lương

**Vấn đề cần sửa:**
1. **Checkbox behavior bất thường** — Row 1 (Đã phát hành, Test Employee) không có checkbox, nhưng Row 2 (Bản nháp, Hoang Xuan Nguyen) có checkbox. Logic ngược: published payslip không nên selectable (đã gửi cho employee), draft mới cần select để bulk publish. Nhưng UI hiện tại: published có "Xem" + không checkbox, draft có "Xem" + checkbox. Có vẻ đúng ý đồ nhưng inconsistent visual.
2. **"Xem" button cho mọi trạng thái** — Cả published và draft đều chỉ có "Xem". Draft nên có "Sửa" hoặc "Publish" action thay vì chỉ "Xem".
3. **Chưa test "Tạo draft" flow** — Không verify được form tạo payslip mới.
4. **Chưa test ESS view** — Employee Self-Service view của payslip chưa được test.

**Khuyến nghị:**
- Thêm action buttons phù hợp: Draft → "Sửa" + "Phát hành" + "Xóa"; Published → "Xem" + "Ẩn" + "Tải PDF"
- Đảm bảo checkbox nhất quán hoặc thêm tooltip giải thích
- Test full flow: Tạo draft → Sửa → Phát hành → Employee view

---

## Tổng kết

### Critical bugs (cần fix ngay)
| ID | Bug | Impact |
|----|-----|--------|
| BUG-CORS-01 | CORS header missing trên `/api/recruitment/cv-review` | Trang CV Review không load được |
| BUG-CAL-01 | Google Calendar 403 không có error handling → UI treo "Đang kiểm tra..." | Trang Interviews precondition treo |

### UX Issues (nên fix trước release)
| ID | Issue | Severity |
|----|-------|----------|
| UX-NAV-01 | Thiếu nav grouping (spec: Nhân sự/Tuyển dụng/Chấm công/Lương/Hệ thống) | Medium |
| UX-NAV-02 | Thiếu hamburger menu cho mobile | High |
| UX-DARK-01 | Không có dark mode (spec yêu cầu) | Medium |
| UX-NAV-03 | Icon Cấu hình dùng `Sparkles` thay vì `Settings` | Low |
| UX-NAME-01 | AI Tool names bị concatenate (không separator) | Medium |
| UX-PAY-01 | Thiếu action buttons cho draft payslip (Sửa/Phát hành) | Medium |

### Điểm mạnh
- Empty state nhất quán trên toàn bộ app
- Error handling + loading states tốt (trừ Google Calendar edge case)
- Form validation chặt chẽ (react-hook-form + zod)
- AppShell DRY: dùng chung cho HR admin + ESS
- Vietnamese mặc định, nhất quán
- Documentation inline trong UI (flow giải thích trong description)
- Audit trail rõ ràng (nguồn xác thực, trạng thái, timestamp)
- Print styles cho payslip
- BUG-10 fix documented → awareness về race condition trong team
