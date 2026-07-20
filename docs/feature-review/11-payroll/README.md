# 11 — Payroll (Tính lương)

> **Nhóm:** Payroll | **Tổng:** 2 chức năng | **Deployed:** 0 | **Chưa triển khai:** 2
> **Backend module:** Chưa có
> **Frontend:** `/payroll/*` → 404 `notFound()`

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| PR-01 | Config/Allowance/Tax | Cấu hình lương, phụ cấp, thuế TNCN → 404 | — | `/payroll/*` (404) | ❌ Chưa triển khai | — |
| PR-02 | Payroll Engine | Engine tính lương chưa có | — | — | ❌ Chưa triển khai | — |

---

## Ghi chú

- Payslip CRUD/publish đã có (nhóm 10), nhưng đây chỉ là bảng kê
- Payroll calculation engine, cấu hình phụ cấp và thuế chưa được triển khai
- Frontend trả 404 qua `notFound()` — đã gỡ placeholder tại `f0a1d07`
- Cần chốt roadmap: chỉ Payslip hay có thêm calculation engine

---

## Kết quả Review

### 🔍 User-Centric UX Review (Pre-Implementation)

**Ngày review:** 2026-07-19
**Người review:** AI Agent (góc độ người dùng hệ thống)
**Phạm vi:** Toàn bộ tính năng Payroll (PR-01 + PR-02), bao gồm cả Payslip hiện tại (nhóm 10) làm nền tảng.

---

## 1. Tổng quan hiện trạng

### Nhóm 10 — Payslip (đã triển khai)

Payslip hiện tại là **bảng kê thủ công hoàn toàn**: HR tự nhập tất cả các con số (lương gross, khấu trừ, BHXH, TN chịu thuế, thuế TNCN, lương net). Hệ thống chỉ validate cơ bản (net = gross - deductions - insurance - pit) dưới dạng **cảnh báo** chứ không chặn.

### Nhóm 11 — Payroll (chưa triển khai)

- **PR-01 (Config/Allowance/Tax):** Backend DB schema đã từng được thiết kế (migrations 021-026, sau đó bị drop ở 027). Frontend trả 404.
- **PR-02 (Payroll Engine):** Chưa có gì. Logic tính lương chỉ tồn tại trong seed script (`seed_all.py`) và docs (`AGENTS.md`).

---

## 2. Góc nhìn người dùng: HR (người tạo & quản lý phiếu lương)

### 2.1 Vấn đề nghiêm trọng (Blockers trước khi gọi là "hoàn thiện")

| # | Vấn đề | Mức độ | Mô tả |
|---|--------|--------|-------|
| **P1** | **HR phải tự tính toán mọi thứ** | 🔴 Nghiêm trọng | HR nhập tay gross, deductions, insurance, taxable_income, pit, net. Với 50+ nhân viên, mỗi tháng HR phải tính từng người một. Đây không phải "phần mềm" — đây là "Excel trên web". HR kỳ vọng hệ thống tự tính từ lương cơ bản đã cấu hình. |
| **P2** | **Không có bulk create** | 🔴 Nghiêm trọng | Mỗi kỳ lương, HR phải tạo từng phiếu cho từng nhân viên. Với công ty 100 người, mỗi tháng HR click 100 lần "Tạo draft" + điền form. Hệ thống cần nút "Tạo phiếu lương hàng loạt cho kỳ X/YYYY". |
| **P3** | **Không có auto-calculate** | 🔴 Nghiêm trọng | Không có engine tính lương. Không kết nối với attendance (công đi làm, OT, nghỉ phép). Không kết nối với salary config. Không áp dụng luật thuế TNCN (7 bậc lũy tiến). Không có logic BHXH (10.5%). Tất cả phải làm tay. |
| **P4** | **Không có cấu hình lương nhân viên** | 🔴 Nghiêm trọng | Không có màn hình để HR thiết lập: lương gross cơ bản, lương đóng BHXH, loại hợp đồng, phụ cấp, người phụ thuộc. Mỗi lần tạo payslip HR phải nhớ/nhập lại từ đầu. |

### 2.2 Vấn đề UX/UI (chất lượng trải nghiệm)

| # | Vấn đề | Mức độ | Mô tả |
|---|--------|--------|-------|
| **U1** | **Cảnh báo net mismatch không chặn save** | 🟡 Trung bình | Form tạo/sửa payslip hiển thị ⚠ khi `gross - deductions - insurance - pit ≠ net` nhưng vẫn cho lưu. HR có thể vô tình lưu số liệu sai. Nên: chặn save nếu mismatch (hoặc ít nhất confirmation dialog). |
| **U2** | **Employee dropdown giới hạn 100** | 🟡 Trung bình | `page_size: 100` cho `listEmployees`. Công ty >100 nhân viên sẽ không thấy hết. Cần pagination hoặc load-more trong dropdown. |
| **U3** | **Pagination text còn tiếng Anh** | 🟢 Nhẹ | `"{data.total} payslips · trang {submitted.page} / {totalPages}"` — chữ "payslips" chưa dịch. Vi phạm chuẩn 100% tiếng Việt. |
| **U4** | **Navigation label lẫn tiếng Anh** | 🟢 Nhẹ | `"Phiếu lương (Payslips)"` trong sidebar — nên bỏ "(Payslips)" để thuần Việt. |
| **U5** | **Không hiển thị công thức/tỷ lệ** | 🟡 Trung bình | HR mới không biết BHXH 10.5% tính trên lương nào, thuế TNCN bậc mấy. UI nên hiển thị hint về cách tính (ví dụ: "BHXH (8% + 1.5% + 1% = 10.5% lương đóng BHXH)"). |
| **U6** | **Không preview tổng quan kỳ lương** | 🟡 Trung bình | HR không có dashboard/màn hình tổng quan: tổng lương gross, tổng net, tổng thuế, tổng BHXH của một kỳ. Rất cần để đối chiếu trước khi phát hành hàng loạt. |
| **U7** | **Thiếu breadcrumb / context** | 🟢 Nhẹ | Khi xem chi tiết payslip, không có breadcrumb quay lại danh sách đã lọc. Modal detail đóng → mất context filter. |
| **U8** | **Không có search theo tên trong table** | 🟢 Nhẹ | Bảng danh sách hiển thị 20 dòng/trang. Muốn tìm 1 nhân viên cụ thể phải dùng filter dropdown (chỉ 100 nhân viên đầu) hoặc lật trang. Nên có ô search text ngay trên table. |

### 2.3 Flow người dùng lý tưởng cho HR (mong đợi)

```
Đầu tháng:
1. HR vào "Cấu hình lương" → kiểm tra lương cơ bản, phụ cấp, người phụ thuộc của từng nhân viên
2. HR vào "Kỳ lương" → Tạo kỳ lương mới (T07/2026)
3. Hệ thống tự động:
   a. Lấy danh sách nhân viên active
   b. Lấy lương gross từ salary_config
   c. Lấy phụ cấp từ allowances (còn hiệu lực trong kỳ)
   d. Lấy công từ attendance_records (ngày đi làm, OT, nghỉ phép)
   e. Tính: lương thực tế = (lương gross / 26) × ngày công + OT + phụ cấp
   f. Tính BHXH: insurance_salary × 10.5%
   g. Tính thu nhập chịu thuế = tổng thu nhập - BHXH - giảm trừ bản thân (11M) - giảm trừ người phụ thuộc (4.4M × N)
   h. Tính thuế TNCN theo 7 bậc lũy tiến
   i. Tính lương net = tổng thu nhập - BHXH - thuế TNCN - khấu trừ khác
4. HR xem bảng tổng hợp → chỉnh sửa nếu cần (vd: thưởng đột xuất, phạt,...)
5. HR "Phát hành" từng phiếu hoặc hàng loạt → nhân viên thấy trên ESS
```

**Khoảng cách giữa hiện tại và lý tưởng:** Toàn bộ bước 1-3 chưa có. Bước 4-5 có một phần (chỉ bước 5).

---

## 3. Góc nhìn người dùng: Nhân viên (người xem phiếu lương)

### 3.1 Đánh giá UX hiện tại

| # | Vấn đề | Mức độ | Mô tả |
|---|--------|--------|-------|
| **E1** | **Không hiểu các con số** | 🟡 Trung bình | Nhân viên thấy: Lương gross, Khấu trừ, BHXH, TN chịu thuế, Thuế TNCN. Nhưng không biết các con số này từ đâu ra. Không có giải thích: "BHXH = 10.5% × lương đóng BHXH", "Thuế TNCN = bậc X (Y%)", "Giảm trừ bản thân 11M + N người phụ thuộc". |
| **E2** | **Không so sánh được giữa các kỳ** | 🟢 Nhẹ | Nhân viên không thấy xu hướng lương qua các tháng. Chỉ có table đơn thuần. Nên có biểu đồ nhỏ hoặc so sánh với kỳ trước. |
| **E3** | **Thiếu download PDF chính thức** | 🟡 Trung bình | PDF URL là optional field do HR nhập link. Không có chức năng generate PDF tự động từ hệ thống. Nhân viên cần phiếu lương PDF để vay ngân hàng, làm thủ tục. |
| **E4** | **Print button thô sơ** | 🟢 Nhẹ | `window.print()` in toàn bộ page gồm sidebar, header. Nên có print stylesheet ẩn UI chrome. |

### 3.2 Flow nhân viên lý tưởng

```
Nhân viên đăng nhập ESS → thấy notification "Phiếu lương T07/2026 đã có" →
Xem phiếu lương → thấy:
  - Tổng thu nhập: lương cơ bản + phụ cấp + OT
  - Các khoản giảm trừ: BHXH (10.5%), giảm trừ bản thân (11M), giảm trừ phụ thuộc
  - Thu nhập chịu thuế → thuế TNCN (bậc X)
  - Lương net (tiền thực nhận)
  - So sánh với kỳ trước
→ Tải PDF chính thức (có dấu/mộc công ty nếu cần)
```

---

## 4. Khuyến nghị triển khai PR-01 (Config/Allowance/Tax)

### 4.1 Màn hình cần có (theo thứ tự ưu tiên)

| # | Màn hình | Mô tả | Priority |
|---|---------|-------|----------|
| 1 | **Cấu hình lương nhân viên** | Mỗi nhân viên có: lương gross, lương đóng BHXH, loại hợp đồng (thử việc/chính thức), ngày hiệu lực. One-to-one với employee. | P0 |
| 2 | **Quản lý phụ cấp** | Mỗi nhân viên có nhiều phụ cấp: loại (xăng, điện thoại, ăn trưa, chức vụ...), số tiền, chịu thuế (có/không), thời hạn (từ-đến). | P0 |
| 3 | **Quản lý người phụ thuộc** | Mỗi nhân viên có nhiều người phụ thuộc: tên, quan hệ, ngày sinh, được giảm trừ thuế (có/không). | P1 |
| 4 | **Cấu hình thuế & BHXH** | Cấu hình toàn công ty: mức giảm trừ bản thân (hiện 11M), giảm trừ phụ thuộc (4.4M), tỷ lệ BHXH (10.5%), bậc thuế lũy tiến, lương tối thiểu vùng. | P1 |

### 4.2 UX Guidelines cho các màn hình này

- **Không để HR phải nhớ công thức**: Mỗi field nên có hint hoặc tooltip giải thích (vd: "BHXH 10.5% = 8% BHXH + 1.5% BHYT + 1% BHTN")
- **Inline validation**: Nếu lương đóng BHXH > 20 lần lương tối thiểu vùng → warning
- **Lịch sử thay đổi**: Khi HR sửa lương/phụ cấp, cần audit log + hiển thị lịch sử (ai sửa, khi nào, từ X → Y)
- **Preview tác động**: Khi sửa cấu hình, hiển thị preview: "Với cấu hình này, lương net ước tính kỳ tới là ~X VND"

---

## 5. Khuyến nghị triển khai PR-02 (Payroll Engine)

### 5.1 Flow tính lương tự động

```
1. HR tạo Payroll Period (chọn tháng/năm)
2. Engine chạy:
   Input:
   - salary_configs (lương gross, lương BHXH)
   - allowances (phụ cấp còn hiệu lực trong kỳ)
   - dependents (người phụ thuộc được giảm trừ)
   - attendance_records (ngày công thực tế)
   - overtime_requests (OT đã approved)
   - leave_requests (nghỉ phép đã approved, nghỉ không lương)
   - tax_config (bậc thuế, giảm trừ)
   
   Process (mỗi nhân viên):
   a. Lương ngày = gross_salary / 26
   b. Lương theo công = lương ngày × ngày công thực tế
   c. Lương OT = lương ngày × giờ OT × tỷ lệ (150%/200%/300%)
   d. Phụ cấp tính thuế = sum(allowances có is_taxable=true)
   e. Tổng thu nhập = lương công + OT + tất cả phụ cấp
   f. BHXH = insurance_salary × 10.5% (tối đa 20× lương tối thiểu vùng)
   g. Giảm trừ = 11M (bản thân) + 4.4M × số người phụ thuộc
   h. TN chịu thuế = tổng thu nhập - BHXH - giảm trừ
   i. Thuế TNCN = progressive_tax(TN chịu thuế)
   j. Lương net = tổng thu nhập - BHXH - thuế TNCN - khấu trừ khác
   
3. Kết quả → tạo Payslip drafts cho tất cả nhân viên
4. HR review → chỉnh sửa (vd: thêm thưởng/phạt) → Publish hàng loạt
```

### 5.2 UX cho Payroll Period

- **Dashboard tổng quan kỳ lương**: Tổng số nhân viên, tổng lương gross, tổng net, tổng thuế TNCN, tổng BHXH (cả NLĐ và NSDLĐ)
- **Progress bar**: Đã tính X/Y nhân viên → HR biết engine đang chạy (nếu xử lý bất đồng bộ)
- **Diff view**: Khi HR sửa số liệu auto-calculated → highlight sự khác biệt (vd: "Net auto: 18.5M → HR sửa: 19M (+500K)")
- **Confirm step**: Trước khi publish hàng loạt → summary dialog: "Bạn sắp phát hành 95 phiếu lương. Tổng lương net: 1.2 tỷ VND. Xác nhận?"
- **Rollback**: Unpublish hàng loạt nếu phát hiện sai sót (đã có unpublish đơn lẻ, cần bulk unpublish)

### 5.3 Tích hợp với Attendance

Attendance module (nhóm 08) hiện có:
- `attendance_records`: check-in/out → tính ngày công
- `overtime_requests`: OT đã approved
- `leave_requests`: nghỉ phép đã approved, nghỉ không lương
- `work_schedules`: lịch làm việc chuẩn

Cần kết nối:
- Payroll engine đọc `attendance_records` để tính ngày công thực tế trong kỳ
- Payroll engine đọc `overtime_requests` (status=approved, trong kỳ) để tính lương OT
- Payroll engine đọc `leave_requests` (status=approved) để phân biệt nghỉ có lương/không lương

---

## 6. Các vấn đề UI/UX cần fix ngay (quick wins)

Những thứ này có thể fix mà không cần xây dựng engine mới:

| # | Fix | File | Effort |
|---|-----|------|--------|
| 1 | Sửa pagination text: `"payslips"` → `"phiếu lương"` | `frontend/.../payroll/payslips/page.tsx:347` | 1 dòng |
| 2 | Bỏ `"(Payslips)"` khỏi sidebar label và page title | `layout.tsx:25`, `page.tsx:198` | 2 dòng |
| 3 | Chặn save khi net mismatch (đổi warning → error) | `page.tsx:411-418` | Logic nhỏ |
| 4 | Tăng `page_size` cho employee dropdown hoặc thêm search API | `page.tsx:65` | 1 dòng + API |
| 5 | Thêm tooltip giải thích công thức BHXH, thuế trong form | `page.tsx:400-402` | Thêm hint text |
| 6 | Thêm nút "In phiếu lương" trong `window.print()` với print CSS | `page.tsx:124` | CSS |

---

## 7. Kết luận

| Khía cạnh | Đánh giá |
|-----------|----------|
| **Logic nghiệp vụ** | ⚠️ Đúng cho use-case thủ công. Thiếu toàn bộ automation engine. Các công thức tính lương, thuế, BHXH đã được định nghĩa trong docs nhưng chưa implemented. |
| **UX cho HR** | ⚠️ Giao diện sạch sẽ nhưng HR phải làm quá nhiều việc thủ công. Hệ thống nên làm thay HR các phép tính và tự động hóa quy trình. Khoảng cách giữa hiện tại và "phần mềm tính lương" là rất lớn. |
| **UX cho Nhân viên** | ⚠️ Đọc được phiếu lương nhưng không hiểu ý nghĩa các con số. Thiếu PDF chính thức. Thiếu so sánh giữa các kỳ. |
| **100% Tiếng Việt** | ⚠️ Gần đạt. Còn một vài chỗ lẫn tiếng Anh (pagination, sidebar label). |
| **Sẵn sàng production** | ❌ Chưa sẵn sàng. PR-01 và PR-02 cần được triển khai trước khi gọi là "phần mềm tính lương". Payslip hiện tại chỉ là "bảng kê điện tử" (thay thế Excel). |

### Ưu tiên triển khai:

1. **P0 — PR-01 Cấu hình lương/phụ cấp**: Không có cấu hình thì engine không có input. Cần màn hình salary config + allowances.
2. **P0 — PR-02 Payroll Engine cơ bản**: Tự tính từ salary config (chưa cần tích hợp attendance). Đã có logic mẫu trong `seed_all.py`.
3. **P1 — Tích hợp Attendance**: Kết nối ngày công, OT, nghỉ phép vào engine.
4. **P1 — Bulk create + Payroll Period**: Tạo kỳ lương, tính hàng loạt, publish hàng loạt.
5. **P2 — Quản lý người phụ thuộc + Cấu hình thuế toàn cục**.
6. **P2 — Dashboard tổng quan kỳ lương cho HR**.
