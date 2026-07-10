# Issue tracker: GitHub

Issue và PRD của repo này sống trong GitHub Issues. Dùng `gh` CLI cho mọi thao tác.

## Quy ước

- **Tạo issue**: `gh issue create --title "..." --body "..."`. Với body nhiều dòng, dùng heredoc.
- **Đọc issue**: `gh issue view <number> --comments`, lọc comment bằng `jq` và lấy luôn labels.
- **Liệt kê issue**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`, thêm `--label` và `--state` khi cần.
- **Comment issue**: `gh issue comment <number> --body "..."`.
- **Gán / bỏ label**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`.
- **Đóng issue**: `gh issue close <number> --comment "..."`.

Dò repo từ `git remote -v` - `gh` tự hiểu khi chạy trong clone của repo.

## PR có phải surface triage không

**PR ngoài là request surface: không.** _(Đổi thành `có` nếu repo này coi PR ngoài là feature request; `/triage` đọc flag này.)_

Khi bật `có`, PR đi qua cùng label và state như issue, dùng lệnh `gh pr` tương ứng:

- **Đọc PR**: `gh pr view <number> --comments` và `gh pr diff <number>` để xem diff.
- **Liệt kê PR ngoài để triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`, rồi giữ lại `authorAssociation` là `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, hoặc `NONE` (bỏ `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / đóng**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub dùng chung một dải số cho issue và PR, nên `#42` mơ hồ - resolve bằng `gh pr view 42`, rồi fallback `gh issue view 42`.

## Khi skill nói "publish to the issue tracker"

Tạo GitHub issue.

## Khi skill nói "fetch the relevant ticket"

Chạy `gh issue view <number> --comments`.

## Wayfinding

Dùng bởi `/wayfinder`. **Map** là một issue đơn với **child** issues làm ticket.

- **Map**: một issue có label `wayfinder:map`, body chứa Notes / Decisions-so-far / Fog. `gh issue create --label wayfinder:map`.
- **Child ticket**: issue nối với map như sub-issue của GitHub (`gh api` qua sub-issues endpoint). Nếu sub-issues không bật, thêm child vào task list trong body map và đặt `Part of #<map>` ở đầu body child. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Khi được claim, ticket được assign cho dev đang xử lý.
- **Blocking**: native issue dependencies của GitHub - biểu diễn chuẩn, hiển thị trên UI. Thêm edge bằng `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, trong đó `<blocker-db-id>` là numeric database id của blocker (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, không phải `#number` hay `node_id`). GitHub trả về `issue_dependencies_summary.blocked_by` (chỉ blocker đang mở - live gate). Nếu không có dependencies, fallback bằng dòng `Blocked by: #<n>, #<n>` ở đầu body child. Ticket hết block khi mọi blocker đã đóng.
- **Frontier query**: liệt kê child đang mở của map (`gh issue list --state open`, scope vào sub-issues / task list của map), bỏ mọi ticket có blocker đang mở (`issue_dependencies_summary.blocked_by > 0`, hoặc issue đang mở trong dòng `Blocked by`) hoặc đã có assignee; ticket đầu tiên theo thứ tự map là ticket tiếp theo.
- **Claim**: `gh issue edit <n> --add-assignee @me` - write đầu tiên của session.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, rồi `gh issue close <n>`, rồi append context pointer (gist + link) vào Decisions-so-far của map.
