import type { Position, PositionCreateData } from "./types";
import { apiFetch } from "./client";

import { API_BASE_URL } from "./client";

const BASE = `${API_BASE_URL}/api/positions`;

export async function listPositions(): Promise<Position[]> {
  return apiFetch<Position[]>(BASE);
}

export async function createPosition(data: PositionCreateData): Promise<Position> {
  return apiFetch<Position>(BASE, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePosition(
  id: string,
  data: Partial<PositionCreateData>,
): Promise<Position> {
  return apiFetch<Position>(`${BASE}/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deletePosition(id: string): Promise<void> {
  await apiFetch<void>(`${BASE}/${id}`, { method: "DELETE" });
}