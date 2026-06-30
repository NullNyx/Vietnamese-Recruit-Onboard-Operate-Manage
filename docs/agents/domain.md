# Domain Docs

How engineering skills should consume repo domain docs when exploring codebase.

## Source order

1. `CONTEXT.md` — canonical glossary.
2. `docs/design-docs/` — working docs reviewed by `grill-with-docs`, `to-prd`, `to-issues`, and follow-up skills. Treat HR-only scope here as source over stale employee wording elsewhere.
3. `docs/decisions/` — ADRs for locked choices and real tradeoffs.

If any file missing, proceed silently. Do not invent docs or ask user to create them upfront.

## File structure

Single-context repo:

```
/
├── CONTEXT.md
├── docs/
│   ├── design-docs/
│   └── decisions/
└── backend/ , frontend/
```

There is no `CONTEXT-MAP.md` and no per-context `CONTEXT.md` files. Read root `CONTEXT.md` only.

## Use glossary vocabulary

When output names domain concept, use term as defined in `CONTEXT.md`. Avoid glossary-banned synonyms.

If needed concept missing from glossary, treat as gap for `/grill-with-docs`, not a synonym search.

## Flag ADR conflicts

If output contradicts ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0005 (remove policy engine) — but worth reopening because…_

## Working-doc rule

`docs/design-docs/` is draft space only. Turn settled rules into `CONTEXT.md` or `docs/decisions/` when product choice is locked. Do not duplicate full specs in `docs/agents/`.