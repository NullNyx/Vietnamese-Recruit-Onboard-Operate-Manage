# Agent Instructions — Vroom HR

You are working on Vroom HR: a self-hosted HRM platform for Vietnamese companies
(Recruit-Onboard-Operate-Manage). One deployment serves exactly one company.
Users prompt in Vietnamese or English; detect intent in either language.

Stack: FastAPI + SQLModel + PostgreSQL 15 + Redis 7 (Python 3.11+, MyPy strict,
Ruff line-length 100) · Next.js 14 + TypeScript + pnpm + Tailwind + shadcn/ui ·
cookie-based JWT auth · MinIO storage · pytest+Hypothesis / Vitest+fast-check.

## Always do first

1. Read `CONTEXT.md` (root). Use its canonical terms verbatim; never substitute a
   synonym it lists under `_Avoid_`.
2. Read the ADRs in `docs/decisions/` that touch the area you are about to change.
   If your work contradicts an ADR, surface it explicitly — do not silently override.
3. Read `docs/agents/` for issue-tracker, triage-label, and domain-doc rules.

## MCP routing

Use MCP only when it beats local files or browser work:

- `atlassian`: Jira Tasks and Jira-linked work. Use the direct Jira fast paths in
  `docs/agents/issue-tracker.md`; re-read after create/update to verify labels.
- `codegraph`: repo symbol/context/impact/trace. Prefer before raw read/grep for
  structure questions.
- `playwright`: browser/UI verification after frontend changes.
- `github` / `gitlab`: remote host metadata, PRs, and repo-hosted workflow.

If MCP choice is obvious, use it directly. If local code answers it faster, stay
local.

## Current scope snapshot

- Scope now is HR-only: no employee login, no employee self-service surface.
- Auth is password-based (`/login`), not Google OAuth.
- First-run flow is `/setup/*` and creates the first `SUPER_ADMIN`.
- Frontend shell is sidebar-first; no header-nav app shell, no employee-facing
  routes.
- Live backend routers are identity/auth + admin, employee, gmail, recruitment
  (candidate, cv-review, metrics), onboarding, attendance, payslip admin, setup.

## How skills work (read this — it changes how you respond)

On every user message:

1. Detect intent and match it against the trigger table below.
2. If a skill matches, activate it and follow its process for the rest of the task.
   Do not improvise a substitute for a skill that exists.
3. Announce in one line which skill you are running (e.g. "Running `diagnose`.").
4. If two skills could match, prefer the more specific one; if genuinely ambiguous,
   ask one short question.
5. If no skill matches, proceed normally.

Trigger → skill (triggers are illustrative, not exhaustive; match on meaning):

| User intent (VI / EN)                                                                                                   | Skill                                                           |
| ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| "grill me", "quay tôi", "phản biện plan", stress-test a design                                                          | `grill-me`                                                      |
| same, but check against project's language/decisions and update docs                                                    | `grill-with-docs`                                               |
| "viết PRD", "tạo PRD từ context", turn this conversation into a PRD                                                     | `to-prd`                                                        |
| "chia issue", "tách thành ticket", break a plan/PRD into issues                                                         | `to-issues`                                                     |
| "implement issue", "làm task", "build feature from issue", pick up a spec or Jira task                                  | `implement`                                                     |
| "code review", "review PR", "xem lại code theo spec"                                                                    | `code-review`                                                   |
| "triage", "phân loại issue", label/route raw incoming bugs or requests                                                  | `triage`                                                        |
| "làm theo TDD", "test trước", build a feature/fix bug test-first                                                        | `tdd`                                                           |
| "debug cái này", "bug", "lỗi", "chậm/regression", diagnose a hard failure                                               | `diagnose`                                                      |
| "cải thiện kiến trúc", "refactor", find deepening/coupling opportunities                                                | `improve-codebase-architecture`                                 |
| explore code structure: repo map, symbols, callers/callees, impact                                                      | `srcwalk` (run `srcwalk guide` first; use before raw read/grep) |
| "codegraph", "trace bằng codegraph", static call graph / symbol impact                                                  | Codegraph workflow (below)                                      |
| "tasteskill", "taste skill", improve frontend taste / redesign UI                                                       | Taste Skill workflow (below)                                    |
| "zoom out", "bức tranh lớn", unfamiliar with how code fits together                                                     | `zoom-out`                                                      |
| "prototype", "thử nghiệm", sanity-check a data model / state machine / UI                                               | `prototype`                                                     |
| "handoff", "bàn giao", compact this session for a successor agent                                                       | `handoff`                                                       |
| "có skill nào cho…", "find a skill", need a capability you don't have                                                   | `find-skills`                                                   |
| "tiến độ tới đâu", "có tính năng gì", "trạng thái dự án", "tìm hiểu luồng X", project status / feature map / flow trace | Project status routine (below)                                  |

Default flow for a fresh feature: `grill-with-docs` → `to-prd` → `to-issues` →
`implement` (which runs `/tdd` internally and closes with `/code-review`).
Use `triage` only for raw incoming issues the user did not create. Don't force
every step; enter at the stage that matches what the user already has.

## Reporting project status, features, and flows

Trigger: the user asks where the project stands, what features exist, or wants to
understand a specific flow ("tiến độ tới đâu rồi", "dự án có những tính năng gì",
"trạng thái hiện tại", "tìm hiểu luồng tuyển dụng/onboarding", "how does X work",
"trace the X flow"). This is read-only reporting — synthesize from the repo's live
state, never from a static progress doc, and never write progress into `docs/`.

Build the answer from these sources of truth (not from memory):

- **What's actually shipped** — read `backend/src/main.py` to see which module
  routers are wired in (currently: identity/auth + admin, employee, gmail,
  recruitment [candidate, cv-review, metrics], onboarding). A module existing on
  disk but not registered there is not live.
- **Why things are the way they are** — `docs/decisions/` ADRs (e.g. scope is the
  recruit→onboard Backbone Flow; attendance/payroll/self-service were shelved).
- **Open work** — Jira Tasks via Atlassian MCP (project `KAN`; filter by
  status/label/assignee).
- **Recent activity** — `git log --oneline -n 20` and merged PRs for momentum.

Then answer in the shape the user asked for:

- **Status / progress** → a short per-area table: area · state (shipped / in spec /
  shelved) · evidence (router wired, ADR). Call out the
  Backbone Flow's completeness specifically.
- **Feature map** → group live capabilities by module, tied to registered routers.
- **Flow trace** → pick the flow and walk it end to end across modules using
  `srcwalk` for the call path; name each step with the `CONTEXT.md` term.

Use canonical terms from `CONTEXT.md`. If a spec contradicts what's wired in code,
trust the code and flag the drift.

## Codegraph workflow

Use Codegraph for static code-intelligence tasks when available, especially when
the user asks how a flow works, where a symbol is used, or what a refactor will
affect. Codegraph complements `srcwalk`: use `srcwalk` when the trigger table
activates that skill, and use Codegraph for call graph, symbol context, and impact
queries after the repo context is clear.

- Start with `codegraph_context` for architecture, bug, or "how does X work"
  questions. It returns entry points, related symbols, and key code in one call.
- Use `codegraph_trace` for "how does A reach B" flow questions. Prefer one trace
  over chaining many raw file reads.
- Use `codegraph_callers` / `codegraph_callees` for local call graph questions.
- Use `codegraph_impact` before refactoring a shared symbol or changing a public
  application service API.
- Use `codegraph_files` / `codegraph_search` to orient quickly, then read only the
  files needed for exact edits.
- Do not commit `.codegraph/`. It is a local generated index; regenerate it from
  source when stale.

For project status or feature-map answers, still trust `backend/src/main.py` for
what is live. A symbol existing in Codegraph does not mean its router is wired.

## Documentation rules

Create docs lazily — only when there is something real to record.

- A domain term is settled → update `CONTEXT.md`. Keep it a glossary only: no
  implementation details, no spec, no scratch notes.
- A decision that is hard to reverse AND surprising without context AND the result
  of a real trade-off → add an ADR to `docs/decisions/` (next sequential number,
  short title + 1–3 sentences).
- Issues, PRDs, and progress/task lists go to Jira Tasks, never into markdown
  under `docs/` by default.
- Exception: when the user or repo owner explicitly asks for implementation-facing
  working docs so human contributors can understand or execute a task, the agent
  may create or update supplemental markdown under `docs/<owner-or-team>/...`.
  Treat these files as temporary working docs, not canonical domain docs or issue
  tracker replacements.

Default layout:

```
/CONTEXT.md            glossary
/docs/agents/          skill config (issue-tracker, triage-labels, domain)
/docs/decisions/       ADRs
```

Allowed exception layouts (explicit user approval):

```
/docs/<owner-or-team>/...      supplemental implementation-facing working docs
/docs/project/                 product strategy, foundation, gap analysis, change plans
```

## Git: branch, commit, push, PR

Trigger: when the user says "commit", "push", "đẩy code", "tạo branch", "mở PR",
"tạo pull request" (or equivalent), run this full workflow autonomously end-to-end
without asking for confirmation at each step. Constraints that always hold:

- Never commit or push to `main`. Always work on a branch.
- Only create commits when the user asks for it (the trigger above counts as asking).
- Never run destructive git (`push --force`, `reset --hard`, `clean -f`, branch -D)
  unless the user explicitly requests it.
- Flag any file that looks like it holds secrets (`.env`, credentials) before staging.

Branch — always cut from fresh `main`:

```bash
git checkout main && git pull origin main
git checkout -b <type>/<short-english-desc>
```

`<type>` ∈ `feature|fix|chore|refactor|docs|hotfix`. Name: lowercase English,
`-`-separated, 2–4 words. No personal names, Vietnamese, underscores, or capitals.

Commit — atomic, stage explicit files (avoid `git add .`):

```bash
git add <files>
git commit -m "<type>(<scope>): <imperative english summary>"
```

`<type>` ∈ `feat|fix|docs|refactor|chore|test|perf|style`. `<scope>` ∈
`identity|employee|gmail|recruitment|attendance|payroll|self-service|frontend|ui|infra|migrations|decisions`.
Summary: imperative, lowercase, < 72 chars. E.g. `feat(payroll): add tax calc for dependents`.

Push + PR — rebase first, set upstream, open PR with What/Why/Testing:

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

PR title uses the commit format. Squash merge. Requires ≥1 approval + passing CI.

## Domain invariants

- All API routes are prefixed `/api/`.
- Auth uses httpOnly secure cookies (`access_token`, `refresh_token`), not Bearer headers.
- Employees are soft-deleted via the `is_active` flag.
- Every admin action must write an audit log.
- OAuth tokens are encrypted AES-256-GCM.
- Vietnamese tax: personal deduction 11M VND/month, dependent 4.4M/person.
- Insurance (employee): 10.5% = BHXH 8% + BHYT 1.5% + BHTN 1%.
- Salary uses 26 work days/month.

## Backend & dev environment

- New backend code follows the module layout `api/ → application/ → domain/ →
infrastructure/` with `container.py` for DI, matching existing modules.

## Agent skills config

- Issue tracker: Jira Tasks via Atlassian MCP → `docs/agents/issue-tracker.md`.
- Triage labels: five canonical roles, default strings → `docs/agents/triage-labels.md`.
- Domain docs: single-context, `CONTEXT.md` + `docs/decisions/` → `docs/agents/domain.md`.
- Code review (OCR): Open Code Review (OCR) CLI instructions → `docs/ocr.md`.
- Code review workflow: Jira-GitHub PR integration via OCR → `docs/agents/code-review.md`.

## Agent skills

### Issue tracker

Jira Tasks via Atlassian MCP. See `docs/agents/issue-tracker.md`.

PRD parents and implementation slices use different names:

- parent spec / PRD ticket: prefix summary with `[PRD]` or `[Spec]`
- implementation slice: prefix summary with `[Slice]`
- do not treat parent PRD ticket as implementation work

Quick Jira checks:

- Natural-language shortcut: `check task` / `xem task trên jira` lists recent
  Jira Tasks in `KAN`.
- Keyed shortcut: `check task KAN-11 bằng mcp jira` reads that specific task.
- Fast path for unkeyed checks: call Atlassian MCP `searchJiraIssuesUsingJql`
  directly with `project = KAN ORDER BY created DESC`. Do not browse, scan source,
  ask for a key, or list MCP tools first.
- Fast path for keyed checks: call Atlassian MCP `getJiraIssue` directly with
  `cloudId: "https://nullnyx.atlassian.net/"`, `issueIdOrKey: "KAN-11"`, fields
  `summary`, `description`, `status`, `labels`, `comment`, `assignee`,
  `issuelinks`, `created`, `updated`, `issuetype`, `priority`, `reporter`, and
  `responseContentFormat: "markdown"`.
- When creating Jira Tasks through Atlassian MCP, do not trust labels passed at
  create time to persist. After each `createJiraIssue`, immediately re-read or
  patch the issue with `editJiraIssue` and verify the `labels` field contains
  the expected values.
- If direct Atlassian tools are unavailable, fallback to the configured
  `atlassian` MCP server through `mcp-remote` and call `tools/call` with
  `name: "searchJiraIssuesUsingJql"` for unkeyed checks or `name: "getJiraIssue"`
  for keyed checks; only list tools/resources while diagnosing fallback.
- List tasks via JQL: call `searchJiraIssuesUsingJql` with
  `project = KAN ORDER BY created DESC`.

### Triage labels

Five canonical roles; labels use the default strings. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: root `CONTEXT.md` + `docs/decisions/`. See `docs/agents/domain.md`.
