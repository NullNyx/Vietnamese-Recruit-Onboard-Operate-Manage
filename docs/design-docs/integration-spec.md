# Integration Spec — Vroom HR

Mục tiêu: chốt module nào phụ thuộc module nào, dữ liệu trao đổi, event trigger, và external connector cho MVP. Không lặp nội dung từ AI Boundary, Data Model, Flow Docs.

## 1. Dependency rule

Chiều dependency: không có cycle.

```
Recruitment ──► Onboarding ──► Document ──► Object Storage
                  ├──► Contract
                  ├──► Task
                  └──► Timeline / Reminder

Assistant ──► Tool Interface ──► Business Service

Notification ──► Reminder Service
```

- Assistant depends only on tool interfaces.
- Tool implementations may call business services.
- Business modules never depend on Assistant.

## 2. Integration matrix

| Producer | Consumer | Integration Mechanism | Data exchanged |
| --- | --- | --- | --- |
| Recruitment | Onboarding | Application Service | candidate_id, full_name, email, phone, job_opening_id, summary |
| Onboarding | Document | Application Service | onboarding_case_id, owner_hr_id, start_date |
| Onboarding | Contract | Application Service | onboarding_case_id, candidate info, contract_template_id |
| Onboarding | Task | Application Service | onboarding_case_id, task_template_id |
| Onboarding | Timeline / Reminder | Application Service | onboarding_case_id, deadline info, event type |
| Assistant | Read Tool | Tool Interface | query params, filters |
| Assistant | Draft Tool | Tool Interface | action type, params, template data |
| Reminder | Notification | Service | case_id, event type, message, due date |
| Document | Object Storage | Infrastructure SDK | file bytes, object key, bucket |

## 3. Event matrix

| Event | Producer | Consumer | Effect |
| --- | --- | --- | --- |
| Candidate Accepted | Recruitment | Onboarding | Create OnboardingCase + generate doc/task/timeline items |
| Document Uploaded | Document | AI Extraction | Create ExtractedSuggestion for file |
| Extraction Applied | HR/UI | Document | Update DocumentItem fields + status |
| AI Draft Generated | Assistant | UI | Return draft preview |
| Draft Confirmed | HR/UI | Business Service | Persist draft + audit |
| Task Status Updated | HR/UI | Task | Update OnboardingTask status |
| Reminder Due | Scheduler | Notification | Create Reminder notification |
| Reminder Dismissed | HR/UI | Notification | Mark reminder dismissed, audit |
| Case Completed | HR/UI | Onboarding | Status → completed, audit, notifications cleared |
| Case Cancelled | HR/UI | Onboarding | Status → cancelled, optional reason saved, audit |

## 4. External integrations

| Connector | Integration type | Purpose | Data direction |
| --- | --- | --- | --- |
| Object Storage | S3-compatible API | Store uploaded document files | Application → Storage (write + signed read) |
| AI Provider | LLM API (tool-calling) | Read + Draft tools | Application → Provider → Response |

Future integrations:

- SMTP / outbound mail
- Google Workspace connector

Object Storage and AI Provider are the two external integrations for MVP.

## 5. Data contract rules

- All IDs are opaque strings / UUIDs.
- All timestamps are UTC.
- Status values use domain enum, not free text.
- Nullable fields must be explicit in service boundary.
- Draft/suggestion payloads carry `source` tag for audit.
- Sensitive data (PII) redacted in integration logs.
- Version API contracts when breaking changes are introduced.

## 6. Integration constraints

- No business module calls another module's repository directly.
- All cross-module access goes through application services or tool interfaces.
- External providers are wrapped behind adapters.
- Integration contracts use DTOs instead of domain entities.

## 7. Integration ownership

| Integration | Boundary Owner |
| --- | --- |
| Recruitment → Onboarding | Recruitment |
| Onboarding → Document / Contract / Task / Timeline | Onboarding |
| Assistant → Read Tool / Draft Tool | Assistant |
| Document → Object Storage | Document |
| Reminder → Notification | Reminder |

## 8. Failure ownership

| Failure | Boundary Owner |
| --- | --- |
| Object Storage unavailable | Document |
| AI timeout | Assistant |
| Candidate not found | Recruitment |
| Reminder generation failed | Reminder |

## 9. Next step

After review, update checklist → Error/exception model.
