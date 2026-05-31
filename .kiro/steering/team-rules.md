---
inclusion: always
---

# Team Rules — Quy Tắc Cho AI Agent

## ⛔ KHÔNG được làm

1. **KHÔNG tạo file docs tùy tiện** trong `docs/`. Thư mục `docs/` có cấu trúc cố định:
   - `docs/agents/` — Agent skill config (issue tracker, triage labels, domain docs)
   - `docs/decisions/` — Architecture Decision Records (ADRs)
   - `CONTEXT.md` (root) — Domain glossary (canonical terms)

2. **KHÔNG tạo thư mục mới** trong `docs/` mà không có lý do rõ ràng.
   - ❌ `docs/cham-cong-nghi-phep/` — SAI (không theo format)
   - ❌ `docs/my-feature-notes/` — SAI
   - ✅ `docs/decisions/0008-payroll-tax-formula.md` — ĐÚNG

3. **KHÔNG viết tiến độ/task list** lan man vào markdown files trong `docs/`.
   - ❌ Tạo file `tien-do-xxx.md` với checklist
   - ✅ Theo dõi công việc bằng issue tracker (GitHub Issues) / PR

4. **KHÔNG nhồi implementation details / hướng dẫn sử dụng vào `CONTEXT.md`.**
   `CONTEXT.md` chỉ là glossary — định nghĩa term, không phải spec hay scratch pad.

## ✅ PHẢI làm

1. **Khi cần ghi lại quyết định kiến trúc**, tạo ADR:
   - Decision → `docs/decisions/<NNNN>-<slug>.md`
   - Chỉ tạo ADR khi quyết định: khó đảo ngược + gây bất ngờ nếu thiếu context + là kết quả của một trade-off thật.

2. **Khi một domain term được chốt**, cập nhật `CONTEXT.md` (root) — một từ cho một khái niệm.

3. **Tuân thủ module architecture** khi tạo code mới:

   ```
   backend/src/modules/<module>/
   ├── api/        (routers, schemas, error_handler)
   ├── application/(services)
   ├── domain/     (entities, enums, exceptions)
   ├── infrastructure/ (repos, configs, clients)
   └── container.py
   ```

4. **Commit message** phải rõ ràng:
   - `feat(payroll): add tax calculation for dependents`
   - `fix(attendance): correct overtime hours query`
   - `docs(decisions): add adr for payroll tax formula`

## 📁 Cấu trúc docs/ hợp lệ

```
/
├── CONTEXT.md        ← Domain glossary (canonical terms)
└── docs/
    ├── agents/       ← Agent skill config (issue tracker, triage labels, domain docs)
    └── decisions/    ← ADRs (architecture decisions)
```

Bất kỳ thư mục/file nào ngoài cấu trúc trên đều cần được di chuyển hoặc xóa.

## 🔧 Workflow docs (Matt Pocock skills)

Project dùng bộ engineering skills (`grill-me`, `grill-with-docs`, `to-issues`,
`triage`, ...). Docs được tạo **lazily** trong lúc grilling:

- Term được chốt → cập nhật `CONTEXT.md`
- Quyết định kiến trúc thật sự → tạo ADR trong `docs/decisions/`
- Issue / PRD → GitHub Issues (xem `docs/agents/issue-tracker.md`)
