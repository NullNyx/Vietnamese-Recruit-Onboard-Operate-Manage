import type {
  Contract,
  ContractCreateData,
  ContractUpdateData,
  ContractSignData,
  ContractRenewData,
  ContractTemplate,
  ContractTemplateCreateData,
  ContractTemplateUpdateData,
  ContractAmendment,
  ContractAmendmentCreateData,
  EmployeeDocument,
  Employee,
  EmployeeListResponse,
  EmployeeCreateData,
  EmployeeUpdateData,
  EmploymentEvent,
  EmployeeStatusChangeData,
  ImportResult,
} from "./types";

const BASE = "/api/employees";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(error.error?.message || `Request failed: ${res.status}`);
  }
  return res.json();
}

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

  const url = searchParams.toString() ? `${BASE}?${searchParams}` : BASE;
  const res = await fetch(url);
  return handleResponse<EmployeeListResponse>(res);
}

export async function getEmployee(id: string): Promise<Employee> {
  const res = await fetch(`${BASE}/${id}`);
  return handleResponse<Employee>(res);
}

export async function createEmployee(data: EmployeeCreateData): Promise<Employee> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Employee>(res);
}

export async function updateEmployee(id: string, data: EmployeeUpdateData): Promise<Employee> {
  const res = await fetch(`${BASE}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Employee>(res);
}

export async function deleteEmployee(id: string): Promise<Employee> {
  const res = await fetch(`${BASE}/${id}`, { method: "DELETE" });
  return handleResponse<Employee>(res);
}

export async function importEmployees(file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/import`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<ImportResult>(res);
}

export async function listDocuments(employeeId: string): Promise<EmployeeDocument[]> {
  const res = await fetch(`${BASE}/${employeeId}/documents`);
  return handleResponse<EmployeeDocument[]>(res);
}

export async function uploadDocument(
  employeeId: string,
  file: File,
  documentType: string,
  description?: string
): Promise<EmployeeDocument> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  if (description) formData.append("description", description);
  const res = await fetch(`${BASE}/${employeeId}/documents`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<EmployeeDocument>(res);
}

export async function downloadDocument(documentId: string): Promise<Blob> {
  const res = await fetch(`/api/documents/${documentId}/download`);
  if (!res.ok) throw new Error("Download failed");
  return res.blob();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`/api/documents/${documentId}`, { method: "DELETE" });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: "Delete failed" } }));
    throw new Error(error.error?.message || "Delete failed");
  }
}




const CONTRACT_TEMPLATES_BASE = "/api/contract-templates";

export async function listEmployeeContracts(employeeId: string): Promise<Contract[]> {
  const res = await fetch(`${BASE}/${employeeId}/contracts`);
  return handleResponse<Contract[]>(res);
}



export async function createEmployeeContract(
  employeeId: string,
  data: ContractCreateData
): Promise<Contract> {
  const res = await fetch(`${BASE}/${employeeId}/contracts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Contract>(res);
}

export async function getContract(contractId: string): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}`);
  return handleResponse<Contract>(res);
}

export async function updateContract(
  contractId: string,
  data: ContractUpdateData
): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Contract>(res);
}

export async function sendContractForSigning(contractId: string): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}/send-for-signing`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<Contract>(res);
}

export async function signContract(contractId: string, data: ContractSignData): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}/sign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Contract>(res);
}

export async function renewContract(contractId: string, data: ContractRenewData): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}/renew`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Contract>(res);
}

export async function terminateContract(contractId: string): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}/terminate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<Contract>(res);
}

export async function cancelContract(contractId: string): Promise<Contract> {
  const res = await fetch(`/api/contracts/${contractId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<Contract>(res);
}

export async function listContractTemplates(): Promise<ContractTemplate[]> {
  const res = await fetch(CONTRACT_TEMPLATES_BASE);
  return handleResponse<ContractTemplate[]>(res);
}

export async function createContractTemplate(
  data: ContractTemplateCreateData
): Promise<ContractTemplate> {
  const res = await fetch(CONTRACT_TEMPLATES_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<ContractTemplate>(res);
}

export async function updateContractTemplate(
  templateId: string,
  data: ContractTemplateUpdateData
): Promise<ContractTemplate> {
  const res = await fetch(`${CONTRACT_TEMPLATES_BASE}/${templateId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<ContractTemplate>(res);
}

export async function archiveContractTemplate(templateId: string): Promise<ContractTemplate> {
  const res = await fetch(`${CONTRACT_TEMPLATES_BASE}/${templateId}/archive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<ContractTemplate>(res);
}

// ---------------------------------------------------------------------------
// Employment Events
// ---------------------------------------------------------------------------

/** GET /api/employees/{employeeId}/events */
export async function listEmployeeEvents(employeeId: string): Promise<EmploymentEvent[]> {
  const res = await fetch(`${BASE}/${employeeId}/events`);
  return handleResponse<EmploymentEvent[]>(res);
}

export async function changeEmployeeStatus(
  employeeId: string,
  data: EmployeeStatusChangeData
): Promise<Employee> {
  const res = await fetch(`${BASE}/${employeeId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<Employee>(res);
}

// ---------------------------------------------------------------------------
// Document status actions
// ---------------------------------------------------------------------------

/** POST /api/documents/{documentId}/verify */
export async function verifyDocument(documentId: string): Promise<EmployeeDocument> {
  const res = await fetch(`/api/documents/${documentId}/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<EmployeeDocument>(res);
}

/** POST /api/documents/{documentId}/reject */
export async function rejectDocument(
  documentId: string,
  note?: string
): Promise<EmployeeDocument> {
  const res = await fetch(`/api/documents/${documentId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  return handleResponse<EmployeeDocument>(res);
}

/** POST /api/documents/{documentId}/expire */
export async function markDocumentExpired(documentId: string): Promise<EmployeeDocument> {
  const res = await fetch(`/api/documents/${documentId}/expire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return handleResponse<EmployeeDocument>(res);
}


// ---------------------------------------------------------------------------
// Contract Amendments
// ---------------------------------------------------------------------------

/** GET /api/contracts/{contractId}/amendments */
export async function listContractAmendments(contractId: string): Promise<ContractAmendment[]> {
  const res = await fetch(`/api/contracts/${contractId}/amendments`);
  return handleResponse<ContractAmendment[]>(res);
}

/** POST /api/contracts/{contractId}/amendments */
export async function createContractAmendment(
  contractId: string,
  data: ContractAmendmentCreateData
): Promise<ContractAmendment> {
  const res = await fetch(`/api/contracts/${contractId}/amendments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<ContractAmendment>(res);
}
