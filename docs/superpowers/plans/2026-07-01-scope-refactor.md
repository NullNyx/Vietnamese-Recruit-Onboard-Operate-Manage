# Scope Refactor — Vroom HR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace employee-self-service + Google OAuth + header-nav layout with HR-only auth/setup/shell according to design-docs.

**Architecture:** Three phases: (1) cut scope-sai FE+BE modules, (2) build new auth+setup, (3) replace app shell and screens. Each phase is independent enough to run/test separately.

**Tech Stack:** FastAPI+SQLModel (BE), Next.js 14+Tailwind+shadcn/ui (FE), cookie JWT, bcrypt for password hash.

---

## File Structure

### Remove

- `frontend/src/app/(employee)/` — entire route group (self-service)
- `frontend/src/lib/ess-nav-config.ts` — employee nav config
- `frontend/src/lib/employee-navigation.ts` — employee nav items
- `frontend/src/components/employee-sidebar.tsx`
- `frontend/src/components/employee-mobile-nav.tsx`
- `frontend/src/lib/api/employee-requests.ts`
- `frontend/src/lib/api/employee-assistant.ts`
- `frontend/src/app/(dashboard)/admin/employee-requests/`
- `frontend/src/components/header-navigation/header-utilities.tsx` — employee link
- `frontend/src/hooks/use-current-user.ts` — only if employee-specific
- `backend/src/modules/employee_request/` — entire module
- `backend/src/modules/payslip/` — employee-facing payslip (keep admin only if exists)
- Backend router registrations: employee_assistant, employee_request, admin_employee_request, employee_payslip

### Create

- `frontend/src/app/setup/layout.tsx` — setup wizard shell
- `frontend/src/app/setup/page.tsx` — step 1: welcome
- `frontend/src/app/setup/administrator/page.tsx` — step 2
- `frontend/src/app/setup/organization/page.tsx` — step 3
- `frontend/src/app/setup/ai-config/page.tsx` — step 4
- `frontend/src/app/setup/templates/page.tsx` — step 5
- `frontend/src/app/setup/complete/page.tsx` — step 6
- `frontend/src/app/(dashboard)/layout.tsx` — replace with sidebar layout
- `frontend/src/app/(dashboard)/onboarding/page.tsx` — redesign
- `frontend/src/app/login/page.tsx` — password auth version
- `frontend/src/components/tour-overlay.tsx`
- `backend/src/modules/identity/api/setup_router.py`
- `backend/src/modules/setup/` — setup module (or extend identity)

### Modify

- `backend/src/main.py` — unregister removed routers, register setup router
- `backend/src/modules/identity/domain/entities.py` — role model (SUPER_ADMIN, etc)
- `backend/src/modules/identity/application/auth_service.py` — password auth
- `backend/src/modules/identity/api/router.py` — password login endpoints
- `backend/src/modules/identity/container.py` — new services
- `frontend/src/middleware.ts` — setup redirect
- `frontend/src/lib/admin-nav-config.ts` — remove employee links
- `frontend/src/lib/navigation.ts` — update items
- `frontend/src/components/app-sidebar.tsx` — new sidebar

---

## Phase 1: Cut scope-sai modules

### Task 1.1: Remove employee self-service FE route group

**Files:**
- Delete: `frontend/src/app/(employee)/`

- [ ] **Delete `(employee)` route group**

```bash
rm -rf frontend/src/app/\(employee\)/
```

- [ ] **Delete employee-only lib files**

```bash
rm -f frontend/src/lib/ess-nav-config.ts
rm -f frontend/src/lib/employee-navigation.ts
```

- [ ] **Delete employee-only components**

```bash
rm -f frontend/src/components/employee-sidebar.tsx
rm -f frontend/src/components/employee-mobile-nav.tsx
```

- [ ] **Delete employee API libs**

```bash
rm -f frontend/src/lib/api/employee-requests.ts
rm -f frontend/src/lib/api/employee-assistant.ts
```

- [ ] **Delete admin employee-requests**

```bash
rm -rf frontend/src/app/\(dashboard\)/admin/employee-requests/
```

- [ ] **Delete related test files**

```bash
rm -f frontend/src/app/\(employee\)/**/*.test.*
find frontend/src -path '*/__tests__/*' -name '*employee*' | xargs rm -f
```

- [ ] **Verify no remaining imports from deleted files**

Run: `rg -n "ess-nav-config\|employee-navigation\|employee-requests\|employee-assistant\|employee-sidebar\|employee-mobile" frontend/src --type ts --type tsx`
Expected: no matches (or matches in test/plan files we want to keep)

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: remove employee self-service surface"
```

### Task 1.2: Remove employee-facing backend routers

**Files:**
- Modify: `backend/src/main.py`

- [ ] **Unregister employee_request, employee_assistant, employee_payslip routers from main.py**

Edit `backend/src/main.py`: delete lines importing and including these routers:
```
src/modules.employee_request.api.admin_router
src/modules.employee_request.api.router
src/modules.assistant.api.employee_router
src/modules.payslip.api.employee_router
```

Keep admin_payslip_router if it exists (HR-admin payslip is in scope).

- [ ] **Remove unused error handler registrations**

Delete `register_employee_request_error_handlers(app)` from main.py.

- [ ] **Remove the backend module directories**

```bash
rm -rf backend/src/modules/employee_request/
```

- [ ] **Search for remaining employee-payslip references**

Run: `rg -n "employee_request\|employee_assistant\|employee_payslip" backend/src/`
Expected: no matches (or matches in admin-only code we keep)

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: remove employee-facing backend modules"
```

### Task 1.3: Clean up FE nav configs

**Files:**
- Modify: `frontend/src/lib/admin-nav-config.ts`
- Modify: `frontend/src/lib/navigation.ts`
- Modify: `frontend/src/components/header-navigation/header-utilities.tsx`

- [ ] **Remove employee links from admin-nav-config**

Edit `frontend/src/lib/admin-nav-config.ts`: remove `/employee/documents` link, `/admin/employee-requests` link.

- [ ] **Remove employee sidebar link from header-utilities**

Edit `frontend/src/components/header-navigation/header-utilities.tsx`: remove `<a href="/employee/profile">`.

- [ ] **Update navigation.ts if needed**

Check if `/employee/*` routes appear in `frontend/src/lib/navigation.ts` and remove.

- [ ] **Fix tests referencing removed routes**

Run: `cd frontend && npx jest --no-coverage 2>&1 | head -50`
If tests fail because of removed routes, update test assertions.

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: clean nav configs after employee scope cut"
```

### Task 1.4: Remove OAuth / whitelist / domain FE pages (auth replacement prep)

**Files:**
- Delete: `frontend/src/app/(dashboard)/admin/oauth/`
- Delete: `frontend/src/app/(dashboard)/admin/whitelist/`
- Delete: `frontend/src/app/(dashboard)/admin/domains/` (if exists)

- [ ] **Remove OAuth config page**

```bash
rm -rf frontend/src/app/\(dashboard\)/admin/oauth/
```

- [ ] **Remove whitelist page**

```bash
rm -rf frontend/src/app/\(dashboard\)/admin/whitelist/
```

Verify: `rg -n "/admin/oauth\|/admin/whitelist\|/admin/domains" frontend/src/`
Expected: no matches in nav configs (if any exist, remove them too)

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: remove OAuth/whitelist admin pages"
```

---

## Phase 2: Auth + Setup

### Task 2.1: Add role model fields to identity entities

**Files:**
- Modify: `backend/src/modules/identity/domain/entities.py`

- [ ] **Extend UserRole enum with new roles**

Edit the `UserRole` enum in `entities.py`:
```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    HR_ADMIN = "hr_admin"
    HR_STAFF = "hr_staff"
    READ_ONLY = "read_only"
```

- [ ] **Add password_hash field to User model**

```python
class User(SQLModel, table=True):
    # ... existing fields ...
    password_hash: str | None = Field(default=None, max_length=255, nullable=True)
    # Keep google_sub for migration period, mark nullable
```

- [ ] **Run migration**

```bash
cd backend && alembic revision --autogenerate -m "add password_hash and role enum"
```

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: add password auth fields to identity model"
```

### Task 2.2: Build password auth service

**Files:**
- Create: `backend/src/modules/identity/application/password_service.py`

- [ ] **Create PasswordService**

```python
"""PasswordService for hashing and verifying passwords."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

@dataclass
class PasswordHashResult:
    hash: str
    salt: str

class PasswordService:
    """Handles password hashing and verification using SHA-256 + salt."""

    @staticmethod
    def hash_password(password: str) -> PasswordHashResult:
        """Hash a password with a random salt."""
        salt = secrets.token_hex(16)
        hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
        return PasswordHashResult(hash=hash_value, salt=salt)

    @staticmethod
    def verify_password(password: str, salt: str, hash_value: str) -> bool:
        """Verify a password against stored salt and hash."""
        computed = hashlib.sha256((salt + password).encode()).hexdigest()
        return computed == hash_value
```

(ponytail: SHA-256 + salt is acceptable for MVP. Upgrade to bcrypt/argon2 when compliance audit required.)

- [ ] **Add test**

Create `backend/tests/modules/identity/test_password_service.py`:
```python
def test_hash_and_verify():
    from src.modules.identity.application.password_service import PasswordService
    result = PasswordService.hash_password("test_password")
    assert PasswordService.verify_password("test_password", result.salt, result.hash)
    assert not PasswordService.verify_password("wrong_password", result.salt, result.hash)
```

Run: `cd backend && python -m pytest tests/modules/identity/test_password_service.py -v`
Expected: PASS

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: add password hash/verify service"
```

### Task 2.3: Add login/register endpoints to auth router

**Files:**
- Modify: `backend/src/modules/identity/api/router.py`
- Modify: `backend/src/modules/identity/api/schemas.py`
- Modify: `backend/src/modules/identity/container.py`

- [ ] **Create LoginRequest/RegisterRequest schemas**

Add to `schemas.py`:
```python
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
```

- [ ] **Add password_login endpoint**

In `router.py`:
```python
@router.post("/api/auth/login")
async def password_login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session),
    settings: AuthSettings = Depends(get_settings),
) -> AuthResponse:
    """Login with email + password."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # For migrated users with no password, check google_sub exists
    if not user.password_hash:
        raise HTTPException(status_code=401, detail="Please use Google OAuth (legacy account)")

    # Verify password
    stored = parse_password_hash(user.password_hash)  # "salt:hash"
    salt, hash_value = stored.split(":", 1)
    if not PasswordService.verify_password(request.password, salt, hash_value):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create tokens
    token_service = TokenService(settings, jwt_utils=JWTUtils(settings))
    tokens = await token_service.create_tokens(user.id, user.role)
    return AuthResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)
```

- [ ] **Register PasswordService in container.py**

```python
from src.modules.identity.application.password_service import PasswordService
# Add to identity container providers
```

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: add password login endpoint"
```

### Task 2.4: Build setup wizard backend

**Files:**
- Create: `backend/src/modules/setup/api/router.py`
- Create: `backend/src/modules/setup/api/schemas.py`
- Create: `backend/src/modules/setup/container.py`
- Modify: `backend/src/main.py`

- [ ] **Create SetupService**

In `backend/src/modules/setup/application/setup_service.py`:
```python
class SetupService:
    """Manages initial system setup flow."""

    async def is_setup_complete(self) -> bool:
        """Check if initial admin has been created."""
        stmt = select(User).where(User.role == UserRole.SUPER_ADMIN).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_first_admin(self, email: str, password: str, name: str) -> User:
        """Create the first SUPER_ADMIN user. Fails if already exists."""
        if await self.is_setup_complete():
            raise SetupAlreadyCompleteError()
        pw = PasswordService.hash_password(password)
        salt_hash = f"{pw.salt}:{pw.hash}"
        user = User(email=email, name=name, password_hash=salt_hash, role=UserRole.SUPER_ADMIN)
        self._session.add(user)
        await self._session.flush()
        return user

    async def configure_organization(self, name: str, tax_code: str, timezone: str) -> Organization:
        """Set up company profile."""
        org = Organization(name=name, tax_code=tax_code, timezone=timezone)
        self._session.add(org)
        await self._session.flush()
        return org

    async def configure_ai_provider(self, provider: str, api_key: str | None) -> None:
        """Save AI provider config (optional)."""
        cfg = AiProviderConfig(provider=provider, api_key_enc=self._crypto.encrypt(api_key or ''))
        self._session.add(cfg)
        await self._session.flush()

    async def complete_setup(self) -> None:
        """Permanently disable setup endpoint."""
        self._settings.setup_completed = True
        await self._session.commit()
```

- [ ] **Create setup API endpoints**

```python
# router.py
router = APIRouter(prefix="/api/setup", tags=["setup"])

@router.get("/status")
async def get_setup_status(
    setup_service: SetupService = Depends(get_setup_service),
):
    """Returns whether setup has been completed."""
    done = await setup_service.is_setup_complete()
    return {"setup_complete": done}

@router.post("/admin")
async def create_first_admin(
    request: CreateAdminRequest,
    setup_service: SetupService = Depends(get_setup_service),
):
    """Create first SUPER_ADMIN. Requires setup not complete."""
    user = await setup_service.create_first_admin(
        email=request.email, password=request.password, name=request.name
    )
    return {"id": str(user.id), "email": user.email}

@router.post("/organization")
async def setup_organization(
    request: OrgRequest,
    setup_service: SetupService = Depends(get_setup_service),
):
    """Configure company info."""
    org = await setup_service.configure_organization(
        name=request.name, tax_code=request.tax_code, timezone=request.timezone
    )
    return {"id": str(org.id)}

@router.post("/ai-provider")
async def setup_ai_provider(
    request: AiProviderRequest,
    setup_service: SetupService = Depends(get_setup_service),
):
    """Configure AI provider (optional)."""
    await setup_service.configure_ai_provider(
        provider=request.provider, api_key=request.api_key
    )
    return {"status": "ok"}

@router.post("/complete")
async def complete_setup(
    setup_service: SetupService = Depends(get_setup_service),
):
    """Finalize setup, disable setup endpoints."""
    await setup_service.complete_setup()
    return {"status": "completed"}
```

- [ ] **Register in main.py**

```python
from src.modules.setup.api.router import router as setup_router
app.include_router(setup_router)
```

- [ ] **Add setup guard to middleware**

In `frontend/src/middleware.ts`: if setup not complete and path not `/login` or `/setup`, redirect to `/setup`.

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: add initial setup wizard backend"
```

### Task 2.5: Build Setup Wizard FE

**Files:**
- Create: `frontend/src/app/setup/layout.tsx`
- Create: `frontend/src/app/setup/page.tsx` (step 1: welcome)
- Create: `frontend/src/app/setup/administrator/page.tsx`
- Create: `frontend/src/app/setup/organization/page.tsx`
- Create: `frontend/src/app/setup/ai-config/page.tsx`
- Create: `frontend/src/app/setup/templates/page.tsx`
- Create: `frontend/src/app/setup/complete/page.tsx`

- [ ] **Build setup layout with step indicator**

```tsx
// layout.tsx — centered card, step progress bar at top
export default function SetupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-[520px]">
        <StepIndicator currentStep={currentStep} />
        {children}
      </div>
    </div>
  );
}
```

- [ ] **Build welcome step**

Welcome screen: logo, welcome text, "Bắt đầu" button → next step.

- [ ] **Build administrator step**

Form: email, name, password, confirm password. POST `/api/setup/admin`.

- [ ] **Build organization step**

Form: company name, tax code, timezone. POST `/api/setup/organization`.

- [ ] **Build AI config step**

Radio/select: OpenAI / Gemini / OpenAI-compatible / Local / Disabled. POST `/api/setup/ai-provider`.

- [ ] **Build template step**

Optional: upload or skip. POST `/api/setup/templates` (or skip).

- [ ] **Build complete step**

Success message, "Vào Dashboard" button → redirect to `/`.

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: add initial setup wizard UI"
```

### Task 2.6: Rebuild login page

**Files:**
- Modify: `frontend/src/app/login/page.tsx`

- [ ] **Replace Google OAuth with username/password form**

Remove: GoogleIcon, Google OAuth button, disabled email/password form, disabled checkboxes.
Keep: Logo, general page structure.
Add: working email input, password input, submit button calling POST `/api/auth/login`.

```tsx
export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Đăng nhập thất bại");
        return;
      }
      window.location.href = "/";
    } catch {
      setError("Lỗi kết nối");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-[400px] space-y-8">
        {/* Logo */}
        {/* Error message */}
        {/* Login form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label>Mật khẩu</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Update login page tests**

Fix tests that reference removed Google OAuth elements.

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: replace Google OAuth login with password login"
```

---

## Phase 3: App shell + screens

### Task 3.1: Replace dashboard layout with sidebar

**Files:**
- Modify: `frontend/src/app/(dashboard)/layout.tsx`
- Install: `frontend/src/components/app-sidebar.tsx` (update if exists)

- [ ] **Rewrite dashboard layout**

From current header-nav layout to sidebar layout matching Pencil:

```tsx
// layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-auto">
        <div className="p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Build sidebar component**

Based on Pencil design: logo top, nav items: Dashboard, Candidates, Job Openings, Onboarding, Employees, Settings.
Use lucide icons. Active state highlighting.

- [ ] **Remove header-nav import from layout**

```bash
# Remove HeaderNavigation, Breadcrumbs, NavigationProgress, PageTransition references
```

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: replace header-nav with sidebar layout"
```

### Task 3.2: Redesign Onboarding Dashboard

**Files:**
- Modify: `frontend/src/app/(dashboard)/onboarding/page.tsx`
- Create: `frontend/src/components/onboarding/StatCard.tsx`
- Create: `frontend/src/components/onboarding/ActivityFeed.tsx`

- [ ] **Replace onboarding page with Pencil design**

From current left/right panel split to:
- Top: stat cards (Total Active, In Progress, Pending Docs, Overdue)
- Middle: Needs Attention section (overdue/missing cases)
- Bottom: case list with progress bars

```tsx
export default function OnboardingPage() {
  return (
    <div>
      <PageHeader title="Onboarding" description="Theo dõi tiến độ nhân viên mới" />
      <div className="grid grid-cols-4 gap-4 mb-6">
        <DashboardCard title="Tổng số" value={counts?.total ?? 0} icon={Users} />
        <DashboardCard title="Đang làm" value={counts?.in_progress ?? 0} icon={Loader2} />
        <DashboardCard title="Hồ sơ thiếu" value={counts?.pending_docs ?? 0} icon={FileText} />
        <DashboardCard title="Quá hạn" value={counts?.overdue ?? 0} icon={AlertCircle} />
      </div>
      <div>
        <h2>Cần xử lý</h2>
        {/* Needs attention section */}
      </div>
      <div>
        {/* Case list */}
      </div>
    </div>
  );
}
```

- [ ] **Build DashboardCard component**

Match Pencil reusable component B7Za3O: label, value, icon, trend.

- [ ] **Build stat queries**

Use react-query from existing `@/lib/api/onboarding`.

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: redesign onboarding dashboard matching Pencil"
```

### Task 3.3: Build Tour Overlay

**Files:**
- Create: `frontend/src/components/tour-overlay.tsx`

- [ ] **Implement tour component**

7 steps: welcome overlay, highlight overview, highlight AI summary, etc.
Semi-transparent backdrop + tooltip/instruction card at target position.

```tsx
export function TourOverlay({ step, onNext, onSkip }: TourOverlayProps) {
  const steps = [
    { title: "Chào mừng", description: "Làm quen với Vroom HR và các tính năng chính" },
    { title: "Tổng quan", description: "Xem nhanh Dashboard và thông tin tổng hợp" },
    { title: "AI Summary", description: "AI tổng hợp hoạt động hàng ngày" },
    { title: "Case Detail", description: "Xem chi tiết case, document checklist, contract" },
    { title: "Document", description: "Upload, verify và theo dõi hồ sơ" },
    { title: "Contract", description: "Soạn thảo hợp đồng từ template với AI" },
    { title: "Hoàn tất", description: "Kết thúc tour và bắt đầu làm việc" },
  ];
  return (
    <div className="fixed inset-0 z-50 bg-black/50">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 bg-card p-6 rounded-lg shadow-xl max-w-md">
        <h3>{steps[step].title}</h3>
        <p>{steps[step].description}</p>
        <div className="flex gap-2 mt-4">
          <button onClick={onSkip}>Bỏ qua</button>
          <button onClick={onNext}>{step < steps.length - 1 ? "Tiếp" : "Hoàn tất"}</button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Add tour trigger to dashboard**

Show tour on first visit (localStorage flag or API).

- [ ] **Commit**

```bash
git add -A
git commit -m "feat: add onboarding tour overlay"
```

### Task 3.4: Update middleware + verify dead routes

**Files:**
- Modify: `frontend/src/middleware.ts`

- [ ] **Update middleware**

Remove `/employee/*` route protection. Add `/setup/*` unprotected route.
Ensure `/login` redirects to `/` if already authenticated.

```typescript
// middleware.ts
const publicPaths = ["/login", "/setup", "/api/setup"];
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (publicPaths.some(p => pathname.startsWith(p))) {
    return NextResponse.next();
  }
  if (!request.cookies.has("access_token")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}
```

- [ ] **Verify no dead links in remaining codebase**

Run: `rg -n "/employee/" frontend/src/ --type ts --type tsx`
Expected: no matches (or only matches in comments/tests for deleted features)

- [ ] **Run FE tests**

```bash
cd frontend && npx jest --no-coverage 2>&1 | tail -20
```

- [ ] **Commit**

```bash
git add -A
git commit -m "refactor: update middleware, remove employee routes"
```

---

## Phase 4: Cleanup

### Task 4.1: Remove unused dependencies and dead imports

- [ ] **Scan for dead imports**

Run: `rg "gapi\|google\|OAuth\|ess-" frontend/src/ --type ts --type tsx`
Remove or comment any remaining references.

- [ ] **Verify build**

```bash
cd frontend && npx next build 2>&1 | tail -20
```
Expected: Build succeeds, no module-not-found errors.

- [ ] **Commit**

```bash
git add -A
git commit -m "chore: remove dead imports after scope change"
```

### Task 4.2: Final verification

- [ ] **Verify route tree**

```bash
find frontend/src/app -name "page.tsx" | sort
```
Expected: only `login`, `setup/*`, `(dashboard)/*` routes remain.

- [ ] **Verify backend router tree**

```bash
rg "include_router" backend/src/main.py
```
Expected: no employee_request, employee_assistant, employee_payslip.

- [ ] **Run backend tests**

```bash
cd backend && pytest -x --no-header -q 2>&1 | tail -20
```
Expected: all tests pass.

- [ ] **Final commit**

```bash
git add -A
git commit -m "chore: final cleanup after scope refactor"
```
