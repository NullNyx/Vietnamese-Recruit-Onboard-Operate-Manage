import { API_BASE_URL } from "./client";

const BASE = `${API_BASE_URL}/api/guide`;

export interface GuideTask {
  id: string;
  label: string;
  done: boolean;
}

export interface GuideProgress {
  completed_tasks: string[];
  dismissed: boolean;
  all_completed: boolean;
  progress: number; // 0-100
  tasks: GuideTask[];
}

export async function getGuideProgress(): Promise<GuideProgress> {
  const res = await fetch(`${BASE}/progress`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch guide progress');
  return res.json();
}

export async function updateGuideProgress(updates: {
  completed_tasks?: string[];
  dismissed?: boolean;
}): Promise<GuideProgress> {
  const res = await fetch(`${BASE}/progress`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error('Failed to update guide progress');
  return res.json();
}

export async function dismissGuide(): Promise<GuideProgress> {
  return updateGuideProgress({ dismissed: true });
}

export async function markTaskDone(taskId: string): Promise<GuideProgress> {
  return updateGuideProgress({ completed_tasks: [taskId] });
}
