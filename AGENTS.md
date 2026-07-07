# AGENTS.md — HR Space (project supplement)

File overlay. Global rule ở `~/.codex/AGENTS.md`. File này chỉ chứa supplement cho repo.

## Project identity

HR Space: AI-powered HR operations work system, không phải HRM Suite.
Stack: FastAPI + SQLModel + PostgreSQL 15 + Redis 7 (Python 3.11+, MyPy strict,
Ruff line-length 100) · Next.js 14 + TypeScript + pnpm + Tailwind + shadcn/ui ·
cookie-based JWT auth · MinIO storage · pytest+Hypothesis / Vitest+fast-check.

## Luôn làm trước

Đọc theo thứ tự này trước khi code. Không nhảy bước.

1. `CONTEXT.md` — glossary, canonical terms. Không synonym.
2. ADR liên quan trong `docs/decisions/0021–0029`. Báo nếu mâu thuẫn — không âm thầm ghi đè.
3. `docs/agents/main-flow.md` — nguyên lý điều phối idea -> ship.
4. `docs/agents/domain.md` — workflow từ decisions ra implement.
5. `docs/agents/issue-tracker.md` — quy trình thực thi task Jira.
6. `docs/api/openapi.v1.skeleton.yaml` — nếu task chạm API/route.

## Scope baseline

- Product Identity: HR operations work system (ADR 0021).
- WorkItem là trung tâm, không phải Employee. Work queue–first (ADR 0022–0023).
- HR-only actor: HR admin/staff dùng system, employee không login, không self-service.
- Phase 1 baseline đã chốt qua ADR 0021–0029. Implementation slice đi từ PRD → Jira task.
- Capability-driven: Work, Inbox, Context Libraries (People/Documents/Contracts/Templates),
  AI Assist, Reports, Admin (ADR 0024).
- Domain model v4 baseline: WorkItem, InboxItem, People + profile extensions, Document,
  Contract, Template, AISuggestion, PromptRun, AIJob (ADR 0025).
- Service boundary + Data Model đã chốt (ADR 0026–0027).
- API v1 contract frozen, OpenAPI skeleton valid (ADR 0028–0029).

## Domain invariants

- API prefix `/api/v1/`. Auth dùng httpOnly cookies (`access_token`, `refresh_token`).
- People soft-delete via status (active/inactive/archived). Không xoá cứng record any entity.
- Mọi admin action ghi audit log (AuditEvent, cùng transaction với mutation).
- AI suggestion không tự ghi — human confirm qua target service.
- organization_id có trên mọi aggregate root; single-tenant MVP.
- Controlled typed reference cho Note, Notification, Audit, AISuggestion.

## Backend conventions

Module layout: `api/ → application/ → domain/ → infrastructure/` + `container.py`.
Xem `backend/AGENTS.md` cho migration map, data flow.

`backend/AGENTS.md` chỉ supplement layout/data flow. Không override repo-level rules trong file này.

## Source of truth

- `docs/decisions/0021–0029`: Product Identity → API contract.
- `docs/agents/main-flow.md`: main flow, on-ramp, context hygiene.
- `docs/api/openapi.v1.skeleton.yaml`: API contract frozen.
- `backend/src/main.py`: routed endpoints (có thể chưa đồng bộ với contract mới).
- `CONTEXT.md`: glossary terms (đã đồng bộ scope mới).
- `docs/agents/domain.md`: workflow từ decisions ra implement.
- `docs/agents/issue-tracker.md`: quy trình thực thi task Jira.
- Jira Tasks (KAN), `git log --oneline -20`.

## Implement task Jira

1. Đọc task Jira → `docs/agents/issue-tracker.md` (Bước 1–2).
2. Code → gate: backend `ruff check && mypy && pytest`, frontend `pnpm lint && pnpm test && pnpm build`. UI thêm browser QA.
3. Branch, commit, push, PR (dùng global git rules).
4. Review sau PR → self-review, đối chiếu task/ADR, sửa theo feedback (theo `docs/agents/issue-tracker.md` Bước 6).
5. Theo dõi CI → verify pass → link PR cho user.
6. Báo Jira comment sau push / review update (theo issue-tracker.md Bước 7).
7. Không tự merge / approve / chuyển Jira Done.

Chi tiết từng bước đã có trong `docs/agents/issue-tracker.md`. File này chỉ routing, không copy.

## FE sub-workflow (trong implement)

Thứ tự bắt buộc. Không nhảy bước.

1. **Đọc `docs/design/README.md`** để hiểu quy ước và workflow.
2. **Đọc `CONTEXT.md` + ADR 0021–0029 + Jira task + `docs/design/notes.md`** (nếu có) để hiểu hệ thống.
3. **Brainstorm design** với user / PRD / slice — chốt UX flow, user goals, pain points.
4. **Chốt format gốc** (design grammar) trong Pencil `.pen` file tại `docs/design/`.
   - `docs/design/system.pen` cho component library, tokens, shell.
   - `docs/design/system.pen` cho showcase canvas, không phải source ref từ screen.
   - `docs/design/screens/*.pen` cho từng surface.
5. **User review + approve** — không code FE khi chưa approve.
6. **Implement BE** theo API contract nhìn từ tổng thể design.
7. **Implement FE** bám design y nguyên — agent không tự suy diễn layout/màu/hierarchy.
8. **QA browser** → `frontend-testing-debugging` (Playwright screenshots, console, a11y, viewports).

Tool routing trong quá trình:
- `grill-with-docs` / `prototype` (UI branch): chốt yêu cầu UX, test variation khi cần.
- `ui-ux-pro-max`: gợi ý style/color/typography, không thay thế pencil design.
- `pencil`: công cụ thiết kế chính cho system + screens.
- `frontend-app-builder`: chỉ dùng concept/redesign lớn bằng Image Gen, không thay pencil.
- `shadcn`: compose component khi implement FE code.
- `react-best-practices`: perf pattern sau implement.
- `frontend-testing-debugging`: QA browser so khớp design.

**Rule cứng:** agent không code FE nếu chưa có design `.pen` đã approve trong `docs/design/`.

## Agent skills routing

- Main flow: `docs/agents/main-flow.md`
- Issue tracker: Jira KAN → `docs/agents/issue-tracker.md`
- Triage labels: canonical roles → `docs/agents/triage-labels.md`
- Domain docs: single-context → `docs/agents/domain.md`

Nội dung chi tiết JQL fast-path, label mapping, domain-doc order đã có
trong các file `docs/agents/*`. File AGENTS.md chỉ routing, không copy.
