# Vroom HR

Vroom HR là nền tảng HRM mã nguồn mở, tự triển khai cho doanh nghiệp Việt Nam.
Mỗi công ty chạy một bản riêng (một database, một server).
Bảng thuật ngữ này chuẩn hóa tên gọi domain để cả đội dùng một từ cho một
khái niệm xuyên suốt spec, code, và tài liệu.

## Quy tắc Actor

**HR/Admin** là actor duy nhất. Mọi hành động ghi đều do HR/Admin thực hiện.
Không có actor hướng đến employee; không có employee login hay self-service.
Dữ liệu employee được cung cấp làm input (ví dụ đơn nghỉ phép, cập nhật hồ sơ)
được HR/Admin nhập hoặc import, không phải employee tự nhập.
_Avoid_: Employee, Applicant, User làm actor

## Ngôn ngữ

**Organization**:
Công ty duy nhất sở hữu một bản cài đặt. Là singleton — chính xác một
mỗi instance đang chạy. Chứa cấu hình cấp công ty (tên, mã số thuế,
múi giờ, ngày lễ, domain email được phép). KHÔNG phải ranh giới phân cách dữ liệu.
_Avoid_: Company, Tenant, Account, Client

**Tenant**:
Thuật ngữ kế thừa từ Policy Engine, nơi `tenant_id` được thiết kế làm khóa
phân cách đa công ty. Trong mô hình self-hosted chỉ có một công ty
mỗi bản cài đặt, nên `tenant_id` thực chất là hằng số.
_Avoid_: dùng Tenant như thể nhiều công ty chung một bản cài đặt

**HR**:
Vai trò người dùng duy nhất. Quản lý hồ sơ employee, hợp đồng, tài liệu, và
vận hành cho Organization. Ánh xạ tới role `admin` hiện tại.
_Avoid_: User (User là khái niệm tài khoản auth)

**Employee**:
Người có hồ sơ lao động trong hệ thống. Employee là thực thể gốc
— mọi tác vụ HR (hợp đồng, tài liệu, chấm công, nghỉ phép, lương,
sự kiện lao động) xoay quanh bản ghi này. Employee KHÔNG phải system user — không
login, không self-service, không quyền ghi.
_Avoid_: User, Account, Member

**Employee Record**:
Tập hợp toàn bộ dữ liệu gắn với một Employee: thông tin cá nhân, trạng thái
lao động, hợp đồng, tài liệu, sự kiện lao động. Nguồn chân lý cho các tác vụ HR.
Chính xác một bản ghi mỗi Employee.
_Avoid_: Profile (quá hẹp), Staff file

**Employment Status**:
Trạng thái hiện tại của mối quan hệ giữa Employee với Organization.
Giá trị: active / resigned / terminated / suspended. Lưu trực tiếp trên Employee.

**Document**:
File đính kèm vào Employee Record (ví dụ scan CCCD, bằng cấp, thẻ bảo hiểm).
Trạng thái: uploaded / verified / rejected / expired. Do HR upload.
_Avoid_: Attachment (quá chung chung)

**Employment Event**:
Thay đổi được ghi nhận trong dữ liệu hoặc trạng thái của Employee.
Loại: profile*update, promotion, transfer, status_change, termination,
document_update, contract_update. Lưu ảnh chụp trước/sau và actor.
\_Avoid*: Audit log (audit log là khái niệm hệ thống rộng hơn)

**Contract**:
Văn bản pháp lý giữa Organization và Employee (hợp đồng lao động,
thư mời nhận việc, NDA). Trạng thái: draft / pending*signature / active /
expired / terminated / cancelled. Một Employee có thể có nhiều Contract.
\_Avoid*: Employment contract (quá hẹp cho NDA/offer)

**Contract Template**:
Mẫu dùng lại để tạo nháp Contract. Có phiên bản (versioning).
Trạng thái: active / archived.

**Contract Amendment**:
Văn bản bổ sung đính kèm vào Contract đang active. Trạng thái: draft /
pending_signature / signed / cancelled.

## Tuyển dụng (vertical slice 1)

Các thuật ngữ bên dưới thuộc slice Tuyển dụng & Onboarding — vertical đầu tiên
xây dựng trên Employee Record làm module lõi. Chúng vẫn là chuẩn trong slice đó.

**Candidate**:
Người đang được xem xét tuyển dụng, được tạo (tự động hoặc thủ công) từ
CV đã phân tích. Di chuyển qua pipeline: new → reviewing → interview*scheduled →
accepted/rejected/archived. Candidate KHÔNG phải Employee.
\_Avoid*: Applicant, Employee

**Job Opening**:
Nhu cầu tuyển cụ thể cho một Position trong Organization. Department của nó
được suy ra từ Position đó. Tùy chọn nhóm các Candidate đang xét và
theo dõi target headcount. Vòng đời: draft → open → closed/cancelled.
_Avoid_: Recruitment Plan, Hiring Plan, Vacancy, Requisition

**Backbone Flow**:
Vertical slice đầu tiên: email đến → phân loại intent bằng AI → phân tích
CV → Candidate → HR review → lên lịch phỏng vấn → accept →
email chúc mừng → onboarding. Đây là slice 1, không phải ranh giới sản phẩm.
_Avoid_: coi đây là luồng duy nhất

**Onboarding**:
Quy trình theo checklist do HR điều phối, dựa trên Onboarding Case. Candidate
được accept tạo ra Onboarding Case; HR xác nhận hoàn tất trước khi
Employee record được tạo hoặc kích hoạt.
_Avoid_: Promotion, Hiring

**Onboarding Case**:
Thực thể gốc cho quy trình onboarding. Trạng thái: in_progress → complete /
cancelled. Case sẵn sàng hoàn tất sau khi checklist đủ điều kiện, sau đó HR
xác nhận hoàn tất và Employee record được tạo hoặc kích hoạt.

**Onboarding Task**:
Một mục đơn lẻ trong checklist của Onboarding Case.
Trạng thái: pending / done.

## Năng lực AI

**AI Automation**:
Tác vụ AI nền chạy theo sự kiện, không có hội thoại: phân loại intent email,
phân tích CV, trích xuất tài liệu.
_Avoid_: gọi nó là "the AI Agent"

**AI Assistant**:
Trợ lý hội thoại chỉ dành cho HR. Có thể ĐỌC dữ liệu từ Employee Records,
tuyển dụng, và onboarding; SOẠN THẢO hành động (ví dụ soạn hợp đồng, tạo
nhắc nhở); và TỔNG HỢP dữ liệu. Không bao giờ ghi — an toàn cấu trúc: không
có tool nào trong bộ tool của LLM có thể ghi database. HR xác nhận mọi lần ghi.
_Avoid_: Chatbot (quá chung chung), Agent (ngụ ý tự chủ ghi)

**AI Agent (autonomous)**:
Năng lực giả định tương lai nơi AI tự quyết và thực hiện ghi.
Hoàn toàn ngoài phạm vi.
_Avoid_: dùng "Agent" cho Assistant hiện tại

## Bên trong AI Assistant

**Tool**:
Hàm có kiểu mà AI Assistant có thể gọi. Chính xác hai loại: Read-Tool và
Draft-Tool. LLM không bao giờ có tool có khả năng ghi.
_Avoid_: Function, Plugin, Skill

**Read-Tool**:
Thực thi một lần đọc thực sự qua service có sẵn, trả về dữ liệu thực.
An toàn gọi tự do.
_Avoid_: Query (dành riêng cho tầng command/query)

**Draft-Tool**:
Trả về Draft Action có cấu trúc (loại action + tham số + bản xem trước) mà
không ghi. LLM chỉ có thể đề xuất; không thể hành động.
_Avoid_: Write-tool, Action-tool

**Draft Action**:
Đề xuất có cấu trúc do Draft-Tool trả về. HR xem xét; khi xác nhận,
frontend gọi trực tiếp endpoint ghi thực sự (không qua LLM).
_Avoid_: Auto-action, Command

## Xác thực & Thiết lập

**Authentication**:
Đăng nhập bằng mật khẩu (email + mật khẩu) dùng PBKDF2-SHA-256 hashing.
Dùng httpOnly secure cookies (`access_token`, `refresh_token`).
Không Google OAuth, không social login, không đăng ký công khai.
_Avoid_: OAuth, Bearer tokens

**Initial Setup Wizard**:
Luồng một lần tạo SUPER*ADMIN đầu tiên và cấu hình Organization
trước khi dashboard có thể truy cập. Route: `/setup/*`.
Sau khi hoàn tất, endpoint setup bị khóa vĩnh viễn.
\_Avoid\*: gọi nó là "onboarding"

**SUPER_ADMIN**:
Vai trò có quyền cao nhất, được tạo trong Initial Setup Wizard.
Có thể quản lý system user, gán vai trò, và thực hiện mọi tác vụ HR.
Chính xác một SUPER*ADMIN tồn tại mỗi bản cài đặt.
\_Avoid*: Super User (kế thừa)

**HR_ADMIN**:
Vai trò tác vụ HR đầy đủ. Có thể quản lý employee, hợp đồng, onboarding,
tuyển dụng, chấm công, lương, và cấu hình AI.
_Avoid_: Admin (gây nhầm với SUPER_ADMIN)

**HR_STAFF**:
Vai trò HR giới hạn, có quyền đọc+ghi vào tác vụ employee nhưng không
có quản trị hệ thống hay quản lý người dùng.
_Avoid_: User (gây nhầm với auth-account), Employee
