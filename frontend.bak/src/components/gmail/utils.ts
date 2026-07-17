/**
 * Gmail UI utility functions
 * - Date formatting (Vietnamese locale)
 * - File size formatting
 * - Label category extraction and color mapping
 * - Email category metadata for classification UI
 */

// ---------------------------------------------------------------------------
// Email Category Metadata
// ---------------------------------------------------------------------------

export interface CategoryMeta {
  label: string;
  icon: string;
  bg: string;
  text: string;
  border: string;
}

/**
 * Full category metadata for the classification UI.
 * Keys match the backend EmailCategory enum values.
 */
export const CATEGORY_META: Record<string, CategoryMeta> = {
  // Recruitment pipeline
  recruitment: {
    label: "Tuyển dụng",
    icon: "📄",
    bg: "bg-blue-100",
    text: "text-blue-700",
    border: "border-blue-200",
  },
  interview: {
    label: "Phỏng vấn",
    icon: "🗓️",
    bg: "bg-orange-100",
    text: "text-orange-700",
    border: "border-orange-200",
  },
  offer: {
    label: "Offer",
    icon: "🤝",
    bg: "bg-purple-100",
    text: "text-purple-700",
    border: "border-purple-200",
  },
  onboarding: {
    label: "Onboarding",
    icon: "🎉",
    bg: "bg-green-100",
    text: "text-green-700",
    border: "border-green-200",
  },
  // Employee relations
  leave_request: {
    label: "Nghỉ phép",
    icon: "🏖️",
    bg: "bg-teal-100",
    text: "text-teal-700",
    border: "border-teal-200",
  },
  payroll: {
    label: "Lương",
    icon: "💰",
    bg: "bg-emerald-100",
    text: "text-emerald-700",
    border: "border-emerald-200",
  },
  employee_request: {
    label: "Yêu cầu NV",
    icon: "📋",
    bg: "bg-sky-100",
    text: "text-sky-700",
    border: "border-sky-200",
  },
  resignation: {
    label: "Nghỉ việc",
    icon: "👋",
    bg: "bg-red-100",
    text: "text-red-700",
    border: "border-red-200",
  },
  complaint: {
    label: "Khiếu nại",
    icon: "⚠️",
    bg: "bg-rose-100",
    text: "text-rose-700",
    border: "border-rose-200",
  },
  // External
  vendor: {
    label: "Đối tác",
    icon: "🏢",
    bg: "bg-indigo-100",
    text: "text-indigo-700",
    border: "border-indigo-200",
  },
  insurance: {
    label: "Bảo hiểm",
    icon: "🛡️",
    bg: "bg-cyan-100",
    text: "text-cyan-700",
    border: "border-cyan-200",
  },
  // Internal & compliance
  internal: {
    label: "Nội bộ",
    icon: "🏠",
    bg: "bg-slate-100",
    text: "text-slate-700",
    border: "border-slate-200",
  },
  compliance: {
    label: "Pháp lý",
    icon: "⚖️",
    bg: "bg-amber-100",
    text: "text-amber-700",
    border: "border-amber-200",
  },
  // System
  notification: {
    label: "Thông báo",
    icon: "🔔",
    bg: "bg-gray-100",
    text: "text-gray-600",
    border: "border-gray-200",
  },
  uncategorized: {
    label: "Chưa phân loại",
    icon: "❓",
    bg: "bg-gray-50",
    text: "text-gray-500",
    border: "border-gray-200",
  },
};

/**
 * Category groups for the filter UI.
 * Organized by HR workflow area.
 */
export const CATEGORY_GROUPS = [
  {
    label: "Tuyển dụng",
    categories: ["recruitment", "interview", "offer", "onboarding"],
  },
  {
    label: "Nhân viên",
    categories: [
      "leave_request",
      "payroll",
      "employee_request",
      "resignation",
      "complaint",
    ],
  },
  {
    label: "Bên ngoài",
    categories: ["vendor", "insurance"],
  },
  {
    label: "Khác",
    categories: ["internal", "compliance", "notification", "uncategorized"],
  },
];

// ---------------------------------------------------------------------------
// Label Colors (backward compatible — maps to CATEGORY_META)
// ---------------------------------------------------------------------------

export const LABEL_COLORS: Record<string, { bg: string; text: string }> =
  Object.fromEntries(
    Object.entries(CATEGORY_META).map(([key, meta]) => [
      key,
      { bg: meta.bg, text: meta.text },
    ]),
  );

// Add the "processed" label which isn't a category
LABEL_COLORS["processed"] = {
  bg: "bg-gray-100",
  text: "text-gray-700",
};

// ---------------------------------------------------------------------------
// Label Category
// ---------------------------------------------------------------------------

/**
 * Extract category from a VroomHR label ID.
 * E.g. "VroomHR/recruitment" → "recruitment"
 * Returns null if the label doesn't match the VroomHR pattern.
 */
export function getLabelCategory(labelId: string): string | null {
  const match = labelId.match(/^VroomHR\/(.+)$/);
  return match ? match[1] : null;
}

// ---------------------------------------------------------------------------
// Relative Date Formatting (Vietnamese)
// ---------------------------------------------------------------------------

/**
 * Format an ISO date string as a Vietnamese relative date.
 *
 * Rules:
 * - < 1 minute  → "Vừa xong"
 * - < 60 minutes → "X phút trước"
 * - < 24 hours  → "X giờ trước"
 * - yesterday   → "Hôm qua"
 * - < 7 days    → "X ngày trước"
 * - otherwise   → dd/MM/yyyy
 */
export function formatRelativeDate(isoDate: string, now?: Date): string {
  const date = new Date(isoDate);
  const currentTime = now ?? new Date();
  const diffMs = currentTime.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMinutes < 1) return "Vừa xong";
  if (diffMinutes < 60) return `${diffMinutes} phút trước`;
  if (diffHours < 24) return `${diffHours} giờ trước`;
  if (diffDays === 1) return "Hôm qua";
  if (diffDays < 7) return `${diffDays} ngày trước`;

  // Format as dd/MM/yyyy
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

// ---------------------------------------------------------------------------
// File Size Formatting
// ---------------------------------------------------------------------------

/**
 * Format a file size in bytes to a human-readable string.
 * - < 1024 bytes → "X B"
 * - < 1 MB → "X.X KB"
 * - >= 1 MB → "X.X MB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
