# Design System FE

Mục tiêu: khóa format gốc của UI trước khi code.

Source of truth cho style là `docs/design/DESIGN.md`:
- AI Labs
- research-paper white (#FAFAF8)
- 1 green accent
- flat, quiet, directable
- IBM Plex Sans / IBM Plex Mono

## Nguyên tắc

- Design là source of truth cho FE layout, hierarchy, color, typography, density, state.
- Pencil `.pen` file là nơi khóa design system và screen family.
- Không code FE khi chưa có design tương ứng đã review/chốt.
- Không để agent suy diễn layout hoặc tone màu từ code cũ.

## Tư duy thiết kế

Thiết kế cho HR dùng mỗi ngày. Họ không phải dân IT. Họ làm trong áp lực:
- giấy tờ deadline
- hợp đồng cần ký nhanh
- onboarding gấp
- inbox dồn tích

UI phải rõ ràng, tĩnh lặng, tiên đoán được.
AI Labs là cool, quiet, flat. Neutral kéo composition, green chỉ dùng cho action.
Không gradient. Không mix accent phụ. Không hiệu ứng rườm rà.
Mỗi pixel phải phục vụ quyết định của HR: việc gì tiếp theo, cần làm gì, trạng thái gì.

---

## Luồng thiết kế tổng thể

Dưới đây là quy trình từ lúc nhận task FE đến khi có design gốc sẵn sàng cho implement.
Agent phải đọc và chạy đúng thứ tự.

```
Bước 1 — Đọc nền
Bước 2 — Hiểu hệ thống
Bước 3 — Ghi notes vào docs/design/notes.md
Bước 4 — Chốt format gốc bằng Pencil (system.pen)
Bước 5 — Sinh screen family bám system (screens/*.pen)
Bước 6 — Review + approve
Bước 7 — Implement BE + FE
Bước 8 — QA browser
```

---

### Bước 1 — Đọc nền

Trước khi thiết kế bất kỳ màn nào, đọc:

1. `CONTEXT.md` — glossary, canonical terms.
2. `docs/design/DESIGN.md` — style source of truth.
3. ADR liên quan trong `docs/decisions/0021–0029`.
4. PRD hoặc Jira task.
5. `docs/design/README.md` (file này).

### Bước 2 — Hiểu hệ thống

Trả lời các câu hỏi này trước khi mở Pencil:

- **Hệ thống làm gì?** — HR operation work system, không phải HRM Suite.
- **Ai dùng?** — HR admin / staff. Employee không login.
- **Họ cần làm gì?** — Xử lý work queue, triage inbox, quản lý hồ sơ/con tract/document.
- **Họ đau ở đâu?** — Chậm do navigation rối, thao tác nhiều bước, trạng thái không rõ.
- **Màn hình chính là gì?** — Today, All Work, Inbox, Context Libraries (People/Document/Contract/Template).
- **Context Libraries để tra, không phải trung tâm xử lý chính.**

Ghi kết quả vào `docs/design/notes.md`.

### Bước 3 — Brainstorm format

Ghi vào `docs/design/notes.md`:

- Mục tiêu UX của toàn bộ app.
- Layout grammar: shell gồm gì (nav, toolbar, main, inspector).
- Density: ít thông tin hay dày đặc.
- Navigation: top nav, sidebar, tab, modal, drawer?
- Hierarchy: cái gì nổi nhất trên mỗi màn.
- Tone màu: tĩnh, trung tính, hay tươi?
- Typography: font nào, scale nào.
- Component family: button, table, form, card, empty state, loading, error state.
- Bất lợi cho user nếu làm sai format là gì.

### Bước 4 — Chốt format gốc trong Pencil

**Mở Pencil.** Tạo `docs/design/system.pen` cho library, và `docs/design/system.pen` cho showcase.

Đây là **source of truth** cho:

- App shell: layout tổng (nav, sidebar, main area).
- Design tokens: màu chủ đạo, text, border, background, spacing.
- Typography: font, size, weight, line height cho heading / body / label / caption.
- Primitives: button (primary / secondary / ghost / danger), input, select, checkbox, toggle.
- Patterns: table, card, form group, empty state, loading skeleton, error state.
- Navigation: nav bar, tab, breadcrumb, pagination.
- Dialog / Sheet / Modal / Drawer.

**Không** thiết kế màn lẻ ở `system.pen`. Chỉ hệ thống.

Search là shell-level pattern, không phải screen family độc lập. Thiết kế search dưới
toolbar / overlay / drawer trong `system.pen` hoặc ghi chú shell. Bản design riêng
đặt ở `docs/design/components/search.lib.pen`, không tính vào bảng `screens/*.pen`.

### Bước 5 — Sinh screen family

Tạo file `.pen` trong `docs/design/screens/`:

| File | Surface | Trạng thái bắt buộc |
|---|---|---|
| `01-today.pen` | Today (Command Center) | default, empty, loading, error |
| `02-all-work.pen` | All Work (Operations Center) | filtered, empty, loading |
| `03-work-detail.pen` | Work Detail (Execution Screen) | default, editing, saving, error |
| `04-inbox.pen` | Inbox (Intake) | unread, triaged, empty, dismissed |
| `05-people.pen` | People | list, detail, profile, empty |
| `06-documents.pen` | Documents | grid, detail, verify modal, empty |
| `07-contracts.pen` | Contracts | list, detail, sign modal, lifecycle |
| `08-admin.pen` | Admin / Settings | form, error |

Mỗi screen là composition từ `system.pen`. Nếu screen cần thứ không có trong system → sửa `system.pen` (không patch lẻ).

## Lưu ý MCP Pencil

- Luôn kiểm `get_editor_state(include_schema: true)` trước khi `batch_design`.
- Active editor quyết định file nào bị sửa. Mở đúng `.pen` file trước khi ghi.
- Không chạy `batch_design` khi editor vẫn trỏ vào `system.pen` nếu mục tiêu là screen riêng.
- Tách rõ: `system.pen` cho system / tokens / shell, `screens/*.pen` cho màn cụ thể.
- Nếu cần đổi màn, mở hoặc nạp đúng file màn trước, rồi mới insert/update.
- Sau mỗi batch, kiểm file đích còn đúng scope, tránh đổ nhầm vào file đang active.

### Bước 6 — Review + approve

Kiểm tra:

- Screen có bám đúng format gốc không?
- Có component nào dùng sai hệ thống không?
- Empty/loading/error có mặt đủ không?
- Flow user có mạch lạc không?

Nếu lệch system → sửa `system.pen`.
Nếu lệch screen → sửa screen.
**Chưa approve là chưa code.**

### Bước 7 — Implement BE + FE

- BE: viết theo API contract, service layer, data model → tổng thể design đã nhìn thấy.
- FE: bám `.pen` đã approve. Không tự suy diễn layout / hierarchy / tone / spacing.

Nếu gặp technical constraint buộc sai lệch → báo user, không âm thầm sửa.

### Bước 8 — QA browser

Dùng `frontend-testing-debugging`.
Kiểm desktop + mobile.
So khớp design: copy, spacing, type scale, interaction, empty/error state, responsive.
Lệch → sửa theo design, không bịa.

---

## Tool routing

| Tool | Khi nào dùng |
|---|---|
| `grill-with-docs` | Chốt yêu cầu UX, lấp gap product không rõ |
| `prototype` (UI branch) | Thử layout/luồng khi chưa chắc |
| `ui-ux-pro-max` | Gợi ý style, palette, font, design pattern |
| `pencil` | Công cụ thiết kế chính (system + screens) |
| `frontend-app-builder` | Chỉ concept/redesign lớn bằng Image Gen |
| `shadcn` | Compose component khi implement FE code |
| `frontend-testing-debugging` | QA browser sau implement |

---

## Quy ước file

- `docs/design/system.pen`: design system gốc, component library, tokens, shell layout.
- `docs/design/system.pen`: canvas showcase để review, không dùng làm source ref.
- `docs/design/screens/*.pen`: mỗi surface một file.
- `docs/design/notes.md`: UX notes, tradeoffs, user flow, brainstorm.
- `docs/design/workflow.md`: quy trình design → implement (agent playbook).
- `docs/design/DESIGN.md`: style spec gốc AI Labs.

## Khi nào đổi system

Chỉ đổi `system.pen` khi có quyết định hệ thống mới về:
- navigation grammar
- density
- typography scale
- tone màu
- component family
- screen architecture

`system.pen` chỉ đổi khi cần cập nhật demo / onboarding / review canvas.

Đổi một screen riêng lẻ → sửa trong `screens/`, không phá system gốc.
