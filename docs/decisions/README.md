# Decisions

Decision records explain why important product or architecture choices were made.

## Source of truth

- `docs/design-docs/` holds draft direction, gaps, and review material. HR-only scope there wins over stale employee wording in working docs.
- `docs/decisions/` holds only locked choices with lasting impact.
- `CONTEXT.md` holds canonical glossary terms.

## When to add ADR

Use ADR format from `grill-with-docs` when a choice becomes real and hard to reverse:
short title plus 1–3 sentences: context, what was decided, why. Number files sequentially (`0008-slug.md`, ...).

Add a decision when:

- A locked technical choice changes.
- A product rule changes meaningfully.
- A validation requirement is added, removed, or weakened.
- A high-risk feature chooses one design over another.
- The source-of-truth hierarchy changes.

## Rule of thumb

If a note is still being debated, keep it in design docs. If teams must code to it for the foreseeable future, write ADR.
