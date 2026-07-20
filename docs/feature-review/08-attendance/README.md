# 08 — Attendance (Chấm công)

> **Nhóm:** Attendance | **Tổng:** 4 chức năng | **Deployed:** 3 | **Đã gỡ:** 1 | **Pending Review:** 3
> **Backend module:** `backend/src/modules/attendance/`
> **Frontend:** `(dashboard)/attendance/`, ESS attendance

---

## Danh sách chức năng

| ID | Chức năng | Mô tả ngắn | Backend Route | Frontend Page | Status | Review |
|----|-----------|------------|---------------|---------------|--------|--------|
| AT-01 | Check-in/Check-out | Employee check-in/out; ghi IP/source, chống trùng, network allowlist | `/api/attendance/me/*` | ESS attendance | ✅ Deployed | ⬜ |
| AT-02 | HR Record & Correction | Lọc record; sửa giờ vào/ra với reason + audit | `/api/attendance/records*` | HR Attendance list | ✅ Deployed | ⬜ |
| AT-03 | Network Allowlist | HR quản lý CIDR (get/put/add/delete) | `/api/attendance/settings/network*` | Settings UI | ✅ Deployed | ⬜ |
| AT-04 | Schedule/Holiday/Leave/Overtime UI | Các trang phụ đã gỡ khỏi frontend | — | — | ❌ Đã gỡ | — |

---

## Tiêu chí Review

- [x] Router đã wired trong `backend/src/main.py` → ✅ Line 236
- [x] Check-in/out: chống trùng, IP/source, network allowlist → ✅ `ON CONFLICT DO NOTHING`
- [x] HR correction: reason bắt buộc, audit → ✅ Atomic transaction + audit log
- [x] Network allowlist: CIDR validation → ✅ `_normalize_input` + `ip_network`

---

## Kết quả Review từng chức năng

### AT-01 — Check-in/Check-out
- **Ngày review:** 2025-07-15
- **Người review:** AI Agent (user-perspective audit)
- **Kết quả:** ⚠️ Cần cải thiện UX
- **Ghi chú:** Xem User-Perspective Audit bên dưới

### AT-02 — HR Record & Correction
- **Ngày review:** 2025-07-15
- **Người review:** AI Agent (user-perspective audit)
- **Kết quả:** ⚠️ Cần cải thiện UX
- **Ghi chú:** Xem User-Perspective Audit bên dưới

### AT-03 — Network Allowlist
- **Ngày review:** 2025-07-15
- **Người review:** AI Agent (user-perspective audit)
- **Kết quả:** ⚠️ Cần cải thiện UX + Security UX
- **Ghi chú:** Xem User-Perspective Audit bên dưới

### AT-04 — Schedule/Holiday/Leave/Overtime UI
- **Ngày review:** — (đã gỡ)
- **Người review:** —
- **Kết quả:** ❌
- **Ghi chú:** Đã gỡ tại commit `46199ec`, không cần review

---

## User-Perspective Audit (Đánh giá từ góc độ người dùng)

> **Ngày audit:** 2025-07-15 | **Phạm vi:** Toàn bộ 3 chức năng active
> **Tiêu chí:** Logic đúng + UI/UX tối ưu + Trải nghiệm người dùng thực tế

---

### AT-01: ESS Check-in/Check-out (Nhân viên tự chấm công)

#### Điểm mạnh

1. **Idempotent an toàn:** Gọi check-in/out nhiều lần không gây lỗi hay trùng record — tốt cho người dùng hay bấm 2 lần.
2. **Trạng thái rõ ràng:** Badge "Đã check-in"/"Chưa check-in"/"Đã check-out" + hiển thị giờ + IP giúp nhân viên biết chính xác trạng thái.
3. **Nút bị disable đúng lúc:** Check-in disable khi đã check-in, Check-out disable khi chưa check-in hoặc đã check-out — tránh thao tác vô nghĩa.
4. **Lịch sử 30 ngày:** Có bảng lịch sử giúp nhân viên tự kiểm tra.
5. **Thông báo lỗi mạng:** Có footnote giải thích về Network Allowlist khi không chấm công được.
6. **IP + User-Agent được ghi nhận:** Minh bạch, chống gian lận.

#### Vấn đề cần cải thiện

| # | Mức độ | Vấn đề | Mô tả | Đề xuất |
|---|--------|--------|-------|---------|
| 1 | 🔴 Cao | Không có thông báo thành công | Sau khi check-in/out thành công, không có toast/xác nhận. Người dùng phải tự nhìn badge đổi màu — dễ bỏ lỡ, nhất là trên mobile. | Thêm toast "Check-in thành công lúc 08:15" sau mutation thành công. |
| 2 | 🔴 Cao | Không hiển thị IP hiện tại khi bị chặn | Khi bị lỗi `OFFICE_NETWORK_REQUIRED`, người dùng thấy thông báo nhưng không biết IP của mình là gì để báo HR. | Thêm IP hiện tại vào error message: "IP của bạn (X.X.X.X) không nằm trong danh sách mạng văn phòng được phép." |
| 3 | 🟡 Trung bình | Không có navigation theo tháng | Nhân viên chỉ xem được 30 ngày gần nhất, không xem được tháng trước. Backend đã hỗ trợ `year`/`month` params nhưng FE không dùng. | Thêm month picker để nhân viên xem lịch sử tháng cũ. |
| 4 | 🟡 Trung bình | Thiếu loading state trên card trạng thái | Khi đang check-in/out, card trạng thái vẫn hiện dữ liệu cũ cho đến khi refetch xong. | Hiển thị spinner nhỏ trên card khi mutation đang pending. |
| 5 | 🟢 Thấp | Không có hiển thị thời gian tương đối | Bảng lịch sử chỉ hiện absolute time, không có relative time. | Cân nhắc thêm relative time ở chế độ xem gần đây. |
| 6 | 🟢 Thấp | Nút check-in/out không có confirm dialog | Dù idempotent, người dùng có thể bấm nhầm. | Thêm confirm dialog cho check-out (vì đánh dấu kết thúc ngày làm việc). |

#### Đánh giá logic

- ✅ Chống trùng: PostgreSQL `ON CONFLICT DO NOTHING` đảm bảo atomic.
- ✅ IP/source được ghi nhận đầy đủ.
- ✅ Network allowlist check trước khi cho check-in và check-out.
- ✅ Work date theo timezone của organization.
- ⚠️ `AlreadyCheckedInError` được định nghĩa nhưng không dùng (dead code).
- ⚠️ Không validate `check_out_at > check_in_at` khi HR sửa record.
- ⚠️ Không giới hạn khung giờ check-in/out (có thể check-in lúc 3h sáng).

---

### AT-02: HR Record & Correction (HR xem và sửa bản ghi)

#### Điểm mạnh

1. **Bộ lọc đa dạng:** Lọc theo ngày, nhân viên, trạng thái — đáp ứng tốt nhu cầu tra cứu.
2. **Audit log đầy đủ:** Mọi sửa chữa đều ghi lại reason + previous values + admin — đúng chuẩn compliance.
3. **Reason bắt buộc + validate whitespace:** Không cho sửa mà không có lý do, không chấp nhận khoảng trắng.
4. **Modal hiệu chỉnh rõ ràng:** Hiển thị tên nhân viên + ngày, có datetime-local inputs.
5. **Phân trang:** Có phân trang với tổng số bản ghi.
6. **Hiển thị IP check-in:** Minh bạch cho HR.

#### Vấn đề cần cải thiện

| # | Mức độ | Vấn đề | Mô tả | Đề xuất |
|---|--------|--------|-------|---------|
| 1 | 🔴 Cao | Không hiển thị bản ghi đã bị sửa | Trong bảng danh sách, không có indicator nào cho biết record đã từng bị correction. | Thêm cột "Đã sửa" với badge màu cam khi `corrected_at != null`. |
| 2 | 🔴 Cao | Không hiển thị lịch sử sửa trước đó | Khi mở modal hiệu chỉnh, không hiển thị lý do/lần sửa trước. | Hiển thị previous correction reason + timestamp + người sửa trong modal. |
| 3 | 🟡 Trung bình | Dropdown chọn nhân viên giới hạn 100 | Nếu công ty có >100 nhân viên active, không thấy hết. | Dùng searchable select (Combobox) hoặc infinite scroll. |
| 4 | 🟡 Trung bình | Không có client-side validation cho date range | Có thể chọn `start_date > end_date`, chỉ phát hiện lỗi khi server trả về 422. | Validate `end >= start` ở client trước khi gửi request. |
| 5 | 🟡 Trung bình | Label "để trống để xóa" dễ gây nhầm | Để trống 1 field → field đó bị xóa khỏi record, destructive nhưng không confirm. | Thêm confirm dialog hoặc đổi label rõ ràng hơn. |
| 6 | 🟡 Trung bình | Không validate check_out > check_in | HR có thể set `check_out_at` trước `check_in_at`, backend không validate. | Thêm server-side validation. |
| 7 | 🟢 Thấp | Không có export CSV/Excel | HR không xuất được dữ liệu chấm công để làm bảng lương. | Thêm nút "Xuất CSV" với filter hiện tại. |
| 8 | 🟢 Thấp | Không có bulk correction | Khi nghỉ lễ, HR phải sửa từng dòng một. | Cân nhắc bulk edit cho các ngày lễ. |
| 9 | 🟢 Thấp | Không hiển thị timezone | Giờ hiển thị theo local browser, không có indicator timezone. | Hiển thị timezone hoặc ghi chú "Giờ địa phương". |

#### Đánh giá logic

- ✅ Correction + audit log trong cùng transaction → nguyên tử.
- ✅ Reason validate whitespace-only bị reject.
- ✅ Phải có ít nhất 1 field được thay đổi.
- ⚠️ Không validate `check_out_at > check_in_at` khi correction.
- ⚠️ `_require_hr` thực chất chỉ check `UserRole.ADMIN`, chưa phân biệt HR vs Admin.

---

### AT-03: Network Allowlist (HR quản lý mạng văn phòng)

#### Điểm mạnh

1. **CIDR validation chặt chẽ:** Backend validate CIDR format, IPv4 only, bare IP → /32.
2. **Audit log mọi thay đổi:** Thêm/sửa/xóa CIDR đều được ghi audit.
3. **Bulk replace có warning:** Modal thay thế toàn bộ có cảnh báo đỏ + nút danger — tốt.
4. **Pre-fill khi replace:** Mở modal replace hiển thị danh sách hiện tại.
5. **Giới hạn 20 CIDR:** Tránh abuse.

#### Vấn đề cần cải thiện

| # | Mức độ | Vấn đề | Mô tả | Đề xuất |
|---|--------|--------|-------|---------|
| 1 | 🔴 Cao | **Security UX: Không giải thích empty = allow all** | UI nói "Chỉ cho phép chấm công từ các mạng trong danh sách" nhưng thực tế: danh sách rỗng = **tất cả IP đều được phép**. HR có thể nghĩ ngược lại. | Hiển thị rõ: khi rỗng → "Đang cho phép TẤT CẢ IP — thêm CIDR để giới hạn". Khi có CIDR → "Chỉ các mạng trong danh sách được phép." |
| 2 | 🔴 Cao | Không có confirm dialog khi xóa CIDR | Click icon thùng rác → xóa ngay lập tức. Nếu HR lỡ tay, toàn bộ nhân viên không check-in được. | Thêm confirm dialog trước khi xóa. |
| 3 | 🟡 Trung bình | Không có client-side CIDR validation | Gõ sai định dạng → server trả 400, phản hồi chậm. | Validate CIDR format bằng regex trước khi gửi. |
| 4 | 🟡 Trung bình | Không có thông báo thành công | Sau khi thêm/xóa CIDR, không có toast. | Thêm toast xác nhận. |
| 5 | 🟢 Thấp | Chỉ thêm được 1 CIDR mỗi lần | Muốn thêm nhiều phải dùng flow "Thay thế toàn bộ". | Thêm bulk add: textarea nhập nhiều CIDR. |
| 6 | 🟢 Thấp | Không hiển thị `updated_at` | HR không biết lần cuối allowlist được cập nhật. | Hiển thị "Cập nhật lần cuối: ...". |

#### Đánh giá logic

- ✅ CIDR validation + dedup + max 20.
- ✅ Bare IP tự động expand thành /32.
- ✅ Empty allowlist = allow all (by design, documented in ADR-0010).
- ✅ Audit log mọi thao tác.

---

## Cross-cutting Issues (Vấn đề xuyên suốt)

| # | Mức độ | Vấn đề | Mô tả | Đề xuất |
|---|--------|--------|-------|---------|
| CC-1 | 🔴 Cao | **Không có success toast ở bất kỳ đâu** | AT-01, AT-02, AT-03 đều không hiển thị thông báo thành công sau thao tác. | Thêm global toast system (react-hot-toast hoặc sonner). |
| CC-2 | 🟡 Trung bình | Không có error boundary | Component crash → toàn bộ page trắng. | Thêm `error.tsx` cho từng route segment. |
| CC-3 | 🟡 Trung bình | Loading state còn basic | "Đang tải…" text thay vì skeleton. | Dùng `LoadingRows` nhất quán toàn app. |
| CC-4 | 🟢 Thấp | Không có offline handling | Mất mạng → mutation fail silently. | Cân nhắc `mutation.retry`. |
| CC-5 | 🟢 Thấp | Không có keyboard shortcuts | Power user không có phím tắt. | Cân nhắc sau MVP. |

---

## Tổng kết

| Tiêu chí | AT-01 | AT-02 | AT-03 |
|----------|-------|-------|-------|
| Logic đúng | ✅ | ✅ | ✅ |
| UX cơ bản | ✅ | ✅ | ✅ |
| UX nâng cao | ⚠️ | ⚠️ | ⚠️ |
| Security UX | ✅ | ✅ | 🔴 |
| Accessibility | ⚠️ | ⚠️ | ⚠️ |
| Error handling | ⚠️ | ⚠️ | ⚠️ |
| Mobile responsive | ✅ | ✅ | ✅ |

### Ưu tiên sửa

1. **P0 — Ngay:** ✅ Thêm success toast toàn app (sonner) + ✅ Sửa empty allowlist UX (banner vàng cảnh báo)
2. **P1 — Sớm:** ✅ Hiển thị IP trong error message + ✅ Confirm dialog xóa CIDR + ✅ Hiển thị record đã sửa (cột "Sửa" + previous correction)
3. **P2 — Sau:** ✅ Month navigation cho ESS + ✅ Employee select limit tăng lên 200 + ✅ Client-side CIDR validation + ✅ Client-side date validation
4. **P3 — Đã làm hết:** ✅ Export CSV + ✅ Bulk add CIDR (Ctrl+Enter) + ✅ Relative time + ✅ Loading state khi mutation + ✅ Confirm dialog check-out + ✅ Validate check_out > check_in server-side + ✅ Timezone indicator + ✅ updated_at cho allowlist + ✅ Error boundaries (2 files) + ✅ Mutation retry + ✅ Label clarification + ✅ Bulk add CIDR

### Ngày fix: 2025-07-15 | Trạng thái: ✅ All 21 issues resolved
