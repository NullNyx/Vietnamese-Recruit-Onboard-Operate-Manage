# 0030 App Authentication vs Gmail Integration OAuth

Date: 2026-07-04

## Status

Accepted

## Context

Hội thoại chốt rõ hai nhu cầu khác nhau:

1. Người dùng cần đăng nhập vào HR Space.
2. Hệ thống cần quyền truy cập Gmail để sync mailbox, ingest inbox item,
   và hỗ trợ AI classify / extract / triage.

Hai nhu cầu này không nên dùng chung một cơ chế auth.

## Decision

### 1. App authentication

HR Space dùng **username/password** cho đăng nhập ứng dụng.

- Login qua `POST /api/v1/auth/login`
- Session dùng cookie-based JWT (`access_token`, `refresh_token`), rotate
- Phù hợp self-host, HR-only, setup wizard tạo `SUPER_ADMIN`
- Không phụ thuộc Google để người dùng đăng nhập app

**Setup Wizard:**
- Tạo `SUPER_ADMIN` bằng password ngay trong wizard — không dùng invite email
- Route: `/api/v1/setup/*`, khóa sau khi hoàn tất
- `SUPER_ADMIN` username immutable sau khi tạo

**Password policy** (chung mọi role, không phân biệt):
- Tối thiểu 12 ký tự, bắt buộc 1 uppercase + 1 number + 1 special char
- Kiểm tra độ mạnh qua `zxcvbn` — score >= 3
- Không banned list trong MVP

**Login identifier:**
- `username` là định danh chính — không dùng email làm login
- Email optional, dùng cho recovery / thông báo

**Tạo user HR_ADMIN / HR_STAFF:**
- SUPER_ADMIN nhập trực tiếp username + password — không invite email

**Session & token:**
- Cookie: `HttpOnly=True`, `Secure=True` (production), `SameSite=Lax`
- `access_token`: 30 phút
- `refresh_token`: 14 ngày, rotate (refresh cấp pair mới, vô hiệu cũ)
- Refresh token theo family: replay token cũ đã rotate → revoke toàn bộ family
  + audit `TOKEN_REPLAY_DETECTED`
- Logout = server-side revoke cả family
- Không giới hạn số session đồng thời

**Đổi / reset mật khẩu:**
- Tự đổi: session hiện tại vẫn sống, toàn bộ session khác bị revoke
- SUPER_ADMIN reset hộ: revoke toàn bộ session của user

**Recovery:**
- Có email: self-service reset link qua email
- Không có email: SUPER_ADMIN reset tay trong admin

**Brute-force protection:**
- 5 lần thử sai → khóa tài khoản 15 phút (không permanent lock)
- Audit log mỗi lần lock/unlock

### 2. Gmail integration authentication

Nếu bật Gmail sync, hệ thống dùng **Google OAuth** riêng cho integration.

- OAuth chỉ phục vụ kết nối Gmail / mailbox sync
- Token Gmail lưu tách biệt với session app
- Dùng cho ingest email, poll mailbox, classify, extract, triage
- Không dùng OAuth này để đăng nhập HR Space

**Token lifecycle:**
- Bảng `gmail_integration` riêng (1:1 với organization)
- Token lưu encrypted trong DB
- Refresh token không tự rotate (Google web-app default)
- Khi token fail (expired / revoked) → set `sync_status = 'disconnected'`
  + tự động tạo InboxItem system notification báo HR_ADMIN
- OAuth flow khởi động từ Settings page bởi SUPER_ADMIN hoặc HR_ADMIN có quyền
- Không dùng Google OAuth trong Setup Wizard


### 3. Separation rule

> **App login** ≠ **Gmail integration auth**

- App login: password
- Gmail sync: Google OAuth
- Không trộn hai flow này

### 4. Fallback khi không dùng OAuth

Nếu tenant không cấp Gmail OAuth:

- chỉ ingest thủ công
- hoặc forward email vào system
- không có sync mailbox tự động

### 5. Scope impact

- `Gmail Integration` vẫn nằm trong scope product
- `InboxService` vẫn có `ingestInboxItem`, `classifyInboxItem`, `convertInboxToWork`
- AI classify / extract / suggest context vẫn dùng cho inbox items
- OAuth chỉ là mechanism cho integration, không đổi product identity

## Consequences


Positive:
- Giữ app login đơn giản, hợp self-host
- Gmail sync vẫn có đường chính thống
- Tách rõ security boundary giữa user session và integration token
- Không làm product phụ thuộc Google cho core auth

Tradeoffs:
- Phải maintain hai auth flows
- Token Gmail cần lifecycle riêng: refresh / revoke / rotate
- Implementation phức tạp hơn nếu bật Gmail sync

## References

- ADR 0021: Product Identity + Work Taxonomy
- ADR 0024: Capability Taxonomy + Module Boundary
- ADR 0028: API v1 Design + Freeze Decisions
