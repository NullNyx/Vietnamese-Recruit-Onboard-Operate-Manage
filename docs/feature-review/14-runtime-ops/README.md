# 14 — Runtime & Operations

> **Nhóm:** Runtime & Ops | **Tổng:** 3 chức năng | **Deployed:** 3 | **Pending Review:** 3
> **Backend:** `backend/src/main.py`, bootstrap, error handlers

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| RT-01 | Health Check | `/health` + `/api/admin/runtime/health` worker heartbeat | `/health`, `/api/admin/runtime/health` | Dashboard + Settings > Tình trạng hệ thống | ✅ Deployed | ✅ PASS |
| RT-02 | Error Handlers | 9 module error handler riêng | `register_*_error_handlers(app)` | — | ✅ Deployed | ✅ PASS |
| RT-03 | Demo Data Seed | Tự động seed khi `auto_seed_sample_data=true` (super admin, demo data, attendance, payslips, tool configs) | Bootstrap at startup | — | ✅ Deployed | ✅ PASS |

---

## Tiêu chí Review

- [x] `/health` endpoint hoạt động
- [x] `/api/admin/runtime/health` báo cáo worker heartbeat
- [x] 9 error handler đã đăng ký đầy đủ
- [x] Demo seed không chạy trên production
- [x] Bootstrap super admin an toàn

---

## Kết quả Review từng chức năng

### RT-01 — Health Check
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (Playwright + API verify)
- **Kết quả:** ✅ PASS
- **Ghi chú:** Route thực tế là `/api/admin/runtime/health` (cần admin auth). Hiển thị ở Dashboard + Settings > Tình trạng hệ thống. 5/5 services healthy.

### RT-02 — Error Handlers
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (code inspection + API verify)
- **Kết quả:** ✅ PASS
- **Ghi chú:** 9 module: auth, employee, gmail, recruitment, onboarding, attendance, assistant, payslip, employee_request. Tất cả đều có error_handler.py riêng + được register trong main.py. Domain exception trả về JSON structured error.

### RT-03 — Demo Data Seed
- **Ngày review:** 2026-07-20
- **Người review:** AI Agent (code review + DB verify)
- **Kết quả:** ✅ PASS
- **Ghi chú:** `auto_seed_sample_data` default=False → safe for production. Idempotent: skip nếu đã có data. Đã seed: 2 departments, 2 positions, 2 employees, 4 attendance records, 4 payslips.

---

## UX/UI Review — Góc nhìn người dùng HR

> **Ngày review:** 2026-07-20 | **Phương pháp:** Playwright end-to-end + code inspection

### Tổng quan trải nghiệm

Dashboard là trang đích sau login → HR nhìn thấy sức khỏe hệ thống ngay lập tức. Đây là quyết định UX tốt. Tuy nhiên, có sự **không nhất quán nghiêm trọng** giữa 2 nơi hiển thị cùng một dữ liệu.

---

### 🔴 Critical — Không nhất quán Dashboard vs Settings

Cùng một API response, Dashboard và Settings hiển thị khác nhau đáng kể:

| Khía cạnh | Dashboard (Tổng quan) | Settings > Tình trạng hệ thống |
|-----------|----------------------|-------------------------------|
| Tên dịch vụ | `Bộ nhớ đệm` (SERVICE_LABELS) | `redis` (raw English) |
| Latency DB | `Nhanh` (formatLatency) | `0.4ms` (raw number) |
| Heartbeat worker | `3 phút trước` (formatRuntimeDetail) | `last beat: 1784513100.19...` (raw) |
| Status icon | `CheckCircle` (Lucide icon) | `🟢` (emoji) |

**Tác động:** HR mở Settings để xem chi tiết thì gặp dữ liệu thô khó hiểu — gây mất niềm tin vào hệ thống. Một HR không kỹ thuật sẽ không hiểu "last beat: 1784513100.191286" nghĩa là gì.

**Fix:** Settings `HealthTab` cần dùng chung `SERVICE_LABELS`, `formatLatency()`, `formatRuntimeDetail()` như Dashboard. Code hiện tại tại `frontend/app/(dashboard)/settings/page.tsx:520-530`.

---

### 🟠 Major

#### 1. Dashboard loading skeleton sai số lượng
- **File:** `frontend/app/(dashboard)/dashboard/page.tsx:167`
- **Vấn đề:** `[...Array(4)]` tạo 4 skeleton card, nhưng có **5 services** (redis, postgresql, minio, gmail-worker, onboarding-worker)
- **Tác động:** Layout nhảy (layout shift) khi data load xong — card thứ 5 đột ngột xuất hiện
- **Fix:** Sửa `4` → `5` hoặc dùng `health?.services?.length`

#### 2. Nút refresh không có accessible label
- **File:** `frontend/app/(dashboard)/settings/page.tsx:508`
- **Vấn đề:** Button chỉ chứa icon `<RefreshCw />`, không có text hay `aria-label`
- **Tác động:** Screen reader không đọc được; người dùng không biết nút đó để làm gì
- **Fix:** Thêm `aria-label="Làm mới trạng thái"` hoặc `title` attribute

#### 3. Không có tooltip giải thích dịch vụ
- **Vấn đề:** Không có giải thích về chức năng từng service (vd: redis = bộ nhớ đệm dùng để cache phiên đăng nhập và job queue)
- **Tác động:** HR không hiểu tại sao một service bị lỗi có nghĩa là gì cho công việc của họ
- **Fix:** Thêm tooltip hoặc icon `?` để giải thích ngắn gọn vai trò từng service

#### 4. Audit log hiển thị mã action_type thô
- **Vấn đề:** Các action như `org_ai_toggle_assistant`, `org_ai_consent`, `payslip_unpublish` hiển thị raw
- **Tác động:** Khó đọc với HR không kỹ thuật
- **Fix:** Dashboard đã có `AUDIT_ACTION_LABELS` mapping, nhưng có vẻ chưa áp dụng nhất quán

---

### 🟡 Minor

#### 5. Tab order không vào sidebar
- **Kết quả kiểm tra lại:** ❌ False positive — tất cả 15 sidebar buttons đều có `tabIndex: 0`, focusable bình thường. Lỗi do test manual không Tab đủ lần.

#### 6. Không có timestamp "cập nhật lúc"
- **Vấn đề:** Không biết dữ liệu health được fetch lần cuối khi nào
- **Fix:** Hiển thị dòng "Cập nhật cách đây X giây" cạnh nút refresh

#### 7. Mobile: Sidebar đẩy main content xuống dưới
- **Vấn đề:** Ở mobile (375px), sidebar 15 mục chiếm toàn bộ không gian trước khi đến được nội dung chính
- **Fix:** Cân nhắc hamburger menu hoặc collapse sidebar trên mobile

#### 8. Mix tiếng Việt / tiếng Anh trong cùng 1 view
- **Vấn đề:** Dashboard: "Pipeline", "Queue depth (đang xử lý)", "0%" — một số label tiếng Anh chưa dịch
- **Fix:** Dịch nhất quán: Pipeline → "Hàng đợi", Queue depth → "Độ sâu hàng đợi"

---

### ✅ Điểm UX đã làm tốt

1. **Landing page = Dashboard:** HR thấy sức khỏe hệ thống ngay — đúng UX pattern cho ops dashboard
2. **Màu sắc trạng thái rõ ràng:** Xanh (healthy), Vàng (degraded), Đỏ (unhealthy) — theo chuẩn industry
3. **Loading skeleton:** Có animation pulse, không phải spinner trơ trọi
4. **Error state riêng:** "Không tải được trạng thái hệ thống" + retry action — đầy đủ
5. **Empty state riêng:** "Không có dữ liệu" — phân biệt với error state
6. **Relative time cho heartbeat:** "Vừa xong", "3 phút trước" thay vì timestamp — rất thân thiện
7. **Latency qualitative:** "Nhanh", "Bình thường", "Chậm" trực quan hơn ms cho HR
8. **Stale time 30s:** Không spam API — hợp lý cho dữ liệu ops
9. **Responsive grid:** 2 cột mobile, 4 cột desktop — thích ứng tốt
10. **Breadcrumb:** `/ Quản trị` cho biết vị trí trong hệ thống

---

### Khuyến nghị ưu tiên

| # | Vấn đề | Mức độ | Effort | File cần sửa | Trạng thái |
|---|--------|--------|--------|-------------|------------|
| 1 | Settings HealthTab dùng raw data thay vì formatter | 🔴 Critical | Thấp | `settings/page.tsx:520-530` | ✅ Fixed |
| 2 | Loading skeleton sai số lượng (4 vs 5) | 🟠 Major | Thấp | `dashboard/page.tsx:167` | ✅ Fixed |
| 3 | Nút refresh thiếu aria-label | 🟠 Major | Thấp | `settings/page.tsx:508` | ✅ Fixed |
| 4 | Audit log hiển thị action_type thô | 🟠 Major | Trung bình | `shared-ui.tsx` AUDIT_ACTION_LABELS | ✅ Fixed |
| 5 | Không có tooltip giải thích service | 🟠 Major | Trung bình | Cả 2 file dashboard & settings | ✅ Fixed |
| 6 | Không có timestamp cập nhật | ✅ Fixed | Thấp | Cả 2 file | ✅ Fixed |
| 7 | ~~Tab order~~ (false positive — đã focusable) | — | — | — |
| 8 | Mobile sidebar chiếm hết fold | ✅ Fixed | Trung bình | `app-shell.tsx` | ✅ Fixed |
| 9 | Mix Anh/Việt trong label | ✅ Fixed | Thấp | `dashboard/page.tsx` |
