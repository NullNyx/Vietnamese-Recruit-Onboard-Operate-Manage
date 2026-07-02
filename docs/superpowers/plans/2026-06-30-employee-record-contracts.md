# Employee Record & Contracts — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build Employee Record as core module + Contract & Employment Documents as first vertical slice. HR/Admin sole actor, no employee self-service.

**Architecture:** Extend existing `backend/src/modules/employee/`. Add `EmploymentEvent`, `Contract`, `ContractTemplate`, `ContractAmendment` domain entities. Add `employment_status` and `termination_date` to Employee. Add status to Document (uploaded/verified/rejected/expired). Frontend: tabbed Employee Detail hub + Contract Detail page.

**Tech Stack:** FastAPI + SQLModel + PostgreSQL, Next.js 14 + Tailwind + shadcn/ui. Follow existing module layout: api/ → application/ → domain/ → infrastructure/ + container.py.

---

### Task 1: Backend — domain entities + migration

**Files:**
- Modify: `backend/src/modules/employee/domain/entities.py`
- Create: `backend/src/modules/employee/domain/employment_event.py`
- Create: `backend/src/modules/employee/domain/contract.py`
- Create: `backend/src/modules/employee/domain/contract_template.py`
- Create: `backend/src/modules/employee/domain/contract_amendment.py`
- Modify: `backend/src/modules/employee/domain/__init__.py`

- [x] **Add `employment_status` + `termination_date` to Employee entity**

In `entities.py`, add fields:
```python
employment_status: str = Field(default="active", max_length=20, nullable=False)  # active/resigned/terminated/suspended
termination_date: date | None = Field(default=None)
```
Make `email` nullable: `email: str | None = Field(default=None, max_length=255, unique=True, index=True)`.
Rename `tax_code` → `personal_tax_code` in field.

- [x] **Add `Document.status` + verification fields**

In `EmployeeDocument`, add:
```python
status: str = Field(default="uploaded", max_length=20, nullable=False)  # uploaded/verified/rejected/expired
verified_by_hr_id: UUID | None = Field(default=None, foreign_key="users.id")
verified_at: datetime | None = Field(default=None)
expired_at: date | None = Field(default=None)
```
Change `document_type` values to match spec: id_card / diploma / insurance / contract_related / other.
Add `uploaded_by_hr_id: UUID = Field(foreign_key="users.id", nullable=False)`.

- [x] **Create EmploymentEvent entity**

```python
# employment_event.py
class EmploymentEvent(SQLModel, table=True):
    __tablename__ = "employment_events"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    event_type: str = Field(max_length=50, nullable=False)  # profile_update/promotion/transfer/status_change/termination/document_update/contract_update
    before_json: dict | None = Field(default=None, sa_column=Column(JSON))
    after_json: dict | None = Field(default=None, sa_column=Column(JSON))
    actor_hr_id: UUID = Field(foreign_key="users.id", nullable=False)
    note: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False))
```

- [x] **Create Contract entity**

```python
# contract.py
class Contract(SQLModel, table=True):
    __tablename__ = "contracts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    employee_id: UUID = Field(foreign_key="employees.id", nullable=False, index=True)
    contract_number: str | None = Field(default=None, max_length=50, unique=True)
    template_id: UUID | None = Field(default=None, foreign_key="contract_templates.id")
    contract_type: str = Field(max_length=30, nullable=False)  # labor/offer/nda/other
    status: str = Field(default="draft", max_length=30, nullable=False)  # draft/pending_signature/active/expired/terminated/cancelled
    signed_on: date | None = Field(default=None)
    started_on: date | None = Field(default=None)
    ended_on: date | None = Field(default=None)
    file_path: str | None = Field(default=None)
    content: str | None = Field(default=None)
    signed_document_path: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False))
    created_by: UUID = Field(foreign_key="users.id", nullable=False)
    updated_by: UUID | None = Field(default=None, foreign_key="users.id")
```

- [x] **Create ContractTemplate entity**

```python
# contract_template.py
class ContractTemplate(SQLModel, table=True):
    __tablename__ = "contract_templates"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    version: int = Field(default=1, nullable=False)
    content: str = Field(nullable=False)
    file_path: str | None = Field(default=None)
    status: str = Field(default="active", max_length=20, nullable=False)  # active/archived
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False))
    created_by: UUID = Field(foreign_key="users.id", nullable=False)
```

- [x] **Create ContractAmendment entity**

```python
# contract_amendment.py
class ContractAmendment(SQLModel, table=True):
    __tablename__ = "contract_amendments"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    contract_id: UUID = Field(foreign_key="contracts.id", nullable=False, index=True)
    name: str = Field(max_length=255, nullable=False)
    content: str = Field(nullable=False)
    file_path: str | None = Field(default=None)
    signed_document_path: str | None = Field(default=None)
    status: str = Field(default="draft", max_length=30, nullable=False)  # draft/pending_signature/signed/cancelled
    signed_on: date | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False))
    created_by: UUID = Field(foreign_key="users.id", nullable=False)
```

- [x] **Commit**

```bash
git add backend/src/modules/employee/domain/entities.py \
       backend/src/modules/employee/domain/employment_event.py \
       backend/src/modules/employee/domain/contract.py \
       backend/src/modules/employee/domain/contract_template.py \
       backend/src/modules/employee/domain/contract_amendment.py \
       backend/src/modules/employee/domain/__init__.py
git commit -m "feat(employee): add contract/event entities, employment_status to Employee"
```

---

### Task 2: Backend — repositories + infrastructure

**Files:**
- Create: `backend/src/modules/employee/infrastructure/employment_event_repository.py`
- Create: `backend/src/modules/employee/infrastructure/contract_repository.py`
- Create: `backend/src/modules/employee/infrastructure/contract_template_repository.py`
- Create: `backend/src/modules/employee/infrastructure/contract_amendment_repository.py`
- Modify: `backend/src/modules/employee/infrastructure/__init__.py`
- Modify: `backend/src/modules/employee/infrastructure/employee_repository.py` (add `update_status` method)

- [x] **Create EmploymentEventRepository**

```python
class EmploymentEventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: EmploymentEvent) -> EmploymentEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_by_employee(self, employee_id: UUID) -> list[EmploymentEvent]:
        stmt = select(EmploymentEvent).where(
            EmploymentEvent.employee_id == employee_id
        ).order_by(EmploymentEvent.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
```

- [x] **Create ContractRepository** (standard CRUD: create, get_by_id, list_by_employee, update, delete)

- [x] **Create ContractTemplateRepository** (standard CRUD: create, get_by_id, list_active, update, archive)

- [x] **Create ContractAmendmentRepository** (create, list_by_contract, update)

- [x] **Update EmployeeRepository** — add `update_status` method

```python
async def update_status(self, employee_id: UUID, status: str, termination_date: date | None = None) -> Employee | None:
    emp = await self.get_by_id(employee_id)
    if emp is None:
        return None
    emp.employment_status = status
    if termination_date:
        emp.termination_date = termination_date
    self._session.add(emp)
    await self._session.flush()
    return emp
```

- [x] **Update container.py** — register new repositories and services

- [x] **Commit**

```bash
git commit -m "feat(employee): add repositories for contract/event/amendment entities"
```

---

### Task 3: Backend — application services

**Files:**
- Create: `backend/src/modules/employee/application/contract_service.py`
- Create: `backend/src/modules/employee/application/contract_template_service.py`
- Create: `backend/src/modules/employee/application/contract_amendment_service.py`
- Create: `backend/src/modules/employee/application/employment_event_service.py`
- Modify: `backend/src/modules/employee/application/employee_service.py`

- [x] **Create ContractService**

Business rules:
- Create contract → status `draft`
- Mark ready for signing → status `pending_signature`
- Upload signed document + set signed_on → status `active`
- Can only renew active contracts (creates new Contract or ContractAmendment)
- Can only terminate/cancel non-terminal contracts
- Every status change writes AuditLog + EmploymentEvent

- [x] **Create EmploymentEventService**

```python
class EmploymentEventService:
    async def record(self, employee_id, event_type, before, after, actor_hr_id, note=None) -> EmploymentEvent
    async def list_by_employee(self, employee_id) -> list[EmploymentEvent]
```

- [x] **Update EmployeeService**

Add methods:
- `change_status(employee_id, new_status, termination_date, actor_hr_id)` — validates transition, calls repo, creates EmploymentEvent
- `update_employee(employee_id, data, actor_hr_id)` — wrap existing update, create EmploymentEvent with before/after diff

- [x] **Update DocumentService** — add verify/reject/expire methods

```python
async def verify_document(doc_id, verified_by_hr_id) -> EmployeeDocument
async def reject_document(doc_id, verified_by_hr_id, note) -> EmployeeDocument
async def mark_expired(doc_id) -> EmployeeDocument
```

- [x] **Commit**

```bash
git commit -m "feat(employee): add contract/event services, employee status change with audit"
```

---

### Task 4: Backend — API routes + schemas

**Files:**
- Modify: `backend/src/modules/employee/api/router.py`
- Modify: `backend/src/modules/employee/api/schemas.py`

- [x] **Add contract API endpoints**

```
POST   /api/employees/{id}/contracts           → create contract
GET    /api/employees/{id}/contracts           → list contracts
GET    /api/contracts/{id}                     → get contract detail
PUT    /api/contracts/{id}                     → update draft
POST   /api/contracts/{id}/send-for-signing    → mark pending_signature
POST   /api/contracts/{id}/sign                → upload signed doc, mark active
POST   /api/contracts/{id}/renew               → create amendment or new contract
POST   /api/contracts/{id}/terminate           → mark terminated
```

- [x] **Add contract template endpoints**

```
GET    /api/contract-templates         → list active templates
POST   /api/contract-templates         → create
PUT    /api/contract-templates/{id}    → update
POST   /api/contract-templates/{id}/archive → archive
```

- [x] **Add employment event endpoint**

```
GET    /api/employees/{id}/events     → list events (read-only)
```

- [x] **Add document verify/reject/expire endpoints**

```
POST   /api/documents/{id}/verify
POST   /api/documents/{id}/reject
POST   /api/documents/{id}/expire
```

- [x] **Add employee status change endpoint**

```
POST   /api/employees/{id}/status    → body: {status, termination_date?, note}
```

- [x] **Update employee schemas** — add `employment_status`, `termination_date` to EmployeeResponse, EmployeeCreate, EmployeeUpdate. Make `email` optional in create.

- [x] **Commit**

```bash
git commit -m "feat(employee): add contract/event/status API routes"
```

---

### Task 5: Frontend — API client + types

**Files:**
- Modify: `frontend/src/lib/api/employees.ts`
- Modify: `frontend/src/lib/api/types.ts`

- [x] **Add contract API client functions**

- [x] **Add contract template API client functions**

- [x] **Add employment event API client function**

- [x] **Add document status change API functions**

```typescript
export async function verifyDocument(documentId: string): Promise<EmployeeDocument>
export async function rejectDocument(documentId: string, note: string): Promise<EmployeeDocument>
export async function markDocumentExpired(documentId: string): Promise<EmployeeDocument>
export async function changeEmployeeStatus(employeeId: string, status: string, terminationDate?: string, note?: string): Promise<Employee>
```

- [x] **Update types.ts** — add Contract, ContractTemplate, ContractAmendment, EmploymentEvent interfaces. Update Employee to include employment_status.

- [x] **Commit**

```bash
git commit -m "feat(ui): add contract/event/doc-status API clients"
```

---

### Task 6: Frontend — Employee List page

**Files:**
- Modify: `frontend/src/app/(dashboard)/employees/page.tsx`

- [x] **Enhance employee table** — add columns: employee_code, full_name, department, position, employment_status, start_date, latest_contract_status (derived or fetched)

- [x] **Add status badge styling** — colored badges for active/resigned/terminated/suspended

- [x] **Commit**

```bash
git commit -m "feat(ui): enhance employee list with status/contract columns"
```

---

### Task 7: Frontend — Employee Detail (tabbed hub)

**Files:**
- Modify: `frontend/src/app/(dashboard)/employees/[id]/page.tsx`

- [x] **Refactor page to tabbed layout** — tabs: Profile / Documents / Contracts / Events & Audit

- [x] **Profile tab** — show employee info + edit button (opens inline form or drawer). Change status action.

- [x] **Documents tab** — list documents with status badges. Upload, verify, reject, mark expired actions.

- [x] **Contracts tab** — list contracts with status. Create contract (drawer/page). Click → Contract Detail.

- [x] **Events & Audit tab** — read-only timeline of EmploymentEvent records.

- [x] **Commit**

```bash
git commit -m "feat(ui): employee detail tabbed hub with profile/documents/contracts/events"
```

---

### Task 8: Frontend — Contract Detail + Create

**Files:**
- Create: `frontend/src/app/(dashboard)/employees/[id]/contracts/[contractId]/page.tsx`
- Modify: `frontend/src/app/(dashboard)/employees/[id]/page.tsx` (create contract modal/drawer)

- [x] **Create Contract Detail page** — show contract info, status, content, signed document. Actions: edit draft, upload signed, send for signing, renew, terminate, export.

- [x] **Create Contract flow** — drawer or page with: select template, enter contract_number, started_on/ended_on, content or template fill.

- [x] **Contract Amendment list** — show under contract detail. Create amendment drawer.

- [x] **Contract status transitions** — buttons only for valid next states per role.

- [x] **Commit**

```bash
git commit -m "feat(ui): contract detail page with lifecycle actions"
```

---

### Task 9: Tests

**Files:**
- Create: `backend/tests/modules/employee/test_employment_event_repository.py`
- Create: `backend/tests/modules/employee/test_contract_service.py`
- Create: `backend/tests/modules/employee/test_status_change.py`
- Create: `backend/tests/modules/employee/test_document_status.py`
- Modify: `backend/tests/modules/employee/__init__.py`

- [x] **Test: status change validates transitions**

```python
async def test_cannot_create_contract_after_terminated(db_session, employee_factory):
    emp = await employee_factory(status="terminated")
    # attempt create contract → should raise InvalidStatusTransition
```

- [x] **Test: document status flow**

```python
async def test_document_verify_sets_verified_by(db_session, document_factory):
    doc = await document_factory()
    svc = DocumentService(...)
    result = await svc.verify_document(doc.id, hr_user.id)
    assert result.status == "verified"
    assert result.verified_by_hr_id == hr_user.id
```

- [x] **Test: status change creates EmploymentEvent**

```python
async def test_status_change_records_event(db_session, employee_factory):
    emp = await employee_factory()
    svc = EmployeeService(...)
    await svc.change_status(emp.id, "resigned", date(2026, 6, 30), hr_user.id)
    events = await EmploymentEventRepository(db_session).list_by_employee(emp.id)
    assert len(events) == 1
    assert events[0].event_type == "status_change"
```

- [x] **Test: contract lifecycle transitions**

```python
async def test_contract_draft_to_active_flow(db_session, contract_factory):
    contract = await contract_factory(status="draft")
    svc = ContractService(...)
    c1 = await svc.mark_sending(contract.id)
    assert c1.status == "pending_signature"
    c2 = await svc.sign(contract.id, signed_doc_path="s3://...", signed_on=date.today())
    assert c2.status == "active"
```

- [x] **Test: cannot edit active contract directly**

```python
async def test_cannot_update_active_contract_content(db_session, contract_factory):
    contract = await contract_factory(status="active")
    svc = ContractService(...)
    with pytest.raises(ContractAlreadyActiveError):
        await svc.update_draft(contract.id, {"content": "new"})
```

- [x] **Commit**

```bash
git commit -m "test(employee): add status/contract/document event tests"
```
