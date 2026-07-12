# Vroom HR

Vroom HR (Vietnamese Recruit-Onboard-Operate-Manage) là nền tảng HR tự host, mã nguồn mở, cho doanh nghiệp Việt Nam. Mỗi công ty chạy một triển khai riêng, một DB riêng, một server riêng. Một triển khai chỉ phục vụ đúng một công ty. Mục lục này chốt nghĩa chuẩn của thuật ngữ domain để team dùng 1 từ cho 1 khái niệm trong spec, code, và docs.

## Agent skills

### Issue tracker

Issue và PRD của repo này sống trong GitHub Issues. PR ngoài không phải surface triage. Xem `docs/agents/issue-tracker.md`.

### Triage labels

5 role triage chuẩn map 1-1 sang label của repo: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Xem `docs/agents/triage-labels.md`.

### Domain docs

Repo single-context. Đọc `CONTEXT.md` ở root và `docs/adr/` cho quyết định kiến trúc. Xem `docs/agents/domain.md`.

### Learning Documents

Sau mỗi task triển khai, tạo file:

```
docs/learning-notes/<YYYY-MM-DD>-<tên-task-ngắn>.md
```

Dùng cấu trúc sau:

- **# Task** — Nhiệm vụ
- **# What I changed** — Những gì đã thay đổi
- **# The real problem** — Vấn đề thực sự
- **# Why this solution** — Tại sao chọn giải pháp này
- **# Production shape** — Hình dạng production
- **# Other possible approaches** — Các hướng tiếp cận khả thi khác
- **# Why I did not choose those alternatives** — Tại sao không chọn các giải pháp thay thế đó
- **# Key concepts to learn** — Các khái niệm chính cần học
- **# Common mistakes** — Các lỗi thường gặp
- **# Small example** — Ví dụ nhỏ
- **# How to think about this next time** — Cách suy nghĩ về điều này lần sau

Với công việc không tầm thường (non-trivial), phải bao gồm ít nhất hai giải pháp thay thế và giải thích khi nào mỗi giải pháp phù hợp.
