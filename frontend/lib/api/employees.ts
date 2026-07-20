import type {
  Employee,
  EmployeeListResponse,
  EmployeeCreateData,
  EmployeeUpdateData,
  EmployeeDocument,
  ImportResult,
} from "./types";
import type {
  EmployeeAccountCreateResponse,
  EmployeeAccountStatusResponse,
} from "./auth";
import { apiFetch, apiFetchBlob } from "./client";

const BASE = "/api/employees";
const DOCS = "/api/documents";

export async function listEmployees(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  department_id?: string;
  position_id?: string;
  is_active?: boolean;
}): Promise<EmployeeListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.page_size) searchParams.set("page_size", String(params.page_size));
  if (params?.search) searchParams.set("search", params.search);
  if (params?.department_id) searchParams.set("department_id", params.department_id);
  if (params?.position_id) searchParams.set("position_id", params.position_id);
  if (params?.is_active !== undefined) searchParams.set("is_active", String(params.is_active));

  const qs = searchParams.toString();
  return apiFetch<EmployeeListResponse>(qs ? `${BASE}?${qs}` : BASE);
}

export async function getEmployee(id: string): Promise<Employee> {
  return apiFetch<Employee>(`${BASE}/${id}`);
}

export async function createEmployee(data: EmployeeCreateData): Promise<Employee> {
  return apiFetch<Employee>(BASE, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateEmployee(id: string, data: EmployeeUpdateData): Promise<Employee> {
  return apiFetch<Employee>(`${BASE}/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/** Soft-delete an employee (sets is_active=false). Returns the deactivated employee. */
export async function deleteEmployee(id: string): Promise<Employee> {
  return apiFetch<Employee>(`${BASE}/${id}`, { method: "DELETE" });
}

export async function importEmployees(file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<ImportResult>(`${BASE}/import`, {
    method: "POST",
    body: formData,
  });
}

export async function listDocuments(employeeId: string): Promise<EmployeeDocument[]> {
  return apiFetch<EmployeeDocument[]>(`${BASE}/${employeeId}/documents`);
}

export async function uploadDocument(
  employeeId: string,
  file: File,
  documentType: string,
  description?: string,
): Promise<EmployeeDocument> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  if (description) formData.append("description", description);
  return apiFetch<EmployeeDocument>(`${BASE}/${employeeId}/documents`, {
    method: "POST",
    body: formData,
  });
}

/** Download a document into the browser via a presigned MinIO byte stream. */
export async function downloadDocument(documentId: string): Promise<Blob> {
  return apiFetchBlob(`${DOCS}/${documentId}/download`);
}

/** Delete a document (admin/HR only). */
export async function deleteDocument(documentId: string): Promise<void> {
  await apiFetch<void>(`${DOCS}/${documentId}`, { method: "DELETE" });
}

export async function getEmployeeAccountStatus(
  employeeId: string,
): Promise<EmployeeAccountStatusResponse> {
  return apiFetch<EmployeeAccountStatusResponse>(`${BASE}/${employeeId}/account`);
}

export async function createEmployeeAccount(
  employeeId: string,
): Promise<EmployeeAccountCreateResponse> {
  return apiFetch<EmployeeAccountCreateResponse>(`${BASE}/${employeeId}/account`, {
    method: "POST",
  });
}

/** Delete Employee Account. Idempotent: succeeds whether or not an account exists. */
export async function deleteEmployeeAccount(
  employeeId: string,
): Promise<void> {
  await apiFetch<void>(`${BASE}/${employeeId}/account`, { method: "DELETE" });
}