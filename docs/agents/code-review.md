# Jira-PR Code Review Integration via OCR

This guide defines how the Agent should integrate Jira Task requirements with GitHub Pull Request reviews using the Open Code Review (OCR) CLI.

> [!IMPORTANT]
> Tất cả các nhận xét, phản hồi review (bao gồm inline comments trên GitHub, review summary, và bình luận trên Jira task) nên được viết bằng **tiếng Việt**, ngoại trừ các thuật ngữ kỹ thuật tiếng Anh (ví dụ: endpoint, database query, validation, test suite, mock...).


## Trigger

When the user requests a code review matching a GitHub PR to a Jira Task, e.g.:
- "Review PR #12 đối chiếu với Jira task KAN-45"
- "ocr review PR 15 check against KAN-22 requirements"

Follow this sequence of steps to execute the review.

---

## 1. Retrieve Jira Task Context

Call the Atlassian MCP tool `getJiraIssue` for the specified Jira Task ID (e.g., `KAN-45`).
Extract the following sections from the Jira issue description:
*   `## Output cần đạt` (Expected Outputs)
*   `## Acceptance criteria` (Acceptance Criteria)

These sections serve as the business context for the code review.

---

## 2. Retrieve GitHub Pull Request Context

Call the GitHub MCP tools to fetch the PR details:
*   Use `get_pull_request` to fetch general PR information (source/target branches, title).
*   Use `get_pull_request_files` to identify the modified files and obtain the diff.

---

## 3. Generate Dynamic Review Rules

Before running OCR, generate a temporary rules JSON file at `.opencodereview/temp_jira_rules.json` to instruct the LLM on specific criteria it must verify. 

Format the JSON file as follows:

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

## 4. Run Open Code Review (OCR)

Run the OCR CLI command using the custom rules:

```bash
ocr review --rule .opencodereview/temp_jira_rules.json
```

Or run using business context directly if rules are not needed:

```bash
ocr review -b "Requirements from Jira: [INSERT REQUIREMENTS HERE]"
```

*Note: Clean up the `.opencodereview/temp_jira_rules.json` file after execution is complete.*

---

## 5. Report Findings

After OCR generates the review results, automate the reporting:

### A. Post Review to GitHub
Call the GitHub MCP tool `create_pull_request_review` to:
*   Post inline comments for specific line changes if OCR identified issues.
*   Submit a global review summary indicating if the PR satisfies the Jira Task's requirements (APPROVE or REQUEST_CHANGES).

### B. Comment on Jira Task
Call the Atlassian MCP tool `addCommentToJiraIssue` to post a summary of the review results:
*   PR Link: Link to the GitHub PR.
*   Status: E.g., `Review completed - [Pass/Fail]`.
*   Key Findings: Bullet points summarizing the main feedback or blocks.
