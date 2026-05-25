# Requirements Document

## Introduction

Cổng tự phục vụ nhân viên (Employee Self-Service Portal) mở rộng hệ thống VROOM HR bằng cách tích hợp tác nhân "Employee" — cho phép nhân viên trực tiếp tương tác với hệ thống thay vì chỉ được quản lý bởi HR Admin. Nhân viên có thể xem thông tin cá nhân, quản lý đơn nghỉ phép, xem chấm công, truy cập tài liệu, và gửi yêu cầu tăng ca thông qua giao diện riêng.

## Glossary

- **Portal**: Giao diện web dành cho nhân viên truy cập các chức năng tự phục vụ
- **Employee_Actor**: Người dùng đã xác thực có liên kết với bản ghi nhân viên trong hệ thống
- **Auth_Service**: Module xác thực và phân quyền hiện tại (Google OAuth2 + JWT)
- **Employee_Service**: Module quản lý thông tin nhân viên hiện tại
- **Attendance_Service**: Module quản lý chấm công hiện tại
- **Leave_Service**: Module quản lý nghỉ phép hiện tại
- **Overtime_Service**: Module quản lý tăng ca hiện tại
- **Document_Vault**: Kho lưu trữ tài liệu nhân viên trên MinIO
- **User_Employee_Link**: Liên kết giữa tài khoản đăng nhập (users) và bản ghi nhân viên (employees) dựa trên email

## Requirements

### Requirement 1: Liên kết tài khoản người dùng với nhân viên

**User Story:** As an Employee_Actor, I want my login account to be automatically linked to my employee record, so that I can access my personal HR data after logging in.

#### Acceptance Criteria

1. WHEN an Employee_Actor logs in with Google OAuth2, THE Auth_Service SHALL resolve the User_Employee_Link by matching the authenticated email with the employee email field
2. IF the authenticated user email does not match any active employee record, THEN THE Portal SHALL display a message indicating no employee profile is linked and restrict access to self-service features
3. THE Auth_Service SHALL include the linked employee_id in the JWT token claims when a User_Employee_Link exists
4. WHEN an Employee_Actor accesses any self-service endpoint, THE Portal SHALL verify that the requested resource belongs to the authenticated employee_id

### Requirement 2: Xem thông tin cá nhân

**User Story:** As an Employee_Actor, I want to view my personal information, so that I can verify my HR records are accurate.

#### Acceptance Criteria

1. WHEN an Employee_Actor requests their profile, THE Portal SHALL return the employee's full_name, email, phone, date_of_birth, gender, address, department name, position name, start_date, and contract_type
2. THE Portal SHALL mask sensitive fields (id_number, tax_code) by showing only the last 4 characters
3. WHEN an Employee_Actor requests their profile, THE Portal SHALL return the data within 500ms under normal load

### Requirement 3: Cập nhật thông tin cá nhân

**User Story:** As an Employee_Actor, I want to update my contact information, so that HR always has my current details.

#### Acceptance Criteria

1. WHEN an Employee_Actor submits a profile update, THE Portal SHALL allow modification of phone, address, and emergency contact fields only
2. THE Portal SHALL validate phone numbers using Vietnamese phone number format (10 digits starting with 0)
3. IF an Employee_Actor attempts to modify restricted fields (full_name, email, department_id, position_id, id_number, tax_code), THEN THE Portal SHALL reject the request with a 403 status code
4. WHEN a profile update is submitted, THE Employee_Service SHALL record the update timestamp in the updated_at field

### Requirement 4: Xem lịch sử chấm công

**User Story:** As an Employee_Actor, I want to view my attendance history, so that I can track my working hours and identify discrepancies.

#### Acceptance Criteria

1. WHEN an Employee_Actor requests attendance records, THE Portal SHALL return records filtered to the authenticated employee_id only
2. THE Portal SHALL support filtering attendance records by month and year
3. WHEN an Employee_Actor requests a monthly attendance report, THE Portal SHALL return daily records including check_in time, check_out time, work_hours, overtime_hours, and status
4. THE Portal SHALL display a monthly summary including total work days, total work hours, total overtime hours, late arrivals count, and early departures count
5. WHEN an Employee_Actor requests attendance records for another employee, THE Portal SHALL reject the request with a 403 status code

### Requirement 5: Chấm công (Check-in / Check-out)

**User Story:** As an Employee_Actor, I want to check in and check out myself, so that my attendance is recorded without HR intervention.

#### Acceptance Criteria

1. WHEN an Employee_Actor performs a check-in, THE Attendance_Service SHALL create an attendance record with the current server timestamp and the authenticated employee_id
2. IF an Employee_Actor attempts to check in when a check-in record already exists for the current date, THEN THE Portal SHALL reject the request and return the existing record
3. WHEN an Employee_Actor performs a check-out, THE Attendance_Service SHALL update the existing attendance record with the check-out timestamp and calculate work_hours
4. IF an Employee_Actor attempts to check out without a prior check-in on the current date, THEN THE Portal SHALL reject the request with a descriptive error message
5. THE Portal SHALL restrict check-in and check-out actions to the authenticated employee only (no proxy check-in for others)

### Requirement 6: Quản lý đơn nghỉ phép

**User Story:** As an Employee_Actor, I want to submit and track my leave requests, so that I can manage my time off without visiting HR in person.

#### Acceptance Criteria

1. WHEN an Employee_Actor submits a leave request, THE Leave_Service SHALL create a leave request with status "pending" and the authenticated employee_id
2. THE Portal SHALL display available leave balance for each leave type before the employee submits a request
3. IF the requested leave days exceed the remaining balance for the selected leave type, THEN THE Portal SHALL reject the request with a message showing current balance
4. WHEN an Employee_Actor requests their leave history, THE Portal SHALL return all leave requests for the authenticated employee_id with status, dates, and approval details
5. WHEN an Employee_Actor cancels a pending leave request, THE Leave_Service SHALL update the request status to "cancelled"
6. IF an Employee_Actor attempts to cancel an approved or rejected leave request, THEN THE Portal SHALL reject the cancellation with a descriptive error message
7. THE Portal SHALL validate that start_date is not in the past and end_date is not before start_date

### Requirement 7: Xem số dư phép

**User Story:** As an Employee_Actor, I want to view my leave balances, so that I know how many days off I have remaining.

#### Acceptance Criteria

1. WHEN an Employee_Actor requests leave balances, THE Portal SHALL return all leave type balances for the current year including total_days, used_days, and remaining_days
2. THE Portal SHALL display leave balance information grouped by leave type with the display_name of each type
3. WHEN an Employee_Actor requests leave balances for another employee, THE Portal SHALL reject the request with a 403 status code

### Requirement 8: Gửi yêu cầu tăng ca

**User Story:** As an Employee_Actor, I want to submit overtime requests, so that I can get approval for extra working hours.

#### Acceptance Criteria

1. WHEN an Employee_Actor submits an overtime request, THE Overtime_Service SHALL create the request with status "pending" and the authenticated employee_id
2. THE Portal SHALL validate that planned_hours is between 0.5 and 4.0 hours
3. THE Portal SHALL validate that work_date is not in the past (except for the current date)
4. WHEN an Employee_Actor requests their overtime history, THE Portal SHALL return all overtime requests for the authenticated employee_id
5. WHEN an Employee_Actor cancels a pending overtime request, THE Overtime_Service SHALL update the request status to "cancelled"
6. IF an Employee_Actor attempts to cancel an approved or rejected overtime request, THEN THE Portal SHALL reject the cancellation

### Requirement 9: Truy cập tài liệu cá nhân

**User Story:** As an Employee_Actor, I want to access my personal documents, so that I can download contracts, certificates, and other HR documents.

#### Acceptance Criteria

1. WHEN an Employee_Actor requests their document list, THE Portal SHALL return all documents associated with the authenticated employee_id including file_name, document_type, file_size, and uploaded_at
2. WHEN an Employee_Actor requests to download a document, THE Document_Vault SHALL generate a pre-signed URL valid for 15 minutes
3. WHEN an Employee_Actor requests documents belonging to another employee, THE Portal SHALL reject the request with a 403 status code
4. THE Portal SHALL support filtering documents by document_type

### Requirement 10: Xem lịch làm việc

**User Story:** As an Employee_Actor, I want to view my work schedule, so that I know my expected working hours and shifts.

#### Acceptance Criteria

1. WHEN an Employee_Actor requests their work schedule, THE Portal SHALL return the active work schedule assigned to the authenticated employee including shift times and working days
2. THE Portal SHALL display upcoming holidays from the holidays table that affect the employee's schedule
3. WHEN no work schedule is assigned to the employee, THE Portal SHALL return a message indicating no schedule is configured

### Requirement 11: Dashboard tổng quan nhân viên

**User Story:** As an Employee_Actor, I want a dashboard overview when I log in, so that I can quickly see my attendance status, pending requests, and important notifications.

#### Acceptance Criteria

1. WHEN an Employee_Actor accesses the dashboard, THE Portal SHALL display today's attendance status (checked-in, not checked-in, checked-out)
2. THE Portal SHALL display the count of pending leave requests and pending overtime requests on the dashboard
3. THE Portal SHALL display the current month's attendance summary (days worked, days absent, total hours) on the dashboard
4. THE Portal SHALL display remaining leave balance for the primary leave type (annual leave) on the dashboard
5. THE Portal SHALL load the dashboard data within 1000ms under normal load

### Requirement 12: Phân quyền và bảo mật

**User Story:** As a system administrator, I want employee self-service endpoints to be properly secured, so that employees can only access their own data.

#### Acceptance Criteria

1. THE Auth_Service SHALL enforce that all self-service API endpoints require a valid JWT token with an employee_id claim
2. WHEN an API request targets a resource not owned by the authenticated employee_id, THE Portal SHALL return a 403 status code
3. THE Auth_Service SHALL rate-limit self-service endpoints to 60 requests per minute per employee
4. THE Portal SHALL log all self-service data access events for audit purposes
5. IF a JWT token does not contain an employee_id claim, THEN THE Portal SHALL return a 403 status code with a message indicating employee profile is not linked
