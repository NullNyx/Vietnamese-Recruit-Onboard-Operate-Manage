# Hướng dẫn Agent cho Frontend

## Stack

- Next.js 14 (App Router), TypeScript 5.6, React 18
- Tailwind CSS 3.4, shadcn/ui (Radix UI primitives)
- react-hook-form + zod validation
- lucide-react icons, sonner toasts, cmdk command palette
- date-fns, next-themes (dark mode)
- pnpm package manager
- Vitest + fast-check (property-based testing)

## Cấu trúc project

```
src/
├── app/
│   ├── (dashboard)/     # HR-only app routes (employees, recruitment, onboarding, gmail, attendance, settings, admin)
│   ├── login/           # Password login page
│   ├── setup/           # First-run setup wizard
│   └── layout.tsx       # Root layout
├── components/
│   ├── ui/              # shadcn/ui base components (KHÔNG sửa tay)
│   └── *.tsx            # App-specific components (sidebar, data-table, etc.)
├── hooks/               # Custom hooks (use-current-user, use-sidebar, use-debounce)
└── lib/
    ├── api/             # API client functions (mỗi module một file)
    ├── navigation.ts    # Sidebar nav config
    └── utils.ts         # cn() helper, formatters
```

## Quy tắc chính

1. **App Router:** dùng thư mục `app/` với layouts, pages, loading, error boundaries
2. **Server Components by default:** chỉ thêm `"use client"` khi thật cần (interactivity, hooks)
3. **API calls:** dùng `lib/api/<module>.ts` — fetch từ `/api/...` (proxy tới backend)
4. **Forms:** luôn dùng react-hook-form + zod schema validation
5. **UI components:** dùng shadcn/ui. Chạy `pnpm dlx shadcn@latest add <component>` cho component mới
6. **Styling:** chỉ Tailwind. Không CSS modules, không styled-components
7. **Icons:** chỉ lucide-react. Không dùng icon library khác
8. **Toasts:** dùng sonner (`toast.success()`, `toast.error()`)
9. **Dark mode:** mọi component phải chạy được ở light và dark mode
10. **Không Bearer tokens:** auth dùng cookie-based. API calls không cần Authorization headers

## Commands

```bash
pnpm dev          # Dev server (port 3000)
pnpm build        # Production build
pnpm lint         # ESLint
pnpm test         # Vitest (single run)
pnpm test:watch   # Vitest (watch mode)
```

## Mẫu API Client

```typescript
// lib/api/employee.ts
const API_BASE = "/api/employees";
export async function getEmployees() {
  const res = await fetch(`${API_BASE}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to fetch employees");
  return res.json();
}
```

## Mẫu Page

```typescript
// app/(dashboard)/employees/page.tsx
"use client";

import { useEffect, useState } from "react";
import { getEmployees } from "@/lib/api/employee";

export default function EmployeeListPage() {
  // ...
}
```

## Trang hiện có

| Route        | Description                                 |
| ------------ | ------------------------------------------- |
| /login       | Password login                              |
| /setup/*     | First-run setup wizard                      |
| /employees   | Employee list + CRUD                        |
| /attendance  | Check-in/out dashboard                      |
| /recruitment | Candidate pipeline                          |
| /onboarding  | Onboarding dashboard                        |
| /gmail       | Email integration                           |
| /contracts/* | Employee contract detail                    |
| /settings    | Organization, departments, positions        |
| /admin       | Users, assistant tools, audit               |
