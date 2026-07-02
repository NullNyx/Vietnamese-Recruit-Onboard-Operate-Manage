export interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  gender: string | null;
  address: string | null;
  department_id: string | null;
  position_id: string | null;
  start_date: string | null;
  id_number: string | null;
  tax_code: string | null;
  employment_status: string;
  termination_date: string | null;
  contract_type: string | null;
  candidate_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeListResponse {
  items: Employee[];
  total: number;
  page: number;
  page_size: number;
}

export interface EmployeeCreateData {
  employee_code?: string;
  full_name: string;
  email?: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  department_id?: string;
  position_id?: string;
  start_date?: string;
  id_number?: string;
  tax_code?: string;
  employment_status?: string;
  termination_date?: string;
  contract_type?: string;
  candidate_id?: string;
}

export interface EmployeeUpdateData {
  employee_code?: string;
  full_name?: string;
  email?: string;
  phone?: string;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  department_id?: string;
  position_id?: string;
  start_date?: string;
  id_number?: string;
  tax_code?: string;
  employment_status?: string;
  termination_date?: string;
  contract_type?: string;
  candidate_id?: string;
  is_active?: boolean;
}


export interface Department {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Position {
  id: string;
  name: string;
  department_id: string | null;
  created_at: string;
}

export interface EmployeeDocument {
  id: string;
  employee_id: string;
  document_type: string;
  status: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  uploaded_by_hr_id: string | null;
  verified_by_hr_id: string | null;
  verified_at: string | null;
  expired_at: string | null;
  description: string | null;
  uploaded_at: string;
}

export interface DepartmentCreateData {
  name: string;
  description?: string;
}

export interface PositionCreateData {
  name: string;
  department_id?: string;
}

// ---------------------------------------------------------------------------
// Contract Types
// ---------------------------------------------------------------------------

export interface Contract {
  id: string;
  employee_id: string;
  contract_number: string | null;
  template_id: string | null;
  contract_type: string;
  status: string;
  signed_on: string | null;
  started_on: string | null;
  ended_on: string | null;
  file_path: string | null;
  signed_document_path: string | null;
  content: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string | null;
}

export interface ContractCreateData {
  contract_type: string;
  contract_number?: string;
  template_id?: string;
  content?: string;
  started_on?: string;
  ended_on?: string;
}

export interface ContractUpdateData {
  contract_number?: string;
  content?: string;
  started_on?: string;
  ended_on?: string;
  file_path?: string;
  signed_document_path?: string;
}

export interface ContractSignData {
  signed_document_path?: string;
  signed_on?: string;
}

export interface ContractRenewData {
  new_started_on?: string;
  new_ended_on?: string;
  new_content?: string;
}

export interface ContractTemplate {
  id: string;
  name: string;
  content: string;
  version: number;
  status: string;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ContractTemplateCreateData {
  name: string;
  content: string;
  file_path?: string;
}

export interface ContractTemplateUpdateData {
  name?: string;
  content?: string;
  file_path?: string;
}

export interface ContractAmendment {
  id: string;
  contract_id: string;
  name: string;
  content: string;
  status: string;
  signed_on: string | null;
  file_path: string | null;
  signed_document_path: string | null;
  created_at: string;
  created_by: string;
}

export interface ContractAmendmentCreateData {
  name: string;
  content: string;
  file_path?: string;
}

export interface EmploymentEvent {
  id: string;
  employee_id: string;
  event_type: string;
  actor_hr_id: string;
  note: string | null;
  created_at: string;
}

export interface EmployeeStatusChangeData {
  status: string;
  termination_date?: string;
  note?: string;
}


export interface ImportError {
  row: number;
  field: string;
  message: string;
}

export interface ImportResult {
  total_rows: number;
  success_count: number;
  error_count: number;
  errors: ImportError[];
  departments_created?: number;
  positions_created?: number;
}

// ---------------------------------------------------------------------------
// Gmail Integration Types
// ---------------------------------------------------------------------------

export type ConnectionStatus = "connected" | "disconnected" | "token_expired";

export interface ConnectionStatusResponse {
  status: ConnectionStatus;
  email: string | null;
}

export interface ConnectResponse {
  status: ConnectionStatus | null;
  redirect_url: string | null;
}

export interface EmailMessage {
  id: string;
  gmail_message_id: string;
  gmail_thread_id: string;
  subject: string;
  sender_email: string;
  sender_name: string;
  recipient_emails: string[];
  cc_emails: string[];
  received_at: string; // ISO datetime
  snippet: string;
  label_ids: string[];
  has_attachments: boolean;
  category: string | null;
  processing_status?: string;
}

export interface MessageBodyResponse {
  plain_text: string | null;
  html: string | null;
}

export interface SendEmailRequest {
  to: string[];
  cc?: string[];
  subject: string;
  body_html?: string;
  body_text?: string;
  reply_to_message_id?: string;
}

export interface SendEmailResponse {
  message_id: string;
  thread_id: string;
}

export interface LabelRemoveRequest {
  label_name: string;
}

export interface SyncResponse {
  synced_count: number;
  status: string;
}

export interface AttachmentMetadata {
  attachment_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
}

export interface AttachmentsResponse {
  fetched_count: number;
  skipped_count: number;
  total_count: number;
  attachments: AttachmentMetadata[];
}

export class ApiError extends Error {
  public statusCode: number;
  public errorCode: string;
  public details?: Record<string, unknown>;

  constructor(
    statusCode: number,
    errorCode: string,
    message: string,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
  }
}
