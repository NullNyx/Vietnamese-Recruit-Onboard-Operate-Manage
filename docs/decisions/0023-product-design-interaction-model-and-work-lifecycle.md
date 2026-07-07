# 0023 Product Design: Interaction Model + Work Lifecycle

Date: 2026-07-04

## Status

Accepted — Product Experience layer hoàn chỉnh. Chuyển pha sang System Design.

## Context

Tiếp nối IA, Screen Skeletons, và Today Decision Model (0022), hội thoại đào sâu:

1. **Today Interaction Model** — cách HR xử lý việc nhanh trên Today không chết
   trong Work Detail.
2. **Interaction Pattern Catalog** — 4 interaction levels chuẩn cho toàn bộ sản
   phẩm, quyết định bởi độ phức tạp hành động, không phải Work Type.
3. **Work Detail Design Principles** — chặn Work Detail thành god screen.
4. **Work Lifecycle** — một work item sống thế nào trong toàn bộ hệ thống.

User chốt: Product Experience đã đủ. Chuyển sang **System Design**: Capabilities
→ Modules → Domain Model → Data Model.

## Decision

### 1. Today Interaction Model

#### 1.1 Nguyên tắc

- Xử lý ngay trên Today nếu được.
- Chỉ mở Work Detail khi buộc phải.
- Mỗi lần click → một bước tiến.
- Không bắt HR quyết định "mở hay không" — card tự thích ứng.

#### 1.2 Bốn trạng thái tương tác

| Level | Tên | Mô tả |
|-------|-----|-------|
| 1 | Collapsed (mặc định) | 3 quick actions + badge + lý do item ở đây |
| 2 | Hover / Hint | AI reasons hiện thêm — không click, chỉ hover |
| 3 | Expand / Inline | Mở rộng card trong Today: context, AI, quick form |
| 4 | Work Detail | Chuyển màn — multi-step, draft, coordinate, timeline |

#### 1.3 Card layout chuẩn

```
┌──────────────────────────────────┐
│ [Badge] [Icon] Title              │
│ Lý do quyết định (overdue, chờ)   │
│ [Action 1] [Action 2] [Action 3]  │
│ ↑ AI reason (hover mới rõ)         │
├──────────────────────────────────┤
│ (inline expand)                    │
│ Context, AI, form                  │
│ [Mở Work Detail ▸]                │
└──────────────────────────────────┘
```

Dòng 1: badge + icon + title. Dòng 2: lý do. Dòng 3: quick actions.
Dòng 4: AI reason mờ (hover mới rõ).

#### 1.4 State → Quick Actions mapping

| Trạng thái item | Action 1 | Action 2 | Action 3 |
|-----------------|----------|----------|----------|
| Quá hạn | Complete | Snooze | Assign |
| Sắp hạn | Complete | Snooze | Assign |
| Đang chờ | Follow-up | Add note | Assign |
| Cần review | Approve | Reject | Open |
| Cần draft | Draft now | Assign | Snooze |
| Blocked | Unblock | Follow-up | Assign |
| Waiting on others | Remind now | Reassign | Open |
| Missing document | Upload now | Notify | Snooze |
| Ready to complete | Complete | Add note | Open |

Action tự động ưu tiên theo trạng thái. HR không cần nghĩ — click action đầu
là đúng. Quick action không form dài, không xác nhận nhiều bước, không chuyển
màn, không popup lớn.

#### 1.5 AI roles

| Mode | Kích hoạt | Hành vi |
|------|-----------|---------|
| Silent | Mặc định | Không popup, không banner, không chat |
| On demand (hint) | Hover | Lý do item ở đây, icon AI nhỏ |
| Inline | Expand | "AI: …" block trong expand |
| Active | Flag critical | Badge đỏ khi detect risk; suggestion → tertiary action |

AI không: tự ghi dữ liệu, tự complete, chiếm diện tích collapsed card.

#### 1.6 Flow patterns

**Single item:**
Today → click Quick Action → confirm nhẹ → item biến mất → focus item tiếp

**Expand:**
Today → click card body → expand → xem context + AI → quick form →
confirm → collapse → item biến mất → focus item tiếp

**Work Detail:**
Today → Open Detail → Work Detail → xử lý → Back to Today →
Today cập nhật → focus item tiếp

**Batch:**
Today → chọn nhiều (checkbox mode) → batch action bar bottom →
confirm N items → audit từng item → focus item tiếp

#### 1.7 Multi-select / Batch

- Icon "select" trên Today header
- Click → checkbox mỗi card
- Chọn → batch bar (Complete, Assign, Snooze, Change status, Add note)
- Confirm → từng item ghi audit riêng

### 2. Interaction Pattern Catalog

#### 2.1 Nguyên tắc

Interaction level quyết định bởi: độ phức tạp hành động, context cần xem,
số bước, mức rủi ro, có cần phối hợp. Không quyết định bởi Work Type.

#### 2.2 Bốn level

| Level | Tên | Mục đích | Dùng khi | UI shape |
|-------|-----|----------|----------|----------|
| L1 | Instant Action | Xử lý 1 click trên Today | Action rõ, rủi ro thấp, không cần nhập | Button nhỏ trên card, confirm nhẹ |
| L2 | Inline Action | Xử lý trong Today nhưng cần expand | Cần context ngắn, form nhỏ, rủi ro vừa | Expand card, inline form, AI inline |
| L3 | Focused Work | Work Detail, multi-step | Multi-step, draft, coordinate, rủi ro cao | Detail đầy đủ: context, timeline, actions |
| L4 | Cross-context | Qua People/Doc/Contract rồi quay lại | Cần đọc ngữ cảnh ngoài, đối chiếu nhiều nguồn | Side panel, back link rõ, state giữ nguyên |

#### 2.3 Decision rule

1. Làm xong trong 1 click? → L1
2. Cần expand xem context ngắn? → L2
3. Cần multi-step, draft, coordination? → L3
4. Cần đi sang context library? → L4

#### 2.4 Pattern contract

Mọi màn sau này phải fit 1 trong 4 level. Nếu không fit, màn đó đang sai vai.

### 3. Work Detail Design Principles

#### 3.1 Mục tiêu

Giúp HR hiểu nhanh, quyết định nhanh, hoàn thành nhanh một việc cụ thể.

Không phải: màn đọc toàn bộ dữ liệu, màn chỉnh sửa entity, màn chứa mọi context.

#### 3.2 Ba câu hỏi duy nhất

1. Việc này là gì?
2. Mình cần làm gì tiếp theo?
3. Làm thế nào để hoàn thành nhanh nhất?

Nếu một block không trả lời 1 trong 3 câu, block đó không thuộc Work Detail.

#### 3.3 Always visible

- Work summary (title, status, priority, owner, due, source, lý do)
- Next step (chỉ 1 việc chính)
- Primary actions (rõ theo trạng thái, không quá nhiều)
- AI short assist (summary ngắn, suggestion ngắn)

#### 3.4 Conditional

- Context details: chỉ khi cần đối chiếu
- Linked items: chỉ khi phụ thuộc
- Timeline: chỉ khi thời gian là cốt lõi
- Notes/history: chỉ khi nhiều vòng xử lý
- Cross-context entry: chỉ khi phải sang library

#### 3.5 Never in Work Detail

Full record browser, long-form admin settings, dashboard metrics, library list,
report screen, config screen, feature discovery, AI chat chung — mọi thứ không
phục vụ 3 câu hỏi.

#### 3.6 Work Detail ≠ Context Library

- Work Detail = execute (context đủ để quyết định và hành động)
- Context Library = inspect (dài, tra cứu, không trực tiếp giúp hoàn thành)

Nếu context dài / ít dùng → đi sang People/Documents/Contracts.

### 4. Work Lifecycle (Product Level)

#### 4.1 Birth — Item được tạo

| Nguồn | Mô tả | Vào đâu đầu tiên |
|-------|-------|------------------|
| Inbox | Email, request, file | Inbox (raw, chưa triage) |
| System trigger | Deadline, hết hạn, reminder | All Work (có context) |
| Manual | HR tự tạo | All Work |
| Dependent | Item con sinh từ item cha | All Work (gắn parent) |
| AI detection | Thiếu dữ liệu, mismatch, risk | Inbox (nếu cần confirm) hoặc All Work |

Inbox chỉ chứa item chưa triage. System trigger + manual → thẳng All Work.

#### 4.2 Triage

Inbox → phân loại → gắn context → thành work item → vào All Work.
Nếu không triage: item chết trong Inbox.

#### 4.3 Activation — All Work

Item vào All Work khi: triage xong, system trigger, manual, dependent, AI tự tin.
All Work chứa: active, waiting, completed (gần đây). Không chứa archived.

#### 4.4 Urgency — Today

Item vào Today theo Decision Model (overdue, due today, blocking, risk, etc).
Item rời Today khi: resolved, snoozed, no longer urgent.
Rời Today KHÔNG đồng nghĩa biến mất khỏi All Work.

#### 4.5 Processing — Xử lý

Trên Today: Instant Action (L1) / Inline Action (L2) → xong → biến mất.
Trong Work Detail (L3): multi-step → xong → Back to Today.

#### 4.6 Waiting

Khi HR không thể làm tiếp, chờ người khác/file/xác nhận.
UX: Today section `Waiting`; All Work status `waiting`.
HR có thể: follow-up, remind, chuyển, reassign.

#### 4.7 Completion

HR confirm → biến mất Today → vẫn trong All Work (completed) →
audit ghi rõ → không thể sửa (chỉ reopen).
AI detect xong → đề xuất complete → không tự động complete.

#### 4.8 Reopen

Cần làm thêm, manager yêu cầu xem lại, AI detect issue sau complete.
→ vào lại All Work (active) → có thể lên Today → audit ghi reopening.

#### 4.9 Archive

Complete + không cần theo dõi / cancelled / manual archive.
→ không còn trong All Work / Today / search mặc định.
Audit trail tồn tại. Có thể tìm bằng advanced search.

#### 4.10 Lifecycle flow

```
Source ──→ Inbox ──triage──→ All Work ──urgency──→ Today
                                ↑                       │
                                │                       ├── L1 Instant  → Done
                                │                       ├── L2 Inline   → Done
                                │                       └── L3 Detail  → Work Detail → Done
                                │                                       │
                                │                                  (reopen) ← ─┘
                                │                                       │
                                │                                  (waiting) ─→ Follow-up
                                │
                                └── Completed (still visible in All Work)
                                       │
                                       ↓
                                    Archive
```

#### 4.11 Screen ownership

| Stage | Màn chính | Hành vi |
|-------|-----------|---------|
| Birth → Intake | Inbox | Chưa phải work item chuẩn |
| Triage | Inbox | Gắn context, chuyển All Work |
| Active | All Work + Today | Tồn tại, available |
| Urgent | Today | Quyết định ưu tiên |
| Processing | Today + Work Detail | Xử lý |
| Waiting | All Work + Today (Waiting) | Paused |
| Completed | All Work (completed filter) | Done |
| Reopened | All Work + có thể Today | Quay lại active |
| Archived | Không | Biến mất khỏi view chính |

### 5. Next Phase — System Design

User chốt: Product Experience đã đủ. Chuyển pha.

Thứ tự tiếp theo:

```
Work Lifecycle
  ↓
Capabilities     ← bắt đầu tại đây
  ↓
Modules
  ↓
Domain Model
  ↓
Data Model
```

**Nguyên tắc:**
- Capability ≠ Module.
- Capability trả lời: hệ thống cần làm được gì.
- Module trả lời: nhóm capability nào đi cùng nhau.
- Domain Model trả lời: dữ liệu + quan hệ cần có.
- Data Model là bước cuối.

Ví dụ capability (không phải module):
Search, Notification, Reminder, Assignment, Audit, AI Assist,
Draft, Review, Attachment, Timeline.

## Consequences

Positive:
- 4 interaction levels chuẩn cho toàn bộ sản phẩm.
- Work Detail có triết lý rõ — không phình thành god screen.
- Work Lifecycle kết nối Inbox → All Work → Today → Detail → Archive.
- Capability-first approach đảo ngược data-driven design.
- Product Experience hoàn chỉnh trước khi chạm implementation.

Tradeoffs:
- Work Lifecycle chưa có state machine chi tiết (implementation phase).
- Interaction Pattern Catalog chưa có trigger/audit/AI behavior spec.
- Capability mapping vẫn còn mở — cần phiên riêng.
- Chưa xác định module boundaries.

## References

- ADR 0022: IA, Screen Skeletons, Today Decision Model
- ADR 0021: Product Identity + Work Taxonomy
- ADR 0015, 0018, 0019: domain decisions chờ Domain Model phase
