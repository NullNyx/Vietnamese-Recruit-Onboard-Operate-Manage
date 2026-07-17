# E2E Smoke Report — Vroom HR (AI Studio UI) × Backend thật qua Docker Compose

> Sub-agent E2E. Mục tiêu: kiểm thử end‑to‑end giao diện `vroom-hr/` (đã tích hợp
> AI Studio qua Phase 0‑3) với **backend thật** qua Docker Compose đầy đủ
> (Postgres + Redis + MinIO + backend + gmail‑worker + onboarding‑worker).
> Nhiệm vụ: ĐO và BÁO CÁO, không sửa feature code. Bug integration phát hiện được
> liệt kê để orchestrator dispatch worker fix.

Ngày chạy: 2026‑07‑17. Repo HEAD tại thời điểm chạy (chưa commit

---

## 1. Môi trường (docker services + ports + env)

### docker compose (`docker-compose.yml` + `docker-compose.override.yml`)
| Service             | Container             | Port        | Health/depends_on                                       |
|---------------------|-----------------------|-------------|---------------------------------------------------------|
| postgres (15)       | vroom-postgres       | 5432        | healthcheck `pg_isready`, volume `postgres_data`         |
| redis (7)           | vroom-redis          | 6379        | healthcheck `redis-cli ping`                            |
| minio (latest)      | vroom-minio          | 9000 / 9001 | healthcheck `curl /minio/health/live`, volume `minio`   |
| backend (FastAPI)   | vroom-backend        | **8000**    | override chạy `alembic upgrade head && uvicorn …reload`, `env_file: backend/.env`, phụ thuộc pg/redis/minio healthy |
| gmail-worker (arq)  | vroom-gmail-worker   | —           | phụ thuộc pg/redis healthy                               |
| onboarding-worker   | vroom-onboarding-worker | —        | phụ thuộc pg/redis healthy                               |
| **frontend (Next 14 cũ)** | vroom-frontend  | 3000        | build `./frontend` → **KHÔNG bật** trong lần chạy này (chạy vroom‑hr bằng host `pnpm dev` để thay thế frontend cũ) |

`docker-compose.override.yml` tự động áp dụng (dev): `AUTH_AUTO_SEED_SAMPLE_DATA=true`,
`RECRUITMENT_DEFAULT_ALLOWED_DOMAINS=["gmail.com"]`, `ASSISTANT_LLM_BASE_URL=http://host.docker.internal:20128/v1`,
`ASSISTANT_LLM_TIMEOUT_SECONDS=5`, `ASSISTANT_LLM_MAX_RETRIES=0`,
`extra_hosts: host.docker.internal:host-gateway`.

### ENV sử dụng
**`backend/.env`** (git‑ignored) — giữ các key thật có sẵn + thêm super‑admin / seed:
```
AUTH_GOOGLE_CLIENT_ID=1072878621750-…apps.googleusercontent.com
AUTH_GOOGLE_CLIENT_SECRET=GOCSPX-…
AUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback
AUTH_JWT_SECRET_KEY=…
AUTH_JWT_ALGORITHM=HS256
AUTH_OAUTH_TOKEN_ENCRYPTION_KEY=…            (base64 32‑byte, thật)
AUTH_SUPER_ADMIN_EMAIL=hr.qa@vroom.example.com   # (đã thêm — có trong E2E_HR_EMAIL)
AUTH_AUTO_SEED_SAMPLE_DATA=true                   # (đã thêm — pin reproduce)
# E2E_HR_NAME/E2E_HR_EMAIL/E2E_HR_PASSWORD/E2E_ORGANIZATION_NAME/E2E_EMPLOYEE_* (có sẵn)
```
> Lưu ý: `AUTH_GOOGLE_*` ở đây là OAuth Workspace thật (dùng cho Gmail/Calendar /callback),
> KHÔNG dùng cho login (login là email+password local sau First‑Run). KHÔNG có
> `GEMINI_API_KEY` thật (legacy route `/api/gemini` đã gỡ ở Phase 0). AI Assistant
> phụ thuộc `ASSISTANT_LLM_*` — hiện trỏ tới `host.docker.internal:20128` **không có
> server chạy** → chat sẽ fail/timeout (blocker 6e, xem §5).

**`vroom-hr/.env.local`** (tạo mới):
```
NEXT_PUBLIC_API_URL=http://localhost:3000
APP_URL=http://localhost:3000
GEMINI_API_KEY=""
```

### Trạng thái DB sau khi dựng (fresh)
`setup_complete=false`, demo seed: 1 Employee active (`hoangxuannguyen2005@gmail.com`),
2 Department, 2 Position, 4 AttendanceRecord (tuần hiện tại), 2 Payslip **published**
(2 tháng gần nhất). Leave types không dùng bảng nữa (`employee_requests` enum).
→ đủ để test First‑Run + ESS payslip/attendance.

---

## 2. Lựa chọn chạy frontend (docker vs host `pnpm dev`) + lý do

**Chọn: host `pnpm dev` cho `vroom-hr/` (port 3001) + reverse proxy Node trên port 3000,
reuse Docker backend/infra. KHÔNG bật service `frontend` (Next 14 cũ).**

Lý do:
- Giao diện test là `vroom-hr/` (Next 15), không phải `frontend/` (Next 14). Service
  `frontend` trong compose build `./frontend` → cũ. Thay vào đó chạy `vroom-hr` bằng
  `pnpm dev` từ host đơn giản hơn rebuild image.
- **BE không có `CORSMiddleware`** (đã xác nhận: `rg "CORS|add_middleware" backend/src` →
  không có). Cross‑origin `http://localhost:3000` → `http://localhost:8000` với
  `credentials:"include"` sẽ bị preflight/cookie reject. Vì KHÔNG được phép sửa code BE
  hay vroom‑hr app, mình dựng **reverse proxy** (`vroom-hr/e2e/proxy.mjs`) ép browser nói
  **cùng origin** `http://localhost:3000`:
  - `/api/*` → `http://localhost:8000` (BE thật)
  - `/*`    → `http://localhost:3001` (`pnpm dev` vroom‑hr)
  → BE cookie `Secure; SameSite=Lax; HttpOnly` được browser (localhost = secure context)
  giữ và gửi cùng‑site, không cần CORS. Đây là **workaround hạ tầng**, không sửa lib/app.

---

## 3. Playwright setup (config, storage state HR/Employee)

### Files tạo (trong scope cho phép)
- `vroom-hr/playwright.config.ts` — workers:1, `fullyParallel:false`, retries:0,
  `testDir:./e2e`, baseURL `http://localhost:3000`, `webServer.command="bash e2e/start-servers.sh"`
  (Playwright 1.61 nhận EITHER `port` OR `url`, dùng `port:3000`), trace/screenshot/video
  on‑failure, reporter `list`+`html`.
- `vroom-hr/e2e/proxy.mjs` — reverse proxy Node http thuần (pipe stream, forward
  headers, 502 khi upstream lỗi).
- `vroom-hr/e2e/start-servers.sh` — khởi `pnpm dev --port 3001` nền, chờ ready, exec
  proxy foreground (Playwright giám sát 1 process).
- `vroom-hr/e2e/vroom-hr.smoke.spec.ts` — 9 test smoke, **khai báo tuần tự** trong 1 file
  (single worker), chia state qua file trên ổ:
  - `e2e/.auth/hr.json` — session HR thật (cookie `access_token`+`refresh_token`)
  - `e2e/.auth/employee.json` — session ESS thật
  - `e2e/.auth/employee-creds.json` — `{email,tempPassword}` HR cấp cho Employee
- `vroom-hr/e2e/.auth/{hr,employee}.json` — placeholder `{}` (Playwright chấp nhận).
- `vroom-hr/.env.local` (xem §1).
- (`vroom-hr/package.json`: thêm `devDependency @playwright/test@1.61.1` + script
  `test:e2e` để chạy được; browsers đã có sẵn `~/.cache/ms-playwright`).

### Storage state — KHÔNG hardcode cookie giả
- **HR state**: do **First‑Run Setup UI thật** sinh ra. Mở `/setup` → wizard 3 bước →
  `POST /api/auth/setup` (atomic ở BE) → BE set cookie HttpOnly → bấm "Mở dashboard"
  → `context.storageState({path:"e2e/.auth/hr.json"})`. File chứa 2 cookie
  `access_token` + `refresh_token` thật (domain localhost, Secure, Lax, expires future).
- Nếu DB đã setup (re‑run), T1 rẽ nhánh: `POST /api/auth/login` thật → dashboard → vẫn
  ghi `hr.json` (login thật, không giả) rồi skip wizard.
- **Employee state**: do ESS onboarding thật — HR tạo Employee Account (BE sinh mật khẩu
  tạm, `must_change_password=true`) → Employee đăng nhập bằng mật khẩu tạm →
  `POST /api/auth/change-password` → vào `/employee` → `context.storageState`.
- Mọi test load storage state qua `test.use({ storageState: path })`.

### Chạy
```bash
cd vroom-hr
export E2E_HR_EMAIL=hr.qa@vroom.example.com \
       E2E_HR_PASSWORD='VroomQA!148#2026' \
       E2E_HR_NAME='HR QA' \
       E2E_ORGANIZATION_NAME='Vroom QA Organization'
pnpm exec playwright test --reporter=list
```

---

## 4. Kết quả (pass/fail per spec, root cause)

### Run riêng T1 trên **DB fresh** (mục tiêu 6a)
```
✓  1 [vroom-hr-smoke] › … › First-Run Setup › wizard 3 bước → submit atomic → dashboard, không re-login (6.5s)
1 passed (15.0s)
```
→ **First‑Run Setup (6a) PASS.** Wizard 3 bước thật (org → HR account → review →
"Kích hoạt hệ thống" → success), `POST /api/auth/setup` atomic thành công, BE cấp
session cookie HttpOnly, bấm "Mở dashboard" vào `/dashboard` **không re‑login**.
`hr.json` ghi 2 cookie thật. DB: tạo đúng 1 Organization, 1 HR admin.

### Full smoke (9 test) — DB đã setup sau T1 standalone (T1 rẽ nhánh fallback login)
```
Running 9 tests using 1 worker
  -  1 First-Run Setup › wizard…                      (skipped: DB đã setup → fallback login + skip wizard)
  ✘  2 HR Dashboard › metrics+runtime+audit            (22.3s)
  ✘  3 HR Employee provisioning → mật khẩu tạm        (23.6s)
  -  4 ESS onboarding login + change password         (skipped: T3 chưa tạo EMP_CREDS)
  ✘  5 ESS check-in                                   (22.0s)
  ✘  6 ESS request nghỉ phép + LEAVE_OVERLAP          (22.0s)
  ✘  7 ESS payslip đã publish                         (22.0s)
  ✓  8 Recruitment backbone render & precondition      (5.1s)
  -  9 HR AI Assistant human-in-the-loop              (skipped: composer không tìm thấy)
5 failed, 3 skipped, 1 passed (2.3m)
```
(Tổng cộng: **1 PASS** (T8) + **1 PASS standalone** (T1 fresh) + **5 FAIL** + **3 SKIP**.)

### Root cause chính (chặn 6b/6c/6d/6e) — BUG‑1 (xem §5)
Tất cả trang bảo vệ HR/ESS redirect về `/login` ngay sau hydration dù `/api/auth/me`
trả **200** với user admin thật. Bằng chứng chẩn đoán (browser dùng `hr.json` thật):
```
[res] 200 /api/auth/me
[res] 200 /api/admin/audit-logs?page=1&page_size=10
[res] 200 /api/recruitment/metrics
[res] 200 /api/admin/runtime/health
/dashboard -> http://localhost:3000/login          ← redirect dù API 200
/recruitment/inbox -> http://localhost:3000/login
/recruitment/interviews -> http://localhost:3000/login
/employees -> http://localhost:3000/login
/assistant -> http://localhost:3000/login
```
→ page load SSR render tạm rồi redirect. T8 "PASS" chỉ vì `toContainText` match text
SSR transient (inbox/interviews render text "Recruitment Inbox"/"Calendar" trước khi
redirect) — **không** nghĩa UI authed dùng được.

### Chi tiết fail
| # | Test | Lỗi | Root cause |
|---|------|-----|------------|
| T2 | HR Dashboard | `getByText(/Sức khỏe hệ thống.*Runtime/)` timeout 20s; snapshot = trang `/login` | BUG‑1: session bug → redirect /login |
| T3 | HR provisioning | `getByRole("heading",{name:/Employee Account/})` not found (đã redirect /login) | BUG‑1 |
| T5 | ESS check‑in | page `/login` (heading "Chấm công" not found) | BUG‑1 |
| T6 | ESS leave+overlap | page `/login` (heading "Yêu cầu" not found) | BUG‑1 |
| T7 | ESS payslip | page `/login` ("Danh sách phiếu lương" not found) | BUG‑1 |
| T9 | HR AI Assistant | composer không thấy → skip | BUG‑1 (page /login) + BUG‑3 (LLM chưa cấu hình) |

> Trace/screenshot/video mỗi fail lưu tại `vroom-hr/test-results/<slug>/` (trace.zip,
> test-failed-1.png, video.webm, error-context.md).

---

## 5. Bug integration phát hiện (list cho orchestrator dispatch fix)

### BUG‑1 — CRITICAL (chặn toàn bộ UI authed) — Phase 0 foundation
**`vroom-hr/lib/auth/session.ts` `useSession()` parse sai shape `GET /api/auth/me`.**

- FE mong đợi `AuthSessionResponse = { user, must_change_password, setup_complete }`
  (dùng `data?.user`, `data?.must_change_password`, `data?.setup_complete`).
- BE trả **flat `CurrentUser`** (`{id, email, name, role, must_change_password,
  gmail_grant_valid, calendar_grant_valid, employee_id, …}`) — xác nhận
  `backend/src/modules/identity/api/router.py` `GET /api/auth/me` trả `UserResponse`,
  và curl: `{"id":…,"email":"hr.qa@…","role":"admin","must_change_password":false,…}`.
- Hậu quả: `data?.user` luôn `undefined` → `isAuthenticated=false` →
  `useAuthGuard({requireAuth})` redirect mọi trang HR + ESS về `/login`.
- Tham chiếu đúng: `frontend/src/hooks/use-current-user.ts` (Next 14 cũ) treats
  `/api/auth/me` là `CurrentUser` flat (`return res.json()` rồi `data` = user).
- **Fix đề xuất** (worker Phase‑0 followup): trong `useSession()` map flat →
  `{ user: <flat CurrentUser>, must_change_password: flat.must_change_password,
  setup_complete: true }` (hoặc đổi `fetchSession` trả flat và sửa `useSession` dùng
  `data` làm `CurrentUser`). Ảnh hưởng toàn `app/(dashboard)`, `app/(employee)`,
  `middleware` không (middleware check cookie raw). Verify lại bằng T2‑T7 sau fix.

### BUG‑2 — Backend thiếu CORSMiddleware (cấu hình vận hành)
- `backend/src/main.py` KHÔNG đăng ký `CORSMiddleware` (đã `rg` xác nhận).
- Với `NEXT_PUBLIC_API_URL=http://<be>:8000` cross‑origin, mọi fetch
  `credentials:"include"` bị browser block preflight/credentials.
- Lần chạy này workaround bằng reverse proxy cùng origin (`e2e/proxy.mjs`).
- **Fix đề xuất** (worker BE/infra — KHÔNG phải feature code): thêm `CORSMiddleware`
  với `allow_credentials=True`, `allow_origins=[http://localhost:3000,
  AUTH_FRONTEND_URL]`, `allow_methods=["*"]`, `allow_headers=["*"]`. Nên đọc
  `AUTH_FRONTEND_URL` (default `http://localhost:3000`) để cho phép origin tường minh
  (không `*` khi credentials). Các phase report (0‑3) đều đã flag — giờ xác nhận bằng E2E.

### BUG‑3 — HR AI Assistant phụ thuộc LLM provider chưa sẵn sàng (blocker 6e)
- `docker-compose.override.yml` set `ASSISTANT_LLM_BASE_URL=http://host.docker.internal:20128/v1`
  trỏ tới server LLM **không chạy** trên host:20128 → chat (Phase 3) fail/timeout
  (`ASSISTANT_LLM_TIMEOUT_SECONDS=5`, `MAX_RETRIES=0`).
- Cần (1) chạy 1 LLM endpoint tương thích OpenAI tại `host.docker.internal:20128`
  hoặc đổi `ASSISTANT_LLM_*` sang provider thật, VÀ (2) HR cấu hình
  Organization AI Configuration (Settings → AI Configuration: provider/base_url/model)
  + bật capability Assistant. Sau đó test T9 mới chạy được Draft Action → confirm ghi thật.
- Đây là **thiếu cấu hình môi trường**, không phải code bug. Note cho human khi
  reproduce 6e.

### BUG‑4 — Recruitment happy‑path (6c) cần Google Workspace thật (blocker)
- `GET /api/auth/organization-google-connection/calendars` → **403** (chưa kết nối).
- Recruitment Inbox rỗng (chưa sync Gmail) → không có Job Application → không promote
  → Candidate; tạo Interview BẮT BUỘC chọn Calendar (GH #214, BE chặn → UI khóa).
- Phase 1 interviews page đã render đúng precondition "calendar/chưa kết nối" (T8 SSR
  match `Calendar`).
- Cần HR chạy `/gmail` connect Google Workspace thật + sync email + chọn calendar để
  exercise Backbone Flow đầy đủ. Note cho human.

### BUG‑5 — `runtime/health` báo `gmail-worker: unhealthy` (non‑fatal)
- `GET /api/admin/runtime/health` →
  `{status:"unhealthy", services:[redis healthy, postgresql healthy, minio healthy,
   gmail-worker unhealthy "no heartbeat", onboarding-worker healthy]}`.
- Container `vroom-gmail-worker` đang up nhưng heartbeat chưa được checker nhận.
  Có thể worker chưa emit heartbeat cùng channel BE check. Không chặn E2E напрямую;
  dashboard Runtime card sẽ hiển thị "KHÔNG KHỎE" (real data). Recommend worker/BE team
  kiểm tra heartbeat config.

### BUG‑6 (minor) — `organization_settings` không có cột `setup_complete`
- `get_setup_status()` thực tế tính = `org tồn tại AND count_admins>0` (service-layer),
  không cột DB. Chỉ ghi note (mapping migration 13 trong `backend/AGENTS.md` đã cũ).

---

## 6. Cấu hình lại (env_final, commands human reproduce)

### prerequisites
- Docker + compose; node 22 + pnpm 11; Playwright browsers (`~/.cache/ms-playwright`).
- Repo root: `/home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage`.

### 1) Dựng hạ tầng + reset DB cho First‑Run thật (6a yêu cầu DB fresh)
```bash
cd /home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage
docker compose down                                   # giữ volumes
docker volume rm vietnamese-recruit-onboard-operate-manage_postgres_data \
                 vietnamese-recruit-onboard-operate-manage_minio_data   # reset First-Run
docker compose up -d postgres redis minio backend gmail-worker onboarding-worker
# chờ healthcheck + alembic (override tự chạy) ; xác nhận:
curl -s http://localhost:8000/api/auth/setup-status   # phải {"setup_complete":false}
```

### 2) Khởi vroom‑hr + proxy (Playwright webServer lo phần này khi `playwright test`)
Nếu chạy bằng tay:
```bash
cd vroom-hr
NEXT_PUBLIC_API_URL=http://localhost:3000 DISABLE_HMR=true pnpm dev --port 3001 &  # Next 15
node e2e/proxy.mjs                                                                  # proxy :3000
```

### 3) Chạy E2E
```bash
cd vroom-hr
export E2E_HR_EMAIL=hr.qa@vroom.example.com \
       E2E_HR_PASSWORD='VroomQA!148#2026' \
       E2E_HR_NAME='HR QA' \
       E2E_ORGANIZATION_NAME='Vroom QA Organization'
pnpm exec playwright test --reporter=list
# xem trace fail:   pnpm exec playwright show-trace test-results/<slug>/trace.zip
# báo cáo HTML:    pnpm exec playwright show-report
```

Tham số E2E khớp `backend/.env` (`E2E_HR_*`). Mật khẩu HR/Employee ≥12 ký tự (BE enforce).

### 4) Muốn test 6c / 6e đầy đủ (cần tích hợp thật, ngoài phạm vi E2E)
- 6c: HR vào `/gmail` → Connect Google Workspace (dùng `AUTH_GOOGLE_*` trong `.env`)
  → sync → chọn calendar → quay lại recruitment flow.
- 6e: chạy LLM endpoint tại `host.docker.internal:20128` (hoặc đổi `ASSISTANT_LLM_*`)
  + HR vào `/settings` cấu hình AI provider + bật Assistant.

### 5) Dọn
```bash
docker compose down                # giữ volumes (cho retry)
# chỉ khi cần reset First-Run lần sau:
# docker volume rm vietnamese-recruit-onboard-operate-manage_postgres_data
```

---

## 7. Tóm tắt

| Spec mục tiêu | Tình trạng | Ghi chú |
|---|---|---|
| 6a First‑Run Setup atomic → dashboard no re‑login | **PASS** (T1 standalone fresh DB) | BE atomic + cookie HttpOnly thật, wizard 3 bước UI hoạt động |
| 6b HR login → dashboard metrics/health/audit thật | **FAIL** (T2) | BUG‑1: session shape → redirect /login; dữ liệu API thật trả 200 |
| 6c Backbone Inbox→promote→Candidate→Interview→accept→Onboarding→Employee active | **PARTIAL**: render PASS (T8 SSR) nhưng happy‑path bị chặn bởi BUG‑1 + BUG‑4 (Google Workspace) |
| 6d ESS check‑in / leave+LEAVE_OVERLAP / payslip published | **FAIL** (T5/T6/T7) | BUG‑1 chặn; backend sẵn sàng (leave type enum, payslip published đã seed) |
| 6e HR AI Assistant Draft Action → confirm ghi thật | **SKIP** (T9) | BUG‑1 + BUG‑3 (LLM chưa cấu hình) |
| Human‑in‑the‑loop (AI không tự ghi) | Chưa verify được UI | Code Phase 3 tuân thủ (draft.confirm_endpoint thật); test bị chặn |

**Kết luận:** First‑Run Setup (6a) xác nhận hoạt động end‑to‑end đầy đủ (BE + cookie +
UI). **Toàn bộ phần authed sau First‑Run bị chặn bởi 1 bug foundation (BUG‑1: parse
`/api/auth/me` sai shape)** — đây là blocker #1 để orchestrator dispatch worker fix
gấp. Sau BUG‑1 được fix, cần cấu hình Google Workspace (BUG‑4) + LLM (BUG‑3) để chạy đủ
6c/6e. CORS (BUG‑2) hiện workaround bằng proxy; nên thêm `CORSMiddleware` cho production.

Không sửa feature code. Không git commit. Tài liệu này là output duy nhất.