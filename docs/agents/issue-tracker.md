# Issue tracker: Jira

Issue, PRD, và task implementation của repo này đều là Jira Tasks trong project `KAN`.
Dùng Atlassian MCP cho mọi thao tác Jira.

## Workflow từ docs

Khi làm việc từ `docs/design-docs/`:

- `grill-with-docs` giải quyết gap glossary / quyết định.
- `to-prd` biến hướng đi đã chốt thành văn bản PRD.
- `to-issues` biến PRD thành Jira Tasks.
- `triage` áp dụng nhãn / routing.

Không nhảy từ bản nháp thẳng tới ticket nếu từ ngữ hoặc scope chưa ổn định.

## Đường nhanh kiểm tra task

Khi user nói "check task", "check tasks", "xem task trên Jira", hoặc tương tự
mà không có Jira key, liệt kê Jira Tasks trong `KAN`. Không hỏi key trước.
Gọi Atlassian MCP trực tiếp:

- Tool: `searchJiraIssuesUsingJql`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `jql`: `project = KAN ORDER BY created DESC`
- `maxResults`: `10`
- `fields`: `summary`, `status`, `labels`, `assignee`, `created`, `updated`, `issuetype`, `priority`
- `responseContentFormat`: `markdown`

Khi user có Jira key, ví dụ `KAN-8` hoặc `KAN-08`, đọc task đó trực tiếp.
Không duyệt web, scan source, hay liệt kê MCP tools trước.

- Tool: `getJiraIssue`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `issueIdOrKey`: key được yêu cầu
- `fields`: `summary`, `description`, `status`, `labels`, `comment`, `assignee`, `issuelinks`, `created`, `updated`, `issuetype`, `priority`, `reporter`
- `responseContentFormat`: `markdown`

Nếu gọi trực tiếp lỗi, dùng server `atlassian` MCP đã cấu hình qua `mcp-remote`
và gọi `tools/call` với `searchJiraIssuesUsingJql` hoặc `getJiraIssue`.
Chỉ liệt kê tools/resources khi đang chẩn đoán fallback.

## Quy ước

- Tạo task: Jira project key `KAN`, issue type `Task`, summary tiếng Anh ngắn gọn.
- Đọc task: lấy theo key kèm description, status, labels, comments, assignee, linked issues.
- Liệt kê task: JQL qua Atlassian MCP.
- Bình luận: thêm Jira comment trên task key.
- Áp dụng nhãn: dùng chuỗi trong `docs/agents/triage-labels.md`.
- Phụ thuộc: dùng Jira issue links; directional links dùng `Blocks`.
- Đóng / chuyển trạng thái: chỉ khi được yêu cầu rõ ràng hoặc triage workflow yêu cầu.

## Cấu trúc task body

Khi skill nói "publish issues" hoặc "create implementation tickets", tạo Jira Tasks
với cấu trúc này:

```markdown
## What to build

## Context

## Output cần đạt

## Acceptance criteria
- [ ] ...
## Codex workflow
## Blocked by
```

Giữ mô tả task ở mức hướng dẫn implementation nhưng không lỗi thời với code:
nhắc domain terms, APIs, ranh giới acceptance, test, và ADR liên quan; tránh
danh sách đường dẫn file dài trừ khi đường dẫn là chủ đề thực sự.

## Quy ước đặt tên PRD parent vs implementation slices

Khi PRD được publish thành Jira issue và sau đó chia thành các implementation work:

- Dùng prefix summary ticket cha kiểu `[PRD]` hoặc `[Spec]`.
- Dùng prefix ticket implementation con kiểu `[Slice]`.
- Coi ticket cha là scope/spec chỉ khi user yêu cầu implement chính ticket đó.
- Slice con nên là lát cắt dọc hẹp mà agent AFK có thể nhặt độc lập.

## Khi skill nói "publish to the issue tracker"

Tạo Jira Tasks trong project `KAN`, không phải GitHub Issues.

## Khi skill nói "fetch the relevant ticket"

Đọc Jira task theo key, ví dụ `KAN-14`.

## Lưu ý Atlassian MCP

Transport cũ `https://mcp.atlassian.com/v1/sse` đã deprecated sau 2026-06-30.
Ưu tiên `https://mcp.atlassian.com/v1/mcp` khi cấu hình MCP client hỗ trợ
transport mới hơn.
