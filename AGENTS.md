# Vroom HR

Vroom HR (Vietnamese Recruit-Onboard-Operate-Manage) là nền tảng HR tự host, mã nguồn mở, cho doanh nghiệp Việt Nam. Mỗi công ty chạy một triển khai riêng, một DB riêng, một server riêng. Một triển khai chỉ phục vụ đúng một công ty. Mục lục này chốt nghĩa chuẩn của thuật ngữ domain để team dùng 1 từ cho 1 khái niệm trong spec, code, và docs.

## Agent skills

### Issue tracker

Issue và PRD của repo này sống trong GitHub Issues. PR ngoài không phải surface triage. Xem `docs/agents/issue-tracker.md`.

### Triage labels

5 role triage chuẩn map 1-1 sang label của repo: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Xem `docs/agents/triage-labels.md`.

### Domain docs

Repo single-context. Đọc `CONTEXT.md` ở root và `docs/adr/` cho quyết định kiến trúc. Xem `docs/agents/domain.md`.

### Agent-Core Orchestration (Herdr)

Workflow điều phối chuẩn (coordinator vs worker, guard phrase `bạn là agent điều phối`, worktree isolation, loop sinh/wait/read/follow-up, nguyên tắc cứng) sống ở **global** `~/.pi/agent/AGENTS.md`. Đọc file đó làm nguồn sự thật cho cách spawn/wait/read worker; KHÔNG tái định nghĩa workflow ở đây.

**Project-specific deviations** (ghi đè/ bổ sung global, giữ tối thiểu):

- **Worker được phép commit + push** branch feature khi orchestrator yêu cầu trong task prompt (repo này cần worker tự đóng gói branch review). Global cấm commit trừ khi yêu cầu → trong project này, yêu cầu là mặc định cho task dispatch/commit-chain. Worker vẫn KHÔNG được tự ý sửa file ngoài scope task (đặc biệt `AGENTS.md`/docs cấu hình) — orchestrator revert nếu worker vi phạm.
- **Worker isolation**: global khuyến nghị git worktree (`worker/<label>`). Project TuẦN THEO global — ưu tiên worktree riêng cho worker, KHÔNG dùng pane-split trên working tree chung (đã từng khiến worker tự sửa `AGENTS.md` ngoài scope vì share checkout).
- Launch worker bằng `pi` mặc định (provider/model từ `~/.pi/agent/settings.json`); chỉ ghi đè `--provider`/`--model` khi human xác nhận.
- Prompt worker mở đầu bằng `Bạn là worker, không phải agent điều phối.` (global), kèm scope file cụ thể + yêu cầu báo ngắn.

**Topo workspace**: orchestrator dùng workspace riêng (ví dụ `agent-workers`); worker chạy trong background workspace/pane của orchestrator đó, `done` khi tab nền.
