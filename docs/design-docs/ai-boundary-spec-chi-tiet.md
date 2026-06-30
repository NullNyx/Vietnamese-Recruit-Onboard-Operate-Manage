# AI Boundary / Spec Chi Tiết — Vroom HR

Mục tiêu: định nghĩa chi tiết ranh giới, kiến trúc, tool và luồng tương tác AI trong Vroom HR. HR là actor duy nhất. AI chỉ hỗ trợ, không thay thế quyết định.

## 1. Nguyên tắc

- Read free, draft with preview, never write.
- Human-in-the-loop enforced by architecture, not discipline.
- AI is a cross-cutting capability, not a business module.
- AI chỉ gợi ý, không xác nhận, không approve, không reject, không decide workflow.
- AI phải đủ input mới propose; thiếu input thì fallback manual.

## 2. AI responsibility

| AI MAY                     | AI MUST NOT                      |
| -------------------------- | -------------------------------- |
| ✓ Draft                    | ✗ Approve                        |
| ✓ Summarize                | ✗ Reject                         |
| ✓ Suggest                  | ✗ Confirm onboarding completion  |
| ✓ Extract (as suggestion)  | ✗ Decide business workflow       |
| ✓ Remind                   | ✗ Replace HR decisions           |
| ✓ Classify                 | ✗ Write to database autonomously |
| ✓ Fill template            | ✗ Send email autonomously        |
| ✓ Highlight missing info   | ✗ Update entity status           |

## 3. AI output types

| Type | Hành vi | Write DB? | Yêu cầu HR? |
| --- | --- | --- | --- |
| **Read Answer** | Trả lời câu hỏi / summary từ Read-Tool | Không | Không |
| **Draft Action** | Preview + action_params | Không, chỉ sau HR confirm | Có, HR review → confirm |
| **Extracted Suggestion** | Kết quả parse từ file/email | Không tự update entity | Có, HR apply nếu muốn |
| **Warning / Missing Info** | Cảnh báo, không block case | Không | Có thể ignore |

## 4. Kiến trúc AI

### 4.1 Pattern

Tool-calling (ADR-0003). MVP không dùng vector RAG. AI chỉ gọi Read-Tools để lấy dữ liệu có cấu trúc từ service.

### 4.2 Module

Standalone `assistant/` module (ADR-0004). Hướng dependency một chiều:
`assistant/` → services của business module (recruitment, onboarding).
Business module không phụ thuộc `assistant/`.

### 4.3 Two tool kinds (ADR-0006)

| Tool kind | Hành vi | Ví dụ |
| --- | --- | --- |
| **Read-Tool** | Gọi service thật, trả dữ liệu live | count candidates by status, get onboarding case, list pending tasks |
| **Draft-Tool** | Không write. Trả Draft Action (action type + params + preview) | compose interview email, draft contract, generate document reminder |

Safety boundary là **structural**: LLM không có tool nào write được database.

### 4.4 Draft Action → Confirm Flow

```
HR nhập prompt
      ↓
LLM trả Draft Action (action_type, params, preview)
      ↓
UI hiển thị preview
      ↓
HR sửa (nếu cần) → confirm
      ↓
Frontend gọi real write endpoint (không qua LLM)
      ↓
AuditLog: actor = HR, source = ai_suggestion
```

### 4.5 Extraction Flow

```
HR upload file / email nhận file
      ↓
Background extraction job parse
      ↓
Tạo ExtractedSuggestion (field values, confidence)
      ↓
UI hiển thị suggestion
      ↓
HR review
      ↓
HR apply (từng field hoặc toàn bộ) → write thật
      ↓
AuditLog: actor = HR, source = ai_suggestion
```

Không auto-update DocumentItem. Extraction chỉ tạo suggestion, HR apply.

## 5. AI capabilities — scope

### 5.1 Capability map

| Capability | Module liên quan | Output type | Chi tiết |
| --- | --- | --- | --- |
| Document checklist suggestion | Document Management | Draft Action | Gợi ý danh sách giấy tờ; phát hiện missing; sinh email bổ sung |
| Information extraction | Document Management | Extracted Suggestion | Đọc CCCD, CV, giấy tờ; điền field; detect thiếu |
| Template filling | Contract Assistant | Draft Action | Điền template offer / contract / NDA / welcome email; highlight placeholder |
| Email drafting | Document / Contract / Task | Draft Action | Draft email nhắc hồ sơ, gửi lịch, nhắc ngày đi làm, follow-up |
| Activity summary | All modules | Read Answer | Daily / weekly / on-demand summary; pending / overdue |
| Remind | Timeline & Reminder | Draft Action | Nhắc nội bộ; draft email nhắc |
| Candidate data query | Recruitment (reference) | Read Answer | Count candidates; list accepted; get candidate |

### 5.2 Capability xuyên suốt

AI không phải business module riêng. Các capability trên được dùng trong ngữ cảnh của business module:

- Document Management → AI checklist suggestion + extraction + reminder
- Contract Assistant → AI template filling + draft
- Task Management → AI suggestion + reminder
- Dashboard → AI summary (on-demand MVP; scheduled daily phase 2)
- Timeline → AI reminder

## 6. Tool definition: Read-Tools

### 6.1 Onboarding (MVP)

| Tool | Input | Output |
| --- | --- | --- |
| `get_onboarding_case` | case_id | case detail + status + progress |
| `list_onboarding_cases` | status_filter, owner_hr_id | list of cases |
| `list_document_items` | case_id | document checklist + status |
| `get_contract_draft` | case_id | draft content + status |
| `list_onboarding_tasks` | case_id, status_filter | task list |
| `get_timeline` | case_id | timeline items |
| `list_pending_reminders` | case_id | pending reminders |

### 6.2 Recruitment (reference MVP)

| Tool | Input | Output |
| --- | --- | --- |
| `get_candidate` | candidate_id | candidate info |

## 7. Tool definition: Draft-Tools

### 7.1 Document

| Tool | Input | Output (proposed_items) |
| --- | --- | --- |
| `draft_document_reminder` | case_id, document_item_ids | email text yêu cầu bổ sung |
| `suggest_document_checklist` | position_context | proposed checklist items |

### 7.2 Contract

| Tool | Input | Output |
| --- | --- | --- |
| `draft_offer_letter` | template_id, candidate_info | filled offer letter content |
| `draft_labor_contract` | template_id, candidate_info | filled contract content |
| `draft_nda` | template_id, candidate_info | filled NDA content |
| `draft_welcome_email` | candidate_info | welcome email text |

### 7.3 Task

| Tool | Input | Output (proposed_items) |
| --- | --- | --- |
| `draft_task_reminder` | task_id | reminder text |
| `suggest_task_template` | position_context | proposed task items |

### 7.4 Timeline

| Tool | Input | Output |
| --- | --- | --- |
| `draft_deadline_reminder` | case_id, deadline_context | reminder text |

### 7.5 Summary

| Tool | Input | Output |
| --- | --- | --- |
| `summarize_cases` | time_range_filter | text summary (Read Answer, không cần confirm) |

## 8. Confidence & fallback

Không dùng số điểm LLM. Dùng rule-based label.

| Mức | Điều kiện | Hành vi |
| --- | --- | --- |
| **high** | Đủ required input + không còn placeholder | AI propose kèm preview, HR confirm hoặc sửa |
| **medium** | Thiếu minor field (ví dụ: salary range, chỗ ngồi) | AI propose kèm cảnh báo; HR edit trước confirm |
| **low** | Thiếu required field hoặc dữ liệu mâu thuẫn | AI không propose; trả fallback: không đủ dữ liệu; gợi ý HR bổ sung |

### 8.1 Fallback pattern

- Hiển thị kết quả như gợi ý, không như kết luận chắc chắn
- Cho phép HR sửa hoặc bỏ qua hoàn toàn
- Fallback về xử lý thủ công nếu dữ liệu quá thiếu hoặc mơ hồ
- Ghi audit với source = ai_suggestion và confidence_label

## 9. Audit integration

Mọi draft action và confirm action đều ghi audit.

| Event | Actor | Source | Ghi chú |
| --- | --- | --- | --- |
| AI suggests draft | system | ai_suggestion | confidence_label, tool_name |
| HR accepts AI draft | HR | ai_suggestion | actor HR, nhưng nguồn nội dung AI |
| HR accepts draft (tự viết) | HR | manual | HR tự nhập không qua AI |
| HR rejects draft | HR | manual | reason nullable |
| HR edits draft before confirm | HR | ai_suggestion | diff between original and final |
| AI extraction | system | ai_suggestion | extracted_fields, source_document_id |
| HR applies extraction | HR | ai_suggestion | từng field hoặc toàn bộ |
| AI summary (scheduled) | system | ai_suggestion | ghi khi scheduled, không ghi on-demand |

### 9.1 Summary audit rule

- Scheduled daily report → ghi audit
- On-demand xem nhanh trên dashboard → không ghi audit tránh phình log

## 10. Design constraints

- Workflow agnostic: không áp đặt quy trình
- Human confirmation required before write action
- AI only suggests, never auto-confirms
- All AI-generated content editable by HR
- Extraction creates suggestion, not auto-update
- Every write action audited
- System supports configurable templates
- No tool in LLM's toolset can write to database (structural safety)

## 11. Language

- MVP: hỗ trợ tiếng Việt trước
- Phase 2: option tone/language

## 12. Open questions cho review

1. Extraction job chạy synchronous trên upload flow hay async background?
2. Draft-Tool cần return preview theo format nào (markdown / json / both)?
3. Suggest tools có cần confidence label riêng cho từng proposed item không?
4. Summary scheduled có cần deliver ra ngoài (email) hay chỉ internal UI?

## 13. Next step

Sau review, chốt tài liệu này → update checklist → UX flow / screen map.
