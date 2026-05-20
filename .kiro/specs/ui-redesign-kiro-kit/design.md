# Technical Design — UI Redesign (kiro-kit)

## Overview

Thiết kế lại giao diện Vroom HR với theme chuyên nghiệp phù hợp role HR, dark mode, và trải nghiệm smooth. Hướng tiếp cận: **"Calm Professional"** — giao diện sạch, tông màu ấm áp nhưng chuyên nghiệp, animations mượt mà, giảm cognitive load cho người dùng HR làm việc cả ngày.

### Design Direction

- **Aesthetic**: "Calm Professional" — chuyên nghiệp, ấm áp, đáng tin cậy
- **Color anchor**: Deep teal (chuyên nghiệp, bình tĩnh) + warm amber accent (thân thiện, năng lượng)
- **Typography**: Plus Jakarta Sans (headings) + DM Sans (body)
- **Motion**: Smooth, subtle — 150-300ms transitions, staggered reveals
- **Layout**: Generous whitespace, clear hierarchy, sidebar-first navigation

## Architecture

### Component Tree

```
RootLayout (Server Component)
├── ThemeProvider (next-themes, attribute="class")
│   ├── Toaster (Sonner, global)
│   └── children
│
├── LoginPage (standalone, full-viewport)
│
└── DashboardLayout (Client Component)
    ├── AppSidebar (collapsible, Sheet on mobile)
    │   ├── Logo + Brand
    │   ├── NavLinks (with active state)
    │   └── UserSection (avatar + logout)
    ├── Header
    │   ├── MobileMenuTrigger (hamburger → Sheet)
    │   ├── Breadcrumbs
    │   ├── CommandBarTrigger (⌘K)
    │   └── ThemeToggle
    ├── CommandBar (Dialog + Command component)
    └── MainContent (with page transition)
        └── <page> (children)
```

### File Structure

```
frontend/src/
├── app/
│   ├── globals.css              # Design tokens (light + dark)
│   ├── layout.tsx               # RootLayout + ThemeProvider + fonts
│   ├── login/page.tsx           # Redesigned login
│   └── (dashboard)/
│       ├── layout.tsx           # Sidebar + Header + CommandBar
│       ├── page.tsx             # Dashboard with stats
│       ├── employees/page.tsx
│       └── settings/
│           ├── departments/page.tsx
│           └── positions/page.tsx
├── components/
│   ├── ui/                      # shadcn/ui (24+ components)
│   ├── app-sidebar.tsx
│   ├── breadcrumbs.tsx
│   ├── command-bar.tsx
│   ├── theme-toggle.tsx
│   ├── data-table.tsx
│   ├── stat-card.tsx
│   └── page-transition.tsx
├── hooks/
│   ├── use-sidebar.ts
│   └── use-debounce.ts
└── lib/
    ├── utils.ts
    └── api/
```

## Components and Interfaces

### ThemeProvider

```typescript
// frontend/src/app/layout.tsx
import { ThemeProvider } from "next-themes";

// Wraps entire app, manages light/dark/system theme
// attribute="class" → adds .dark to <html>
// defaultTheme="system" → respects OS preference
// enableSystem → listens to prefers-color-scheme changes
```

### AppSidebar

```typescript
// frontend/src/components/app-sidebar.tsx
interface AppSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

// States: expanded (256px) | collapsed (64px) | mobile (Sheet)
// Persists state in localStorage via useSidebar() hook
// Contains: Logo, NavLinks, UserSection (logout)
```

### CommandBar

```typescript
// frontend/src/components/command-bar.tsx
interface CommandBarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Built on shadcn/ui Command (cmdk library)
// Triggered by ⌘K / Ctrl+K
// Lists navigation pages, filters in real-time
// Navigates on selection
```

### DataTable

```typescript
// frontend/src/components/data-table.tsx
interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  loading: boolean;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onSearch: (query: string) => void;
  onRowClick?: (row: T) => void;
  toolbar?: React.ReactNode;
}

// Responsive: table on md+, card list on mobile
// Built-in: search (debounced 300ms), pagination, skeleton loading
// Empty/error states with Vietnamese messages
```

### ThemeToggle

```typescript
// frontend/src/components/theme-toggle.tsx
// DropdownMenu with 3 options: Sáng (Sun), Tối (Moon), Hệ thống (Monitor)
// Uses useTheme() from next-themes
// Keyboard accessible
```

### StatCard

```typescript
// frontend/src/components/stat-card.tsx
interface StatCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  loading?: boolean;
  href?: string;
}

// Used on Dashboard page for summary statistics
// Skeleton state while loading
// Staggered fade-in animation
```

### Breadcrumbs

```typescript
// frontend/src/components/breadcrumbs.tsx
// Reads current pathname, maps segments to Vietnamese labels
// Each ancestor is a clickable link, last segment is plain text
// Example: Trang chủ / Nhân viên / Chi tiết
```

### PageTransition

```typescript
// frontend/src/components/page-transition.tsx
interface PageTransitionProps {
  children: React.ReactNode;
}

// Wraps main content, applies fade-in animation on route change
// Uses key={pathname} to trigger re-animation
// Duration: 200ms, opacity 0→1
```

## Data Models

### Design Tokens (CSS Variables)

```
Light Theme:
  --primary: 168 65% 28%  (deep teal)
  --accent: 35 90% 52%    (warm amber)
  --background: 0 0% 99%  (near-white)
  --foreground: 200 20% 12% (dark blue-gray)

Dark Theme:
  --primary: 168 55% 45%  (brighter teal)
  --accent: 35 85% 55%    (brighter amber)
  --background: 210 20% 8% (deep blue-black)
  --foreground: 180 5% 92% (light gray)
```

### Sidebar State (localStorage)

```typescript
interface SidebarState {
  collapsed: boolean;  // persisted in localStorage key "sidebar-collapsed"
}
```

### Theme State (next-themes)

```typescript
// Managed by next-themes, persisted in localStorage key "theme"
type Theme = "light" | "dark" | "system";
```

### Navigation Config

```typescript
interface NavItem {
  href: string;
  label: string;       // Vietnamese label
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { href: "/", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/employees", label: "Nhân viên", icon: Users },
  { href: "/settings/departments", label: "Phòng ban", icon: Building2 },
  { href: "/settings/positions", label: "Chức vụ", icon: Briefcase },
  { href: "/gmail", label: "Gmail", icon: Mail },
];
```

## Error Handling

- **API errors in DataTable**: Display centered error message "Lỗi: {message}" in place of table body
- **Form submission errors**: Toast notification (Sonner) with error variant, preserve form data
- **Network errors**: Toast with "Không thể kết nối đến máy chủ"
- **Empty states**: "Không có dữ liệu" message with optional action button
- **Theme loading**: `suppressHydrationWarning` on `<html>` to prevent flash mismatch

## Correctness Properties

### Property 1: Theme Token Completeness
All CSS variables defined in `:root` MUST have a corresponding value in `.dark`. No variable may be undefined in either theme.
**Validates: Requirements 1.1, 1.2**

### Property 2: Focus Visibility
All interactive elements (buttons, links, inputs, selects) MUST have `focus-visible:ring-2 focus-visible:ring-ring` styles applied.
**Validates: Requirements 4.3, 13.2**

### Property 3: Contrast Compliance
All text MUST meet WCAG 2.1 AA contrast ratio (4.5:1 for normal text, 3:1 for large text) in both light and dark themes.
**Validates: Requirements 3.5, 13.6**

### Property 4: State Persistence
Sidebar collapsed/expanded state and theme preference MUST persist across page reloads via localStorage without visible flash.
**Validates: Requirements 3.2, 5.2**

### Property 5: Motion Respect
All animations and transitions MUST be disabled when `prefers-reduced-motion: reduce` is active on the user's system.
**Validates: Requirements 6.5, 7.4**

### Property 6: Language Consistency
All UI text (navigation, buttons, labels, messages) MUST be in Vietnamese, except brand names (Vroom HR, Gmail, Google).
**Validates: Requirements 14.1, 14.5**

## Testing Strategy

- **Visual regression**: Manual comparison of light vs dark theme on all pages
- **Accessibility**: Keyboard navigation test (Tab through all interactive elements), screen reader basic flow
- **Responsive**: Test at 320px, 640px, 768px, 1024px, 1280px viewports
- **Build verification**: `pnpm build` must pass without errors after all changes
- **Component rendering**: Verify all shadcn/ui components render correctly with new tokens
- **Animation**: Verify `prefers-reduced-motion` disables animations
- **Theme persistence**: Reload page → theme should not flash
