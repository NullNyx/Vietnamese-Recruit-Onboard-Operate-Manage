# Implementation Plan:

## Overview

Triển khai UI redesign cho Vroom HR theo kiro-kit design philosophy. Chia thành 4 phase: Foundation → Shell → Pages → Polish. Mỗi task có thể thực hiện độc lập trong phase của nó.

## Tasks

- [x] 1. Rewrite `frontend/src/app/globals.css` with full design token system: light theme CSS variables (background, foreground, card, popover, primary deep-teal, secondary, muted, accent warm-amber, destructive, border, input, ring, sidebar, chart-1 through chart-5) + `.dark` class with all dark theme variables + stagger animation utilities + reduced-motion media query
  - Requirements: 1, 3
  - Files: `frontend/src/app/globals.css`

- [x] 2. Update `frontend/tailwind.config.ts`: add `darkMode: "class"`, font families (heading, body), animation keyframes (fade-in, slide-in-from-left, scale-in, slide-up), animation utilities, extended colors for sidebar and chart tokens, shadow tokens (sm, md, lg), border-radius tokens
  - Requirements: 1, 6
  - Files: `frontend/tailwind.config.ts`

- [x] 3. Update `frontend/src/app/layout.tsx`: replace Inter with Plus Jakarta Sans (heading) + DM Sans (body) via next/font with latin-ext subset, set `lang="vi"`, add antialiased class, install and wrap with ThemeProvider (next-themes, attribute="class", defaultTheme="system"), add suppressHydrationWarning to html tag
  - Requirements: 2, 3, 14
  - Dependencies: Task 1, Task 2
  - Files: `frontend/src/app/layout.tsx`

- [x] 4. Install shadcn/ui components and dependencies: run `pnpm dlx shadcn@latest add input label textarea select checkbox switch dialog sheet dropdown-menu table card badge avatar tooltip separator skeleton tabs command popover calendar sonner form navigation-menu`, install peer deps `pnpm add next-themes sonner react-hook-form @hookform/resolvers zod cmdk date-fns`
  - Requirements: 4
  - Files: `frontend/package.json`, `frontend/src/components/ui/*`

- [x] 5. Create `frontend/src/components/theme-toggle.tsx`: DropdownMenu with 3 options (Sáng/Sun, Tối/Moon, Hệ thống/Monitor), uses useTheme() from next-themes, keyboard accessible (Tab, Enter, Arrow keys)
  - Requirements: 3
  - Dependencies: Task 3, Task 4
  - Files: `frontend/src/components/theme-toggle.tsx`

- [x] 6. Create `frontend/src/hooks/use-sidebar.ts`: manages collapsed/expanded boolean state, persists to localStorage key "sidebar-collapsed", defaults to expanded if localStorage unavailable
  - Requirements: 5
  - Files: `frontend/src/hooks/use-sidebar.ts`

- [x] 7. Create `frontend/src/components/app-sidebar.tsx`: collapsible sidebar (expanded 256px with icon+label, collapsed 64px icon-only with tooltips), toggle button, width transition 200ms ease-out, Vietnamese nav labels (Tổng quan, Nhân viên, Phòng ban, Chức vụ, Gmail), active link with primary color, user section at bottom with logout
  - Requirements: 5, 14
  - Dependencies: Task 4, Task 6
  - Files: `frontend/src/components/app-sidebar.tsx`

- [x] 8. Add mobile navigation: on viewport < 768px hide sidebar, show hamburger button in header that opens Sheet (slide from left) with same nav content, Sheet closes on nav link click / outside click / close button / Escape, touch targets minimum 44x44px
  - Requirements: 5, 12
  - Dependencies: Task 7
  - Files: `frontend/src/components/app-sidebar.tsx`, `frontend/src/app/(dashboard)/layout.tsx`

- [x] 9. Create `frontend/src/components/breadcrumbs.tsx`: reads pathname, maps route segments to Vietnamese labels (employees→Nhân viên, settings→Cài đặt, departments→Phòng ban, positions→Chức vụ, gmail→Gmail), ancestor segments are clickable links, last segment is plain text
  - Requirements: 5, 14
  - Files: `frontend/src/components/breadcrumbs.tsx`

- [x] 10. Create `frontend/src/components/command-bar.tsx`: uses shadcn/ui Command (cmdk), triggered by ⌘K/Ctrl+K, lists all navigation pages with Vietnamese labels, real-time filter, navigate on selection, close on Escape, empty state "Không tìm thấy kết quả"
  - Requirements: 5
  - Dependencies: Task 4
  - Files: `frontend/src/components/command-bar.tsx`

- [x] 11. Rewrite `frontend/src/app/(dashboard)/layout.tsx`: integrate AppSidebar (collapsible + mobile Sheet), Header with [MobileMenuTrigger | Breadcrumbs | spacer | CommandBarTrigger | ThemeToggle], main content area with page transition wrapper, register ⌘K keyboard shortcut
  - Requirements: 5, 12
  - Dependencies: Task 5, Task 7, Task 8, Task 9, Task 10
  - Files: `frontend/src/app/(dashboard)/layout.tsx`

- [x] 12. Create `frontend/src/components/page-transition.tsx`: wraps children with fade-in animation keyed by pathname, duration 200ms, opacity 0→1, respects prefers-reduced-motion
  - Requirements: 6
  - Dependencies: Task 2
  - Files: `frontend/src/components/page-transition.tsx`

- [x] 13. Rewrite `frontend/src/app/(dashboard)/page.tsx` (Dashboard): fetch summary stats from API (employees, departments, positions, unread emails), display 4 StatCard components with lucide icons, "Hành động nhanh" section with shortcut buttons, responsive grid (1/2/4 columns), skeleton loading, staggered fade-in animation
  - Requirements: 8
  - Dependencies: Task 4, Task 11
  - Files: `frontend/src/app/(dashboard)/page.tsx`, `frontend/src/components/stat-card.tsx`

- [x] 14. Create `frontend/src/components/data-table.tsx` and `frontend/src/hooks/use-debounce.ts`: reusable DataTable with columns config, search input (debounced 300ms), pagination controls (page/total/size selector 10/20/50/100), skeleton rows while loading, empty state "Không có dữ liệu", error state "Lỗi: ...", row click handler
  - Requirements: 9
  - Dependencies: Task 4
  - Files: `frontend/src/components/data-table.tsx`, `frontend/src/hooks/use-debounce.ts`

- [x] 15. Add responsive card layout to DataTable: when viewport < 768px, render cards instead of table, each card shows labeled field-value pairs preserving all visible data from table columns
  - Requirements: 9, 12
  - Dependencies: Task 14
  - Files: `frontend/src/components/data-table.tsx`

- [x] 16. Rewrite employee list page using DataTable: columns (Họ tên, Email, Phòng ban, Chức vụ, Trạng thái), toolbar filters (department, position, active status), action buttons ("Thêm nhân viên", "Import Excel"), row click navigates to detail
  - Requirements: 9, 14
  - Dependencies: Task 14
  - Files: `frontend/src/app/(dashboard)/employees/page.tsx`

- [x] 17. Rewrite department and position pages using DataTable: departments (Tên, Mô tả, Số nhân viên), positions (Tên, Phòng ban, Mô tả), action button "Thêm mới"
  - Requirements: 9, 14
  - Dependencies: Task 14
  - Files: `frontend/src/app/(dashboard)/settings/departments/page.tsx`, `frontend/src/app/(dashboard)/settings/positions/page.tsx`

- [x] 18. Redesign login page: full-viewport with atmospheric CSS gradient mesh background, centered card (logo, "Vroom HR", tagline in Vietnamese, consent notice, Google OAuth button), staggered fade-in entrance (400-1200ms), dark mode adaptation, prefers-reduced-motion respect, maintain redirect to /api/auth/login
  - Requirements: 7
  - Dependencies: Task 1, Task 2, Task 3
  - Files: `frontend/src/app/login/page.tsx`

- [x] 19. Setup form patterns: create employee/department/position forms using shadcn/ui Form + react-hook-form + zod, inline error messages (destructive color), loading spinner on submit button, toast on success ("Tạo thành công") → navigate to list, toast on error ("Lỗi: ...") → preserve form data
  - Requirements: 10
  - Dependencies: Task 4, Task 20
  - Files: `frontend/src/components/employee-form.tsx`, `frontend/src/app/(dashboard)/employees/new/page.tsx`

- [x] 20. Setup global toast system: add `<Toaster />` (Sonner) to root layout, configure position bottom-right, max 5 visible, richColors, success auto-dismiss 4s, error persist until dismissed, replace existing gmail toast-provider with global Sonner
  - Requirements: 11
  - Dependencies: Task 4
  - Files: `frontend/src/app/layout.tsx`, `frontend/src/components/gmail/toast-provider.tsx`

- [x] 21. Final accessibility audit: verify semantic landmarks (header, nav, main, aside), decorative icons have aria-hidden="true", actionable icons have aria-label, focus-visible ring on all interactive elements, form inputs have associated labels + aria-describedby for errors, color contrast both themes (4.5:1/3:1), keyboard Tab order follows visual layout
  - Requirements: 13
  - Dependencies: Task 11, Task 14, Task 18, Task 19
  - Files: All frontend components

## Task Dependency Graph

```json
{
  "waves": [
    {"id": "wave1", "tasks": ["1", "2", "4", "6"]},
    {"id": "wave2", "tasks": ["3", "9", "12"]},
    {"id": "wave3", "tasks": ["5", "7", "10", "14", "20"]},
    {"id": "wave4", "tasks": ["8", "15"]},
    {"id": "wave5", "tasks": ["11", "16", "17", "18"]},
    {"id": "wave6", "tasks": ["13", "19"]},
    {"id": "wave7", "tasks": ["21"]}
  ]
}
```

## Notes

- Dùng `pnpm` cho tất cả package operations (không dùng npm/yarn)
- Chạy `pnpm build` sau mỗi phase để verify không có lỗi TypeScript
- Theme toggle và sidebar state persist qua localStorage — không cần backend
- Tất cả UI text phải bằng tiếng Việt (trừ brand names: Vroom HR, Gmail, Google)
- Animations phải respect `prefers-reduced-motion`
- Không thay đổi API backend — chỉ thay đổi frontend
