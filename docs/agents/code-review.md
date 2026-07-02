# Tích hợp Jira-PR Code Review qua OCR

Hướng dẫn này định nghĩa cách Agent tích hợp yêu cầu Jira Task với GitHub Pull
Request review dùng Open Code Review (OCR) CLI.

> [!IMPORTANT]
> Tất cả nhận xét, phản hồi review (gồm inline comments trên GitHub, review
> summary, và bình luận trên Jira task) viết bằng **tiếng Việt**, ngoại trừ
> thuật ngữ kỹ thuật tiếng Anh (ví dụ: endpoint, database query, validation,
> test suite, mock...).

## Kích hoạt

Khi user yêu cầu code review đối chiếu GitHub PR với Jira Task, ví dụ:
- "Review PR #12 đối chiếu với Jira task KAN-45"
- "ocr review PR 15 check against KAN-22 requirements"

Chạy theo trình tự các bước sau.

---

## 1. Lấy ngữ cảnh Jira Task

Gọi Atlassian MCP tool `getJiraIssue` cho Jira Task ID (vd `KAN-45`).
Trích xuất các phần sau từ mô tả issue:
*   `## Output cần đạt`
*   `## Acceptance criteria`

Các phần này làm ngữ cảnh nghiệp vụ cho code review.

---

## 2. Lấy ngữ cảnh GitHub Pull Request

Gọi GitHub MCP tools để lấy chi tiết PR:
*   Dùng `get_pull_request` lấy thông tin chung (source/target branches, title).
*   Dùng `get_pull_request_files` xác định file đã sửa và lấy diff.

---

## 3. Tạo Dynamic Review Rules

Trước khi chạy OCR, tạo file rules JSON tạm tại
`.opencodereview/temp_jira_rules.json` để hướng dẫn LLM tiêu chí cần kiểm tra.

File JSON có format:

```json
{
  "rules": [
    {
      "path": "**/*",
      "rule": "Verify that the code changes in this Pull Request satisfy the following requirements from Jira:\n\n[INSERT EXTRACTED OUTPUT CẦN ĐẠT AND ACCEPTANCE CRITERIA HERE]"
    }
  ]
}
```

---

## 4. Chạy Open Code Review (OCR)

Chạy OCR CLI với custom rules:

```bash
ocr review --rule .opencodereview/temp_jira_rules.json
```

Hoặc dùng business context trực tiếp nếu không cần rules:

```bash
ocr review -b "Requirements from Jira: [INSERT REQUIREMENTS HERE]"
```

*Lưu ý: Xoá file `.opencodereview/temp_jira_rules.json` sau khi chạy xong.*

---

## 5. Báo cáo kết quả

Sau khi OCR tạo kết quả review, báo cáo tự động:

### A. Đăng Review lên GitHub
Gọi GitHub MCP tool `create_pull_request_review` để:
*   Đăng inline comments cho các dòng cụ thể nếu OCR phát hiện vấn đề.
*   Gửi review summary tổng thể chỉ ra PR có đáp ứng yêu cầu Jira Task hay không
    (APPROVE hoặc REQUEST_CHANGES).

### B. Bình luận trên Jira Task
Gọi Atlassian MCP tool `addCommentToJiraIssue` để đăng tóm tắt kết quả review:
*   PR Link: Link đến GitHub PR.
*   Status: Ví dụ `Review completed - [Pass/Fail]`.
*   Key Findings: Danh sách gạch đầu dòng tóm tắt phản hồi chính hoặc block.
