# Issue tracker: Jira

Issues, PRDs, and implementation tasks for this repo live as Jira Tasks in `KAN`.
Use Atlassian MCP for all Jira operations.

## Workflow from docs

When working from `docs/design-docs/`:

- `grill-with-docs` resolves glossary / decision gaps.
- `to-prd` turns settled direction into PRD text.
- `to-issues` turns PRD into Jira Tasks.
- `triage` applies labels / routing.

Do not skip straight from draft to tickets if wording or scope is still unsettled.

## Fast path for checking tasks

When user says "check task", "check tasks", "xem task trên Jira", or similar without a Jira key, list Jira Tasks in `KAN`. Do not ask for a key first. Call Atlassian MCP directly:

- Tool: `searchJiraIssuesUsingJql`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `jql`: `project = KAN ORDER BY created DESC`
- `maxResults`: `10`
- `fields`: `summary`, `status`, `labels`, `assignee`, `created`, `updated`, `issuetype`, `priority`
- `responseContentFormat`: `markdown`

When user includes Jira key, e.g. `KAN-8` or `KAN-08`, read that task directly. Do not browse web, scan source, or list MCP tools first.

- Tool: `getJiraIssue`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `issueIdOrKey`: requested key
- `fields`: `summary`, `description`, `status`, `labels`, `comment`, `assignee`, `issuelinks`, `created`, `updated`, `issuetype`, `priority`, `reporter`
- `responseContentFormat`: `markdown`

If direct call fails, use configured `atlassian` MCP server through `mcp-remote` and call `tools/call` with `searchJiraIssuesUsingJql` or `getJiraIssue`. Only list tools/resources when diagnosing fallback.

## Conventions

- Create task: Jira project key `KAN`, issue type `Task`, concise English summary.
- Read task: fetch by key with description, status, labels, comments, assignee, linked issues.
- List tasks: JQL through Atlassian MCP.
- Comment: add Jira comment on task key.
- Apply labels: use strings in `docs/agents/triage-labels.md`.
- Dependencies: use Jira issue links; directional links use `Blocks`.
- Close / transition: only when explicitly asked or triage workflow says so.

## Task body shape

When a skill says "publish issues" or "create implementation tickets", create Jira Tasks with this structure:

```markdown
## What to build

## Context

## Output cần đạt

## Acceptance criteria
- [ ] ...
## Codex workflow
## Blocked by
```

Keep task descriptions implementation-guiding but not code-stale: mention domain terms, APIs, acceptance boundaries, tests, and relevant ADRs; avoid long file-path lists unless path is actual subject.

## Naming convention for PRD parents vs implementation slices

When a PRD is published as a Jira issue and later split into implementation work:

- Use a parent ticket summary prefix like `[PRD]` or `[Spec]`.
- Use child implementation ticket summary prefix like `[Slice]`.
- Treat the parent as scope/spec only unless the user explicitly asks to implement the parent ticket itself.
- Child slices should be narrow vertical cuts that an AFK agent can pick up independently.

## When a skill says "publish to the issue tracker"

Create Jira Tasks in project `KAN`, not GitHub Issues.

## When a skill says "fetch the relevant ticket"

Read the Jira task by key, e.g. `KAN-14`.

## Atlassian MCP note

The older `https://mcp.atlassian.com/v1/sse` transport is deprecated after 2026-06-30. Prefer `https://mcp.atlassian.com/v1/mcp` when configuring MCP clients that support the newer transport.
