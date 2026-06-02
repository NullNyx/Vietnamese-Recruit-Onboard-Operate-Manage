# Hệ thống Chấm Công & Tính Lương — Kế hoạch Self-Hosted

> **Stack:** FastAPI (Python) · PostgreSQL · Redis · React/Next.js · Docker Compose
> **Triết lý:** HR tự cấu hình toàn bộ qua giao diện web — không cần chỉnh code.

---







## 3. Module Chấm Công

### 3.1 Phương thức check-in

HR vào **Settings → Chấm công → Phương thức** để bật/tắt từng cách:

#### Web Check-in
- Employee đăng nhập web → bấm nút Check-in / Check-out
- Backend ghi: `employee_id` + `timestamp` + `ip_address`
- HR có thể bật **IP Whitelist** — chỉ cho phép check-in từ IP công ty

```
[Employee] → Bấm Check-in trên web
    → POST /api/v1/attendance/checkin
    → Backend kiểm tra IP whitelist (nếu bật)
    → Ghi attendance_record
    → Trả về: { status: "success", checkin_time: "08:02" }
```

#### QR Check-in
- HR tạo QR trong admin, dán tại reception / phòng ban
- QR mã hóa `qr_code_id` + `location` — reset theo ca hoặc ngày (HR setting)
- Employee quét bằng điện thoại → web redirect → check-in

```
[HR] → Tạo QR code tại Settings → Chấm công → QR
    → In / hiển thị tại vị trí
[Employee] → Quét QR
    → GET /api/v1/attendance/qr/{qr_code_id}
    → Backend xác thực QR còn hiệu lực
    → Ghi attendance_record với source="qr", location_id
```

#### Device (Vân tay / Face ID)
- HR thêm device: nhập `tên`, `IP`, `API key` tại Settings → Devices
- Device gọi API về hệ thống khi nhân viên chạm/chụp
- Hệ thống khớp `device_employee_id` với `employee_id` nội bộ

```
[Device] → Nhận diện nhân viên
    → POST /api/v1/attendance/device-checkin
       Headers: X-Device-Key: {api_key}
       Body: { device_employee_id, timestamp, device_id }
    → Backend xác thực device key
    → Map device_employee_id → employee_id
    → Ghi attendance_record với source="device"
```

> **Lưu ý Self-Hosted:** Face recognition chạy trên server nội bộ bằng `DeepFace` hoặc `face_recognition` (Python). Không gửi ảnh ra ngoài. Cần GPU hoặc CPU mạnh nếu số lượng nhân viên lớn.

---

### 3.2 Mô hình giờ làm

HR vào **Settings → Chấm công → Mô hình giờ làm** để cấu hình:

#### Fixed (Giờ cố định)

```json
{
  "type": "fixed",
  "start_time": "08:00",
  "end_time": "17:00",
  "break_start": "12:00",
  "break_end": "13:00",
  "late_tolerance_minutes": 10,
  "early_leave_tolerance_minutes": 10
}
```

#### Shift (Ca làm việc)

HR tạo các ca tại **Settings → Chấm công → Quản lý ca**:

| Ca | Bắt đầu | Kết thúc | Nghỉ giữa ca |
|----|---------|----------|-------------|
| Ca Sáng | 06:00 | 14:00 | 09:30–10:00 |
| Ca Chiều | 14:00 | 22:00 | 17:30–18:00 |
| Ca Cả ngày | 08:00 | 17:00 | 12:00–13:00 |
| Ca Tối | 22:00 | 06:00 | 02:00–02:30 |

HR phân ca cho nhân viên tại **Nhân sự → Nhân viên → Phân ca**:
- Phân theo tuần (lặp lại)
- Phân theo tháng (lịch cụ thể)
- Phân theo nhóm (group rotation)

#### Flexible (Linh hoạt)

```json
{
  "type": "flexible",
  "checkin_earliest": "07:00",
  "checkin_latest": "09:30",
  "checkout_earliest": "16:00",
  "checkout_latest": "20:00",
  "min_hours_per_day": 8.0
}
```

#### Hybrid

Kết hợp Fixed + Flexible theo phòng ban: một số phòng dùng Fixed, phòng khác dùng Flexible.

---

### 3.3 Quy định OT

HR vào **Settings → Chấm công → OT**:

| Loại ngày | Tỷ lệ OT |
|-----------|----------|
| Ngày thường (T2–T6) | 1.5× |
| Thứ 7 | 2.0× |
| Chủ nhật | 2.0× |
| Ngày lễ VN | 3.0× |
| Làm đêm (22:00–06:00) | +30% vào tỷ lệ hiện tại |

Cấu hình thêm:
- Giới hạn OT tối đa / ngày (giờ)
- Giới hạn OT tối đa / tháng (giờ)
- Bắt buộc đăng ký OT trước: Có / Không
- Người duyệt OT: HR / Manager

---

### 3.4 Ngày nghỉ & Lịch lễ

HR vào **Settings → Chấm công → Ngày nghỉ**:

- **Ngày nghỉ hàng tuần:** Chọn T7, CN hoặc tùy chỉnh
- **Ngày lễ Việt Nam:** Tự động load từ API lịch VN hoặc HR nhập thủ công
- **Ngày nghỉ đặc biệt:** HR thêm thủ công (nghỉ bù, nghỉ công ty)

Ngày lễ cần load sẵn:

| Ngày | Tên lễ |
|------|--------|
| 01/01 | Tết Dương lịch |
| 10/3 âm | Giỗ Tổ Hùng Vương |
| 30/04 | Ngày Giải phóng |
| 01/05 | Quốc tế Lao động |
| 02/09 | Quốc khánh |
| Tết Nguyên Đán | 5–7 ngày (load theo năm âm lịch) |

---

### 3.5 Luồng Employee chấm công

```
[Tháng bắt đầu]
      │
      ▼
[HR đã setting: phương thức + mô hình giờ + ca]
      │
      ▼
[Employee đăng nhập web]
      │
      ▼
[Xem ca hôm nay + giờ check-in/out cần thiết]
      │
      ▼
[Check-in] ──── Web / QR / Device
      │
      ▼
[Làm việc trong ngày]
      │
      ▼
[Check-out]
      │
      ▼
[Backend tự động tính]:
   work_hours = checkout - checkin - break_time
   late_minutes = max(0, checkin - shift_start)
   early_minutes = max(0, shift_end - checkout)
   ot_hours = max(0, checkout - ot_start_time)
      │
      ▼
[Employee xem lịch sử & báo cáo cá nhân]
```

---

### 3.6 Điều chỉnh thủ công (HR)

Khi nhân viên quên check-in/out, HR vào **Chấm công → Quản lý record**:

```
[HR] → Chọn employee + ngày
    → Nhập lại giờ check-in / check-out
    → Nhập lý do bắt buộc (nếu setting = bắt buộc nhập lý do)
    → Lưu
    → Backend ghi audit_log: { editor_id, original_record, new_record, reason, timestamp }
```

HR setting cho phần này:

| Setting | Giá trị |
|---------|---------|
| Cho phép HR sửa record | Bật / Tắt |
| Bắt buộc nhập lý do | Có / Không |
| Audit log khi sửa | Bật / Tắt |

---

### 3.7 Cảnh báo (Alert)

Celery worker chạy scheduled job kiểm tra hàng ngày:

| Loại cảnh báo | Trigger | Gửi cho |
|---------------|---------|---------|
| Quên check-in | Sau 30 phút giờ bắt đầu mà chưa check-in | HR |
| Quên check-out | Sau 2 tiếng giờ kết thúc mà chưa check-out | HR |
| Đi muộn liên tục | > N lần / tháng (HR setting ngưỡng) | HR |
| OT vượt giới hạn | OT > N giờ / tháng | HR |

Kênh gửi alert: email nội bộ (SMTP tự host) hoặc hiển thị trong dashboard admin.

---

### 3.8 Báo cáo Chấm công

HR vào **Báo cáo → Chấm công**:

| Báo cáo | Nội dung |
|---------|----------|
| Bảng công ngày | Check-in/out, giờ làm, đi muộn/về sớm |
| Bảng công tháng | Tổng công, OT, ngoại lệ per employee |
| Báo cáo đi muộn | Danh sách employee đi muộn > N lần |
| Báo cáo OT | Tổng giờ OT per employee |
| Báo cáo ngoại lệ | Quên check-in/out, sửa thủ công |
| Báo cáo phòng ban | Tổng hợp theo department |

Xuất file: **Excel (.xlsx)** · **CSV** · **PDF**

---

## 4. Module Tính Lương

### 4.1 Luồng tổng thể

```
[Cuối tháng]
      │
      ▼
[HR vào Tính lương → Chọn tháng]
      │
      ▼
[Hệ thống tự động lấy]:
   · Danh sách employee + lương gross + phụ cấp
   · Attendance tháng (công, OT, muộn, sớm, nghỉ)
   · Danh sách nghỉ phép có phép (từ module Leave nếu có)
      │
      ▼
[Tính toán tự động]:
   1. Lương theo công
   2. Tiền OT
   3. Phụ cấp & thưởng
   4. Trừ BHXH/BHYT/BHTN
   5. Thuế TNCN theo bậc lũy tiến
   6. Lương Net = (1+2+3) - (4+5)
      │
      ▼
[HR xem preview bảng lương]
      │
      ▼
[HR sửa nếu cần: thưởng thêm, phạt, điều chỉnh]
      │
      ▼
[HR chốt lương → Lock bảng lương]
      │
      ▼
[Employee xem phiếu lương cá nhân]
      │
      ▼
[HR xuất Excel / PDF toàn bộ]
```

---

### 4.2 Cấu hình chung (HR)

HR vào **Settings → Tính lương → Cấu hình chung**:

| Setting | Giá trị mặc định | Ghi chú |
|---------|-----------------|---------|
| Cách tính | Gross | Hoặc Net (tính ngược) |
| Ngày công chuẩn / tháng | 26 ngày | Có thể đổi theo công ty |
| Giờ công chuẩn / ngày | 8 giờ | Dùng tính lương giờ OT |
| Chu kỳ trả lương | 1 lần / tháng | Hoặc 2 lần (ngày 15 + cuối tháng) |
| Ngày chốt lương | 25 hàng tháng | HR setting |

---

### 4.3 Bảo hiểm

**Phần employee đóng (trừ vào lương):**

| Loại | Tỷ lệ |
|------|-------|
| BHXH | 8% |
| BHYT | 1.5% |
| BHTN | 1% |
| **Tổng** | **10.5%** |

**Phần công ty đóng (không trừ vào lương nhân viên, HR cần biết để hạch toán):**

| Loại | Tỷ lệ |
|------|-------|
| BHXH | 17.5% |
| BHYT | 3% |
| BHTN | 1% |
| **Tổng** | **21.5%** |

Mức lương đóng BH: tối thiểu 4,420,000 VND — tối đa 29,800,000 VND/tháng (cập nhật theo quy định hiện hành, HR có thể chỉnh).

---

### 4.4 Thuế TNCN

Giảm trừ gia cảnh (HR setting, có thể điều chỉnh theo quy định mới):

| Loại | Mức |
|------|-----|
| Bản thân | 11,000,000 VND / tháng |
| Mỗi người phụ thuộc | 4,400,000 VND / tháng |

Bậc thuế lũy tiến:

| Bậc | Thu nhập chịu thuế / tháng | Thuế suất |
|-----|---------------------------|----------|
| 1 | ≤ 5,000,000 | 5% |
| 2 | 5,000,001 – 10,000,000 | 10% |
| 3 | 10,000,001 – 18,000,000 | 15% |
| 4 | 18,000,001 – 32,000,000 | 20% |
| 5 | > 32,000,000 | 25% |

---

### 4.5 Công thức tính lương

```
# 1. Lương theo công
luong_theo_cong = (gross / ngay_cong_chuan) × ngay_cong_thuc_te

# 2. Tiền OT
luong_gio = gross / ngay_cong_chuan / gio_chuan_ngay
tien_ot = sum(gio_ot × luong_gio × ti_le_ot)
  ti_le_ot: 1.5 (thường), 2.0 (T7/CN), 3.0 (lễ), +0.3 (đêm)

# 3. Tổng thu nhập
tong_thu_nhap = luong_theo_cong + tien_ot + phu_cap

# 4. Bảo hiểm employee đóng
bh_employee = gross × (8% + 1.5% + 1%) = gross × 10.5%

# 5. Thu nhập chịu thuế
tnct = gross - bh_employee - giam_tru_ban_than - giam_tru_phu_thuoc

# 6. Thuế TNCN (lũy tiến theo bậc)
thue_tncn = tinh_luy_tien(tnct)

# 7. Lương Net
luong_net = tong_thu_nhap - bh_employee - thue_tncn
```

---

### 4.6 Phụ cấp & Thưởng (Tùy chỉnh hoàn toàn)

Hệ thống phụ cấp hoàn toàn **dynamic** — HR tự tạo, đặt tên, cấu hình bao nhiêu loại tuỳ ý. Không hardcode danh sách.

HR vào **Settings → Tính lương → Phụ cấp → Thêm phụ cấp mới**:

| Trường | Giá trị | Ghi chú |
|--------|---------|---------|
| Tên phụ cấp | VD: "Phụ cấp xăng xe", "Phụ cấp độc hại" | HR tự đặt |
| Kiểu tính | `fixed` / `per_day` / `percent_gross` | Cố định / Theo ngày công / % lương |
| Số tiền / Tỷ lệ | VD: 500,000 hoặc 2% | Tùy kiểu tính |
| Chịu thuế TNCN | Có / Không | Ảnh hưởng thuế |
| Tính vào BH | Có / Không | Ảnh hưởng mức đóng BH |
| Áp dụng cho | Toàn công ty / Phòng ban / Từng cá nhân | Phạm vi |
| Trạng thái | Bật / Tắt | Tắt thì không tính vào lương |

**Ví dụ một số công ty hay dùng:**

| Tên phụ cấp | Kiểu | Mức |
|-------------|------|-----|
| Ăn trưa | fixed | 730,000 / tháng |
| Xăng xe | fixed | 500,000 / tháng |
| Điện thoại | fixed | 200,000 / tháng |
| Nhà ở | fixed | 1,000,000 / tháng |
| Độc hại | fixed | 800,000 / tháng |
| Chuyên cần | per_day | 30,000 / ngày công |
| Thâm niên | percent_gross | 2% / năm làm việc |
| Thưởng hiệu suất | percent_gross | 10% gross |
| Thưởng tháng 13 | fixed | = 1 tháng lương gross |

**Gán phụ cấp cho nhân viên:**

HR vào **Nhân sự → Nhân viên → Sửa → Phụ cấp**: chọn những loại phụ cấp áp dụng cho nhân viên đó và nhập mức riêng nếu khác mặc định.

```
allowance_types (định nghĩa loại — HR tạo)
  id, name, calc_type, default_amount, taxable, include_in_insurance, scope, is_active

employee_allowances (gán cho từng nhân viên)
  id, employee_id, allowance_type_id, custom_amount, effective_from, effective_to
```

**Công thức tính phụ cấp:**

```
# Với mỗi phụ cấp được gán cho employee:
if calc_type == 'fixed':
    amount = custom_amount ?? default_amount

if calc_type == 'per_day':
    amount = (custom_amount ?? default_amount) × actual_working_days

if calc_type == 'percent_gross':
    amount = gross × (rate / 100)

tong_phu_cap = sum(amount for each active allowance)
```

---

### 4.7 Dữ liệu từ Chấm công → Lương

| Dữ liệu Attendance | Công thức áp dụng |
|--------------------|-------------------|
| Ngày công thực tế | `(gross/26) × ngày_công` |
| Giờ OT | `giờ_OT × lương_giờ × tỷ_lệ` |
| Phút đi muộn (vượt tolerance) | `phút_muộn × (lương_giờ/60)` (nếu HR bật trừ muộn) |
| Phút về sớm (vượt tolerance) | Tương tự |
| Ngày nghỉ không phép | `ngày_nghỉ × lương_ngày` |
| Ngày nghỉ phép có phép | Không trừ lương |

---

### 4.8 Phiếu lương Employee

Employee vào **Lương → Phiếu lương** để xem:

| Mục | Nội dung |
|-----|----------|
| Lương gross | Lương cơ bản |
| Ngày công | X/26 ngày |
| Lương theo công | Tính từ ngày công |
| Giờ OT | X giờ |
| Tiền OT | Theo tỷ lệ |
| Phụ cấp | Từng loại |
| **Tổng thu nhập** | |
| BHXH (8%) | − |
| BHYT (1.5%) | − |
| BHTN (1%) | − |
| Thuế TNCN | − |
| **Lương Net** | **= Số tiền thực nhận** |

---

## 5. Tính năng bổ sung

### 5.1 Duyệt Timesheet cuối tháng

Luồng khóa công trước khi tính lương:

```
[Cuối tháng — ngày HR setting]
      │
      ▼
[Hệ thống tổng hợp attendance tháng → trạng thái "pending_review"]
      │
      ▼
[HR vào Duyệt công → Xem danh sách employee + tổng ngày công + OT + ngoại lệ]
      │
      ├── Có vấn đề → Sửa record thủ công (ghi audit log)
      │
      ▼
[HR bấm "Duyệt & Khóa" → trạng thái = "locked"]
      │
      ▼
[Chuyển sang tính lương — không sửa được attendance đã locked]
```

---

### 5.2 Xin ngoại lệ (Employee quên check-in/out)

```
[Employee] → Quên check-in / check-out
      │
      ▼
[Vào web → Xin ngoại lệ → Nhập]:
   · Ngày
   · Loại: Quên check-in / check-out / cả hai
   · Giờ thực tế
   · Lý do
      │
      ▼
[HR nhận request trong admin → Duyệt / Từ chối]
      │
      ├── Duyệt → Backend cập nhật attendance record + ghi audit log
      └── Từ chối → Employee nhận thông báo
```

HR setting:

| Setting | Giá trị |
|---------|---------|
| Cho phép employee xin ngoại lệ | Bật / Tắt |
| Cần HR duyệt | Bật / Tắt |
| Thời hạn xin (N ngày sau ngày quên) | VD: 3 ngày |

---

### 5.3 Đăng ký OT

```
[Employee] → Vào Đăng ký OT → Nhập]:
   · Ngày
   · Giờ bắt đầu / kết thúc OT
   · Lý do / mô tả công việc
      │
      ▼
[Manager hoặc HR nhận request → Duyệt / Từ chối]
      │
      ├── Duyệt → OT request ở trạng thái "approved"
      │         → Employee check-out sau giờ → hệ thống tự tính tiền OT
      └── Từ chối → Employee nhận thông báo
```

HR setting:

| Setting | Giá trị |
|---------|---------|
| Bắt buộc đăng ký trước | Có / Không |
| Người duyệt | HR / Manager |
| Giới hạn OT / ngày | ___ giờ |
| Giới hạn OT / tháng | ___ giờ |

---

### 5.4 Audit Log

Mọi hành động có ảnh hưởng đến dữ liệu đều được ghi:

| Hành động | Ghi log |
|-----------|---------|
| HR sửa / tạo / xóa attendance record | ✓ |
| HR thay đổi bất kỳ setting nào | ✓ |
| HR chốt / lock bảng lương | ✓ |
| HR duyệt ngoại lệ / OT | ✓ |
| System tự động tính công, tính lương | ✓ |

HR vào **Cài đặt → Audit Log** để xem lịch sử. Lưu trữ: 6 tháng / 1 năm / vĩnh viễn (HR chọn).

---

## 6. Database schema (tóm tắt)

```sql
-- Nhân viên (đã có từ module Employee)
employees (id, name, department_id, email, ...)

-- Cấu hình chấm công
attendance_settings (
  id, company_id,
  checkin_method,        -- 'web' | 'qr' | 'device' | 'all'
  work_model,            -- 'fixed' | 'shift' | 'flexible' | 'hybrid'
  ip_whitelist,          -- JSON array
  ot_rules,              -- JSON
  late_tolerance_min, early_tolerance_min,
  alert_settings         -- JSON
)

-- Ca làm việc
shifts (id, name, start_time, end_time, break_start, break_end)

-- Phân ca
employee_shifts (id, employee_id, shift_id, date_from, date_to, recurrence)

-- Bản ghi chấm công
attendance_records (
  id, employee_id, date,
  checkin_time, checkout_time,
  source,              -- 'web' | 'qr' | 'device'
  ip_address, device_id, qr_code_id, location,
  work_hours, late_minutes, early_minutes, ot_hours,
  status,              -- 'present' | 'absent' | 'late' | 'manual'
  is_locked,
  created_at, updated_at
)

-- Audit log
audit_logs (
  id, actor_id, action,
  entity_type, entity_id,
  old_value, new_value,    -- JSON
  reason, created_at
)

-- Đăng ký OT
ot_requests (
  id, employee_id,
  date, start_time, end_time,
  reason, status,          -- 'pending' | 'approved' | 'rejected'
  approved_by, approved_at
)

-- Xin ngoại lệ
exception_requests (
  id, employee_id,
  date, type,              -- 'missing_checkin' | 'missing_checkout'
  actual_time, reason,
  status, approved_by, approved_at
)

-- Cấu hình lương chung
payroll_settings (
  id, company_id,
  calc_type,               -- 'gross' | 'net'
  standard_working_days, standard_hours_per_day,
  bhxh_employee_rate, bhyt_employee_rate, bhtn_employee_rate,
  bhxh_company_rate, bhyt_company_rate, bhtn_company_rate,
  personal_deduction, dependent_deduction,
  pay_cycle                -- 'monthly' | 'bimonthly'
)

-- Lương nhân viên
employee_salaries (
  id, employee_id,
  gross_salary, dependents,
  allowances               -- JSON: { lunch, transport, phone, ... }
)

-- Bảng lương tháng
payroll_records (
  id, employee_id, month, year,
  working_days, ot_hours,
  gross, total_income,
  bhxh, bhyt, bhtn,
  tax_income, personal_income_tax,
  net_salary,
  status,                  -- 'draft' | 'approved' | 'locked'
  locked_by, locked_at
)
```

---

## 7. API endpoints chính

### Attendance

```
POST   /api/v1/attendance/checkin           # Web / QR / Device check-in
POST   /api/v1/attendance/checkout          # Check-out
GET    /api/v1/attendance/today             # Trạng thái check-in hôm nay
GET    /api/v1/attendance/history           # Lịch sử của employee
GET    /api/v1/attendance/records           # HR: xem tất cả (filter)
PATCH  /api/v1/attendance/records/{id}      # HR: sửa record
POST   /api/v1/attendance/device-checkin    # Device gọi vào (API key auth)

POST   /api/v1/ot-requests                  # Đăng ký OT
PATCH  /api/v1/ot-requests/{id}/approve    # Duyệt OT
POST   /api/v1/exception-requests          # Xin ngoại lệ
PATCH  /api/v1/exception-requests/{id}/approve  # Duyệt ngoại lệ
```

### Settings (HR only)

```
GET/PUT  /api/v1/settings/attendance        # Cấu hình chấm công
GET/PUT  /api/v1/settings/payroll           # Cấu hình lương
GET/POST /api/v1/shifts                     # Quản lý ca
POST     /api/v1/devices                    # Thêm device
POST     /api/v1/qr-codes                   # Tạo QR
```

### Payroll

```
POST   /api/v1/payroll/calculate/{month}    # Tính lương tháng
GET    /api/v1/payroll/preview/{month}      # Xem preview
PATCH  /api/v1/payroll/{id}                 # HR sửa trước khi chốt
POST   /api/v1/payroll/lock/{month}         # Lock bảng lương
GET    /api/v1/payroll/slip/{month}         # Employee xem phiếu lương
GET    /api/v1/payroll/export/{month}       # Xuất Excel / PDF
```

### Reports

```
GET  /api/v1/reports/attendance/daily
GET  /api/v1/reports/attendance/monthly
GET  /api/v1/reports/attendance/late
GET  /api/v1/reports/attendance/ot
GET  /api/v1/reports/payroll/monthly
GET  /api/v1/audit-logs
```

---

## 8. Triển khai Self-Hosted

### Yêu cầu server tối thiểu

| Số nhân viên | CPU | RAM | Disk |
|-------------|-----|-----|------|
| ≤ 50 | 2 core | 4 GB | 50 GB |
| 50–200 | 4 core | 8 GB | 100 GB |
| 200–500 | 8 core | 16 GB | 200 GB |
| Có Face Recognition | +2 core / +4 GB RAM | | |

### Cấu trúc thư mục

```
attendance-system/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/          # Router cho từng module
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   │   ├── attendance.py
│   │   │   ├── payroll.py
│   │   │   ├── face_recognition.py
│   │   │   └── alerts.py
│   │   ├── tasks/        # Celery tasks (alerts, reports)
│   │   └── core/         # Config, auth, database
├── frontend/
│   ├── Dockerfile
│   └── src/
│       ├── pages/
│       │   ├── hr/       # HR dashboard, settings
│       │   ├── employee/ # Check-in, lịch sử, phiếu lương
│       │   └── manager/  # Team attendance
│       └── components/
└── nginx/
    └── nginx.conf
```

### File .env chính

```env
# Database
DATABASE_URL=postgresql://user:password@db:5432/attendance_db
REDIS_URL=redis://redis:6379/0

# Auth
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Email alerts (SMTP tự host hoặc relay)
SMTP_HOST=smtp.company.local
SMTP_PORT=587
SMTP_USER=noreply@company.com
SMTP_PASSWORD=

# Face Recognition (tắt nếu không dùng)
FACE_RECOGNITION_ENABLED=false
FACE_MODEL=DeepFace  # hoặc face_recognition

# App
COMPANY_NAME=Tên công ty
TIMEZONE=Asia/Ho_Chi_Minh
```

### Khởi động

```bash
# Lần đầu
cp .env.example .env
# Chỉnh .env theo môi trường

docker compose up -d
docker compose exec backend alembic upgrade head  # Tạo database
docker compose exec backend python -m app.seed    # Tạo HR admin đầu tiên

# Production (HTTPS)
docker compose -f docker-compose.prod.yml up -d
```

---

## 9. Lộ trình phát triển theo giai đoạn

### Giai đoạn 1 — MVP (4–6 tuần)

Mục tiêu: HR và nhân viên dùng được ngay, tính công + lương cơ bản.

- [ ] Auth: đăng nhập, phân quyền 3 role (hr, manager, employee)
- [ ] HR Settings: phương thức (Web + QR), mô hình giờ Fixed, ngày nghỉ tuần
- [ ] Web Check-in / Check-out
- [ ] QR Check-in / Check-out
- [ ] Tính công: work_hours, late_minutes, early_minutes
- [ ] Employee xem lịch sử chấm công
- [ ] HR xem & sửa record thủ công + audit log
- [ ] Settings: late_tolerance, early_leave_tolerance, weekly_off_day
- [ ] Tính lương cơ bản: gross → BH → thuế → net
- [ ] Employee xem phiếu lương
- [ ] HR export Excel bảng công + bảng lương

### Giai đoạn 2 — Ca & OT (3–4 tuần)

- [ ] Quản lý ca (Shift) + phân ca cho nhân viên
- [ ] Đăng ký & duyệt OT
- [ ] Tính OT tự động theo tỷ lệ
- [ ] Ngày lễ VN tự động
- [ ] Holiday calendar config
- [ ] Alert/notification qua email
- [ ] Duyệt timesheet cuối tháng

### Giai đoạn 3 — Mở rộng (3–4 tuần)

- [ ] Giờ linh hoạt (Flexible)
- [ ] Xin ngoại lệ (employee tự gửi request)
- [ ] Dashboard HR (widget tổng quan)
- [ ] Manager xem attendance team + duyệt OT
- [ ] Export PDF phiếu lương
- [ ] IP Whitelist

### Giai đoạn 4 — Nâng cao (theo nhu cầu)

- [ ] Device integration (ZKTeco vân tay)
- [ ] Face ID (DeepFace, chạy offline trên server)
- [ ] Hybrid work model
- [ ] Tích hợp module Nghỉ phép (Leave)
- [ ] Kế toán role + duyệt lương
- [ ] Báo cáo nâng cao + biểu đồ

---

---

## Related Decisions

- **ADR 0009**: Attendance & Payroll Default Decisions — rationale for all
  defaults listed in Section 10.

*Version: 1.1*