# 09 — Employee Request

> **Nhóm:** Employee Request | **Tổng:** 3 chức năng | **Deployed:** 3 | **Pending Review:** 3
> **Backend module:** `backend/src/modules/employee_request/`
> **Frontend:** ESS Requests, Admin requests

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| ER-01 | Leave Request | Employee tạo/hủy/xem request nghỉ phép | `/api/employee-requests/leave*` | ESS Requests | ✅ Deployed | ⬜ |
| ER-02 | Overtime Request | Employee tạo/hủy/xem request làm thêm | `/api/employee-requests/overtime*` | ESS Requests | ✅ Deployed | ⬜ |
| ER-03 | HR Review | Queue, approve/reject (reject cần reason), audit | `/api/admin/employee-requests*` | Admin requests UI | ✅ Deployed | ⬜ |

---

## Tiêu chí Review

- [ ] Router đã wired trong `backend/src/main.py`
- [ ] Employee chỉ thao tác request của chính mình
- [ ] HR review: reject bắt buộc reason
- [ ] Audit log cho approve/reject
- [ ] Validate thời gian (overtime)

---

## Kết quả Review từng chức năng

### ER-01 — Leave Request
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### ER-02 — Overtime Request
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

### ER-03 — HR Review
- **Ngày review:** —
- **Người review:** —
- **Kết quả:** ⬜
- **Ghi chú:** —

---

## UX Review — Góc nhìn người dùng

> **Ngày review:** 2025-07-17
> **Người review:** AI Agent (UX perspective)
> **Phạm vi:** Toàn bộ flow Employee + HR, UI/UX, logic, error handling

### Tổng quan đánh giá

- **Mức độ hoàn thiện:** 7/10 — Core flows hoạt động đúng, nhưng nhiều rough edge về UX
- **Critical issues:** 4 vấn đề ảnh hưởng trực tiếp đến khả năng sử dụng thực tế
- **Major issues:** 7 vấn đề làm giảm chất lượng trải nghiệm
- **Minor issues:** 6 vấn đề cải tiến nhỏ

---

### 🔴 CRITICAL — Ảnh hưởng nghiệp vụ

#### C-1: Employee không thấy số ngày phép còn lại (Leave Balance)

**File:** `backend/src/modules/employee_request/application/leave_service.py:144-169`

Backend có method `get_my_leave_balance()` tính toán remaining days (12 ngày/năm trừ approved và pending). **Nhưng không có API endpoint nào exposed, và frontend không hiển thị.**

Người dùng không thể biết mình còn bao nhiêu ngày phép trước khi gửi request. HR cũng không thấy số dư khi duyệt. Đây là thông tin **bắt buộc** để người dùng ra quyết định.

**Đề xuất:**
- Thêm `GET /api/employee-requests/me/leave/balance` endpoint
- Hiển thị summary card trên trang ESS: "Còn X/12 ngày phép năm"
- HR review queue: hiển thị remaining balance trong modal duyệt

#### C-2: Thiếu toàn bộ error_code mappings cho Employee Request module

**File:** `frontend/lib/api/error-codes.ts`

Backend trả về các error_code: `OVERTIME_END_BEFORE_START`, `OVERTIME_OVERLAP`, `LEAVE_END_BEFORE_START`, `LEAVE_OVERLAP`, `REQUEST_NOT_FOUND`, `REQUEST_NOT_OWNED`, `REQUEST_NOT_CANCELLABLE`, `REQUEST_NOT_REVIEWABLE`.

**Không có mapping nào** trong `ERROR_CODE_MESSAGES`. Khi lỗi xảy ra, `ErrorBanner` rơi vào fallback `"Lỗi hệ thống (OVERTIME_OVERLAP)"` — người dùng thấy mã lỗi kỹ thuật, không hiểu lỗi gì.

**Đề xuất:** Thêm mappings:
```ts
OVERTIME_END_BEFORE_START: "Giờ kết thúc phải sau giờ bắt đầu",
OVERTIME_OVERLAP: "Bạn đã có đơn tăng ca trong ngày này",
LEAVE_END_BEFORE_START: "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu",
LEAVE_OVERLAP: "Khoảng thời gian nghỉ trùng với đơn đã tồn tại",
REQUEST_NOT_FOUND: "Không tìm thấy yêu cầu",
REQUEST_NOT_OWNED: "Bạn không sở hữu yêu cầu này",
REQUEST_NOT_CANCELLABLE: "Chỉ có thể hủy yêu cầu đang chờ duyệt",
REQUEST_NOT_REVIEWABLE: "Chỉ có thể duyệt yêu cầu đang chờ",
```

#### C-3: HR không có bulk action — xử lý từng request một

**File:** `frontend/app/(dashboard)/requests/page.tsx`

HR phải duyệt/từ chối từng request một. Với công ty có 50+ nhân viên, ngày cao điểm có thể có 20-30 đơn nghỉ phép cùng lúc. Thao tác click → chờ API → click tiếp cực kỳ tốn thời gian.

**Đề xuất:**
- Thêm checkbox select + "Duyệt tất cả đã chọn" / "Từ chối tất cả đã chọn"
- Khi từ chối hàng loạt: modal nhập 1 lý do chung cho tất cả
- Optimistic UI update để không phải chờ từng API call

#### C-4: HR không thấy số ngày phép còn lại của employee khi duyệt

Khi HR nhận được một leave request, họ cần biết employee đó còn bao nhiêu ngày phép để đưa ra quyết định. Hiện tại **không có thông tin này ở bất kỳ đâu** — không trong queue list, không trong modal, không có API.

---

### 🟠 MAJOR — Ảnh hưởng trải nghiệm

#### M-1: Không có success feedback sau khi submit request

**File:** `frontend/app/(employee)/employee/requests/page.tsx:44-48, 51-55`

Sau khi gửi thành công, form reset nhưng không có toast/alert xác nhận. Người dùng phải scroll xuống list để kiểm tra xem request đã xuất hiện chưa. Dễ gây confusion: "Đã gửi được chưa nhỉ?"

**Đề xuất:** Thêm toast notification hoặc scroll đến request vừa tạo trong list.

#### M-2: Không validate client-side cho date/time

**File:** `frontend/app/(employee)/employee/requests/page.tsx:94-95, 110-113`

`end_date < start_date` hoặc `end_time <= start_time` chỉ được backend bắt. Người dùng phải submit → chờ network → nhận lỗi. Với Pydantic validators đã có sẵn logic, có thể replicate đơn giản trên client.

**Đề xuất:** Validate ngay trong form:
- Leave: disable button + inline error nếu end_date < start_date
- Overtime: disable button + inline error nếu end_time <= start_time
- Real-time feedback khi user thay đổi giá trị

#### M-3: Overtime duration không hiển thị real-time

**File:** `backend/src/modules/employee_request/domain/entities.py:85-93`

`derive_duration()` tính duration từ start_time và end_time, nhưng chỉ chạy sau khi lưu. Người dùng điền giờ nhưng không biết tổng thời gian tăng ca là bao nhiêu phút/giờ cho đến khi request đã được submit.

**Đề xuất:** Tính real-time trên client khi user thay đổi start_time hoặc end_time, hiển thị dưới dạng "Tổng: X giờ Y phút".

#### M-4: Lỗi không được clear khi chuyển tab

**File:** `frontend/app/(employee)/employee/requests/page.tsx:98, 117`

Khi có lỗi ở tab Nghỉ phép, chuyển sang tab Tăng ca rồi quay lại, lỗi vẫn hiển thị. Người dùng nghĩ rằng lỗi còn tồn tại.

**Đề xuất:** Reset mutation state khi chuyển tab: `leaveMut.reset()` / `otMut.reset()`.

#### M-5: Hủy request không cho phép nhập lý do

**File:** `frontend/app/(employee)/employee/requests/page.tsx:56-65`

Backend hỗ trợ `cancellation_reason` tùy chọn, nhưng frontend luôn gửi `null`. Người dùng không có cơ hội giải thích lý do hủy — hữu ích cho HR khi review audit log.

**Đề xuất:** Thêm optional text input trong modal hủy: "Lý do hủy (không bắt buộc)".

#### M-6: Employee filter chỉ load 100 employees

**File:** `frontend/app/(dashboard)/requests/page.tsx:33`

`page_size: 100` cứng. Công ty > 100 nhân viên sẽ không thấy tất cả trong dropdown filter.

**Đề xuất:** Load page_size lớn hơn hoặc dùng search-typeahead thay vì dropdown.

#### M-7: Reject reason dùng TextInput thay vì TextArea

**File:** `frontend/app/(dashboard)/requests/page.tsx:173`

Lý do từ chối bắt buộc, nhưng chỉ có 1 dòng input. HR có thể muốn viết giải thích chi tiết (vài câu) để employee hiểu rõ lý do.

**Đề xuất:** Đổi `<TextInput>` thành `<TextArea rows={3}>` để HR có không gian viết.

---

### 🟡 MINOR — Cải tiến nhỏ

#### m-1: Không có pagination trên list của employee

Cả `/api/employee-requests/me` và frontend list đều không có pagination. Sau 1 năm, employee có thể có 50+ requests, list sẽ rất dài.

#### m-2: HR approve không có confirmation step

Khác với reject (có modal), approve là instant action. Vô tình click nhầm sẽ duyệt ngay. Nên có confirmation nhẹ hoặc undo capability.

#### m-3: Không hiển thị số lượng pending requests ở navigation

HR không biết có bao nhiêu request đang chờ nếu chưa vào trang. Badge "3 pending" trên sidebar menu sẽ rất hữu ích.

#### m-4: Không có link đến employee profile từ review queue

Trong queue, tên employee là text thuần. HR không thể click để xem thông tin chi tiết của employee đó.

#### m-5: Không có empty state phân biệt cho HR queue

`<EmptyState filtered={hasFilters} />` dùng chung component. Nhưng khi `hasFilters=false` mà vẫn empty, message "Chưa có bản ghi nào" không nói rõ: queue thực sự trống (tốt!) hay chưa có dữ liệu.

#### m-6: Không có breadcrumb hoặc back-link giữa các trang

Employee page và Admin page không có navigation context. Người dùng có thể bị lạc nếu vào thẳng URL.

---

### ✅ Kiểm tra checklist gốc

- [x] Router đã wired trong `backend/src/main.py` — Cả employee + admin router đều đã include
- [x] Employee chỉ thao tác request của chính mình — Check `request.employee_id != employee_id` trong cancel; create luôn dùng `employee.id` từ token
- [x] HR review: reject bắt buộc reason — Client disable button khi `!rejectReason.trim()`, server `RejectRequest.decision_reason` có `min_length=1`, service layer check thêm `if not review_reason or not review_reason.strip(): raise ValueError`
- [x] Audit log cho approve/reject — `audit_service.log_action()` với `REQUEST_APPROVE` / `REQUEST_REJECT`
- [x] Validate thời gian (overtime) — `OvertimeEndBeforeStartError`, `OvertimeOverlapError`, `LeaveEndBeforeStartError`, `LeaveOverlapError`

---

### 📊 Bảng tổng hợp đề xuất theo độ ưu tiên

| Priority | ID | Vấn đề | Impact | Effort |
|----------|----|--------|--------|--------|
| 🔴 Critical | C-1 | Thiếu hiển thị leave balance | Employee + HR không thể ra quyết định | 2-3h |
| 🔴 Critical | C-2 | Thiếu error_code mappings | Người dùng thấy mã lỗi kỹ thuật | 30min |
| 🔴 Critical | C-3 | Không có bulk action cho HR | HR tốn thời gian xử lý từng request | 4-6h |
| 🔴 Critical | C-4 | HR không thấy leave balance của employee | Quyết định duyệt thiếu thông tin | 2-3h |
| 🟠 Major | M-1 | Thiếu success feedback sau submit | Confusion cho người dùng | 1h |
| 🟠 Major | M-2 | Thiếu client-side validation | Trải nghiệm chậm, phụ thuộc network | 1-2h |
| 🟠 Major | M-3 | Không hiển thị real-time overtime duration | Thiếu thông tin khi điền form | 30min |
| 🟠 Major | M-4 | Lỗi không clear khi chuyển tab | Gây confusion | 15min |
| 🟠 Major | M-5 | Hủy không cho nhập lý do | Thiếu context cho HR | 30min |
| 🟠 Major | M-6 | Employee filter giới hạn 100 | Không scale | 1h |
| 🟠 Major | M-7 | Reject reason dùng TextInput | HR không có đủ không gian viết | 15min |
| 🟡 Minor | m-1 | Thiếu pagination employee list | List dài sau nhiều tháng | 2h |
| 🟡 Minor | m-2 | Approve không confirmation | Rủi ro click nhầm | 30min |
| 🟡 Minor | m-3 | Thiếu pending count badge | HR phải vào trang mới biết | 1h |
| 🟡 Minor | m-4 | Thiếu link đến employee profile | HR phải tìm kiếm thủ công | 30min |
| 🟡 Minor | m-5 | Empty state message không rõ ràng | UX copy chưa tối ưu | 10min |
| 🟡 Minor | m-6 | Thiếu breadcrumb | Navigation context yếu | 1h |
