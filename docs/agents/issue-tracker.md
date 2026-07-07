# Issue tracker: Jira

Issue, PRD, và implementation slice của repo này đều là Jira Tasks trong project `KAN`.
Dùng Atlassian MCP (`atlassian` server) cho mọi thao tác Jira.

## Quy ước chung

- Tạo task: project key `KAN`, issue type `Task`, summary tiếng Việt ngắn gọn.
- Đọc task: lấy description + status + labels + comments + assignee + linked issues.
- Bình luận: `addCommentToJiraIssue` trên task key.
- Nhãn: dùng mapping trong `docs/agents/triage-labels.md`.
- Phụ thuộc: Jira issue links; directional dùng `Blocks`.
- Đóng / chuyển status: chỉ khi được yêu cầu rõ ràng. Agent không tự chuyển.

## Đường nhanh kiểm tra task

Khi user nói "check task", "xem task", hoặc tương tự mà không có key,
liệt kê tasks trong `KAN`. Không hỏi key trước.

- Tool: `searchJiraIssuesUsingJql`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `jql`: `project = KAN ORDER BY created DESC`
- `maxResults`: 10
- `fields`: `summary`, `status`, `labels`, `assignee`, `created`, `updated`, `issuetype`, `priority`
- `responseContentFormat`: `markdown`

Khi user có key (VD `KAN-8`), đọc task đó trực tiếp. Không duyệt web, scan source, liệt kê tools.

- Tool: `getJiraIssue`
- `cloudId`: `https://nullnyx.atlassian.net/`
- `issueIdOrKey`: key
- `fields`: `summary`, `description`, `status`, `labels`, `comment`, `assignee`, `issuelinks`, `created`, `updated`, `issuetype`, `priority`, `reporter`
- `responseContentFormat`: `markdown`

Nếu gọi lỗi, fallback qua `server "atlassian" tools/call`.

---

## Tạo task Jira từ PRD hoặc issue thô

Khi đầu vào là PRD, brainstorm, hoặc yêu cầu mới chưa có task Jira:

1. **Kiểm trùng**
   - search Jira trong `KAN` trước.
   - nếu đã có task cùng scope, link vào task cũ thay vì tạo mới.
   - nếu ADR / PRD / design đã có downstream artifact đầy đủ và task chỉ lặp lại
     cùng scope, **không tạo task mới**; chỉ comment/đánh dấu task liên quan là done
     hoặc closed nếu nó đang là task theo dõi cùng phạm vi.
2. **Chọn nguồn**
   - PRD đã chốt → tạo các task con `[Slice]`.
   - idea lớn / scope reference → tạo task cha `[PRD]`.
   - issue thô từ ngoài vào → đi qua `triage` trước nếu cần xác minh.
3. **Viết body**
   - dùng [Cấu trúc issue body](#cấu-trúc-issue-body).
   - viết tiếng Việt, đủ để agent AFK implement.
   - giữ thuật ngữ kỹ thuật tiếng Anh nguyên văn khi cần.
4. **Tạo task**
   - project key `KAN`
   - issue type `Task`
   - summary ngắn, rõ scope
   - gắn label theo `docs/agents/triage-labels.md` nếu đã biết vai trò
5. **Liên kết nguồn**
   - nếu task sinh ra từ PRD hoặc issue cha, link Jira issue gốc vào phần `Blocked by` hoặc issue links.
   - nếu có phụ thuộc kỹ thuật, dùng `Blocks`.
6. **Báo lại nguồn**
   - comment vào PRD / issue nguồn: task key mới, scope, và trạng thái sẵn sàng cho `implement`.

Task tạo xong mới chuyển sang luồng `implement`.

---

## Luồng tổng: decisions → implement

```text
docs/decisions/0021–0029
    │  decision layer: WHAT và WHY
    ▼
docs/api/openapi.v1.skeleton.yaml
    │  contract frozen: HOW (API shape)
    ▼
to-prd skill
    │  → PRD cho từng surface (Work, Inbox, People, Documents, Contracts, ...)
    ▼
to-issues skill
    │  → Jira Tasks (KAN), mỗi task 1–2 service commands
    ▼
implement skill
    │  → code → gate → push → PR
```

- **to-prd**: Lấy ADR 0021–0029 + OpenAPI skeleton → viết PRD.
- **to-issues**: Mỗi PRD → nhiều Jira Tasks nhỏ, có acceptance criteria + cách implement.
- **implement**: Agent nhặt task AFK, code theo contract, chạy gate, push PR.

Decisions không tự thành task. Phải qua `to-prd` → rõ slice. Phải qua `to-issues` → command nhỏ.
Implement luôn bám CONTEXT.md + ADR + OpenAPI.

---

## Cấu trúc issue body

Khi tạo task (qua `to-issues` hoặc tay), dùng format này.
Viết tiếng Việt. Mô tả đủ để agent AFK implement.
Giữ thuật ngữ kỹ thuật tiếng Anh nguyên văn nếu là canonical term.

```markdown
## Mục tiêu
Một câu: feature này làm gì.

## Bối cảnh
Surface nào / service nào / vì sao cần.

## Yêu cầu
Đầu vào, đầu ra, ràng buộc kỹ thuật.

## Cách implement
Thứ tự code, file cần sửa/thêm, service/handler/test pattern.
Viết đủ để agent làm theo, không cần suy luận thêm.

## Acceptance criteria
- [ ] ...

## Blocked by
(task key nếu có dependency, optional)

## ADR tham chiếu
0025, 0026, 0028, ...
```

### Quy ước đặt tên

- Ticket cha: prefix `[PRD]` — scope reference, chỉ implement nếu user yêu cầu.
- Ticket con: prefix `[Slice]` — lát cắt dọc hẹp, agent nhặt độc lập.
- Summary tiếng Việt, rõ feature/fix/refactor.

---

## Thực thi task (agent workflow)

Đây là quy trình khi agent nhặt task từ Jira để implement.
Chạy đúng thứ tự. Không nhảy bước.

### Bước 0 — Đặt goal

Gọi `create_goal` trước khi làm bất kỳ thao tác nào:

- `objective`: `"Implement KAN-xx: [summary tiếng Việt]"` + 1–2 acceptance criteria chính.
- Không set `token_budget` trừ khi user yêu cầu.

Khi task hoàn thành (PR merged hoặc closed), gọi `update_goal(status: "complete")`.
Không dùng goal thay thế Jira status — goal là local session tracking.

---

### Bước 1 — Đọc issue

Gọi `getJiraIssue` với task key. Lấy toàn bộ body:

- `## Mục tiêu` — feature này làm gì
- `## Bối cảnh` — bối cảnh tính năng
- `## Yêu cầu` — đầu vào, đầu ra, ràng buộc
- `## Cách implement` — **làm theo**, không tự suy luận khác
- `## Acceptance criteria` — tiêu chí pass
- `## Blocked by` — nếu có, đọc task kia trước
- `## ADR tham chiếu` — ADR nào liên quan
- Labels + Comments — trạng thái triage, ai đã hỏi gì

Nếu `## Cách implement` không rõ → comment hỏi, không tự đoán.

### Bước 2 — Lấy ngữ cảnh codebase

Trước khi code, đọc:

1. **CONTEXT.md** — glossary scope mới, canonical terms. Không synonym.
2. **ADR tham chiếu** — file trong `docs/decisions/` được liệt kê.
3. **OpenAPI skeleton** — nếu chạm API: mở `docs/api/openapi.v1.skeleton.yaml`, xem path/response shape. Không tự đổi.
4. **Service boundary** — ADR 0026–0027: service nào owns entity nào, link table nào.
5. **Design docs** — nếu task chạm UI, đọc `docs/design/README.md` và file `.pen` liên quan trước khi implement.

### Bước 3 — Implement

Làm theo `## Cách implement`. Thứ tự code mặc định:

> **service → handler → test → integration**

- Code theo OpenAPI contract. Không tự đổi route / response / error code.
- Bám domain terms từ CONTEXT.md. Không dùng synonym scope cũ.
- Xem ADR 0025–0027 để biết ownership (WorkService owns WorkItem + link tables; DocumentService owns Document + PeopleDocumentLink; ...).
- Error code từ catalog: VALIDATION_ERROR, PERMISSION_DENIED, RESOURCE_NOT_FOUND, INVALID_STATUS_TRANSITION, DUPLICATE_RESOURCE, CONFLICT, AI_SUGGESTION_MISMATCH, IDEMPOTENCY_CONFLICT.
- Giữ diff nhỏ, không kéo refactor ngoài scope.

### Bước 4 — Gate

Chạy trước khi push:

```bash
cd backend && ruff check && mypy && pytest
cd frontend && pnpm lint && pnpm test && pnpm build
```

Nếu chạm UI: trước hết phải có design `.pen` tương ứng trong `docs/design/` đã approve. Chưa có → dừng, quay lại thiết kế trước.
Có design rồi → code → thêm browser QA (Playwright screenshots, console check, viewports).
Gate đỏ → sửa → chạy lại. Không push qua gate đỏ.

### Bước 5 — Push + PR

- Branch từ `main`.
- Commit theo từng bước. Message tiếng Việt, format: `service: action`.
- Push.
- Tạo PR dùng GitHub MCP. PR description: summary ngắn tiếng Việt, list thay đổi, ADR reference, link Jira task.
- Task lớn: dùng `code-review` skill self-review trước.

### Bước 6 — Review sau PR

Sau khi PR mở xong, quy trình review đi theo 2 lớp:

1. **Self-review trước**
   - Đọc lại diff của chính mình.
   - Chạy `srcwalk review --staged` nếu còn local change trước khi push.
   - So từng thay đổi với `CONTEXT.md`, ADR liên quan, OpenAPI skeleton, và AC của Jira task.
   - Tự tìm lỗi logic, thiếu test, lệch naming, lệch contract, và diff thừa.

2. **Review đối chiếu task**
   - Dùng skill `code-review` khi cần review branch/PR against fixed point.
   - Lấy Jira task làm spec nguồn.
   - Kết luận theo 2 trục:
     - **Standards**: code có theo chuẩn repo không.
     - **Spec**: code có đúng yêu cầu task/PRD không.
   - Nếu task chạm UI, kiểm thêm screenshot / browser QA / responsive states.

3. **Xử lý feedback**
   - Nếu có comment review: sửa code, thêm test, cập nhật PR.
   - Nếu review phát hiện thiếu context hoặc spec mơ hồ: comment lại Jira task/PR, không đoán.
   - Không merge khi còn unresolved feedback quan trọng.
   - Mọi review comment, Jira comment, và PR summary viết bằng tiếng Việt, trừ thuật ngữ kỹ thuật tiếng Anh.

### Bước 7 — Báo cáo kết quả

Gọi `addCommentToJiraIssue`:

```text
Đã push, PR #xx — đang chờ review.
Thay đổi: [list ngắn]
Gate: ruff/mypy/pytest pass
Review: [PASS / NEEDS_CHANGES / BLOCKED]
```

Nếu cần user phê duyệt tiếp: ghi rõ bước cần chốt.

### Bước 8 — Khi bị block

Không implement được vì:

- **Thiếu context** (`## Cách implement` không rõ, AC mơ hồ) → comment hỏi, không tự suy luận.
- **Mâu thuẫn với ADR / CONTEXT** → comment, không âm thầm sửa.
- **Dependency chưa xong** (task trong `Blocked by`) → comment, không implement tay.

**Giữ nguyên task status.** Không chuyển In Progress / Done nếu không có chỉ thị.

### Bước 9 — Iterate

- Sửa theo review feedback.
- Cập nhật Jira comment khi trạng thái thay đổi.
- Chỉ đóng task khi acceptance criteria khớp. Không tự close.

---

## Khi skill nói "publish to the issue tracker"

Tạo Jira Tasks trong `KAN`. Không phải GitHub Issues.
Định dạng body theo [Cấu trúc issue body] ở trên.

## Khi skill nói "fetch the relevant ticket"

Đọc Jira task theo key. Chạy Bước 1 — Đọc issue để inspect đầy đủ.
