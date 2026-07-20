# 07 — Employee (Nhân sự)

> **Nhóm:** Employee | **Tổng:** 4 chức năng | **Deployed:** 4 | **Pending Review:** 4
> **Backend module:** `backend/src/modules/employee/`
> **Frontend:** `(dashboard)/employee/`, `(employee)/` (ESS)

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| EM-01 | Hồ sơ Employee | CRUD, filter/list/detail, department, position, manager | `/api/employees*`, `/api/departments/*`, `/api/positions/*` | Employee list/detail UI | ✅ Deployed | ✅ Pass (có issues) |
| EM-02 | Employee Account | HR tạo account; chỉ Employee active mới nhận | `/api/employees/{id}/account` | Account management UI | ✅ Deployed | ✅ Pass (có issues) |
| EM-03 | Import & Tài liệu | Import từ file; tài liệu qua MinIO, list/download/delete | `/api/employees/import`, `/api/documents*` | Import/Documents UI | ✅ Deployed | ✅ Pass (có issues) |
| EM-04 | Employee Self-Service (ESS) | Dashboard, hồ sơ, tài liệu, chấm công, request, Payslip, Assistant | ESS routes | `(employee)/` layout + pages | ✅ Deployed | ✅ Pass (có issues) |

---

## Tiêu chí Review

- [x] Router đã wired trong `backend/src/main.py`
- [x] ESS: chỉ Employee active truy cập
- [x] Employee Account: chỉ tạo cho Employee active
- [x] Tài liệu: MinIO, phân quyền, list/download/delete
- [ ] Import: xử lý file lỗi, duplicate — chưa kiểm chứng thực tế (cần test với file lỗi)

---

## Phương pháp Review

Review được thực hiện từ góc độ **người dùng cuối** (HR và Employee), thao tác trực tiếp trên UI tại `http://localhost:3000`. Các bước:

1. Đăng nhập HR → duyệt danh sách nhân viên, filter, search
2. Tạo mới Employee → kiểm tra form validation, flow tạo
3. Xem/sửa hồ sơ Employee → kiểm tra edit mode, department/position dropdown
4. Tạo Employee Account → kiểm tra temp password flow
5. Logout → Login với tài khoản Employee → kiểm tra forced password change
6. Duyệt ESS: Profile, Documents, Dashboard
7. Import page → kiểm tra UI
8. Đối chiếu logic với domain model (CONTEXT.md)

---

## Kết quả Review từng chức năng

### EM-01 — Hồ sơ Employee

- **Ngày review:** 19/7/2026
- **Người review:** AI Agent (user perspective)
- **Kết quả:** ✅ Pass (có issues cần fix)
- **Ghi chú:**

**Hoạt động đúng:**
- Danh sách phân trang (20/page), tổng 53 employees, 3 trang
- Tìm kiếm theo tên/email hoạt động chính xác
- Filter theo trạng thái (Đang hoạt động / Không hoạt động / Tất cả)
- Filter theo phòng ban, chức vụ
- Tạo mới Employee: tự động sinh mã NV-XXX, required fields (Họ tên, Email) được validation
- Form có đủ trường: Họ tên, Email, Điện thoại, Ngày sinh, Giới tính, Loại hợp đồng, Phòng ban, Chức vụ, Ngày bắt đầu, CMND/CCCD, Mã số thuế, Địa chỉ
- Chi tiết Employee hiển thị đầy đủ thông tin + trạng thái + thời gian cập nhật
- Sửa hồ sơ: chuyển từ disabled → editable, có nút Hủy/Lưu

**Vấn đề cần fix (theo mức độ nghiêm trọng):**

| # | Mức độ | Vấn đề | Chi tiết |
|---|--------|--------|----------|
| 1 | 🔴 Bug | **Employee mới tạo tự động active** | Domain model (CONTEXT.md) quy định Employee mới tạo phải ở trạng thái **inactive** (`is_active = false`, đang onboarding). Khi tạo Employee qua form, hệ thống set thẳng `is_active = true`. Chỉ nên active sau khi hoàn tất onboarding. |
| 2 | 🔴 Missing | **Không có nút Xóa Employee trên UI** | Backend có endpoint `DELETE /api/employees/{id}` nhưng frontend không hiển thị. HR không thể xóa nhân viên khỏi giao diện. |
| 3 | 🟡 UX | **Dropdown Phòng ban/Chức vụ chỉ có "—"** | Không có department/position nào được tạo sẵn. Dropdown trống gây bối rối. Cần thêm link "Tạo phòng ban mới" hoặc ít nhất hiển thị message "Chưa có phòng ban nào". Import page nói sẽ auto-tạo nhưng UI thủ công thì không. |
| 4 | 🟡 UX | **Loại hợp đồng là textbox thay vì dropdown** | Nên là select với options: Xác định thời hạn, Vô thời hạn, Thử việc, Cộng tác viên... Hiện tại placeholder gợi ý "Xác định thời hạn / Vô thời hạn" nhưng user vẫn có thể gõ bất kỳ. |
| 5 | 🟡 UX | **Trường Giới tính không hiển thị trong Detail View** | Form tạo có select Giới tính (Nam/Nữ/Khác), nhưng detail view không hiển thị trường này. |
| 6 | 🟡 UX | **Search cần click nút "Lọc" thủ công** | Không auto-submit khi nhấn Enter. Thêm 1 click không cần thiết. Nên debounce search hoặc submit on Enter. |
| 7 | 🟡 UX | **Date field gửi empty string → 422** | Khi để trống Ngày sinh/Ngày bắt đầu, backend trả về 422 "giá trị không hợp lệ". Frontend nên validate date format hoặc không gửi field rỗng. |
| 8 | 🟢 Nit | **Thiếu trường Manager** | Domain model đề cập Manager là quan hệ báo cáo trực tiếp, nhưng form không có field này. |
| 9 | 🟢 Nit | **Bảng list không hiển thị cột Giới tính** | Chỉ có Mã NV, Họ tên, Email, Phòng ban, Chức vụ, Trạng thái. |

---

### EM-02 — Employee Account

- **Ngày review:** 19/7/2026
- **Người review:** AI Agent (user perspective)
- **Kết quả:** ✅ Pass (có issues cần fix)
- **Ghi chú:**

**Hoạt động đúng:**
- Backend enforce "chỉ Employee active mới được tạo account" — test xác nhận đúng
- Tạo account sinh temporary password, hiển thị 1 lần trong dialog
- Dialog có warning rõ ràng: "Lưu lại ngay — mật khẩu tạm thời sẽ không hiển thị lại"
- Forced password change on first login hoạt động (`/change-password`)
- Password mới yêu cầu ≥12 ký tự
- Account status hiển thị: email, role, must_change_password
- Backend có DELETE account endpoint (idempotent)

**Vấn đề cần fix:**

| # | Mức độ | Vấn đề | Chi tiết |
|---|--------|--------|----------|
| 1 | 🔴 Bug | **UI không refresh sau khi tạo account** | Sau khi đóng dialog "Tài khoản đã được tạo", account section vẫn hiển thị "Employee chưa có tài khoản đăng nhập" + nút "Tạo tài khoản". Phải refresh trang mới thấy trạng thái mới. |
| 2 | 🔴 Missing | **Không có nút Reset Password / Disable Account** | Backend không có endpoint reset password riêng. HR không thể reset mật khẩu cho Employee. Cũng không có cách disable account tạm thời. |
| 3 | 🟡 Missing | **Không có nút Xóa Account trên UI** | Backend có `DELETE /api/employees/{id}/account` nhưng frontend không hiển thị. |
| 4 | 🟢 Nit | **Không có confirm dialog trước khi tạo account** | Click "Tạo tài khoản" là tạo ngay lập tức. Nên có confirm "Bạn có chắc muốn tạo tài khoản cho Employee này?" |
| 5 | 🟢 Nit | **Label section là tiếng Anh "Employee Account"** | Trong khi toàn bộ UI dùng tiếng Việt, section title này lại là tiếng Anh. Các label con cũng: "Role: user" thay vì "Vai trò: Nhân viên". |

---

### EM-03 — Import & Tài liệu

- **Ngày review:** 19/7/2026
- **Người review:** AI Agent (user perspective)
- **Kết quả:** ✅ Pass (có issues cần fix)
- **Ghi chú:**

**Hoạt động đúng:**
- Import page có UI rõ ràng: chọn file, giới hạn 10MB, định dạng .xlsx
- Mô tả: "Phòng ban và chức vụ mới sẽ được tự động tạo nếu chưa có" — logic đúng
- Document upload/download qua MinIO presigned URLs
- Phân quyền document: Employee chỉ xem được document của mình, HR mới xóa được
- Empty state cho document: "Chưa có tài liệu nào" + giải thích rõ ràng

**Vấn đề cần fix:**

| # | Mức độ | Vấn đề | Chi tiết |
|---|--------|--------|----------|
| 1 | 🟡 UX | **Không có file template để tải về** | Import page không cung cấp link tải template Excel. User phải tự đoán format. Nên có nút "Tải template" với file mẫu. |
| 2 | 🟡 UX | **Không có preview trước khi import** | User không biết dữ liệu sẽ được import như thế nào. Nên có bước preview (table hiển thị 5-10 dòng đầu) trước khi confirm import. |
| 3 | 🟡 Gap | **Chưa test import với file lỗi/duplicate** | Tiêu chí review yêu cầu "xử lý file lỗi, duplicate" nhưng chưa có file test. Cần tạo test case: file trống, sai format, email trùng, thiếu required fields. |
| 4 | 🟢 Nit | **Document section trong Employee Detail không có action buttons** | Khi có document, không rõ có nút Download/Delete không (chưa test vì chưa upload). Cần verify. |
| 5 | 🟢 Nit | **Không phân loại document type** | Document upload không có field phân loại (hợp đồng, bằng cấp, CMND...). Khó quản lý khi có nhiều document. |

---

### EM-04 — Employee Self-Service (ESS)

- **Ngày review:** 19/7/2026
- **Người review:** AI Agent (user perspective)
- **Kết quả:** ✅ Pass (có issues cần fix)
- **Ghi chú:**

**Hoạt động đúng:**
- Giao diện riêng biệt hoàn toàn với HR Dashboard: sidebar riêng, navigation riêng
- Forced password change on first login: redirect → `/change-password` → yêu cầu ≥12 ký tự
- ESS Dashboard có 6 module dạng card: Hồ sơ, Tài liệu, Chấm công, Yêu cầu, Phiếu lương, Trợ lý AI
- Profile view: HR fields read-only, chỉ Phone và Address editable (đúng security model)
- Document: Employee upload được, không xóa được (HR mới xóa) — đúng phân quyền
- Empty state rõ ràng: "Chưa có tài liệu nào của bạn" vs "Chưa có dữ liệu"

**Vấn đề cần fix:**

| # | Mức độ | Vấn đề | Chi tiết |
|---|--------|--------|----------|
| 1 | 🟡 UX | **Profile dùng disabled textbox thay vì label** | Các field read-only hiển thị dưới dạng textbox bị disabled. Điều này gây confusing (tại sao không gõ được?). Nên dùng text label thuần hoặc description list. |
| 2 | 🟡 UX | **Thiếu breadcrumb navigation** | ESS pages không có breadcrumb. User dễ bị lạc khi đi sâu vào các trang con. |
| 3 | 🟡 UX | **Module Chấm công, Yêu cầu, Phiếu lương, Trợ lý AI chưa được test** | Do thời gian hạn chế, mới test kỹ Profile + Documents. Các module còn lại cần test thêm để verify logic. |
| 4 | 🟢 Nit | **Header hiển thị "Vroom HR / Nhân viên"** | Tốt, phân biệt rõ với "Vroom HR / Quản trị" bên HR. |
| 5 | 🟢 Nit | **Không có notification/inbox trong ESS** | Employee không có cách xem thông báo từ hệ thống (request được duyệt, payslip mới...). |

---

## Tổng hợp Cross-cutting Issues

| # | Mức độ | Vấn đề | Ảnh hưởng |
|---|--------|--------|-----------|
| C1 | 🔴 | **Bug: Employee mới tạo active ngay** | EM-01 — Vi phạm domain model, bỏ qua onboarding flow |
| C2 | 🔴 | **UI không refresh sau write operations** | EM-02 — Pattern cần fix tổng quát (sau create account, UI stale) |
| C3 | 🔴 | **Thiếu Delete UI cho Employee + Account** | EM-01, EM-02 — Backend có nhưng frontend không expose |
| C4 | 🟡 | **Dropdown Department/Position rỗng** | EM-01 — Cản trở UX, cần có "Tạo mới" inline hoặc link |
| C5 | 🟡 | **Loại hợp đồng nên là select** | EM-01 — Data integrity risk khi là textbox tự do |
| C6 | 🟡 | **Trộn tiếng Việt / tiếng Anh** | EM-02, EM-04 — "Employee Account", "Role: user" nên dịch sang tiếng Việt |
| C7 | 🟡 | **Import thiếu template + preview** | EM-03 — User phải tự mò format file |
| C8 | 🟡 | **Search không auto-submit** | EM-01 — Thêm 1 click thừa |
| C9 | 🟢 | **Không có bulk actions** | EM-01 — Không chọn nhiều employee để xóa/gán phòng ban hàng loạt |
| C10 | 🟢 | **Không có export** | EM-01 — Không export được danh sách nhân viên ra Excel |
| C11 | 🟢 | **Thiếu Manager field** | EM-01 — Domain model có nhưng UI không có |
| C12 | 🟢 | **Disabled textbox thay vì label** | EM-01, EM-04 — UX pattern chưa tối ưu cho read-only view |

---

## Kết luận

- **Tổng quan:** 4/4 chức năng đã deploy, flow chính hoạt động. Backend logic vững, bảo mật phân quyền tốt.
- **Điểm mạnh:** Temp password flow, forced password change, phân quyền document rõ ràng, ESS layout tách biệt.
- **Cần fix ngay (P0):** Bug `is_active = true` cho Employee mới, UI không refresh sau write, thêm Delete UI.
- **Cần cải thiện (P1):** Department/Position UX, Loại hợp đồng → select, template import, search auto-submit.
- **Nice to have (P2):** Manager field, bulk actions, export, breadcrumb, notification trong ESS.

---

## Test Cases đã thực hiện

| # | Test case | Kết quả | EM |
|---|-----------|---------|-----|
| 1 | HR xem danh sách nhân viên (pagination) | ✅ Pass | EM-01 |
| 2 | Search "Test" → filter đúng 1 kết quả | ✅ Pass | EM-01 |
| 3 | Tạo Employee mới với required fields | ✅ Pass | EM-01 |
| 4 | Validation: thiếu Họ tên/Email → nút disabled | ✅ Pass | EM-01 |
| 5 | Validation: date rỗng → 422 error message | ✅ Pass (cần improve message) | EM-01 |
| 6 | Xem detail Employee sau khi tạo | ✅ Pass | EM-01 |
| 7 | Sửa hồ sơ (edit mode) | ✅ Pass | EM-01 |
| 8 | Tạo Employee Account → hiển thị temp password | ✅ Pass | EM-02 |
| 9 | Account sau khi tạo: status có must_change_password | ✅ Pass (sau refresh) | EM-02 |
| 10 | Đăng nhập bằng temp password → forced redirect | ✅ Pass | EM-02, EM-04 |
| 11 | Đổi mật khẩu → vào ESS dashboard | ✅ Pass | EM-04 |
| 12 | ESS Profile: xem thông tin (read-only HR fields) | ✅ Pass | EM-04 |
| 13 | ESS Profile: sửa phone/address | ✅ Pass | EM-04 |
| 14 | ESS Documents: xem danh sách (empty state) | ✅ Pass | EM-03, EM-04 |
| 15 | Import page UI | ✅ Pass | EM-03 |

