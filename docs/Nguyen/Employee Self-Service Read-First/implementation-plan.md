# Kế hoạch triển khai: Employee Self-Service Read-First

**Task**: Task 5  
**Branch**: `feature/employee-self-service-read`  
**Owner**: Hoàng Xuân Nguyên  
**Ngày**: 2026-06-05

---

## Tổng quan vấn đề

Hiện tại **mọi authenticated user** đều đọc/sửa/xóa được dữ liệu employee bất kỳ vì backend **không có ownership check**. Employee login xong landing trang admin dashboard thay vì trang của mình. Nav vẫn hiển thị Attendance/Payroll chưa live. Chưa có sample documents cho demo.

Triển khai theo 8 bước: redirect → dependency → ownership → self-edit → nav → seed → tests → verification.

---

## PHẦN 0: FRONTEND — Post-login redirect theo role

### Bước 0 — Auto-redirect employee sau OAuth callback

**Vấn đề:** Sau khi Google OAuth callback, backend redirect về `http://localhost:3000` (root). Next.js render `(dashboard)/page.tsx` — trang admin dashboard với stats, import Excel, tuyển dụng. **Cả admin lẫn employee đều landing trang này.**

**Employee cần landing** `/employee/dashboard` thay vì `/`.

**Cách giải quyết:** Tạo root `page.tsx` tại `frontend/src/app/page.tsx`:

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/hooks/use-current-user";
import { Loader2 } from "lucide-react";

export default function RootPage() {
  const { user, loading } = useCurrentUser();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    // Employee → ESS dashboard
    if (user.role === "user" && user.employee_id) {
      router.replace("/employee/dashboard");
      return;
    }
    // Admin → admin dashboard (route group handles this)
    router.replace("/");
  }, [user, loading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}
```

**Flow sau khi fix:**

```
Employee login → OAuth callback → redirect http://localhost:3000
→ Root page.tsx render
→ GET /api/auth/me → user.role="user", user.employee_id="abc-123"
→ useEffect: router.replace("/employee/dashboard")
→ Employee thấy trang dashboard của mình ✅

Admin login → OAuth callback → redirect http://localhost:3000
→ Root page.tsx render
→ GET /api/auth/me → user.role="admin", user.employee_id=null
→ useEffect: router.replace("/") → render admin dashboard ✅
```

**File sửa:** `frontend/src/app/page.tsx` (tạo mới — hiện tại không có root page)

---

## PHẦN 1: BACKEND — Tạo dependency phân quyền

### Bước 1 — `get_current_employee` dependency

**File mới**: `backend/src/modules/employee/api/dependencies.py`

**Tác dụng:** Khi employee gọi API, dependency này:
1. Đọc JWT token → lấy `employee_id`
2. Query database → lấy Employee record
3. Kiểm tra `is_active` — nếu inactive → chặn (403)
4. Trả về Employee object

```python
async def get_current_employee(
    current_user: User = Depends(get_current_user),
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
) -> Employee:
    """Resolve Employee từ JWT employee_id claim.
    
    Flow:
      JWT { employee_id: "abc-123" }
      → employee_repo.get_by_id("abc-123")
      → Employee { id: "abc-123", is_active: true, ... }
      → Return Employee
    
    Raises 403 nếu:
      - JWT không có employee_id (user chưa link employee)
      - employee_id không tồn tại trong DB
      - Employee.is_active == False
    """
    if current_user.employee_id is None:
        raise HTTPException(403, "User is not linked to an employee record")
    
    employee = await employee_repo.get_by_id(current_user.employee_id)
    if employee is None:
        raise HTTPException(403, "Employee record not found")
    if not employee.is_active:
        raise HTTPException(403, "Employee account is inactive")
    
    return employee
```

**Cách dùng trong endpoint:**

```python
@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: UUID,
    current_employee: Employee = Depends(get_current_employee),  # ← mới
    employee_service: EmployeeServiceDep,
):
    # current_employee.id = ID của người đang đăng nhập
    # employee_id = ID trong URL
    if employee_id != current_employee.id:
        raise HTTPException(403, "Access denied")
    
    return await employee_service.get_employee(employee_id)
```

---

## PHẦN 2: BACKEND — Ownership boundary

### Bước 2 — Ownership guard cho profile endpoints

**File sửa**: `backend/src/modules/employee/api/router.py`

**Logic phân quyền:**

```
Request: GET /api/employees/{id}

1. Kiểm tra role:
   - role=admin → bypass (HR xem được tất cả) → trả data
   - role=user → kiểm tra ownership tiếp

2. Ownership check:
   - JWT.employee_id == URL.employee_id? → ✅ cho xem
   - JWT.employee_id != URL.employee_id? → ❌ 403
```

**Áp dụng cho các endpoint:**

| Endpoint | Thay đổi |
|----------|----------|
| `GET /api/employees/{id}` | Thêm ownership check khi role=user |
| `PUT /api/employees/{id}` | Thêm ownership check + restriction phone/address |
| `GET /api/employees/{id}/documents` | Thêm ownership check |
| `POST /api/employees/{id}/documents` | Thêm ownership check |

**Giữ nguyên cho HR admin:**
- `GET /api/employees` (list all) — HR cần xem danh sách
- `POST /api/employees` — HR tạo nhân viên mới
- `DELETE /api/employees/{id}` — HR xóa nhân viên

---

### Bước 3 — Ownership guard cho document download

**File sửa**: `backend/src/modules/employee/api/router.py`

**Vấn đề hiện tại:** `GET /api/documents/{id}/download` không check ai sở hữu document. Bất kỳ ai authenticated đều tải được.

**Sửa:** Thêm check `document.employee_id == current_user.employee_id` khi role=user.

```python
@document_router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
) -> Response:
    document, file_data = await document_service.download_document(document_id)
    
    # Ownership check
    if current_user.role != "admin":  # HR bypass
        if current_user.employee_id is None:
            raise HTTPException(403, "Not linked to an employee")
        if document.employee_id != current_user.employee_id:
            raise HTTPException(403, "Access denied")
    
    return Response(content=file_data, media_type=document.mime_type, ...)
```

---

## PHẦN 3: BACKEND — Self-edit restriction

### Bước 4 — Giới hạn field self-edit (phone + address only)

**File sửa**: `backend/src/modules/employee/api/router.py`

**Vấn đề:** Endpoint `PUT /api/employees/{id}` hiện tại nhận toàn bộ `EmployeeUpdate` schema — employee có thể sửa `full_name`, `email`, `department_id`, v.v.

**Sửa:** Khi role=user, chỉ cho phép 2 field: `phone` và `address`.

```python
@employee_router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    body: EmployeeUpdate,
    current_user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
) -> EmployeeResponse:
    data = body.model_dump(exclude_unset=True)
    
    # Self-edit restriction
    if current_user.role != "admin":  # HR bypass
        allowed_fields = {"phone", "address"}
        disallowed = set(data.keys()) - allowed_fields
        if disallowed:
            raise HTTPException(
                403,
                f"Employees can only update phone and address. "
                f"Disallowed fields: {', '.join(disallowed)}"
            )
    
    employee = await employee_service.update_employee(employee_id, data)
    return EmployeeResponse.model_validate(employee)
```

**Ví dụ request/response:**

```
✅ allowed:
PUT /api/employees/{id}
{ "phone": "0912345678", "address": "456 Nguyễn Huệ, Q1" }
→ 200 OK

❌ disallowed:
PUT /api/employees/{id}
{ "full_name": "Hacker", "email": "hack@evil.com" }
→ 403 "Employees can only update phone and address. Disallowed fields: full_name, email"
```

---

## PHẦN 4: FRONTEND — Ẩn nav chưa live

### Bước 5 — Cập nhật essNavConfig

**File sửa**: `frontend/src/lib/ess-nav-config.ts`

**Tác dụng:** Employee nav bar hiện tại có 3 group: "Hồ sơ", "Chấm công", "Lương". Task 5 yêu cầu ẩn "Chấm công" và "Lương" vì chưa implement.

```typescript
// TRƯỚC (3 groups):
groups: [
  { id: "ho-so", ... },          // ← giữ
  { id: "cham-cong-ess", ... },  // ← XÓA
  { id: "luong-ess", ... },      // ← XÓA
]

// SAU (1 group):
groups: [
  {
    id: "ho-so",
    label: "Hồ sơ",
    links: [
      { href: "/employee/profile", label: "Thông tin", icon: User },
      { href: "/employee/documents", label: "Tài liệu", icon: FileText },
    ],
    activeRoutes: ["/employee/profile", "/employee/documents"],
  },
]
```

**Cũng xóa link "Cập nhật"** (`/employee/profile/update`) — self-edit nằm trong trang Profile sẵn rồi.

---

## PHẦN 5: SEED — Sample documents

### Bước 6 — Thêm EmployeeDocument vào demo seed

**File sửa**: `backend/src/bootstrap/demo_data.py`

**Tác dụng:** Hiện tại demo seed tạo 3 nhân viên nhưng **không tạo document nào**. Trang Documents sẽ hiện "Chưa có tài liệu nào". Cần thêm 3 sample documents cho employee đầu tiên.

```python
async def _seed_employee_documents(
    session: AsyncSession,
    employee: Employee,
) -> None:
    """Tạo 3 sample documents cho employee."""
    docs = [
        EmployeeDocument(
            employee_id=employee.id,
            document_type="cccd",
            file_name="CCCD_Nguyen_Thi_Anh.pdf",
            storage_path=f"employees/{employee.id}/cccd/CCCD_Nguyen_Thi_Anh.pdf",
            file_size=245_000,
            mime_type="application/pdf",
            description="CCCD/CMND",
        ),
        EmployeeDocument(
            employee_id=employee.id,
            document_type="contract",
            file_name="Hop_dong_lao_dong.pdf",
            storage_path=f"employees/{employee.id}/contract/Hop_dong_lao_dong.pdf",
            file_size=520_000,
            mime_type="application/pdf",
            description="Hợp đồng lao động",
        ),
        EmployeeDocument(
            employee_id=employee.id,
            document_type="degree",
            file_name="Bang_dai_hoc.pdf",
            storage_path=f"employees/{employee.id}/degree/Bang_dai_hoc.pdf",
            file_size=380_000,
            mime_type="application/pdf",
            description="Bằng đại học",
        ),
    ]
    session.add_all(docs)
```

Gọi trong `seed_demo_data()` sau khi tạo employees:

```python
# Seed documents cho employee đầu tiên
first_employee = (await session.execute(
    select(Employee).where(Employee.is_active == True).limit(1)
)).scalars().first()
if first_employee:
    await _seed_employee_documents(session, first_employee)
```

**Lưu ý:** Sample documents chỉ tạo metadata trong DB, không upload file thực lên MinIO. Download sẽ trả lỗi nếu MinIO container không chạy — đây là demo seed, UI list documents vẫn hoạt động bình thường.

---

## PHẦN 6: TESTS

### Bước 7 — Backend authz boundary tests

**File mới**: `backend/tests/modules/employee/test_self_service_authz.py`

**Mục đích:** Bảo vệ boundary giữa Employee và dữ liệu của employee khác. Nếu ai đó sửa code bypass ownership check, test sẽ bắt được.

| # | Test case | Mô tả | Mong đợi |
|---|-----------|-------|----------|
| 1 | `test_employee_can_view_own_profile` | Employee A gọi GET `/api/employees/{A_id}` | 200 OK |
| 2 | `test_employee_cannot_view_other_profile` | Employee A gọi GET `/api/employees/{B_id}` | 403 |
| 3 | `test_employee_can_update_own_phone_address` | Employee A PUT `/api/employees/{A_id}` {phone, address} | 200 |
| 4 | `test_employee_cannot_update_disallowed_fields` | Employee A PUT `/api/employees/{A_id}` {full_name} | 403 |
| 5 | `test_employee_can_list_own_documents` | Employee A GET `/api/employees/{A_id}/documents` | 200 |
| 6 | `test_employee_cannot_list_other_documents` | Employee A GET `/api/employees/{B_id}/documents` | 403 |
| 7 | `test_employee_cannot_download_other_document` | Employee A GET `/api/documents/{B_doc_id}/download` | 403 |
| 8 | `test_inactive_employee_blocked` | Inactive Employee gọi endpoint | 403 |
| 9 | `test_user_without_employee_id_blocked` | User (chưa link employee) gọi endpoint | 403 |
| 10 | `test_admin_can_access_any_employee` | Admin gọi GET `/api/employees/{any_id}` | 200 |

---

## PHẦN 7: VERIFICATION

### Bước 8 — Kiểm tra end-to-end

```bash
# 1. Chạy backend authz tests
cd backend && python -m pytest tests/modules/employee/test_self_service_authz.py -v

# 2. Kiểm tra nav không còn Attendance/Payroll
grep -r "cham-cong\|luong-ess\|attendance\|payroll" frontend/src/lib/ess-nav-config.ts
# → phải trả về rỗng (không có dòng nào match)

# 3. Kiểm tra dependency import hoạt động
cd backend && python -c "from src.modules.employee.api.dependencies import get_current_employee; print('OK')"

# 4. Kiểm tra seed documents
cd backend && python -c "
from src.bootstrap.demo_data import _seed_employee_documents
print('Function exists and importable')
"

# 5. Kiểm tra root page.tsx tồn tại
test -f frontend/src/app/page.tsx && echo "Root page exists" || echo "MISSING root page"
```

---

## Danh sách file thay đổi

| File | Hành động | Mô tả |
|------|-----------|-------|
| `frontend/src/app/page.tsx` | **Tạo mới** | Root page: auto-redirect employee → `/employee/dashboard` |
| `backend/src/modules/employee/api/dependencies.py` | **Tạo mới** | `get_current_employee` dependency |
| `backend/src/modules/employee/api/router.py` | **Sửa** | Thêm ownership guard + self-edit restriction |
| `frontend/src/lib/ess-nav-config.ts` | **Sửa** | Xóa Attendance/Payroll groups |
| `backend/src/bootstrap/demo_data.py` | **Sửa** | Thêm seed employee documents |
| `backend/tests/modules/employee/test_self_service_authz.py` | **Tạo mới** | Authz boundary tests |

---

## Lưu ý triển khai

1. **Không đụng HR admin endpoints** — ownership guard chỉ áp dụng khi `role == "user"`. HR admin (`role == "admin"`) vẫn xem/sửa được tất cả employee.

2. **Không tạo route mới** — tận dụng endpoint có sẵn (`/api/employees/{id}`, `/api/documents/{id}/download`), chỉ thêm guard vào.

3. **Root page.tsx dùng `router.replace()`** thay vì `router.push()` — để tránh lịch sử điều hướng rác. Employee login →(`/employee/dashboard`) thay vì `/ → /employee/dashboard`.

4. **Document download cần MinIO running** — sample documents chỉ tạo metadata trong DB, không upload file thực lên MinIO. Download sẽ trả lỗi MinIO nếu container không chạy. Đây là demo seed, không ảnh hưởng UI list documents.

5. **Flow login đúng cho employee:**

```
1. Mở http://localhost:3000/login
2. Click "Đăng nhập bằng Google" → redirect /api/auth/login → Google OAuth
3. Google consent → callback /api/auth/callback
4. Backend set cookies (access_token + refresh_token) → redirect http://localhost:3000
5. Root page.tsx render → GET /api/auth/me → role=user + employee_id
6. Auto redirect → /employee/dashboard
7. Employee thấy trang dashboard của mình ✅
```
