# Domain Docs

Cách skill engineering tiêu thụ domain docs khi khám phá codebase.

## Thứ tự nguồn

1. `CONTEXT.md` — từ điển thuật ngữ chuẩn.
2. `docs/decisions/` — ADR cho các quyết định đã chốt và tradeoff thực sự.
3. `docs/prd/` — PRD theo slice khi phase phân rã bắt đầu (nếu có).
4. `docs/agents/main-flow.md` — lớp điều phối từ idea tới ship.

Nếu thiếu file nào, cứ tiếp tục im lặng. Không tự chế tài liệu hay yêu cầu user tạo trước.

## Cấu trúc file

Repo single-context:

```
/
├── CONTEXT.md
├── docs/
│   ├── decisions/
│   └── prd/
└── backend/ , frontend/
```

Không có `CONTEXT-MAP.md` và không có file `CONTEXT.md` riêng theo context. Chỉ đọc `CONTEXT.md` gốc.

## Dùng từ vựng trong glossary

Khi output nhắc tới khái niệm domain, dùng term như định nghĩa trong `CONTEXT.md`. Tránh synonym bị cấm trong glossary.

Nếu khái niệm cần thiết chưa có trong glossary, coi là gap cho `/grill-with-docs`, không phải tìm synonym.

## Báo ADR xung đột

Nếu output mâu thuẫn với ADR, nêu rõ thay vì âm thầm ghi đè:

> _Mâu thuẫn với ADR-0021 (Product Identity and Work Taxonomy) — nhưng cần xem xét lại vì…_

## Quy tắc working-doc

`docs/design-docs/` đã retired. Chuyển quy tắc đã chốt vào `CONTEXT.md`,
`docs/decisions/` khi lựa chọn sản phẩm đã khóa. Không copy spec đầy đủ vào `docs/agents/`.

## Workflow từ decisions ra implement

Khi bắt đầu từ `docs/decisions/` để đi tới task implement, đi theo luồng này:

```text
docs/decisions/0021–0029
    │  ← decision layer: xác định WHAT và WHY
    ▼
docs/api/openapi.v1.skeleton.yaml
    │  ← contract frozen: xác định HOW (API shape)
    ▼
to-prd skill
    │  ← biến decision + contract thành PRD cho từng surface
    │     Work PRD, Inbox PRD, People PRD, Documents PRD, Contracts PRD, ...
    ▼
to-issues skill
    │  ← biến mỗi PRD thành Jira Task (KAN)
    │     Work: create + update + complete + archive + suggestion accept
    │     Inbox: ingest + triage + classify + dismiss
    │     People: CRUD + profile
    │     Document: upload + verify + reject + extraction
    │     Contract: draft + send + sign + terminate + amendment
    │     AI: suggestion create/reject + prompt + job
    ▼
implement skill
    │  ← code → gate (ruff, mypy, pytest) → push → PR
    │     thứ tự: service → handler → test → integration
```

Giải thích ngắn:

- `0021–0029` định nghĩa sản phẩm, trải nghiệm, capability, domain, service,
  data model, API shape.
- `to-prd` lấy ADR + OpenAPI skeleton để viết PRD cho từng surface.
- `to-issues` lấy PRD để tách Jira Tasks nhỏ, mỗi task gắn 1–2 service commands,
  có test và gate kèm theo.
- `implement` nhặt task AFK, code theo OpenAPI contract, chạy gate, push PR.

Mấu chốt:

- Decisions không tự thành task.
- Phải qua `to-prd` để rõ từng slice.
- Phải qua `to-issues` để bẻ ra command nhỏ cho agent nhặt.
- Implement luôn bám `CONTEXT.md` + ADR liên quan + OpenAPI contract.
