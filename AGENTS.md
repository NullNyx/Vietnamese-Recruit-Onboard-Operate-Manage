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

Orchestrator (pi, workspace user) là **điều phối viên**, không phải worker:
- Nhận task từ human, phân tích, chia nhỏ
- Dispatch cho sub-agent (pi model rẻ, workspace background)
- Theo dõi tiến độ, xử lý blocked, tổng hợp kết quả
- Báo cáo cho human review
- **Không** tự làm task (không code, không fix bug, không viết test). Mọi implementation do sub-agent đảm nhận.

**Topology bắt buộc**: sub-agent trong **workspace background riêng** (`agent-workers`). Lý do: foreground → completion báo `idle`, background → báo `done`. Background workspace đảm bảo `done` luôn đúng.

**Spawn**:
```bash
herdr pane split --pane <worker-pane> --direction right --no-focus
herdr pane rename <id> "task-label"
herdr pane run <id> "pi --provider opencode-go --model deepseek-v4-flash --thinking low"
herdr wait agent-status <id> --status idle --timeout 30000
herdr pane run <id> "<task>"
```

**Wait + read**:
```bash
herdr wait agent-status <id> --status done --timeout 300000
herdr pane read <id> --source recent-unwrapped --lines 120
```

**Check / follow-up**:
```bash
herdr pane get <id>                          # idle|done=xong, blocked=cần input
herdr pane run <id> "<follow-up>"            # gửi tiếp task
```
