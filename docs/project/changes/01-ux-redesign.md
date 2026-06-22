# Change 01 — UX Redesign

## Mục tiêu

Thay đổi UX hiện tại từ dạng functional interface sang user journey–driven interface — nơi người dùng thấy ngay trạng thái, biết next action, và tin hệ thống.

## Foundation liên quan

- `07-ux-design-tenets.md`: status first, next action first, queue over clutter, trust visible
- `02-target-user-personas.md`: 3 nhóm HR / Employee / Owner
- `03-user-journey.md`: HR path, Employee path, Owner path

## Trạng thái hiện tại

- Giao diện tiếng Anh
- HR và Employee dùng cùng design system
- Chưa có status / next action / trust visible pattern
- Chưa có queue ưu tiên pending items
- Chưa có tiếng Việt

## Trạng thái mong muốn

- Giao diện tiếng Việt, giữ nguyên canonical term tiếng Anh
- HR UX: queue → detail → action, status first
- Employee UX: read-first, self-service, chỉ thấy data mình
- Mỗi màn hình trả lời được: tôi đang ở đâu, cần làm gì tiếp
- Audit visible cho HR
- Design tokens theo DESIGN.md (Heritage): Fraunces + Public Sans + Space Grotesk, màu tertiary #B8422E cho primary action

## Các bước

### Bước 1: Thiết lập design foundation

- Chốt design tokens (đã có DESIGN.md)
- Xác định component patterns cần thay đổi
- Tạo style guide cho frontend team

### Bước 2: Tách HR layout và Employee layout

- HR: queue dashboard + detail view + action buttons
- Employee: read dashboard + self-service + request
- Navigation khác nhau

### Bước 3: Status pattern

- Mỗi entity (Candidate, Onboarding, Request) có status bar rõ
- Status timeline ở header detail view
- Màu sắc status rõ: pending / active / done / error

### Bước 4: Next action pattern

- Mỗi màn hình có section "Cần xử lý" hoặc "Next step"
- Queue ưu tiên pending items
- Action button gần context

### Bước 5: Vietnamese localization

- Chuyển toàn bộ UI text sang tiếng Việt
- Giữ nguyên canonical term tiếng Anh

### Bước 6: Trust visible

- Audit log có nút xem cho HR
- Action important có confirm dialog
- Trạng thái của mỗi action đều có trace

## Rủi ro / Lưu ý

- Thay đổi UX phải đi cùng với thay đổi code — không chỉ design
- Cần đồng bộ giữa frontend và backend: status / next action / audit phải có API hỗ trợ
- Localization là effort riêng, có thể làm theo module
- UX redesign có thể ảnh hưởng user current nếu không rollout dần

## Kế hoạch

| Module | Bước | Ưu tiên |
|--------|------|---------|
| Recruitment (Candidate queue + detail) | 1→2→3→4→5→6 | P1 |
| Onboarding (Process + Task) | 1→2→3→4→5→6 | P1 |
| Employee Request (Queue + Detail) | 1→2→3→4→5→6 | P2 |
| ESS (Dashboard + Self-service) | 1→2→3→4→5→6 | P2 |
| Attendance / Payroll | 3→4→5→6 | P3 |

## File status

<!-- FILE STATUS: ACTIVE -->
<!-- Cập nhật khi có thay đổi cụ thể -->
