# PRD: Identity — Gate Employee Login by Organization Domains

**Issue**: [#55](https://github.com/NullNyx/Vietnamese-Recruit-Onboard-Operate-Manage/issues/55)
**Module**: identity / admin / auth
**Status**: Draft — Giai đoạn 1: Backend API + Frontend Admin UI
**Date**: 2026-06-03

---

## 1. Background & Problem

Vroom HR is a self-hosted HRM platform. Each deployment serves exactly one **Organization** (per ADR-0001). Currently, login access is controlled by a file-based email whitelist (`WhitelistService`) that gates HR/admin access. There is no mechanism to restrict login by **email domain** at the Organization level.

An HR admin needs the ability to say: "Only emails from `@company.vn` and `@subsidiary.vn` may authenticate." Without this, anyone who knows the deployment URL and has a Google account can attempt login — the whitelist only blocks after the fact and is not domain-scoped.

## 2. Goals

| # | Goal |
|---|------|
| G1 | HR can manage a list of allowed email domains on the Organization via admin API. |
| G2 | Google OAuth login is gated: email domain must be in `Organization.allowed_domains[]`. |
| G3 | Login with a non-allowed domain is denied with a clear, specific error. |
| G4 | Existing whitelist check (HR access) remains intact and runs after the domain gate. |
| G5 | Employee and auth-account remain separate lifecycles (no auto-employee-creation from OAuth). |

## 3. Non-Goals (Giai đoạn 1)

- **Login gate integration** — tích hợp domain gate vào OAuth callback (giai đoạn 2).
- **Login error handling** — frontend hiển thị lỗi domain trên trang login (giai đoạn 2).
- Multi-company / multi-tenant domain routing (ADR-0001: one deployment = one Organization).
- Self-registration or auto-employee provisioning from OAuth.
- Changes to onboarding, recruitment, or assistant modules.
- Replacing the existing whitelist system — the domain gate is an additional layer.

## 4. Data Model

### 4.1 Add `allowed_domains` to `OrganizationSettings`

The existing `organization_settings` table (single-row, currently holds `timezone`) gains a new column:

```sql
ALTER TABLE organization_settings
  ADD COLUMN allowed_domains TEXT[] NOT NULL DEFAULT '{}';
```

- Type: `TEXT[]` (PostgreSQL array of strings).
- Default: empty array `{}` — meaning **no domain restriction** (backwards-compatible; existing deployments are not locked out).
- Each element is a bare domain, e.g. `company.vn`, `subsidiary.vn` (no `@` prefix, lowercase-normalized).

### 4.2 Entity change

```python
# backend/src/modules/recruitment/domain/entities.py
class OrganizationSettings(SQLModel, table=True):
    __tablename__ = "organization_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timezone: str = Field(max_length=50, nullable=False)
    allowed_domains: list[str] = Field(
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}"),
    )
```

### 4.3 Migration

A new Alembic migration adds the column with the `DEFAULT '{}'` constraint so existing rows get an empty array.

## 5. API Changes

### 5.1 Admin endpoints (under `/api/admin`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/organization/domains` | List current `allowed_domains`. |
| `PUT` | `/api/admin/organization/domains` | Replace the entire `allowed_domains` list. |
| `POST` | `/api/admin/organization/domains` | Add one or more domains to the list. |
| `DELETE` | `/api/admin/organization/domains/{domain}` | Remove a single domain. |

All endpoints require Admin role (`require_admin` dependency). All mutations write an audit log entry (`AuditActionType.ORG_DOMAIN_UPDATE`).

**Request / Response schemas:**

```python
class DomainListResponse(BaseModel):
    allowed_domains: list[str]

class DomainAddRequest(BaseModel):
    domains: list[str] = Field(..., min_length=1, max_length=50)

class DomainRemoveResponse(BaseModel):
    removed: str
    allowed_domains: list[str]
```

**Validation rules:**
- Domain must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$` (lowercase, no protocol, no `@`).
- Duplicate domains are rejected (set semantics).
- Domain values are normalized to lowercase before storage.

### 5.2 New audit action type

```python
class AuditActionType(str, Enum):
    # ... existing ...
    ORG_DOMAIN_UPDATE = "org_domain_update"
```

## 6. Auth Flow Changes (Giai đoạn 2 — chưa triển khai)

### 6.1 Current flow (simplified)

```
1. Validate CSRF state
2. Exchange code for Google tokens
3. Decode ID token → get email
4. Check whitelist (file-based)
5. Upsert User (role = ADMIN if super_admin_email match)
6. Store OAuth tokens
7. Issue session tokens
```

### 6.2 New flow — domain gate inserted at step 4

```
1. Validate CSRF state
2. Exchange code for Google tokens
3. Decode ID token → get email
4. [NEW] Extract domain from email
5. [NEW] Load Organization.allowed_domains[]
6. [NEW] If allowed_domains is non-empty AND domain NOT in list → deny
7. Check whitelist (file-based, existing)
8. Upsert User (role = ADMIN if super_admin_email match)
9. Store OAuth tokens
10. Issue session tokens
```

**Key design decision:** The domain gate runs **before** the whitelist check. Rationale: if the domain is not allowed at the Organization level, there is no reason to proceed to whitelist matching. This also means the error message can be specific to domain restriction rather than generic "access denied."

**Backwards compatibility:** When `allowed_domains` is empty (`{}`), the gate is a no-op — all domains pass. This ensures existing deployments continue to work without configuration.

### 6.3 New service: `DomainGateService`

Lives in `identity/application/`:

```python
class DomainGateService:
    """Checks whether an email's domain is allowed by the Organization."""

    def __init__(self, org_settings_repository: OrganizationSettingsRepository):
        self._repo = org_settings_repository

    async def is_email_allowed(self, email: str) -> bool:
        allowed = await self._repo.get_allowed_domains()
        if not allowed:
            return True  # Empty list = no restriction
        domain = email.split("@")[-1].lower()
        return domain in allowed
```

This service is injected into `AuthService` alongside the existing `WhitelistService`.

### 6.4 Integration point in `AuthService.handle_callback`

```python
# Step 4: Domain gate
if not await self._domain_gate_service.is_email_allowed(user_info.email):
    raise AccessDeniedError(
        code="DOMAIN_NOT_ALLOWED",
        message=f"Email domain '{user_info.email.split('@')[-1]}' is not authorized for this Organization.",
    )

# Step 5: Whitelist check (existing, unchanged)
if not self._whitelist_service.is_allowed(user_info.email):
    raise AccessDeniedError()
```

## 7. Error Handling

### 7.1 New error code

| HTTP Status | Code | Message |
|-------------|------|---------|
| 403 | `DOMAIN_NOT_ALLOWED` | `Email domain '{domain}' is not authorized for this Organization.` |

This reuses the existing `AccessDeniedError` exception with a domain-specific code, so the frontend can distinguish between "domain not allowed" (Organization-level) and "email not whitelisted" (HR access-level).

### 7.2 Frontend redirect

The OAuth callback redirect includes an error query parameter. The login page reads it and displays the appropriate message:

- `DOMAIN_NOT_ALLOWED` → "Your email domain is not authorized. Contact your HR administrator."
- Default `ACCESS_DENIED` → "Access denied. Contact your HR administrator."

## 8. Dependency Injection (Giai đoạn 2 — chưa triển khai)

`DomainGateService` needs access to `OrganizationSettingsRepository`, which currently lives in the recruitment module. Two options:

**Option A (recommended):** Import `OrganizationSettingsRepository` from the recruitment module into the identity container. Acceptable because `OrganizationSettings` is a singleton org-level config, not recruitment-specific data.

**Option B:** Move `OrganizationSettings` and its repository to a shared `core` module. Cleaner long-term but a larger refactor — defer to a follow-up.

The PRD proceeds with **Option A**. The identity container gains a new provider:

```python
def get_domain_gate_service(session = Depends(get_db_session)) -> DomainGateService:
    repo = OrganizationSettingsRepository(session)
    return DomainGateService(org_settings_repository=repo)
```

## 9. Testing

### 9.1 Unit tests

| Test | Expected |
|------|----------|
| `is_email_allowed` with empty `allowed_domains` | Returns `True` (no restriction). |
| `is_email_allowed` with matching domain | Returns `True`. |
| `is_email_allowed` with non-matching domain | Returns `False`. |
| Domain normalization: `User@Company.VN` → `company.vn` | Case-insensitive match. |
| `is_email_allowed` with no `@` in email | Returns `False` (malformed). |

### 9.2 Integration tests (OAuth callback)

| Scenario | Setup | Expected |
|----------|-------|----------|
| Login with allowed domain | `allowed_domains = ["company.vn"]`, email = `user@company.vn` | Login succeeds, session tokens issued. |
| Login with non-allowed domain | `allowed_domains = ["company.vn"]`, email = `user@other.vn` | 403 `DOMAIN_NOT_ALLOWED`. |
| Login with empty allowed_domains | `allowed_domains = []`, any email | Login succeeds (gate is no-op). |

### 9.3 Admin API tests

| Scenario | Expected |
|----------|----------|
| `GET /api/admin/organization/domains` | Returns current list. |
| `POST /api/admin/organization/domains` with valid domain | Domain added, audit logged. |
| `POST /api/admin/organization/domains` with duplicate | 400 duplicate error. |
| `DELETE /api/admin/organization/domains/{domain}` | Domain removed, audit logged. |
| Non-admin calls any domain endpoint | 403. |

## 10. Out of Scope

- Frontend admin UI for domain management (can be a follow-up; admin uses API directly or via tools for now).
- Domain-based routing or multi-company logic.
- Employee auto-creation from OAuth.
- Changes to onboarding / recruitment / assistant modules.

## 11. Open Questions

1. **Should the super_admin_email bypass the domain gate?** Recommendation: no — the super admin should also have an email in an allowed domain. This keeps the invariant simple: "no domain allowed = no one logs in."
2. **Maximum number of allowed domains?** Suggest 50 as a practical limit (matches `max_length=50` on the add request).
3. **Should removing the last allowed domain lock out all logins?** Yes — HR must consciously decide. The empty-array case means "no restriction," not "no access." If HR wants to block everyone, they should use a different mechanism.

---

## Giải thích thiết kế (tiếng Việt)

### Vấn đề là gì?

Hiện tại, khi ai đó truy cập Vroom HR và nhấn "Đăng nhập bằng Google", hệ thống chỉ kiểm tra **danh sách email trắng** (whitelist) — tức là kiểm tra từng email cụ thể có nằm trong danh sách cho phép chưa. Nhưng chưa có cơ chế kiểm tra **tên miền (domain)** của email.

Ví dụ: HR muốn chỉ cho nhân viên công ty `@company.vn` và `@subsidiary.vn` đăng nhập, nhưng hiện tại không có cách nào chặn người dùng có email `@gmail.com` hay `@outlook.com` đăng nhập vào hệ thống.

### Giải pháp

Thêm một lớp kiểm soát mới: **cổng domain (domain gate)**. Khi người dùng đăng nhập bằng Google OAuth, hệ thống sẽ:

1. Lấy email từ Google (đã xác thực).
2. Tách phần domain từ email (ví dụ: `user@company.vn` → `company.vn`).
3. Đối chiếu domain đó với danh sách `allowed_domains` của Organization.
4. Nếu domain nằm trong danh sách → cho qua.
5. Nếu domain không nằm trong danh sách → từ chối, trả lỗi rõ ràng.

### Lưu ý quan trọng về thiết kế

**Domain gate chạy TRƯỚC whitelist hiện tại.** Tại sao? Vì nếu domain đã bị Organization chặn, thì không cần kiểm tra whitelist từng email nữa — tiết kiệm và lỗi trả về rõ ràng hơn (lỗi domain thay vì lỗi chung chung).

**Mảng rỗng = không giới hạn.** Khi `allowed_domains` là `[]` (rỗng), mọi domain đều được phép đăng nhập. Điều này đảm bảo các deployment hiện tại không bị khóa sau khi upgrade — họ cần chủ động thêm domain vào danh sách.

**Không tự tạo Employee từ OAuth.** Yêu cầu nói rõ: việc tạo Employee vẫn do HR quản lý. OAuth chỉ tạo auth-account (User), không liên quan đến Employee lifecycle.

### Dữ liệu thay đổi gì?

Bảng `organization_settings` hiện tại chỉ có cột `timezone`. Sẽ thêm cột `allowed_domains` kiểu `TEXT[]` (mảng chuỗi PostgreSQL), mặc định `{}`.

### API mới cho HR

HR quản lý danh sách domain qua 4 endpoint:

| Thao tác | Endpoint | Ý nghĩa |
|----------|----------|---------|
| Xem danh sách | `GET /api/admin/organization/domains` | Xem các domain đang cho phép |
| Thêm domain | `POST /api/admin/organization/domains` | Thêm 1 hoặc nhiều domain mới |
| Thay toàn bộ | `PUT /api/admin/organization/domains` | Thay thế toàn bộ danh sách |
| Xóa domain | `DELETE /api/admin/organization/domains/{domain}` | Xóa một domain cụ thể |

Mọi thao tác đều ghi **audit log** (ai sửa, sửa lúc nào, sửa gì).

### Lỗi khi đăng nhập bị từ chối

| Tình huống | HTTP Status | Mã lỗi | Thông báo |
|------------|-------------|---------|-----------|
| Domain không hợp lệ | 403 | `DOMAIN_NOT_ALLOWED` | Email domain '{domain}' is not authorized for this Organization. |
| Email không trong whitelist | 403 | `ACCESS_DENIED` | Access denied (lỗi hiện tại, không đổi) |

Frontend sẽ hiển thị: *"Tên miền email của bạn chưa được ủy quyền. Liên hệ quản trị viên HR."*

### Ai viết code phần nào?

| Phần | File/Layer |
|------|-----------|
| Migration | Alembic — thêm cột `allowed_domains` |
| Entity | `recruitment/domain/entities.py` — sửa `OrganizationSettings` |
| Service mới | `identity/application/domain_gate_service.py` — logic check domain |
| Admin API | `identity/api/admin_router.py` — 4 endpoint CRUD |
| Schemas | `identity/api/admin_schemas.py` — request/response models |
| Audit | `identity/domain/entities.py` — thêm `ORG_DOMAIN_UPDATE` enum |
| Auth integration | `identity/application/auth_service.py` — chèn domain gate vào `handle_callback` |
| Container | `identity/container.py` — inject `DomainGateService` |
| Tests | Unit + integration cho domain gate, OAuth callback, admin API |

### Câu hỏi chưa trả lời

1. **Super admin có cần tuân thủ domain gate không?** Khuyến nghị: có — giữ nguyên tắc "không domain = không ai đăng nhập".
2. **Tối đa bao nhiêu domain?** Gợi ý: 50.
3. **Xóa domain cuối cùng có khóa mọi người không?** Có — HR phải chủ động. Mảng rỗng nghĩa là "không giới hạn", không phải "không cho ai đăng nhập".

---

## 12. Sequencing

### Giai đoạn 1 (hiện tại)
1. Alembic migration: add `allowed_domains` column.
2. Entity + repository changes.
3. Admin API endpoints + tests.
4. Frontend admin page + components.

### Giai đoạn 2 (tương lai)
5. `DomainGateService` + unit tests.
6. `AuthService` integration + integration tests.
7. Frontend error handling on login page.
