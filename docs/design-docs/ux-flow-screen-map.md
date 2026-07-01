# UX Flow / Screen Map — Vroom HR

Mục tiêu: mô tả HR đi qua các màn hình như thế nào, mục tiêu từng màn, hành động chính, AI hỗ trợ gì, điều hướng sang đâu. Không đi vào UI/component chi tiết.

## 1. Nguyên tắc UX

- Tool-like focus: mỗi màn trả lời "HR cần làm gì ở đây".
- Workflow agnostic: không ép người dùng theo một luồng cố định.
- AI output luôn thể hiện rõ là suggestion/preview, không phải kết luận.
- Feedback rõ ràng: hệ thống cung cấp phản hồi rõ ràng cho mỗi action.
- Settings (template, config) không phải primary navigation.

## 2. Screen map

### 2.1 Onboarding Dashboard

**Entry Point**

- Login
- Global Search result
- Notification Center

**Purpose**

Quick overview of all active onboarding cases. HR enters onboarding module here.

**Primary Actions**

- View active case list with progress indicator
- Filter by: my cases / all / overdue
- Open a case to Case Detail
- Access Notification Center

**AI Support**

- Daily summary card (total active, pending documents, overdue cases)
- Needs Attention summary for cases with overdue items, missing documents, or pending contract

**Navigation**

→ Onboarding Case Detail (when HR opens a case)
→ Notification Center
→ Global Search result

**States**

| State | Behaviour |
| --- | --- |
| Normal | case list + summary |
| Empty (no active case) | "Chưa có onboarding case nào" + link tới candidate list |
| Loading | skeleton placeholders |
| Error | retry button + error message |

### 2.2 Onboarding Case Detail

**Entry Point**

- Onboarding Dashboard
- Global Search result
- Notification Center

**Purpose**

Process one onboarding case fully: documents, contract, tasks, timeline.

**Primary Actions**

- View candidate information
- Manage document checklist
- Review/edit contract draft
- Track tasks
- View timeline milestones

**AI Support**

- Document checklist suggestion
- Information extraction from uploaded files
- Template filling for contract
- Task generation from template
- Deadline reminder

**Navigation**

→ Document checklist actions (inline)
→ Contract review (inline or sub-tab)
→ Task board (inline or sub-tab)
→ Timeline view (inline or sub-tab)
→ Template Management (Settings)

**States**

| State | Behaviour |
| --- | --- |
| Normal | tabbed or sectioned view |
| Loading | skeleton per section |
| Error | section-level error banner + retry |

### 2.3 Document Checklist

Part of Case Detail.

**Purpose**

Review and manage required documents for this onboarding case.

**Primary Actions**

- Upload document file
- View / download uploaded file
- Mark verified
- Mark rejected (với reason note)
- Apply or reject AI extraction suggestion

**AI Support**

- Extract information from uploaded file (CCCD, CV, certificate)
- Suggest additional checklist items
- Remind HR when document is still missing near deadline

**Navigation**

→ Case Detail (back)

### 2.4 Contract Review

Part of Case Detail.

**Purpose**

Prepare onboarding documents: offer letter, labor contract, NDA, welcome email.

**Primary Actions**

- Review AI-filled draft from template
- Edit draft content
- Update contract progress
- Export / copy draft content

**AI Support**

- Fill template with candidate info
- Highlight placeholder còn thiếu
- Generate email draft for sending to candidate

**Navigation**

→ Case Detail (back)

### 2.5 Task Board

Part of Case Detail.

**Purpose**

Track onboarding tasks and update their progress.

**Primary Actions**

- View task list
- Update task status
- Update task owner label
- Filter by status / category

**AI Support**

- Generate tasks from template
- Remind when task is overdue

**Navigation**

→ Case Detail (back)

### 2.6 Timeline View

Part of Case Detail.

**Purpose**

Review upcoming milestones and deadlines for this case.

**Primary Actions**

- View milestone timeline
- View deadline / reminder

**AI Support**

- Generate reminder for near-deadline items

**Navigation**

→ Case Detail (back)

### 2.7 Notification Center

**Purpose**

View reminders, AI suggestions, system notifications in one place.

**Primary Actions**

- See unread count
- Open notification to see context
- Mark as read or dismiss
- Link to relevant case

**AI Support**

- Daily summary notification
- Overdue task/document reminder
- Missing document alert
- Contract signing follow-up reminder

**Navigation**

→ Relevant Case Detail (on click)
→ Notification Center (accessible from dashboard top bar)

**States**

| State | Behaviour |
| --- | --- |
| Normal | notification list grouped by date |
| Empty | "Không có thông báo mới" |
| Loading | skeleton |
| Error | error message |

### 2.8 Template Management

**Entry Point**

- Settings
- Case Detail → template-related action

**Purpose**

Manage templates used during onboarding generation.

**Primary Actions**

- View template list (Document / Task / Contract)
- Preview template
- Create new template
- Edit existing template
- Set template version

**AI Support**

- Suggest template content based on position/context (future)

**Navigation**

→ Settings / Management section

**States**

| State | Behaviour |
| --- | --- |
| Normal | list grouped by type (3 tabs: Document, Task, Contract) |
| Empty | "Chưa có template" + create button. System defaults for demo. |
| Loading | skeleton |
| Error | error message |

## 3. AI interaction flow (cross-cutting)

### 3.1 AI Draft Flow

```
HR clicks "Generate Draft" or prompts AI
        ↓
AI processes input → preview appears
        ↓
HR reviews preview (marked as "AI suggested")
        ↓
HR edits (optional)
        ↓
HR confirms → data saved, audit written
```

### 3.2 AI Extraction Flow

```
HR uploads document
        ↓
Background extraction → suggestion appears inline
        ↓
HR reviews extracted fields
        ↓
HR applies per field or all → field updated
        ↓
HR rejects → suggestion dismissed
```

## 4. Navigation map (user flow)

```
Login
  ↓
Global Search / Onboarding Dashboard
  ├── Case Detail ──┬── Document tab
  │                  ├── Contract tab
  │                  └── Task tab / Timeline tab
  ├── Notification Center
  └── Template Management (Settings)
        ├── Document Templates
        ├── Task Templates
        └── Contract Templates
```

- Template Management is settings, not core onboarding flow.
- HR can jump from Notification Center directly into a relevant Case Detail.
- Global Search can reach cases and notifications.

## 5. Quyết định thiết kế đã chốt (Locked Design Decisions)

1. **Phần quyền màn hình**: MVP chỉ sử dụng một vai trò duy nhất là `HR`/`Admin`, chưa phân tách màn hình phức tạp cho `HR Admin` vs `HR Member` để tránh tăng độ phức tạp RBAC.
2. **Template Management**: MVP chỉ hỗ trợ ghi đè (overwrite) cấu hình và ghi log audit thay đổi, chưa xây dựng giao diện hiển thị lịch sử phiên bản (version history UI).
3. **Notification Center**: Tải lại dữ liệu (refresh) dựa trên hành động của người dùng hoặc polling cơ bản, chưa áp dụng cơ chế realtime phức tạp.

## 6. Next step

After review, update checklist → UI wireframe / design spec.
