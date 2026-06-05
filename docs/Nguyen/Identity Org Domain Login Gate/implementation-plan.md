# Kế hoạch triển khai: Identity — Gate Employee Login by Organization Domains

**Issue**: [#55](https://github.com/NullNyx/Vietnamese-Recruit-Onboard-Operate-Manage/issues/55)
**Branch**: `feat/org-domain-login-gate`
**Ngày**: 2026-06-03

---

## Tổng quan

Full feature: **backend API** CRUD domains + **domain gate logic** chặn login + **frontend admin page** quản lý domains + **login error handling**.

---

## PHẦN 1: BACKEND

### Bước 1 — Migration

**File**: `backend/alembic/versions/030_add_organization_allowed_domains.py`

```sql
ALTER TABLE organization_settings
  ADD COLUMN allowed_domains TEXT[] NOT NULL DEFAULT '{}';
```

---

### Bước 2 — Entity

**File**: `backend/src/modules/recruitment/domain/entities.py`

```python
allowed_domains: list[str] = Field(
    sa_column=Column(ARRAY(String), nullable=False, server_default="{}"),
)
```

---

### Bước 3 — Repository methods

**File**: `backend/src/modules/recruitment/infrastructure/org_settings_repository.py`

| Method | Mô tả |
|--------|-------|
| `get_allowed_domains() -> list[str]` | Đọc danh sách |
| `set_allowed_domains(domains) -> list[str]` | Thay thế toàn bộ |
| `add_domains(domains) -> list[str]` | Thêm (set semantics, reject dup) |
| `remove_domain(domain) -> list[str]` | Xóa một domain |

Validation: lowercase, regex, max 50.

---

### Bước 4 — New exception

**File**: `backend/src/modules/identity/domain/exceptions.py`

```python
class DomainAccessDeniedError(AuthError):
    status_code = 403
    error_code = "DOMAIN_NOT_ALLOWED"
    message = "Email domain is not authorized for this Organization."
```

Tách riêng khỏi `AccessDeniedError` (whitelist) để phân biệt lỗi.

---

### Bước 5 — DomainGateService + unit tests

**File mới**: `backend/src/modules/identity/application/domain_gate_service.py`

```python
class DomainGateService:
    def __init__(self, org_settings_repository):
        self._repo = org_settings_repository

    async def is_email_allowed(self, email: str) -> bool:
        allowed = await self._repo.get_allowed_domains()
        if not allowed:
            return True  # Empty = no restriction
        domain = email.split("@")[-1].lower()
        return domain in allowed
```

**Tests** (`tests/identity/test_domain_gate_service.py`):
- Empty list → `True`
- Matching domain → `True`
- Non-matching → `False`
- Case insensitive → `True`
- No `@` → `False`

---

### Bước 6 — Auth integration

**File**: `backend/src/modules/identity/application/auth_service.py`

Constructor thêm `domain_gate_service` parameter.

`handle_callback` — chèn sau decode ID token, trước whitelist check:

```python
if self._domain_gate_service is not None:
    if not await self._domain_gate_service.is_email_allowed(user_info.email):
        raise DomainAccessDeniedError(
            message=f"Email domain '{user_info.email.split('@')[-1]}' is not authorized."
        )
```

---

### Bước 7 — Container wiring

**File**: `backend/src/modules/identity/container.py`

```python
async def get_domain_gate_service(
    session: AsyncSession = Depends(get_db_session),
) -> DomainGateService:
    from src.modules.recruitment.infrastructure.org_settings_repository import (
        OrganizationSettingsRepository,
    )
    repo = OrganizationSettingsRepository(session)
    return DomainGateService(org_settings_repository=repo)
```

Sửa `get_auth_service` — inject `domain_gate_service`.

---

### Bước 8 — Callback redirect với error

**File**: `backend/src/modules/identity/api/router.py`

Sửa `callback` endpoint — catch `DomainAccessDeniedError`, redirect frontend:

```python
except DomainAccessDeniedError as exc:
    return RedirectResponse(
        url=f"{settings.frontend_url}/login?error={exc.error_code}",
        status_code=302,
    )
```

---

### Bước 9 — Admin API + schemas

**File**: `backend/src/modules/identity/api/admin_router.py`

Thêm `ORG_DOMAIN_UPDATE` vào `AuditActionType`.

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/api/admin/organization/domains` | Liệt kê |
| `POST` | `/api/admin/organization/domains` | Thêm domain(s) |
| `PUT` | `/api/admin/organization/domains` | Thay toàn bộ |
| `DELETE` | `/api/admin/organization/domains/{domain}` | Xóa một |

Schemas trong `admin_schemas.py`. Mọi mutation ghi audit log.

---

### Bước 10 — Container: wire repository cho admin

**File**: `backend/src/modules/identity/container.py`

```python
async def get_organization_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizationSettingsRepository:
    from src.modules.recruitment.infrastructure.org_settings_repository import (
        OrganizationSettingsRepository,
    )
    return OrganizationSettingsRepository(session)
```

---

## PHẦN 2: FRONTEND

### Bước 11 — Nav config

**File**: `frontend/src/lib/admin-nav-config.ts`

Thêm `Globe` icon + `{ href: "/admin/domains", label: "Domains", icon: Globe }` vào group `he-thong`.

---

### Bước 12 — API client

**File**: `frontend/src/lib/api/admin.ts`

```typescript
export async function listDomains(): Promise<DomainListResponse>
export async function addDomains(domains: string[]): Promise<DomainListResponse>
export async function replaceDomains(domains: string[]): Promise<DomainListResponse>
export async function removeDomain(domain: string): Promise<DomainRemoveResponse>
```

---

### Bước 13 — Zod schema

**File**: `frontend/src/lib/api/admin-schemas.ts`

```typescript
export const domainAddSchema = z.object({
  domain: z.string()
    .min(3).max(255)
    .regex(/^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$/,
      "Domain không hợp lệ (ví dụ: company.vn)"),
});
```

---

### Bước 14 — Components

**File mới**: `frontend/src/components/admin/domain-table.tsx`
- Pattern từ `whitelist-table.tsx`
- Cột: domain + nút xóa (AlertDialog confirm)
- Empty state: "Chưa có domain nào"

**File mới**: `frontend/src/components/admin/domain-add-form.tsx`
- Pattern từ `whitelist-add-form.tsx`
- Input: domain (ví dụ: `company.vn`)
- Button: "Thêm domain"

---

### Bước 15 — Admin page

**File mới**: `frontend/src/app/(dashboard)/admin/domains/page.tsx`

```
┌─────────────────────────────────────────────┐
│ Quản lý domain đăng nhập     [Làm mới]     │
│ Danh sách domain được phép cho Organization │
├─────────────────────────────────────────────┤
│ ┌─ Thêm domain mới ──────────────────────┐ │
│ │ [company.vn______________] [Thêm]      │ │
│ └────────────────────────────────────────┘ │
│ ┌─ Danh sách domain (3) ────────────────┐ │
│ │ Domain          │ Hành động            │ │
│ │ company.vn      │ [🗑]                 │ │
│ │ subsidiary.vn   │ [🗑]                 │ │
│ │ partner.vn      │ [🗑]                 │ │
│ └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

### Bước 16 — Login page: xử lý error

**File**: `frontend/src/app/login/page.tsx`

Đọc `?error=` từ URL, hiển thị alert:

- `DOMAIN_NOT_ALLOWED` → "Tên miền email chưa được ủy quyền. Liên hệ HR."
- `AUTH_ACCESS_DENIED` → "Truy cập bị từ chối. Liên hệ HR."

---

## PHẦN 3: TESTING

| File | Test cases |
|------|-----------|
| `tests/identity/test_domain_gate_service.py` | 5 unit tests |
| `tests/identity/test_admin_domain_api.py` | 5 API tests (list, add, dup, remove, non-admin) |
| `tests/identity/test_org_settings_repository.py` | 6 repo tests |
| `tests/admin/domains-page.test.tsx` | Render, add, remove, empty |

---

## PHẦN 4: THỨ TỰ

| # | Bước | File(s) | Deps |
|---|------|---------|------|
| 1 | Migration | `030_...py` | — |
| 2 | Entity | `entities.py` | #1 |
| 3 | Repository | `org_settings_repository.py` | #2 |
| 4 | Exception | `exceptions.py` | — |
| 5 | DomainGateService + test | `domain_gate_service.py` | #3 |
| 6 | Auth integration | `auth_service.py` | #4, #5 |
| 7 | Container | `container.py` | #5, #6 |
| 8 | Callback redirect | `router.py` | #4, #6 |
| 9 | Admin API + schemas | `admin_router.py`, `admin_schemas.py` | #3 |
| 10 | Audit enum | `entities.py` | — |
| 11 | Nav config | `admin-nav-config.ts` | — |
| 12 | API client | `admin.ts` | — |
| 13 | Zod schema | `admin-schemas.ts` | — |
| 14 | Components | `domain-table.tsx`, `domain-add-form.tsx` | #12, #13 |
| 15 | Admin page | `domains/page.tsx` | #14 |
| 16 | Login error | `login/page.tsx` | — |
| 17 | Backend tests | `tests/identity/` | #5, #9 |
| 18 | Frontend tests | `tests/admin/` | #15 |

---

## LƯU Ý

- `allowed_domains = []` → không giới hạn (backwards-compatible).
- Domain gate chạy **trước** whitelist check.
- Super admin KHÔNG bypass domain gate.
- Cross-module import: admin_router → OrganizationSettingsRepository (recruitment module).
