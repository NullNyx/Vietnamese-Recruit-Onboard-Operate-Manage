# Hướng dẫn Agent — Vroom HR

Bạn đang làm việc trên Vroom HR: nền tảng HRM tự triển khai cho doanh nghiệp Việt Nam
(Tuyển dụng - Onboarding - Vận hành - Quản lý). Một bản cài đặt phục vụ đúng một công ty.
User nhập bằng tiếng Việt hoặc tiếng Anh; phát hiện intent bằng cả hai ngôn ngữ.

Stack: FastAPI + SQLModel + PostgreSQL 15 + Redis 7 (Python 3.11+, MyPy strict,
Ruff line-length 100) · Next.js 14 + TypeScript + pnpm + Tailwind + shadcn/ui ·
cookie-based JWT auth · MinIO storage · pytest+Hypothesis / Vitest+fast-check.

## Luôn làm trước

1. Đọc `CONTEXT.md` (gốc). Dùng canonical terms y nguyên; không thay thế bằng
   synonym nó liệt kê trong `_Avoid_`.
2. Đọc ADR trong `docs/decisions/` liên quan tới vùng bạn sắp sửa.
   Nếu việc làm mâu thuẫn ADR, nêu rõ — không âm thầm ghi đè.
3. Đọc `docs/agents/` để biết luật issue-tracker, triage-label, domain-doc.

## Điều phối MCP

Chỉ dùng MCP khi nó tốt hơn file cục bộ hoặc dùng trình duyệt:

- `atlassian`: Jira Tasks và việc liên quan Jira. Dùng đường nhanh Jira trong
  `docs/agents/issue-tracker.md`; đọc lại sau create/update để xác minh labels.
- `playwright`: xác minh trình duyệt/UI sau thay đổi frontend.
- `github` / `gitlab`: metadata host từ xa, PR, workflow trên repo.

Nếu chọn MCP rõ ràng, dùng trực tiếp. Nếu code cục bộ trả lời nhanh hơn, ở lại.

## Ảnh chụp scope hiện tại

- Scope bây giờ là HR-only: không có employee login, không có employee self-service.
- Auth dùng mật khẩu (`/login`), không Google OAuth.
- Luồng chạy đầu tiên là `/setup/*` và tạo `SUPER_ADMIN` đầu tiên.
- Frontend shell là sidebar-first; không có header-nav app shell, không có route
  employee-facing.
- Backend router đang sống: identity/auth + admin, employee, gmail, recruitment
  (candidate, cv-review, metrics), onboarding, attendance, payslip admin, setup.

## Cách skill hoạt động (đọc cái này — nó thay đổi cách bạn trả lời)

Mỗi tin nhắn user:

1. Phát hiện intent và đối chiếu với bảng trigger bên dưới.
2. Nếu skill khớp, kích hoạt và làm theo quy trình của nó cho phần còn lại của task.
   Không tự chế thay thế cho skill tồn tại.
3. Thông báo một dòng bạn đang chạy skill nào (vd "Running `diagnose`.").
4. Nếu hai skill cùng khớp, ưu tiên skill cụ thể hơn; nếu thực sự mơ hồ,
   hỏi một câu ngắn.
5. Nếu không skill nào khớp, xử lý bình thường.

Trigger → skill (triggers để minh họa, không đầy đủ; khớp theo ý nghĩa):

| User intent (VI / EN) | Skill |
|---|---|
| "grill me", "quay tôi", "phản biện plan", stress-test a design | `grill-me` |
| same, kèm check project language/decisions và update docs | `grill-with-docs` |
| "viết PRD", "tạo PRD từ context", turn this conversation into a PRD | `to-prd` |
| "chia issue", "tách thành ticket", break a plan/PRD into issues | `to-issues` |
| "implement issue", "làm task", "build feature from issue", pick up a spec hoặc Jira task | `implement` |
| "code review", "review PR", "xem lại code theo spec" | `code-review` |
| "triage", "phân loại issue", label/route raw incoming bugs hoặc requests | `triage` |
| "làm theo TDD", "test trước", build feature/fix bug test-first | `tdd` |
| "debug cái này", "bug", "lỗi", "chậm/regression", diagnose a hard failure | `diagnose` |
| "cải thiện kiến trúc", "refactor", find deepening/coupling opportunities | `improve-codebase-architecture` |
| explore code structure: repo map, symbols, callers/callees, impact | `srcwalk` (chạy `srcwalk guide` trước; dùng trước read/grep thô) |
| "zoom out", "bức tranh lớn", unfamiliar with how code fits together | `zoom-out` |
| "prototype", "thử nghiệm", sanity-check data model / state machine / UI | `prototype` |
| "handoff", "bàn giao", compact this session cho successor agent | `handoff` |
| "có skill nào cho…", "find a skill", cần capability bạn không có | `find-skills` |
| "tiến độ tới đâu", "có tính năng gì", "trạng thái dự án", "tìm hiểu luồng X", project status / feature map / flow trace | Project status routine (bên dưới) |

Luồng mặc định cho feature mới: `grill-with-docs` → `to-prd` → `to-issues` →
`implement` (chạy `/tdd` nội bộ và kết thúc với `/code-review`).
Dùng `triage` chỉ cho issue raw đến mà user không tự tạo. Không ép mọi bước;
vào ở stage khớp với những gì user đã có.

Nếu task còn mơ hồ hoặc nhiều nhánh, dùng `/plan` như preflight ngắn trước
`grill-with-docs` hoặc `to-prd`; không bắt buộc cho task đã rõ.

Khi `implement` task dài hoặc phải giữ context qua nhiều turn, đặt `/goal`
ngay từ đầu với outcome + acceptance criteria ngắn. Giữ goal active cho tới
khi task xong; nếu phải ngắt giữa chừng thì `/goal pause`, quay lại thì
`/goal resume`.

Gate tối thiểu cho mọi slice: trước khi báo xong, chứng minh bằng lệnh thật.
Backend ưu tiên `ruff check`, `mypy`, `pytest`; frontend ưu tiên `npm run lint`,
`npm run test`, `npm run build`; task UI thì thêm Playwright/browser QA.
Nếu slice chạm scope file cụ thể, kiểm tra không sửa ngoài scope trừ khi có
defer hợp lệ. Không nhận "xong" nếu thiếu log test hoặc thiếu bằng chứng chạy.
Micro-harness v1 sống trong `agent-harness/`: giữ allowlist, evidence log, và
gate scripts ở đó; `AGENTS.md` chỉ giữ rule nền.

Khi task chạm vào giao diện web, `implement` kích hoạt FE sub-workflow theo
thứ tự này. Nếu có màn mới, redesign, hoặc cần chốt bố cục trước khi code,
dùng Pencil MCP để dựng `.pen` canvas làm source of truth cho từng screen.

1. `pencil` để thiết kế screen trong `.pen` canvas trước khi code
2. `ui-ux-pro-max` để review hướng UI, density, spacing, màu, icon, interaction
3. `frontend-app-builder` khi cần concept hoặc redesign lớn
4. `shadcn` để chọn component đúng
5. `react-best-practices` để giữ pattern và performance đúng
6. `frontend-testing-debugging` để QA browser cuối

Playwright MCP là tool chính cho bước QA đó. Dùng nó để:

- chụp screenshot desktop và mobile
- đọc console error/warning
- lấy accessibility snapshot
- resize viewport để bắt overflow / overlap / wrap lỗi
- mở nhiều tab để kiểm tra luồng điều hướng
- bật `vision` hoặc `devtools` caps khi cần soi UI sâu hơn

FE sub-workflow không thay thế luồng mặc định; nó chỉ chạy bên trong
`implement` khi task dính frontend.

## Báo cáo trạng thái dự án, tính năng, và luồng

Trigger: user hỏi dự án đang ở đâu, có tính năng gì, hoặc muốn hiểu luồng cụ thể
("tiến độ tới đâu rồi", "dự án có những tính năng gì",
"trạng thái hiện tại", "tìm hiểu luồng tuyển dụng/onboarding", "how does X work",
"trace the X flow"). Đây là báo cáo chỉ đọc — tổng hợp từ trạng thái sống của repo,
không bao giờ từ progress doc tĩnh, và không bao giờ ghi progress vào `docs/`.

Xây câu trả lời từ các nguồn chân lý này (không từ trí nhớ):

- **What's actually shipped** — đọc `backend/src/main.py` xem module router nào
  được đấu dây (hiện tại: identity/auth + admin, employee, gmail,
  recruitment [candidate, cv-review, metrics], onboarding). Module tồn tại trên đĩa
  nhưng không đăng ký ở đó là không sống.
- **Why things are the way they are** — `docs/decisions/` ADRs (vd scope là
  recruit→onboard Backbone Flow; attendance/payroll/self-service bị shelved).
- **Open work** — Jira Tasks qua Atlassian MCP (project `KAN`; filter theo
  status/label/assignee).
- **Recent activity** — `git log --oneline -n 20` và PR đã merged cho momentum.

Sau đó trả lời theo hình user yêu cầu:

- **Status / progress** → bảng ngắn theo area: area · state (shipped / in spec /
  shelved) · evidence (router wired, ADR). Nêu rõ mức độ hoàn thiện của
  Backbone Flow.
- **Feature map** → nhóm capability sống theo module, gắn với router đã đăng ký.
- **Flow trace** → chọn luồng và đi nó end-to-end qua các module dùng
  `srcwalk` cho call path; đặt tên mỗi bước bằng term từ `CONTEXT.md`.

Dùng canonical terms từ `CONTEXT.md`. Nếu spec mâu thuẫn với code đã đấu dây,
tin code và flag drift.

## Quy tắc tài liệu

Tạo doc lazily — chỉ khi có thứ gì thực sự cần ghi lại.

- Domain term được chốt → cập nhật `CONTEXT.md`. Giữ nó chỉ là glossary: không
  implementation details, không spec, không ghi chú nháp.
- Quyết định khó đảo ngược VÀ gây ngạc nhiên nếu thiếu context VÀ là kết quả
  của trade-off thực sự → thêm ADR vào `docs/decisions/` (số thứ tự tiếp theo,
  title ngắn + 1–3 câu).
- Issues, PRD, và progress/task lists vào Jira Tasks, không bao giờ vào markdown
  dưới `docs/` mặc định.
- Ngoại lệ: khi user hoặc repo owner yêu cầu implementation-facing working docs
  để human contributor có thể hiểu hoặc thực thi task, agent có thể tạo hoặc
  cập nhật markdown bổ sung dưới `docs/<owner-or-team>/...`.
  Coi các file này là working docs tạm thời, không phải canonical domain docs
  hay issue tracker replacement.

Layout mặc định:

```
/CONTEXT.md            glossary
/docs/agents/          skill config (issue-tracker, triage-labels, domain)
/docs/decisions/       ADRs
```

Layout ngoại lệ được phép (user approval rõ ràng):

```
/docs/<owner-or-team>/...      supplemental implementation-facing working docs
/docs/project/                 product strategy, foundation, gap analysis, change plans
```

## Git: branch, commit, push, PR

Trigger: khi user nói "commit", "push", "đẩy code", "tạo branch", "mở PR",
"tạo pull request" (hoặc tương đương), chạy full workflow này tự động end-to-end
không cần xác nhận từng bước. Constraint luôn giữ:

- Không bao giờ commit hoặc push lên `main`. Luôn làm trên branch.
- Chỉ tạo commit khi user yêu cầu (trigger trên được tính là yêu cầu).
- Không bao giờ chạy destructive git (`push --force`, `reset --hard`, `clean -f`, branch -D)
  trừ khi user yêu cầu rõ ràng.
- Flag file nào trông chứa secret (`.env`, credentials) trước khi stage.

Branch — luôn cắt từ `main` mới:

```bash
git checkout main && git pull origin main
git checkout -b <type>/<short-english-desc>
```

`<type>` ∈ `feature|fix|chore|refactor|docs|hotfix`. Name: lowercase English,
`-`-separated, 2–4 words. Không tên riêng, tiếng Việt, underscore, hoặc capitals.

Commit — atomic, stage file rõ ràng (tránh `git add .`):

```bash
git add <files>
git commit -m "<type>(<scope>): <imperative english summary>"
```

`<type>` ∈ `feat|fix|docs|refactor|chore|test|perf|style`. `<scope>` ∈
`identity|employee|gmail|recruitment|attendance|payroll|self-service|frontend|ui|infra|migrations|decisions`.
Summary: imperative, lowercase, < 72 ký tự. Vd `feat(payroll): add tax calc for dependents`.

Push + PR — rebase trước, set upstream, mở PR với What/Why/Testing:

```bash
git fetch origin main && git rebase origin/main
git push -u origin <branch>
gh pr create --title "<type>(<scope>): <summary>" --body "## What
- ...
## Why
- ...
## Testing
- ..."
```

PR title dùng format commit. Squash merge. Yêu cầu ≥1 approval + CI pass.

## Cách thực hiện task Jira

Khi user yêu cầu **implement task Jira**:

1. Trước khi code, đặt `/goal` từ summary + acceptance criteria của ticket.
2. Sau khi code, chạy gate đúng slice: backend dùng `ruff check`, `mypy`,
   `pytest`; frontend dùng `npm run lint`, `npm run test`, `npm run build`;
   UI dùng thêm browser QA.
3. Implement xong thì tạo branch, commit, push, mở PR như bình thường.
4. Theo dõi checks trên PR cho tới khi toàn bộ CI pass.
5. Chạy verify cuối để bảo đảm không còn lỗi runtime / test / lint / typecheck
   liên quan tới slice đó.
6. Gửi user link PR và trạng thái verified pass.
5. Dừng tại đó.

Không tự merge, không tự approve, không tự chuyển Jira Done, trừ khi user
giao thêm bước đó.

## Domain invariants

- Tất cả API routes có prefix `/api/`.
- Auth dùng httpOnly secure cookies (`access_token`, `refresh_token`), không Bearer headers.
- Employee được soft-delete qua flag `is_active`.
- Mọi admin action phải ghi audit log.
- OAuth tokens được mã hóa AES-256-GCM.
- Thuế Việt Nam: giảm trừ cá nhân 11M VND/tháng, người phụ thuộc 4.4M/người.
- Bảo hiểm (employee): 10.5% = BHXH 8% + BHYT 1.5% + BHTN 1%.
- Lương dùng 26 ngày công/tháng.

## Backend & dev environment

- Backend code mới phải theo layout module `api/ → application/ → domain/ →
  infrastructure/` với `container.py` cho DI, matching module hiện có.

## Cấu hình agent skills

- Issue tracker: Jira Tasks qua Atlassian MCP → `docs/agents/issue-tracker.md`.
- Triage labels: năm vai trò canonical, default strings → `docs/agents/triage-labels.md`.
- Domain docs: single-context, `CONTEXT.md` + `docs/decisions/` → `docs/agents/domain.md`.
- Code review: quy trình review PR task Jira dùng `code-review` skill.

## Agent skills

### Issue tracker

Jira Tasks qua Atlassian MCP. Xem `docs/agents/issue-tracker.md`.

PRD parents và implementation slices dùng tên khác nhau:

- parent spec / PRD ticket: prefix summary với `[PRD]` hoặc `[Spec]`
- implementation slice: prefix summary với `[Slice]`
- không coi parent PRD ticket là implementation work

Kiểm tra Jira nhanh:

- Shortcut tự nhiên: `check task` / `xem task trên jira` liệt kê Jira Tasks
  trong `KAN`.
- Shortcut có key: `check task KAN-11 bằng mcp jira` đọc task cụ thể đó.
- Fast path cho unkeyed checks: gọi Atlassian MCP `searchJiraIssuesUsingJql`
  trực tiếp với `project = KAN ORDER BY created DESC`. Không browse, scan source,
  hỏi key, hoặc list MCP tools trước.
- Fast path cho keyed checks: gọi Atlassian MCP `getJiraIssue` trực tiếp với
  `cloudId: "https://nullnyx.atlassian.net/"`, `issueIdOrKey: "KAN-11"`, fields
  `summary`, `description`, `status`, `labels`, `comment`, `assignee`,
  `issuelinks`, `created`, `updated`, `issuetype`, `priority`, `reporter`, và
  `responseContentFormat: "markdown"`.
- Khi tạo Jira Tasks qua Atlassian MCP, không tin labels truyền lúc create sẽ
  tồn tại. Sau mỗi `createJiraIssue`, lập tức đọc lại hoặc patch issue với
  `editJiraIssue` và verify field `labels` chứa giá trị mong đợi.
- Nếu Atlassian tools trực tiếp không có, fallback tới server `atlassian` MCP
  đã cấu hình qua `mcp-remote` và gọi `tools/call` với
  `name: "searchJiraIssuesUsingJql"` cho unkeyed checks hoặc `name: "getJiraIssue"`
  cho keyed checks; chỉ list tools/resources khi đang chẩn đoán fallback.
- Liệt kê tasks qua JQL: gọi `searchJiraIssuesUsingJql` với
  `project = KAN ORDER BY created DESC`.

### Triage labels

Năm vai trò canonical; labels dùng default strings. Xem `docs/agents/triage-labels.md`.

### Domain docs

Repo single-context: root `CONTEXT.md` + `docs/decisions/`. Xem `docs/agents/domain.md`.

# --- just-harness start ---

## Harness workflow

### Phân loại task
→ docs/FEATURE_INTAKE.md

### Gate scope
→ scripts/run-gate.sh --profile full-stack --allowlist <file>

### Ghi evidence
→ scripts/record-evidence.sh "<label>" <command>

### Ghi note nếu truth stale
→ scripts/record-note.sh <topic> <scope> <content>

### Luật nền

1. Dùng docs/workflow-skills.md để map phase → skill.
2. Task dài dùng /goal từ đầu với outcome + acceptance.
3. Task mơ hồ dùng /plan trước.
4. Gate trước khi báo xong: chứng minh bằng lệnh thật.
   - Backend: ruff check, mypy, pytest
   - Frontend: npm run lint, npm run test, npm run build
   - UI: Playwright (screenshot, console, accessibility)
5. Evidence là output thật từ gate/test/build, không phải lời model.
6. Friction lặp → ghi note → về sau biến thành rule.

### Quy ước

- state/ chỉ runtime state của harness, không commit.
- docs/notes/ giữ truth tạm thay đổi nhanh.
- scripts/ dùng lại được qua slice.

# --- just-harness end ---

## Gate tối thiểu

- Backend: `ruff check`, `mypy`, `pytest`
- Frontend: `npm run lint`, `npm run test`, `npm run build`
- UI: thêm Playwright/browser QA nếu đụng màn hình
- Slice có allowlist: không sửa file ngoài scope nếu không có defer hợp lệ

## Luồng mặc định

1. Nếu task còn mơ hồ, chạy `grill-with-docs` hoặc `/plan`.
2. Task lớn: tạo `/goal` ngay từ đầu.
3. Task mới: đi theo `grill-with-docs` → `to-prd` → `to-issues` → `implement`.
4. `implement` phải kết thúc bằng `/tdd` nội bộ và `/code-review` khi phù hợp.
5. Trước khi báo xong, chạy gate thật và ghi evidence.

## Tài liệu cần đọc trước khi sửa

- `CONTEXT.md`
- `docs/decisions/` liên quan
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-labels.md`
- `docs/agents/domain.md`

# --- just-harness end ---
