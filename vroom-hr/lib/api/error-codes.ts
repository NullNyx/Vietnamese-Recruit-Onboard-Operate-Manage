/**
 * Error Codes Registry — maps BE error_code → Vietnamese display message.
 *
 * Source of truth: backend/AGENTS.md Error Codes Registry section.
 * Every error_code returned by the BE should have a mapping here.
 * Unknown error_codes fall back to the raw message from the BE.
 */

export const ERROR_CODE_MESSAGES: Record<string, string> = {
  // ── Identity Module ──
  AUTH_ERROR: "Lỗi xác thực hệ thống",
  AUTH_INVALID_STATE: "Trạng thái xác thực không hợp lệ",
  AUTH_GOOGLE_ERROR: "Xác thực Google thất bại",
  AUTH_ACCESS_DENIED: "Truy cập bị từ chối. Vui lòng liên hệ quản trị viên.",
  AUTH_INSUFFICIENT_SCOPE: "Vui lòng cấp tất cả quyền được yêu cầu",
  AUTH_INVALID_TOKEN: "Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
  AUTH_RATE_LIMITED: "Quá nhiều lần đăng nhập, vui lòng thử lại sau",
  AUTH_SETUP_ALREADY_COMPLETED: "Hệ thống đã được thiết lập trước đó",

  // ── Employee Module ──
  EMPLOYEE_ERROR: "Lỗi module nhân viên",
  EMPLOYEE_DUPLICATE_EMAIL: "Email nhân viên đã tồn tại",
  EMPLOYEE_NOT_FOUND: "Không tìm thấy nhân viên",
  DEPARTMENT_NOT_FOUND: "Không tìm thấy phòng ban",
  POSITION_NOT_FOUND: "Không tìm thấy chức vụ",
  DEPARTMENT_HAS_EMPLOYEES: "Không thể xóa phòng ban có nhân viên đang hoạt động",
  POSITION_HAS_EMPLOYEES: "Không thể xóa chức vụ có nhân viên đang hoạt động",
  FILE_TOO_LARGE: "Tệp vượt quá kích thước tối đa 10MB",
  UNSUPPORTED_FILE_TYPE: "Định dạng tệp không được hỗ trợ",

  // ── Recruitment Module ──
  RECRUITMENT_ERROR: "Lỗi module tuyển dụng",
  CANDIDATE_NOT_FOUND: "Không tìm thấy ứng viên",
  CV_DOCUMENT_NOT_FOUND: "Không tìm thấy tài liệu CV",
  INVALID_STATUS_TRANSITION: "Chuyển trạng thái không hợp lệ",
  CV_FILE_MISSING: "Không tìm thấy tệp CV trong bộ nhớ",
  STORAGE_SERVICE_UNAVAILABLE: "Dịch vụ lưu trữ không khả dụng",
  GMAIL_NOT_CONNECTED: "Gmail chưa được kết nối",
  PIPELINE_TIMEOUT: "Xử lý CV quá thời gian chờ",
  OCR_EXTRACTION_FAILED: "Trích xuất OCR thất bại",
  LLM_PARSE_FAILED: "Phân tích CV bằng AI thất bại",

  // ── Attendance Module ──
  ATTENDANCE_ERROR: "Lỗi module chấm công",
  LEAVE_TYPE_NOT_FOUND: "Không tìm thấy loại nghỉ phép",
  LEAVE_REQUEST_NOT_FOUND: "Không tìm thấy đơn nghỉ phép",
  INSUFFICIENT_LEAVE_BALANCE: "Số ngày phép không đủ",
  LEAVE_OVERLAP: "Đơn nghỉ phép trùng với đơn đã tồn tại",
  INVALID_LEAVE_STATUS_TRANSITION: "Chuyển trạng thái đơn nghỉ không hợp lệ",
  LEAVE_DATE_IN_PAST: "Không thể hủy đơn nghỉ đã bắt đầu",
  ALREADY_CHECKED_IN: "Đã check-in hôm nay",
  NOT_CHECKED_IN: "Chưa check-in hôm nay",
  ALREADY_CHECKED_OUT: "Đã check-out hôm nay",
  ATTENDANCE_RECORD_NOT_FOUND: "Không tìm thấy bản ghi chấm công",
  OVERTIME_REQUEST_NOT_FOUND: "Không tìm thấy đơn tăng ca",
  OVERTIME_LIMIT_EXCEEDED: "Vượt quá giới hạn tăng ca",
  SCHEDULE_NOT_FOUND: "Không tìm thấy lịch làm việc",

  // ── Gmail Module ──
  GMAIL_ERROR: "Lỗi module Gmail",
  UNAUTHORIZED: "Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
  GMAIL_CONNECT_FAILED: "Kết nối Gmail thất bại",
  LABEL_NAMESPACE_VIOLATION: "Nhãn phải nằm trong không gian tên VroomHR/",
  GMAIL_FETCH_ERROR: "Lấy dữ liệu từ Gmail API thất bại",
  MESSAGE_NOT_FOUND: "Không tìm thấy thư Gmail",
  GMAIL_LABEL_REMOVE_FAILED: "Xóa nhãn thất bại",
  GMAIL_SEND_FAILED: "Gửi email thất bại",
  RATE_LIMITED: "Vượt quá giới hạn tần suất",

  // ── Payroll Module ──
  PAYROLL_ERROR: "Lỗi module lương",
  PERIOD_NOT_FOUND: "Không tìm thấy kỳ lương",
  PERIOD_ALREADY_CLOSED: "Kỳ lương đã đóng",
  EMPLOYEE_NOT_IN_PERIOD: "Nhân viên không trong kỳ lương",
  SALARY_NOT_CONFIGURED: "Chưa cấu hình lương cho nhân viên",
  TAX_CALCULATION_ERROR: "Tính thuế thất bại",

  // ── Self-Service Module ──
  ESS_ERROR: "Lỗi hệ thống tự phục vụ",
  ESS_FORBIDDEN: "Không thể truy cập tài nguyên này",
  ESS_NOT_FOUND: "Không tìm thấy tài nguyên",
};

/**
 * Get human-readable message for an error_code.
 * Falls back to the raw error code if not mapped.
 */
export function getErrorMessage(errorCode?: string): string {
  if (!errorCode) return '';
  return ERROR_CODE_MESSAGES[errorCode] ?? `Lỗi hệ thống (${errorCode})`;
}
