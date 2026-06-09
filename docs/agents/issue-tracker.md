# Issue tracker: Jira

Issues, PRDs, and implementation tasks for this repo live as Jira Tasks in the
`KAN` project on `https://nullnyx.atlassian.net/`. Use Atlassian MCP for all Jira
operations.

## Fast path for checking tasks

When the user says "check task", "check tasks", "xem task trên Jira", or similar
without a Jira key, treat it as a request to list Jira Tasks in `KAN`. Do not ask
for a key first. Call Atlassian MCP directly:

- Tool: `searchJiraIssuesUsingJql`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `jql`: `project = KAN ORDER BY created DESC`
- `maxResults`: `10`
- `fields`: `summary`, `status`, `labels`, `assignee`, `created`, `updated`,
  `issuetype`, `priority`
- `responseContentFormat`: `markdown`

When the user includes a Jira key, e.g. `KAN-8` or `KAN-08`, treat it as a request
to read that specific task. Do not browse the web, scan source code, or list MCP
tools first. Call Atlassian MCP directly:

- Tool: `getJiraIssue`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `issueIdOrKey`: the requested key, e.g. `KAN-8` or `KAN-08`
- `fields`: `summary`, `description`, `status`, `labels`, `comment`, `assignee`,
  `issuelinks`, `created`, `updated`, `issuetype`, `priority`, `reporter`
- `responseContentFormat`: `markdown`

If the direct call fails because the Atlassian tools are not exposed in the
current session, use the configured `atlassian` MCP server through `mcp-remote`
and call `tools/call` with `name: "searchJiraIssuesUsingJql"` for list requests
or `name: "getJiraIssue"` for keyed reads. Only list tools or resources when
diagnosing that fallback.

## Conventions

- **Create a task**: use Jira project key `KAN`, issue type `Task`, and a concise
  English summary. Leave assignee empty unless the user explicitly provides one.
- **Read a task**: fetch by Jira key, e.g. `KAN-14`, including description,
  status, labels, comments, assignee, and linked issues.
- **List tasks**: use JQL through Atlassian MCP. Common filters:
  - `project = KAN ORDER BY created DESC`
  - `project = KAN AND statusCategory != Done ORDER BY created DESC`
  - `project = KAN AND labels = ready-for-agent ORDER BY created DESC`
- **Comment on a task**: add a Jira comment on the task key.
- **Apply labels**: update Jira labels. Use the strings in
  `docs/agents/triage-labels.md`.
- **Dependencies**: use Jira issue links. For directional links, use `Blocks` so
  the blocker blocks the dependent task.
- **Close / transition**: transition the Jira task only when explicitly asked or
  when a triage workflow says to do so.

## Task body shape

When a skill says "publish issues" or "create implementation tickets", create
Jira Tasks with this structure:

```markdown
## What to build

## Context

## Output cần đạt

## Acceptance criteria

- [ ] ...

## Codex workflow

## Blocked by
```

Keep task descriptions implementation-guiding but not code-stale: mention domain
terms, APIs, acceptance boundaries, tests, and relevant ADRs; avoid long file-path
lists unless the path is the actual subject of the task.

## When a skill says "publish to the issue tracker"

Create Jira Tasks in project `KAN`, not GitHub Issues.

## When a skill says "fetch the relevant ticket"

Read the Jira task by key, e.g. `KAN-14`.

## Atlassian MCP note

The older `https://mcp.atlassian.com/v1/sse` transport is deprecated after
2026-06-30. Prefer `https://mcp.atlassian.com/v1/mcp` when configuring MCP
clients that support the newer transport.
