import type { Department, DepartmentCreateData } from "./types";
import { apiFetch } from "./client";

import { API_BASE_URL } from "./client";

const BASE = `${API_BASE_URL}/api/departments`;

export async function listDepartments(): Promise<Department[]> {
  return apiFetch<Department[]>(BASE);
}

export async function createDepartment(data: DepartmentCreateData): Promise<Department> {
  return apiFetch<Department>(BASE, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateDepartment(
  id: string,
  data: Partial<DepartmentCreateData>,
): Promise<Department> {
  return apiFetch<Department>(`${BASE}/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteDepartment(id: string): Promise<void> {
  await apiFetch<void>(`${BASE}/${id}`, { method: "DELETE" });
}