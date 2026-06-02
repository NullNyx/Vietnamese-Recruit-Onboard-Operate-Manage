# PRD — Onboarding E2E UI (Task 2)

## Flow hiện tại (Backend)

```
Candidate accepted → ARQ event → OnboardingService.start_from_event()
→ Tạo Employee (inactive) + Process + 4 tasks cố định
→ HR tick tasks → Process complete → Employee active
```

**Vấn đề:** 4 tasks cố định (sign_contract, submit_documents, assign_dept, set_start_date).
Không linh hoạt theo vị trí. HR không upload được tài liệu onboarding riêng.

---

## Flow mới đề xuất

### 1. Onboarding Template (tài liệu theo vị trí)

**Concept:** Mỗi vị trí (Dev, Design, Sales, ...) có bộ tài liệu onboarding riêng.
HR upload template trước, khi onboarding nhân viên thì hệ thống gợi ý template theo vị trí.

**Backend cần thêm:**

```
/positions/{id}/onboarding-templates → GET, POST, DELETE
```

```sql
-- Migration mới (không đụng bảng cũ)
CREATE TABLE onboarding_templates (
    id UUID PRIMARY KEY,
    position_id UUID REFERENCES positions(id),
    name VARCHAR(100) NOT NULL,          -- "Dev Onboarding Checklist"
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE onboarding_template_items (
    id UUID PRIMARY KEY,
    template_id UUID REFERENCES onboarding_templates(id),
    title VARCHAR(100) NOT NULL,         -- "Đọc docs codebase"
    description TEXT,
    order_index INT NOT NULL,
    is_required BOOLEAN DEFAULT true     -- bắt buộc hay tùy chọn
);
```

### 2. HR tạo Onboarding cho nhân viên mới

**Flow mới:**

```
1. HR chọn nhân viên (hoặc tạo mới từ Candidate accepted)
2. HR chọn vị trí cho nhân viên
3. Hệ thống gợi ý onboarding template theo vị trí
4. HR xem, thêm/bớt task từ template
5. HR upload tài liệu đính kèm (contract, forms, ...)
6. Submit → Tạo OnboardingProcess với tasks tùy chỉnh
```

### 3. Dashboard quản lý onboarding

**HR cần xem:**

```
┌─────────────────────────────────────────────────────────┐
│ Onboarding Dashboard                                     │
├─────────────────────────────────────────────────────────┤
│ [All] [In Progress] [Complete]                          │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Nguyễn Văn A    | Dev     | ████████░░ 4/5 | 70%  │ │
│ │ Trần Thị B      | Design  | ██████████ 5/5 | 100% │ │
│ │ Lê Văn C        | Sales   | ██░░░░░░░░ 2/5 | 40%  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Click vào → Detail panel:                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Onboarding: Nguyễn Văn A                            │ │
│ │ Position: Developer                                  │ │
│ │ Status: In Progress                                  │ │
│ │                                                      │ │
│ │ ☑ Sign Contract              01/06/2026             │ │
│ │ ☑ Submit Documents           02/06/2026             │ │
│ │ ☑ Read Codebase Docs         03/06/2026             │ │
│ │ ☑ Setup Dev Environment      04/06/2026             │ │
│ │ ☐ Complete First PR          --                     │ │
│ │                                                      │ │
│ │ [Mark Done] button cho task đang pending             │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Backend changes cần thiết

### A. Patch nhỏ cho Task 2 (được phép)

**1. Thêm employee_full_name, employee_email, employee_code vào response**

File: `backend/src/modules/onboarding/application/onboarding_service.py`

```python
# ProcessListItem — thêm:
employee_full_name: str
employee_email: str
employee_code: str | None

# ProcessDetail — thêm:
employee_full_name: str
employee_email: str
employee_code: str | None
```

File: `backend/src/modules/onboarding/api/schemas.py`

```python
# OnboardingProcessListItem — thêm:
employee_full_name: str
employee_email: str
employee_code: str | None

# OnboardingProcessDetailResponse — thêm:
employee_full_name: str
employee_email: str
employee_code: str | None
```

File: `backend/src/modules/onboarding/api/router.py`

```python
# list_processes endpoint — fetch Employee data:
employee = await employee_repo.get_by_id(process.employee_id)
# Map vào response
```

**2. Thêm position_name vào response (để hiển thị vị trí)**

```python
# Thêm vào read model:
position_name: str | None  # "Developer", "Designer", ...
```

### B. Flow mới (post-Task 2)

**1. Onboarding Template CRUD**

```python
# New endpoints:
POST   /api/onboarding/templates           # Tạo template theo vị trí
GET    /api/onboarding/templates?position_id=X  # List template
GET    /api/onboarding/templates/{id}      # Detail template
DELETE /api/onboarding/templates/{id}      # Xóa template

POST   /api/onboarding/templates/{id}/items    # Thêm task vào template
DELETE /api/onboarding/templates/{id}/items/{item_id}  # Xóa task
```

**2. Tạo Onboarding với Template**

```python
# Modified endpoint:
POST /api/onboarding/processes
Body: {
    "candidate_id": "uuid",
    "position_id": "uuid",           # optional
    "template_id": "uuid",           # optional — load tasks từ template
    "custom_tasks": [...]            # optional — thêm task tùy chỉnh
}
```

**3. Upload tài liệu onboarding**

```python
# New endpoint:
POST /api/onboarding/processes/{id}/documents
Body: multipart/form-data { file, name, type }
GET  /api/onboarding/processes/{id}/documents
DELETE /api/onboarding/processes/{id}/documents/{doc_id}
```

---

## Frontend scope cho Task 2

### Files cần tạo/sửa

```
frontend/src/
├── lib/api/onboarding.ts                    ← API client (sửa: dùng relative path)
├── components/onboarding/
│   ├── ProcessCard.tsx                      ← Card list item
│   ├── OnboardingDetail.tsx                 ← Detail panel + checklist
│   └── OnboardingDashboard.tsx             ← Dashboard layout (list + detail)
└── app/(dashboard)/onboarding/
    └── page.tsx                             ← Route chính
```

### UI Components

**1. ProcessCard.tsx**
- Hiển thị: employee_name, position, progress bar, status badge
- Click → mở detail panel

**2. OnboardingDetail.tsx**
- Header: employee name, position, status
- Checklist: danh sách tasks, tick done/pending
- Action: Mark Done button

**3. page.tsx (Dashboard)**
- Left panel: list ProcessCard + filter tabs (All/In Progress/Complete)
- Right panel: OnboardingDetail
- Loading/Error/Empty states

---

## Acceptance Criteria (Task 2)

- [ ] HR thấy danh sách nhân viên đang onboarding với tên + vị trí
- [ ] Filter All / In Progress / Complete hoạt động
- [ ] Progress bar completed_count / total_count hiển thị đúng
- [ ] HR mở detail, thấy danh sách Onboarding Task
- [ ] HR tick task → task cập nhật ngay
- [ ] Tick hết task → process complete → Employee is_active = true
- [ ] Employee đó xuất hiện trong Employee module
- [ ] Loading skeleton, error state, empty state đầy đủ
- [ ] CORS fix: dùng relative path `/api/onboarding/...`
- [ ] Không đụng backend/src/main.py
- [ ] Không đụng Gmail/recruitment code

---

## Timeline

| Phase | Scope | Time |
|-------|-------|------|
| Task 2 (hiện tại) | Frontend onboarding UI + backend patch enrichment | 2-3 ngày |
| Task 3 (tương lai) | Onboarding Template CRUD + upload docs | 3-5 ngày |
| Task 4 (tương lai) | Template suggestions theo vị trí | 2-3 ngày |

