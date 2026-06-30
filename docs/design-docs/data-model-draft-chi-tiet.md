# Data Model Draft Chi Tiết — Vroom HR

Mục tiêu: định nghĩa entity, quan hệ, state và field cốt lõi cho Vroom HR theo đúng philosophy HR Assistant. Hệ thống hỗ trợ HR theo dõi và điều phối onboarding, không chuẩn hóa workflow doanh nghiệp.

## 1. Nguyên tắc mô hình dữ liệu

- Workflow agnostic: không hard-code quy trình nội bộ của doanh nghiệp.
- HR là actor duy nhất trong phạm vi tài liệu này.
- Dữ liệu phải đủ để theo dõi, nhắc việc, tổng hợp, soạn thảo, audit.
- State càng ít càng tốt; phần nào chỉ là nhãn hiển thị thì không biến thành state machine cứng.
- Template là điểm mở rộng chính: doanh nghiệp có thể tùy biến checklist, task label, deadline, contract template.

## 2. Entity list

### 2.1 Candidate

Bản ghi ứng viên trong pipeline tuyển dụng. Chỉ giữ phần cần cho onboarding.

### 2.2 OnboardingCase

Thực thể trung tâm cho onboarding sau khi Candidate accepted.

### 2.3 DocumentTemplate

Mẫu giấy tờ cần theo dõi theo vị trí / doanh nghiệp.

### 2.4 DocumentTemplateItem

Một dòng trong template giấy tờ.

### 2.5 DocumentItem

Một giấy tờ cụ thể trong checklist của OnboardingCase.

### 2.6 ContractTemplate

Mẫu tài liệu cần điền / xuất ra cho onboarding.

### 2.7 ContractDraft

Bản nháp hợp đồng / offer / NDA do AI hoặc HR tạo.

### 2.8 TaskTemplate

Mẫu task onboarding.

### 2.9 TaskTemplateItem

Một dòng task trong template onboarding.

### 2.10 OnboardingTask

Task cụ thể được sinh ra từ template cho một OnboardingCase.

### 2.11 TimelineItem

Mốc thời gian và deadline liên quan onboarding.

### 2.12 Reminder

Nhắc việc sinh ra từ timeline, document, task, contract.

### 2.13 AuditLog

Log ghi mọi hành động có write effect hoặc human confirm.

## 3. Entity detail

## 3.1 Candidate

### Mục đích

Lưu thông tin ứng viên và trạng thái pipeline tối thiểu cần cho onboarding.

### Fields cốt lõi

- id
- organization_id
- job_opening_id nullable
- full_name
- email
- phone nullable
- status
- summary nullable
- source_email_id nullable
- created_at
- updated_at
- archived_at nullable

### Status

- accepted
- rejected
- archived

### Notes

- Candidate data đầy đủ của ATS có thể nằm ở module khác.
- Tài liệu này chỉ giữ các trạng thái đủ để khởi tạo onboarding.
- Candidate accepted là trigger tạo OnboardingCase.

## 3.2 OnboardingCase

### Mục đích

Bao bọc toàn bộ onboarding cho một Candidate accepted.

### Fields cốt lõi

- id
- organization_id
- candidate_id unique
- owner_hr_id
- case_code
- status
- start_date nullable
- target_start_date nullable
- completed_at nullable
- cancelled_at nullable
- cancelled_reason nullable
- created_by_hr_id
- updated_by_hr_id nullable
- created_at
- updated_at

### Status

- in_progress
- completed
- cancelled

### Notes

- Không cần Draft nếu case tạo xong là bắt đầu dùng.
- Completed là HR xác nhận case xong theo tiêu chí doanh nghiệp.
- Cancelled cho các trường hợp rút offer / hủy.
- `owner_hr_id` dùng cho “case của tôi” trên dashboard.

## 3.3 DocumentTemplate

### Mục đích

Định nghĩa bộ giấy tờ cần theo dõi cho một nhóm onboarding.

### Fields cốt lõi

- id
- organization_id
- name
- description nullable
- scope_key nullable
- version
- is_active
- created_at
- updated_at

### Notes

- Template phải cho phép doanh nghiệp đổi bộ giấy tờ theo policy nội bộ.
- Không hard-code danh sách giấy tờ cố định trong application logic.
- `version` nằm ngay trên template, không dùng entity version chung.

## 3.4 DocumentTemplateItem

### Mục đích

Một dòng trong template giấy tờ.

### Fields cốt lõi

- id
- document_template_id
- label
- required boolean
- sort_order
- due_offset_days nullable
- ai_hint nullable
- created_at
- updated_at

### Notes

- Mỗi template có nhiều item.
- `required` là đặc tính của item trong template.
- `due_offset_days` giúp sinh deadline tương đối nếu cần.

## 3.5 DocumentItem

### Mục đích

Một giấy tờ cụ thể trong checklist của OnboardingCase.

### Fields cốt lõi

- id
- onboarding_case_id
- document_template_item_id nullable
- label
- required boolean
- status
- origin nullable
- note nullable
- extracted_data_json nullable
- reviewed_by_hr_id nullable
- reviewed_at nullable
- created_at
- updated_at

### Status

- missing
- received
- verified
- rejected

### Notes

- `required` là flag, không phải state.
- `rejected` dùng cho file mờ, sai, thiếu hợp lệ.
- `origin` chỉ nguồn của giấy tờ: upload / email / ai_import / manual.
- `extracted_data_json` lưu dữ liệu AI parse được từ CCCD, CV, giấy tờ.

## 3.6 ContractTemplate

### Mục đích

Template cho offer / labor contract / NDA / welcome email.

### Fields cốt lõi

- id
- organization_id
- name
- contract_type
- version
- template_body
- placeholder_schema_json nullable
- is_active
- created_at
- updated_at

### Contract type

- offer_letter
- labor_contract
- nda
- welcome_email
- other

### Notes

- `version` nằm ngay trên template.
- Template phải đủ linh hoạt để fit nhiều doanh nghiệp.

## 3.7 ContractDraft

### Mục đích

Bản nháp tài liệu sinh từ template để HR review.

### Fields cốt lõi

- id
- onboarding_case_id
- contract_template_id nullable
- contract_type
- status
- title
- content
- filled_fields_json nullable
- missing_placeholders_json nullable
- exported_at nullable
- signed_at nullable
- cancelled_at nullable
- reviewed_by_hr_id nullable
- reviewed_at nullable
- revision
- created_at
- updated_at

### Status

- draft
- ready
- sent
- signed
- cancelled

### Notes

- `ready` = HR đã review xong, bản nháp đủ để export hoặc gửi ra ngoài.
- Hệ thống không xử lý e-signature.
- `content` không giới hạn text thuần.
- `revision` giúp giữ vết sửa nháp nếu HR làm nhiều vòng.

## 3.8 TaskTemplate

### Mục đích

Mẫu task onboarding do doanh nghiệp định nghĩa.

### Fields cốt lõi

- id
- organization_id
- name
- scope_key nullable
- task_category
- default_owner_label nullable
- due_offset_days nullable
- is_required boolean
- sort_order
- version
- is_active
- created_at
- updated_at

### Notes

- `task_category` do doanh nghiệp tự định nghĩa, không hard-code logic nghiệp vụ.
- `is_required` giúp phân biệt task bắt buộc và task tùy chọn.
- `version` nằm ngay trên template.

## 3.9 TaskTemplateItem

### Mục đích

Một dòng task trong template onboarding.

### Fields cốt lõi

- id
- task_template_id
- task_category
- title
- default_owner_label nullable
- due_offset_days nullable
- is_required boolean
- sort_order
- created_at
- updated_at

### Notes

- Mỗi template có nhiều item.
- Item sinh ra task thực tế cho từng OnboardingCase.

## 3.10 OnboardingTask

### Mục đích

Task thực tế sinh ra từ template cho một OnboardingCase.

### Fields cốt lõi

- id
- onboarding_case_id
- task_template_item_id nullable
- task_category
- title
- owner_label nullable
- status
- note nullable
- due_date nullable
- completed_at nullable
- blocked_reason nullable
- created_at
- updated_at

### Status

- pending
- in_progress
- completed
- blocked

### Notes

- `owner_label` là nhãn nghiệp vụ, không phải quyền hệ thống.
- Nếu cần nhiều task theo cùng category, mỗi task vẫn là một record riêng.

## 3.11 TimelineItem

### Mục đích

Lưu mốc thời gian / deadline để hiển thị timeline và tạo reminder.

### Fields cốt lõi

- id
- onboarding_case_id
- item_type
- title
- due_date
- source_type
- source_id nullable
- note nullable
- created_at
- updated_at

### Item type

- accepted
- document_deadline
- contract_deadline
- task_deadline
- start_date
- custom

### Notes

- Timeline là data hỗ trợ reminder và view, không phải workflow engine.
- Status của timeline item không cần lưu cứng; có thể derive từ due_date và current date.
- Source có thể trỏ tới DocumentItem, ContractDraft, OnboardingTask hoặc case-level milestone.

## 3.12 Reminder

### Mục đích

Nhắc việc sinh tự động từ deadline / pending / overdue.

### Fields cốt lõi

- id
- onboarding_case_id
- reminder_type
- channel
- status
- message_preview
- source_type
- source_id nullable
- scheduled_at
- sent_at nullable
- cancelled_at nullable
- created_at
- updated_at

### Reminder type

- document_missing
- contract_pending
- task_overdue
- start_date_approaching
- summary
- custom

### Channel

- internal_ui
- email_draft
- other

### Notes

- Reminder có thể chỉ là internal notification hoặc draft message.
- Không cần acknowledged state; HR đọc hay chưa đọc không ảnh hưởng business flow.
- `status` đủ dùng với pending / sent / cancelled.

## 3.13 AuditLog

### Mục đích

Truy vết mọi hành động có ảnh hưởng tới dữ liệu.

### Fields cốt lõi

- id
- organization_id
- actor_hr_id
- action
- entity_type
- entity_id
- source
- correlation_id nullable
- before_json nullable
- after_json nullable
- created_at

### Source

- manual
- ai_suggestion
- system

### Notes

- Mọi write action cần có audit.
- Audit phải đọc được ai làm, làm gì, trên object nào, từ trạng thái nào sang trạng thái nào.
- `correlation_id` gom nhiều log cho cùng một hành động AI/HR.

## 4. Quan hệ giữa entity

```text
Candidate 1 ── 1 OnboardingCase
OnboardingCase 1 ── N DocumentItem
OnboardingCase 1 ── N ContractDraft
OnboardingCase 1 ── N OnboardingTask
OnboardingCase 1 ── N TimelineItem
OnboardingCase 1 ── N Reminder
Organization 1 ── N tất cả entity chính
DocumentTemplate 1 ── N DocumentTemplateItem
TaskTemplate 1 ── N TaskTemplateItem
DocumentTemplateItem 1 ── N DocumentItem
TaskTemplateItem 1 ── N OnboardingTask
OnboardingCase / DocumentItem / ContractDraft / OnboardingTask / Reminder / TimelineItem 1 ── N AuditLog
```

## 5. State summary

### Candidate status

- accepted
- rejected
- archived

### OnboardingCase status

- in_progress
- completed
- cancelled

### DocumentItem status

- missing
- received
- verified
- rejected

### ContractDraft status

- draft
- ready
- sent
- signed
- cancelled

### OnboardingTask status

- pending
- in_progress
- completed
- blocked

### Reminder status

- pending
- sent
- cancelled

## 6. Derived data

Một số thứ chỉ nên là derived, không lưu cứng nếu không cần:

- onboarding progress %
- overdue count
- pending required documents count
- pending required task count
- dashboard summary cards
- case risk label nếu chỉ dùng để hiển thị

## 7. Open questions for review

1. `TaskTemplateItem` có cần support assignee role mặc định hay chỉ label?
2. `ContractDraft` có cần version history riêng hay `revision` là đủ?
3. `OnboardingCase` có cần `case_code` theo format nào hay chỉ unique string tự do?
4. `DocumentTemplateItem` có cần `required` + `optional_reason` không?
5. `Reminder.status` có cần thêm `failed` nếu delivery lỗi không?

## 8. Next step

Sau review bản này, chuyển sang UX screen map và API boundary.
