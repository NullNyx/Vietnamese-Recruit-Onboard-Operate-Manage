# 0022 Product Design: IA, Screen Skeletons, Today Decision Model

Date: 2026-07-04

## Status

Accepted — Product Design layer. Screens và Decision Model là skeleton,
chưa phải UI spec. Interaction Model còn đang mở.

## Context

Sau khi Work Taxonomy (0021) chốt, hội thoại chuyển sang Product Design.
Mục tiêu: thiết kế trải nghiệm làm việc hằng ngày của HR, không thiết kế
module hay entity.

Ba phiên liên tiếp xây dựng:

1. IA Skeleton — cấu trúc điều hướng, phân vai Today / All Work / Inbox / Work Detail / Context Libraries
2. Screen-Level Skeleton — mục tiêu + thông tin + quyết định + hành động của từng màn
3. Today Decision Model — hệ thống xếp hạng và phân loại work items để quyết định việc nào xuất hiện trên Today

User chốt: Decision Model đủ mạnh, không đào sâu rubric/score nữa. Bước tiếp
theo là **Today Interaction Model** — cách HR xử lý việc nhanh trên Today.

## Decision

### 1. Product Design Principles (từ hội thoại)

- User không cần thấy `Work Type` hay taxonomy nội bộ.
- UI language: việc cần làm, quá hạn, đang chờ, cần phối hợp, cảnh báo.
- Navigation không quay thành module list. Trung tâm là Today / All Work / Inbox / Detail.
- Context Libraries (People, Documents, Contracts, Templates) là thứ cấp — dùng làm ngữ cảnh, không làm entry point.
- AI xuất hiện xuyên suốt, không phải chatbot riêng.

### 2. IA Skeleton

```
Today           — Command Center: ưu tiên, quyết định việc làm trước
All Work        — Operations Center: toàn bộ work items, filter, search, batch
Inbox           — Intake: đầu vào thô chưa xử lý (email, request, file, notification)
Search          — Tìm kiếm toàn hệ thống
  ├─ People        — Context library (hồ sơ nhân sự)
  ├─ Documents     — Context library (giấy tờ, chứng từ)
  ├─ Contracts     — Context library (hợp đồng)
  ├─ Templates     — Context library (mẫu)
  ├─ AI Assistant  — Hỗ trợ hội thoại
  ├─ Reports       — Báo cáo / thống kê
  └─ Settings      — Cấu hình hệ thống
```

**Core** (Today, All Work, Inbox, Search) đứng trên.
**Context Libraries** đứng dưới — chỉ mở từ Work Detail hoặc Search.

### 3. Screen-Level Skeleton — Ba màn cốt lõi

#### 3.1 Today — Command Center

| Góc | Mô tả |
|-----|-------|
| Mục tiêu | Trong 10 giây biết việc gì quan trọng nhất, quá hạn, rủi ro |
| Thông tin chính | Overdue alerts, Blockers, Priority actions, Risk flags, Quick numbers |
| Quyết định | Việc nào làm trước, giao lại, đẩy sang mai, cần hỏi ai |
| Hành động | Open work item, Assign, Snooze, Quick reply, Ask AI |

Thứ tự section trên Today:

1. **Overdue** — quá hạn, luôn nổi trước
2. **Needs attention** — sắp hạn, blocker, chờ phản hồi
3. **Waiting for me** — assigned nhưng chưa chạm
4. **Need coordination** — cần hỏi/phối hợp
5. **Today's summary** — số liệu tổng
6. **AI brief** — tóm tắt ngắn (<3 dòng), điểm nóng

Mỗi item hiển thị: title, source, owner, due, status, next action, priority, AI hint.

#### 3.2 All Work — Operations Center

| Góc | Mô tả |
|-----|-------|
| Mục tiêu | Toàn bộ work items đang sống, tra cứu, filter, batch action |
| Thông tin chính | Work items list (không giới hạn ngày), filter mạnh, search nhanh |
| Quyết định | Việc nào tồn đọng, của ai, còn gì chưa xử lý, việc nào trôi |
| Hành động | Filter, Search, Sort, Batch action, Open work item |

Chế độ xem: List (mặc định), Board (group by status), By person, Timeline.

Khác Today: Today = khẩn + quyết định; All Work = tra cứu + xử lý toàn bộ.

#### 3.3 Work Detail — Execution Screen

| Góc | Mô tả |
|-----|-------|
| Mục tiêu | Xử lý xong việc trong màn này, không mở thêm màn khác |
| Thông tin chính | Title + Status, Next step, Context, Activity, Actions |
| Quyết định | Việc đã xong chưa? Cần làm gì tiếp? Cần hỏi ai? Cần file nào? |
| Hành động | Complete, Update status, Add note, Assign, Follow-up, Coordinate, Draft, Link, AI assist |

Cấu trúc màn:

```
Header: title, status, priority, owner, due, source
Next step — hiện ngay đầu content area
Context summary — work này là gì, liên quan ai/cái gì
Linked context — People, Documents, Contracts, Inbox thread
Activity timeline — ai làm gì, khi nào
Actions — đồng bộ với status hiện tại
AI panel — summary, suggestion, draft, reminder
```

### 4. Today Decision Model

#### 4.1 Mục đích

Today trả lời: *Trong toàn bộ work đang có, HR nên chạm việc nào trước?*

Không phải báo cáo, không phải module page, không phải inbox thứ hai.
Today là **bộ lọc + bộ xếp hạng + bộ cảnh báo** (operational triage layer).

#### 4.2 Ba tầng quyết định

```
All Work
  ↓
Eligibility filter — việc nào đủ điều kiện vào Today
  ↓
Classification — gán nhãn Critical / Attention / Planned Today / Waiting / Info
  ↓
Ranking — xếp thứ tự trong từng nhóm theo signals
  ↓
Today
```

#### 4.3 Eligibility

Item vào Today nếu có ít nhất 1 tín hiệu:
- quá hạn
- đến hạn hôm nay
- sắp chạm deadline quan trọng
- đang block việc khác
- có escalation
- có risk cao
- owner là HR, cần action hôm nay
- vừa phát sinh, độ khẩn cao

#### 4.4 Classification — 5 nhãn

| Nhãn | Ý nghĩa | Điều kiện |
|------|---------|-----------|
| Critical | Phải lên đầu | Overdue, blocking others, legal/compliance risk, external person waiting trực tiếp, deadline sát không lùi |
| Attention | Đáng chú ý | Sắp hạn, blocker nhẹ, cần review sớm, AI thấy thiếu dữ liệu, item mới thay đổi |
| Planned Today | Nên làm hôm nay | HR hoặc hệ thống đưa vào kế hoạch, cần tiến triển bình thường, không blocker mạnh |
| Waiting | Chờ bên khác | HR chưa thể làm tiếp, đợi phản hồi/file/xác nhận/approve |
| Info only | Không cần Today | Item vẫn sống trong All Work nhưng không cần trên Today |

#### 4.5 Decision Signals

Hệ thống nhóm tín hiệu:

- **Thời gian**: overdue, due today, due soon, no due date, recently changed
- **Blocking**: block item khác, dependents đang chờ, dependency chưa xong
- **Rủi ro**: legal risk, data risk, process risk, missing required artifact
- **Con người**: manager/candidate/employee/external waiting, HR explicit request
- **Trạng thái**: new, in_progress, waiting, blocked, review_needed, ready_to_complete
- **AI**: low confidence, missing field, mismatch detected, context unclear

#### 4.6 Priority Order (khi xung đột)

1. Blocking others
2. Overdue
3. Legal / compliance risk
4. External person waiting
5. Manager escalation
6. Due today
7. Due soon
8. Recently changed + unresolved
9. Planned today
10. Info only

#### 4.7 AI Role

AI làm 3 việc: **detect** → **suggest** → **explain**

**Được phép:**
- flag `Attention`
- flag `Potential Critical`
- đề xuất order trong nhóm cùng mức
- tóm tắt lý do

**Không được phép:**
- tự biến item thành `Critical` nếu không có tín hiệu cứng
- tự xoá item khỏi Today nếu item có signal quan trọng
- tự override rule ưu tiên cứng

### 5. Next Phase — Today Interaction Model

User chốt: Decision Model đủ dùng. Không đi sâu rubric/score/weight.
Bước kế tiếp là **Today Interaction Model**:

1. Một work item trên Today cho phép thao tác nhanh đến đâu?
2. Khi nào cần mở Work Detail?
3. Quick actions nào xuất hiện ngay trên card?
4. AI xuất hiện theo cơ chế nào để không gây nhiễu?
5. Làm thế nào để HR xử lý nhiều việc liên tiếp không chuyển màn hình?

Sau Interaction Model → Capabilities → Modules → Domain Model.

### 6. Dòng chảy user (đã chốt)

```
Inbox (intake chưa xử lý)
  │ triage
  ├──→ All Work
  │        │
Today ────┤
          ├── Work Detail (xử lý)
          │
          ├── People (context)
          ├── Documents (context)
          └── Contracts (context)
```

Người dùng không bao giờ cần:
- chọn module trước
- biết work type là gì
- vào People/Documents/Contracts trước khi xử lý việc
- mở AI chat riêng để hỏi thông tin

## Consequences

Positive:
- IA lấy work execution làm trung tâm, không phải module hay entity.
- Today Decision Model phân biệt rõ eligibility, classification, ranking.
- AI role được giới hạn rõ: detect, suggest, explain — không tự quyết.
- Screen skeletons định nghĩa mục tiêu, quyết định, hành động — không chỉ wireframe.
- Dòng chảy user rõ: Inbox → Today/All Work → Work Detail → Context.

Tradeoffs:
- Decision Model chưa có rubric chi tiết — implementation cần bổ sung sau.
- Chưa có Interaction Model — chưa biết quick action pattern, bulk action, AI trigger.
- Context Libraries (People/Documents/Contracts) chưa được design — chỉ biết chúng là thứ cấp.
- Chưa xác định module boundaries — không thể code cho tới khi capability mapping xong.

## Open Questions (User đang giữ)

1. One-click actions trên Today card đến đâu?
2. Khi nào cần mở Work Detail?
3. Quick actions nào trên card?
4. AI xuất hiện proactive hay reactive?
5. Flow xử lý nhiều việc liên tiếp?

## References

- ADR 0021: Product Identity + Work Taxonomy (Action Types / Work Types / AI Capabilities)
- ADR 0015, 0018, 0019: domain-level decisions, chờ Domain Model phase
