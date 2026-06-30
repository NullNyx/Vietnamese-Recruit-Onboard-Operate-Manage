# Evaluation / Acceptance Criteria — Vroom HR

Mục tiêu: định nghĩa tiêu chí đánh giá và acceptance criteria cho Vroom HR MVP, tập trung vào onboarding module. HR là actor duy nhất.

## 1. Nguyên tắc

- Mỗi tiêu chí phải measurable (pass / fail rõ ràng).
- Ưu tiên functional over non-functional ở MVP.
- Acceptance criteria test **hành vi**, không test implementation.
- AI feature acceptance: AI chỉ hỗ trợ, không quyết định.
- Workflow agnostic: hệ thống không yêu cầu doanh nghiệp thay đổi quy trình.

## 2. Acceptance criteria by module

### 2.1 Onboarding Case

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| OC-1 | HR tạo Onboarding Case từ Candidate accepted | Case tạo thành công, status in_progress, candidate_id unique |
| OC-2 | HR xem danh sách case active | Dashboard hiển thị case list, filter by my cases / all / overdue hoạt động |
| OC-3 | HR mở chi tiết một case | Case detail hiển thị candidate info + document checklist + contract + task + timeline |
| OC-4 | HR hoàn tất case | Status thành completed, audit ghi lại |
| OC-5 | HR hủy case | Status thành cancelled, optional reason lưu được, audit ghi lại |
| OC-6 | Mọi status change đều ghi audit | Audit log có đủ actor + action + object + timestamp + source |

### 2.2 Document Management

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| DM-1 | HR xem document checklist case | Checklist hiển thị từ template, mỗi item có label + status + required flag |
| DM-2 | HR tải lên file cho document item | File upload thành công, status chuyển received |
| DM-3 | HR đánh dấu verified | Status chuyển verified |
| DM-4 | HR đánh dấu rejected | Status chuyển rejected, ghi reason note |
| DM-5 | HR apply AI extraction suggestion | Extracted fields apply vào document item, audit ghi source = ai_suggestion |
| DM-6 | HR reject AI extraction suggestion | Suggestion dismissed, document item không thay đổi |
| DM-7 | AI nhắc HR khi document missing gần deadline | Notification được sinh, audit tồn tại |
| DM-8 | Template sinh document items | Tạo case → document checklist generate từ template |

### 2.3 Contract Assistant

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| CA-1 | HR xem contract draft case | Draft hiển thị content từ template + AI-filled fields |
| CA-2 | AI fill template đúng candidate info | Placeholder được thay bằng dữ liệu tương ứng |
| CA-3 | HR edit draft content | Field sửa được, lưu thành công, audit ghi lại |
| CA-4 | HR update contract progress | Status case chuyển (Draft → Ready → Sent → Signed), audit ghi |
| CA-5 | HR export draft | Export ra định dạng text / copy được |
| CA-6 | Contract generate từ template | Case tạo xong, draft tồn tại nếu template tồn tại |

### 2.4 Task Management

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| TM-1 | HR xem task list case | Task list hiển thị từ template, mỗi task có status + owner_label + due date + category |
| TM-2 | HR update task status | Status chuyển: pending → in_progress → completed / blocked |
| TM-3 | HR filter task by status / category | Filter hoạt động, list cập nhật |
| TM-4 | Task generate từ template | Tạo case → tasks generate từ task template |

### 2.5 Timeline & Reminder

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| TR-1 | HR xem timeline case | Timeline hiển thị các configured milestones |
| TR-2 | Deadline item cũ hiển thị overdue nếu quá hạn | Overdue state derive từ due date |
| TR-3 | AI sinh reminder đúng hạn | Notification được tạo vào thời điểm phù hợp |
| TR-4 | HR dismiss notification | Notification đánh dấu dismissed, không xuất hiện lại |

### 2.6 Dashboard

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| DB-1 | Dashboard hiển thị case active list | Danh sách case active, mỗi case có progress + status + candidate name |
| DB-2 | Filter my cases / all | Filter hoạt động, list cập nhật |
| DB-3 | Filter overdue | Filter hiển thị case có item overdue |
| DB-4 | Summary numbers hiển thị đúng | Total active + pending docs + pending tasks + overdue (tính live từ DB) |
| DB-5 | Needs Attention section visible | Section hiển thị case với overdue / missing doc / pending contract |

### 2.7 AI Capabilities

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| AI-1 | AI draft sinh preview, không ghi dữ liệu khi chưa có HR confirm | Preview hiển thị. DB không thay đổi cho đến khi HR confirm. |
| AI-2 | AI extraction không tự cập nhật DocumentItem | Extracted values hiển thị. Item status không đổi cho đến khi HR apply. |
| AI-3 | AI summary trả dữ liệu từ DB live | Summary đúng số liệu tại thời điểm query. |
| AI-4 | AI không thể write data nếu HR chưa confirm | Gửi yêu cầu write (update candidate status, complete task...) qua AI → AI trả lời cần HR confirm hoặc refuse. Entity không thay đổi. |
| AI-5 | AI suggestion ghi audit | Audit log có source = ai_suggestion + confidence_label + tool_name. |
| AI-6 | AI không thể hoàn tất nghiệp vụ 1 mình | Entity remains unchanged until HR confirms. Không có code path auto-confirm. |

### 2.8 Security & Audit

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| SA-1 | Auth session được bảo vệ | Cookie httpOnly + Secure + SameSite=Lax/Strict. Không có token trong localStorage. |
| SA-2 | Cross-site forged write request bị chặn | Gửi write request từ bên ngoài không có CSRF token → request bị reject. |
| SA-3 | Audit ghi đầy đủ | AuditLog có actor + action + object + timestamp + source. |
| SA-4 | PII không xuất hiện trong application log | Log không chứa CV text, contract body, ID number, raw prompt/response. |
| SA-5 | Sensitive audit diff redacted | Audit log sensitive field ghi "field changed", không lưu raw before/after. |

### 2.9 Template Management

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| TP-1 | Document/Task/Contract template available | Các loại template có thể xem trong management section |
| TP-2 | HR preview template | Preview hiển thị nội dung template + các item |
| TP-3 | HR tạo template mới | Tạo thành công, template xuất hiện trong list |
| TP-4 | HR sửa template | Sửa thành công, audit ghi lại thay đổi |
| TP-5 | System default template cho demo | Khi chưa có template nào, system default được dùng |

## 3. Integration criteria

| ID | Tiêu chí | Pass condition |
| --- | --- | --- |
| INT-1 | Candidate accepted trigger tạo OnboardingCase | Case tồn tại sau khi candidate status thành accepted |
| INT-2 | File upload gắn với DocumentItem | Uploaded file có thể xem/download từ DocumentItem |
| INT-3 | Notification mở đúng Case | Click notification → Case Detail đúng case |
| INT-4 | Audit gắn với object | Audit log có thể truy xuất theo object ID |

## 4. Non-functional criteria

| ID | Tiêu chí | Target |
| --- | --- | --- |
| NFR-1 | Response time cho list/read API | < 500ms (không có AI call) |
| NFR-2 | Response time cho AI draft | < 5s hoặc streaming |
| NFR-3 | File upload size | Configurable, default 10MB |
| NFR-4 | Concurrent users | >= 5 concurrent HR users |
| NFR-5 | Data consistency | Case không thể ở cả completed và in_progress cùng lúc |

## 5. End-to-end acceptance flows

Các flow dùng để demo / UAT. Precondition + Steps + Expected Result.

### Flow 1: Candidate → Documents → Complete

**Precondition:** Candidate accepted, onboarding case created.

| Step | Action | Expected |
| --- | --- | --- |
| 1 | HR mở Dashboard | Case visible, status = in_progress, pending docs count > 0 |
| 2 | HR mở Case Detail → Documents tab | Document checklist hiển thị items từ template |
| 3 | HR upload file cho document item | Status chuyển received, file có thể xem |
| 4 | AI extract thông tin từ file | Suggestion hiển thị inline, item chưa thay đổi |
| 5 | HR apply extraction | Fields apply, audit ghi source = ai_suggestion |
| 6 | HR mark verified | Status chuyển verified |
| 7 | HR lặp cho các required items | Checklist completed |
| 8 | HR set case completed | Status = completed, audit tồn tại, notification cleared |

### Flow 2: Contract → Review → Export

**Precondition:** Onboarding case in_progress, contract template available.

| Step | Action | Expected |
| --- | --- | --- |
| 1 | HR mở Case Detail → Contract tab | Draft hiển thị từ template, AI-filled fields |
| 2 | HR review draft | Content hiển thị đúng candidate info |
| 3 | HR sửa một field | Field updated, audit ghi |
| 4 | HR mark Ready | Status = ready |
| 5 | HR mark Sent | Status = sent |
| 6 | HR export draft | Draft được tải xuống / copy được |

### Flow 3: Reminder → Task → Completion

**Precondition:** Onboarding case in_progress, task gần deadline.

| Step | Action | Expected |
| --- | --- | --- |
| 1 | System sinh reminder | Notification visible, unread count > 0 |
| 2 | HR mở Notification Center | Reminder hiển thị, link đến case |
| 3 | HR click notification | Mở đúng Case Detail |
| 4 | HR mở Task tab | Task visible, status = pending |
| 5 | HR update task → completed | Status = completed, audit ghi |
| 6 | HR dismiss notification | Notification đánh dấu dismissed |

### Flow 4: AI Draft → Confirm

**Precondition:** Onboarding case in_progress.

| Step | Action | Expected |
| --- | --- | --- |
| 1 | HR trigger AI draft (contract / email) | Preview hiển thị, labeled "AI suggested" |
| 2 | HR sửa nội dung | Field updated, preview cập nhật |
| 3 | HR confirm | Data saved, audit ghi source = ai_suggestion |
| 4 | HR check DB | Entity updated đúng với data đã confirm |
| 5 | HR gửi AI yêu cầu write trực tiếp | AI refuses / cần HR confirm. Entity không thay đổi. |

## 6. Grading rubric (thesis evaluation — advisory, not part of system spec)

| Aspect | Weight | Criteria |
| --- | --- | --- |
| Scope correctness | 15% | Đúng HR-only, không over-scope |
| Functional completeness | 25% | Acceptance criteria pass ≥ 80% |
| AI integration | 20% | AI đúng suggestion role, audit-first |
| UX coherence | 15% | Navigation map hợp lý, state xử lý tốt |
| Code quality | 15% | Clean architecture, DI, audit |
| Documentation | 10% | Non-contradictory, đúng thiết kế |

Rubric này là tham khảo. Điều chỉnh theo yêu cầu giảng viên.

## 7. Open questions

Đã trả lời:
- Q1: 3–5 flow complete cho demo là đủ.
- Q2: Streaming AI draft là nice-to-have, không must.
- Q3: Code review không nằm trong evaluation scope.

## 8. Next step

Update checklist → Integration spec hoặc chuyển implementation phase.
