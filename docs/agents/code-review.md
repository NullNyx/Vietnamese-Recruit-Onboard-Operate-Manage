# Tích hợp Jira-PR Code Review qua skill `code-review`

Hướng dẫn cách Agent review GitHub PR đối chiếu Jira Task dùng skill
`code-review` đã cài từ skill list.

> [!IMPORTANT]
> Tất cả nhận xét, phản hồi review (gồm inline comments trên GitHub, review
> summary, và bình luận trên Jira task) viết bằng **tiếng Việt**, ngoại trừ
> thuật ngữ kỹ thuật tiếng Anh.

## Kích hoạt

Khi user yêu cầu code review đối chiếu GitHub PR với Jira Task:
- "Review PR #12 đối chiếu với Jira task KAN-45"
- "Review changes since main against KAN-22 requirements"

Chạy theo trình tự các bước sau.

## 1. Lấy ngữ cảnh Jira Task

Gọi Atlassian MCP tool `getJiraIssue` cho Jira Task ID.
Trích xuất từ mô tả issue:
- `## Output cần đạt`
- `## Acceptance criteria`

Các phần này làm ngữ cảnh nghiệp vụ cho code review.

## 2. Xác định điểm so sánh

Dùng GitHub MCP tools:
- `get_pull_request` lấy thông tin PR (source/target branches, title).
- `get_pull_request_files` xác định file đã sửa.

Điểm so sánh: `merge-base` giữa source branch và target branch,
hoặc commit range của PR.

## 3. Chạy skill `code-review`

Skill code-review đã cài sẵn. Nó review changes từ một điểm cố định
(commit, branch, tag, merge-base) theo hai trục:
- **Standards**: code có theo coding standards của repo không.
- **Spec**: code có đáp ứng yêu cầu từ issue/PRD không.

Cách gọi: agent đọc skill `code-review` và làm theo hướng dẫn trong skill.

## 4. Báo cáo kết quả

### A. Đăng Review lên GitHub
Gọi GitHub MCP tool `create_pull_request_review`:
- Inline comments cho findings cụ thể.
- Review summary tổng thể: APPROVE / REQUEST_CHANGES.

### B. Bình luận trên Jira Task
Gọi Atlassian MCP tool `addCommentToJiraIssue`:
- PR Link
- Status: `Review completed - [Pass/Fail]`
- Key Findings: gạch đầu dòng chính
