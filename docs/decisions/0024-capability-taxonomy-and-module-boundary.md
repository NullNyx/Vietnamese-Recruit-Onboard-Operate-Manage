# 0024 Capability Taxonomy + Module Boundary

Date: 2026-07-04

## Status

Accepted — System Design layer. Module boundary đã chốt. Domain Model bắt đầu.

## Context

Sau Product Experience (0021–0023), hội thoại chuyển sang System Design.
Bước đầu: định nghĩa **Capability** (hệ thống làm được gì) trước khi gom
module hay chạm domain model.

Hai bước:

1. **Capability Taxonomy** — 14 core capabilities, không lẫn infra.
2. **Module Boundary v2** — 5 product surfaces + cross-cutting capabilities.
   Context Libraries gom People/Documents/Contracts/Templates làm một nhóm.
   AI Assist không phải module. Work owns lifecycle, không owns mọi capability.

User chốt: Module boundary ổn. Bước kế là **Domain Model**.

## Decision

### 1. Nguyên tắc Capability

Capability trả lời: *HR làm được gì khi xử lý work?*

Không trả lời:
- hệ thống cấu hình gì
- storage gì
- backup gì
- session gì
- import/export kỹ thuật gì

### 2. Capability Taxonomy v2

| # | Capability | Mô tả | Phục vụ |
|---|------------|-------|---------|
| 1 | Work Management | tạo, cập nhật, complete/reopen/archive, assign, snooze, batch | Today, All Work, Work Detail |
| 2 | Intake & Triage | nhận input thô, phân loại, gắn ngữ cảnh, chuyển work item, dismiss | Inbox |
| 3 | Prioritization | lọc Today, gán Critical/Attention/Planned/Waiting, xếp thứ tự, explain | Today |
| 4 | Search & Filter | search hệ thống, filter status/owner/due/priority, cross-context, recent | Today, All Work, Inbox, Libraries |
| 5 | Assignment & Coordination | assign, hand-off, request action, track dependency, follow-up | Today, Work Detail |
| 6 | Notification & Reminder | reminder deadline, risk alert, daily brief, dismiss/snooze | Today, Inbox, Work Detail |
| 7 | Context Linking | gắn People/Document/Contract vào work, mở context/quay lại | Work Detail, Libraries |
| 8 | Document & File Handling | upload, view, download, verify/reject, link file, detect thiếu/hết hạn | Work Detail, Documents |
| 9 | Draft & Template Generation | fill template, generate draft, preview, highlight placeholder | Work Detail, Templates |
| 10 | AI Assist | classify, extract, summarize, suggest, fill, draft, answer, rank, explain | toàn bộ |
| 11 | Audit & Trace | log action, log before/after, trace history, redact sensitive | toàn bộ |
| 12 | Notes & Comments | add note, reply, internal comment, pin | Work Detail |
| 13 | Reporting & Summary | daily/weekly/queue summary, status snapshot, natural language answer | Today, Reports |
| 14 | Permission | authenticate, authorize, enforce access scope, protect write | toàn bộ |

### 3. Module Boundary v2

#### 3.1 Work

| Góc | Mô tả |
|-----|-------|
| Surface | Today, All Work, Work Detail |
| Purpose | Trung tâm thực thi công việc hằng ngày |
| Owns | Work lifecycle, prioritization, execution flow, status transitions, return path về Today |
| Uses | Search, Notification, Audit, AI, Permission, Assignment, Draft & Template Gen, Doc & File, Context Linking |
| Does not own | Intake, context data, system settings, reporting, AI config, template admin |
| Relation | Nhận item từ Inbox, đọc ngữ cảnh từ Context Libraries, đẩy summary lên Reports |

#### 3.2 Inbox

| Góc | Mô tả |
|-----|-------|
| Surface | Inbox |
| Purpose | Tiếp nhận input thô, triage, phân loại, convert thành work item |
| Owns | Raw input intake, triage, classify, convert, dismiss |
| Uses | Search, AI, Audit, Notification, Permission |
| Does not own | Work execution, context library data, reporting, settings |
| Relation | Output sang Work, cổng vào không phải nơi xử lý cuối |

#### 3.3 Context Libraries

| Góc | Mô tả |
|-----|-------|
| Surface | People, Documents, Contracts, Templates |
| Purpose | Nơi inspect/reference context — không phải trung tâm vận hành |
| Owns | Linked context data, detail view, search trong context, read/update library content |
| Uses | Search, AI, Audit, Permission, Notification, Doc & File, Draft & Template, Notes, Context Linking |
| Does not own | Work lifecycle, Today prioritization, inbox triage, dashboard, reporting tổng hợp |
| Relation | Work mở sang đây khi cần inspect, Inbox gắn context từ đây |

**Bao gồm:**

**People** — inspect hồ sơ nhân sự. Owns people reference, profile detail, linked notes/docs/contracts.

**Documents** — inspect và quản lý giấy tờ. Owns file detail, verify/reject, linked docs, expiry tracking.

**Contracts** — inspect và quản lý hợp đồng. Owns contract detail, draft review, signed file, status view.

**Templates** — inspect và quản lý mẫu dùng lại. Owns template list, edit, version, archive, defaults.

#### 3.4 Reports

| Góc | Mô tả |
|-----|-------|
| Surface | Reports |
| Purpose | Summary, snapshot, answers từ dữ liệu sống |
| Owns | Daily/weekly summary, status snapshot, queue summary, natural language answers, trend |
| Uses | Search, AI, Audit, Permission |
| Does not own | Work execution, intake, context management, system config |
| Relation | Đọc từ Work, Inbox, Context Libraries. Không ghi vào core workflow. |

#### 3.5 Admin / Settings

| Góc | Mô tả |
|-----|-------|
| Surface | Settings |
| Purpose | Cấu hình hệ thống và quyền truy cập |
| Owns | Users, permissions, integrations, org config, system defaults, AI provider config, storage/backup |
| Uses | Permission, Audit, Search, AI |
| Does not own | Work lifecycle, intake, context inspect, reports content |
| Relation | Cấp cấu hình toàn hệ thống, enforce access control |

#### 3.6 Cross-cutting (không phải module)

| Capability | Ghi chú |
|------------|---------|
| AI Assist | Inline trong Inbox, Work, Context Libraries, Reports |
| Audit & Trace | Ghi hành vi toàn hệ thống |
| Search | Dùng ở nhiều surface |
| Notification | Đẩy reminder/alert vào surfaces |
| Permission | Enforce quyền ở mọi nơi |

### 4. Ownership tóm tắt

| Surface | Owns | Không owns |
|---------|------|------------|
| Work | lifecycle, prioritization, execution | intake, context data |
| Inbox | raw input, triage | execution, context library |
| Context Libraries | inspect/reference data | daily work loop |
| Reports | summaries, snapshots, answers | workflow execution |
| Admin | config, users, permissions | work data |

### 5. Next Phase — Domain Model

Sau khi module boundary chốt, bước kế là **Domain Model**.

Thứ tự tiếp theo:

```
Module Boundary v2
  ↓
Domain Model          ← bắt đầu tại đây
  ↓
Data Model
```

## Consequences

Positive:
- Capability taxonomy sạch — không lẫn infra, config, implementation detail.
- Module boundary theo product surface, không theo engineering concern.
- Context Libraries gom 4 surface thành 1 nhóm — giảm navigation clutter.
- AI Assist không phải module — đúng với design principle từ đầu.
- Cross-cutting capabilities tách biệt rõ — không module hoá everything.

Tradeoffs:
- Context Libraries chưa được design detail (People/Documents/Contracts/Templates behavior).
- Draft & Template Generation chưa rõ module boundary (tách hay gộp với Contracts/Documents).
- Permission còn mơ hồ — Role model chưa chốt.
- Chưa chạm Domain Model — chưa có entity hay relationship.

## References

- ADR 0023: Interaction Model + Work Lifecycle
- ADR 0022: IA, Screen Skeletons, Today Decision Model
- ADR 0021: Product Identity + Work Taxonomy
