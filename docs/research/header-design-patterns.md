# Header Navigation Design Patterns — Research

> Mục tiêu: Tìm hiểu thiết kế header navigation chuẩn, đẹp từ các design system lớn để áp dụng cho Vroom HR (Next.js 14 + Tailwind CSS + shadcn/ui).

**Ngày research:** 2025-07-17
**Nguồn tham khảo:** shadcn/ui, Radix UI, Tailwind UI, Linear, Stripe, Vercel Geist

---

## 1. Hover State Pattern cho Nav Items

### 1.1 shadcn/ui (Navigation Menu)

shadcn/ui dùng `cva()` để định nghĩa `navigationMenuTriggerStyle` với hover style chuẩn:

```tsx
// Source: https://github.com/shadcn-ui/ui/blob/b59f68ec/apps/v4/registry/new-york-v4/ui/navigation-menu.tsx
const navigationMenuTriggerStyle = cva(
  "group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-[color,box-shadow] outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 disabled:pointer-events-none disabled:opacity-50 data-[state=open]:bg-accent/50 data-[state=open]:text-accent-foreground data-[state=open]:hover:bg-accent data-[state=open]:focus:bg-accent"
)
```

| State | Style | Ghi chú |
|---|---|---|
| Default | `bg-background` `text-sm font-medium` | Nền trong suốt |
| Hover | `hover:bg-accent` `hover:text-accent-foreground` | Dùng màu accent/primary system |
| Focus | `focus:bg-accent` `focus:text-accent-foreground` | Giống hover |
| Focus-visible | `focus-visible:ring-[3px]` `focus-visible:ring-ring/50` | Ring outline cho keyboard |
| Open (mega menu) | `data-[state=open]:bg-accent/50` `data-[state=open]:text-accent-foreground` | Opacity thấp hơn hover |
| Open + Hover | `data-[state=open]:hover:bg-accent` | Full accent khi hover lúc open |
| Disabled | `disabled:pointer-events-none disabled:opacity-50` | Opacity giảm |

*(Nguồn: [shadcn/ui navigation-menu.tsx](https://github.com/shadcn-ui/ui/blob/b59f68ec/apps/v4/registry/new-york-v4/ui/navigation-menu.tsx))*

**Kết luận:** shadcn/ui không dùng màu foreground/background riêng cho hover. Thay vào đó dùng `--accent` (màu chủ đạo thứ cấp) làm hover background. Đây là pattern phổ biến và dễ maintain vì chỉ cần đổi 1 CSS variable.

### 1.2 Vercel Geist Design System

Geist dùng color scale riêng cho trạng thái:

| Màu | Vai trò |
|---|---|
| Color 1 | Default background |
| Color 2 | Hover background |
| Color 3 | Active background |
| Color 9 | Secondary text & icons |
| Color 10 | Primary text & icons |

*(Nguồn: [Vercel Geist — Colors](https://vercel.com/geist/colors))*

Hover state trong Geist được implement bằng cách chuyển từ Color 1 → Color 2 (nền) hoặc Color 9 → Color 10 (text). Pattern này tương tự `hover:bg-muted` hoặc `hover:bg-accent` trong Tailwind.

### 1.3 Linear.app

Linear dùng hệ thống theme generation dựa trên LCH color space. Hover effect cho navigation items rất tinh tế:

- **Light mode:** `background-color: rgba(0,0,0,0.06)` (tương đương `hover:bg-black/6`)
- **Dark mode:** `background-color: rgba(255,255,255,0.08)` (tương đương `hover:bg-white/8`)
- **Transition:** `transition: background-color 0.15s ease`

*(Nguồn: [Reverse engineering Linear — part 1: Header](https://pustelto.com/blog/reverse-engineer-linear-1-header/), [How we redesigned the Linear UI](https://linear.app/blog/how-we-redesigned-the-linear-ui))*

Điểm đặc biệt: Linear dùng opacity của **foreground color** (không phải accent) để tạo hiệu ứng hover neutral, tránh ám màu không mong muốn. Pattern này tương đương `hover:bg-foreground/8` trong Tailwind.

### 1.4 Tailwind UI Navbars

Các navbar component của Tailwind UI dùng:

- **Simple:** `hover:text-gray-900` (light) / `hover:text-white` (dark) — chỉ đổi màu text
- **With background highlight:** `hover:bg-gray-50` (light) / `hover:bg-gray-800` (dark)
- **Active:** `bg-gray-100` (light) / `bg-gray-700` (dark) + text color tương phản hơn

*(Nguồn: [Tailwind CSS Navbars](https://tailwindcss.com/plus/ui-blocks/application-ui/navigation/navbars))*

### 1.5 Stripe

Stripe.com navigation nổi tiếng với mega menu morphing effect. Hover state:

- **Trigger:** Chỉ đổi màu text nhẹ (`color` transition)
- **Popover:** Background trắng với `box-shadow` elevation, không background highlight trên trigger
- **Animation:** CSS transform (scaleX/scaleY) thay vì animating width/height — hiệu suất cao hơn

*(Nguồn: [Tutorial: Stripe.com's main navigation](https://lokeshdhakar.com/dev-201-stripe.coms-main-navigation/))*

### 1.6 So sánh light vs dark mode

| Hệ thống | Light mode hover | Dark mode hover |
|---|---|---|
| shadcn/ui | `bg-accent` (dùng system variable) | Giống light (variable tự đổi) |
| Geist | Color 2 (`gray-100` tương đương) | Color 2 (`gray-800` tương đương) |
| Linear | `rgba(0,0,0,0.06)` | `rgba(255,255,255,0.08)` |
| Tailwind UI | `bg-gray-50` | `bg-gray-800` |

**Điểm chung:** Dark mode luôn dùng opacity thấp hơn hoặc màu tối hơn để tránh chói. Linear dùng opacity-based approach giúp tự động thích ứng cả 2 mode.

---

## 2. Active/Current Indicator

### 2.1 Các pattern phổ biến

| Pattern | Ví dụ | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Background highlight** | shadcn/ui `data-[active=true]:bg-accent/50` | Dễ thấy, consistent với hover | Có thể gây nặng nề |
| **Underline** | shadcn/blocks animated-underline | Nhẹ nhàng, thanh lịch | Khó thấy trên mobile |
| **Dot indicator** | Linear sidebar | Gọn, không chiếm space | Chỉ phù hợp sidebar |
| **Text weight/color** | `font-semibold` + `text-primary` | Đơn giản, không cần thêm element | Dễ bỏ sót |
| **Gradient underline** | Vroom HR hiện tại | Đẹp, hiện đại | Over-engineered? |

*(Nguồn: [shadcn/blocks navbar-animated-underline](https://www.shadcn.io/blocks/navbar-animated-underline), [Radix NavigationMenu](https://www.radix-ui.com/primitives/docs/components/navigation-menu))*

### 2.2 Cách kết hợp active + hover

shadcn/ui dùng nguyên tắc:

1. **Active** = `data-[active=true]:bg-accent/50` (opacity 50% của accent)
2. **Hover on active** = `data-[active=true]:hover:bg-accent` (full accent khi hover)
3. **Focus** = `focus:bg-accent focus:text-accent-foreground`

Linear dùng:
1. **Active** = font-weight: 600 + color: primary
2. **Hover** = chỉ background opacity
3. **Hover on active** = background opacity tăng nhẹ

*(Nguồn: [Reverse engineering Linear — part 1](https://pustelto.com/blog/reverse-engineer-linear-1-header/))*

**Khuyến nghị:** Không nên dùng 2 background effect chồng lên nhau (active highlight + hover highlight). Thay vào đó dùng active = text style thay đổi, hover = background thay đổi.

---

## 3. Spacing & Alignment trong Header

### 3.1 Khoảng cách chuẩn

| Hệ thống | Logo → Nav items | Nav item padding | Nav item gap | Font |
|---|---|---|---|---|
| shadcn/ui | `gap-1` (4px) | `px-4 py-2` (16/8px) | `gap-1` | `text-sm font-medium` |
| Radix UI demo | — | `padding: 8px 16px` | `gap: 4px` | `14px` |
| Tailwind UI | `gap-x-8` (32px) | `px-3 py-2` (12/8px) | — | `text-sm font-medium` |
| Linear | ~24px | `padding: 6px 12px` | ~4px | `13px font-medium` |

*(Nguồn: [shadcn/ui navigation-menu.tsx](https://github.com/shadcn-ui/ui/blob/b59f68ec/apps/v4/registry/new-york-v4/ui/navigation-menu.tsx), [Radix NavigationMenu demo](https://github.com/radix-ui/website/blob/26c0217b/components/demos/NavigationMenu/tailwind/index.jsx), [Tailwind UI navbars](https://tailwindcss.com/plus/ui-blocks/application-ui/navigation/navbars))*

### 3.2 Vertical centering

- **Header height chuẩn:** `h-14` (56px) hoặc `h-16` (64px) — tuỳ độ phức tạp
- **shadcn/ui trigger height:** `h-9` (36px) — chiếm ~64% header height
- **Linear:** Header items chiếm ~70-80% header height, tạo breathing room

### 3.3 Font conventions

| Hệ thống | Font size | Font weight | Letter spacing |
|---|---|---|---|
| shadcn/ui | `text-sm` (14px) | `font-medium` (500) | Default |
| Geist/Vercel | `14px` | `500` | -0.01em |
| Linear | `13px` | `500` | -0.01em |

*(Nguồn: [Vercel Geist — Typography](https://vercel.com/geist/typography))*

### 3.4 Khuyến nghị spacing cho Vroom HR

```tsx
// Header layout pattern chuẩn (sau khi đã fix)
<header className="fixed top-0 left-0 right-0 z-40 h-14">
  <nav className="flex h-full items-center px-6 gap-3">
    {/* Logo: 40-48px width */}
    {/* Breadcrumbs / Spacer */}
    {/* Nav items: px-3 py-2 text-sm font-medium, gap-1 */}
    {/* Utilities: search, notifications, account */}
  </nav>
</header>
```

Các giá trị spacing này đã được áp dụng (xem header-fix-3).

---

## 4. Mega Menu / Dropdown Design

### 4.1 Hover vs Click để mở

| Approach | Ưu điểm | Nhược điểm | Áp dụng cho |
|---|---|---|---|
| **Hover open** | Khám phá nhanh, ít click | Vô tình mở khi di chuột qua | Stripe, Linear (desktop nav) |
| **Click open** | Kiểm soát, không false positive | Cần thêm 1 click | Vroom HR (sau fix) |
| **Hybrid** | Hover sau click (lazy hover) | Phức tạp, khó predict | Một số app enterprise |

**Kết luận của Vroom HR:** Sau khi bỏ hover intent (chỉ click open là đủ — xem header-fix-1). Quyết định này phù hợp với hầu hết web application (không phải marketing site) nơi user cần kiểm soát navigation.

### 4.2 Animation pattern chuẩn

| Hệ thống | Open animation | Close animation | Duration |
|---|---|---|---|
| shadcn/ui | `fade-in-0 zoom-in-95` | `fade-out-0 zoom-out-95` | 200ms |
| Radix UI | `data-[state=open]:animate-in` | `data-[state=closed]:animate-out` | Tuỳ chỉnh |
| Stripe | `rotateX(-15deg) → rotateX(0)` | Reverse | 300ms |
| Linear | `opacity + translateY` | Reverse | 150ms |

*(Nguồn: [shadcn/ui navigation-menu.tsx](https://github.com/shadcn-ui/ui/blob/b59f68ec/apps/v4/registry/new-york-v4/ui/navigation-menu.tsx), [Stripe navigation tutorial](https://lokeshdhakar.com/dev-201-stripe.coms-main-navigation/), [Radix NavigationMenu animation](https://www.radix-ui.com/primitives/docs/components/navigation-menu))*

shadcn/ui dùng `group-data-[viewport=false]/navigation-menu:data-[state=open]:animate-in` pattern — animation chỉ chạy khi viewport mode (mega menu inline) chứ không phải viewport riêng.

### 4.3 Khuyến nghị cho Vroom HR

Mega menu hiện tại có thể cải thiện:

1. **Animation:** Thêm `fade-in` + `slide-in` nhẹ (8-12px translateY) thay vì open/close đột ngột
2. **Arrow indicator:** Thêm mũi tên nhỏ nối trigger với panel (như shadcn/ui NavigationMenuIndicator)
3. **Timing:** 150-200ms duration với `ease-out` easing

---

## 5. Bảng so sánh tổng hợp

| Tiêu chí | shadcn/ui | Tailwind UI | Linear | Vercel Geist | Vroom HR (hiện tại) | Vroom HR (đề xuất) |
|---|---|---|---|---|---|---|
| **Hover bg** | `bg-accent` | `bg-gray-50/800` | `bg-foreground/8` | Color 2 | `bg-foreground/8` | `bg-foreground/8` ✅ |
| **Hover text** | `text-accent-foreground` | `text-gray-900/white` | opacity | Color 10 | `text-accent-foreground` | `text-accent-foreground` ✅ |
| **Active indicator** | `bg-accent/50` | `bg-gray-100/700` | font-weight | Color 3 | gradient underline | Text + subtle bg |
| **Open state** | `bg-accent/50` | N/A | bg opacity | Color 2 | `bg-accent/10` | `bg-accent/10` ✅ |
| **Trigger height** | `h-9` (36px) | `py-2` | ~28px | ~32px | `py-2` | `py-2` (giữ) |
| **Trigger padding** | `px-4` | `px-3` | `12px` | `12px` | `px-3` | `px-3` (giữ) |
| **Font size** | `text-sm` (14px) | `text-sm` (14px) | 13px | 14px | `text-sm` | `text-sm` ✅ |
| **Font weight** | `font-medium` | `font-medium` | 500 | 500 | `font-medium` | `font-medium` ✅ |
| **Header gap** | `gap-1` | `gap-x-8` | ~24px | ~16px | `gap-3` | `gap-3` ✅ |
| **Menu trigger** | Click + Hover | Click | Hover | Click | Click | Click ✅ |
| **Animation** | Fade + Zoom | None | Opacity + Y | None | None (cần cải thiện) | Fade + Slide (todo) |

---

## 6. Đề xuất áp dụng cho Vroom HR

### 6.1 Giữ nguyên (đã fix đúng)

- `hover:bg-foreground/8 hover:text-accent-foreground` — pattern giống Linear, hoạt động tốt cả 2 mode
- Click để mở menu (không hover intent)
- `gap-3` spacing đồng đều trong header

### 6.2 Cần cải thiện

1. **Animation cho mega menu:** Thêm `fade-in` + `translateY(-8px)` khi open, duration 150-200ms
2. **Active state rõ hơn:** Kết hợp `font-semibold` text + gradient underline hiện tại là ok, có thể thêm `bg-accent/5` nhẹ cho active nav item nếu muốn rõ hơn
3. **Focus ring:** Đảm bảo `focus-visible:ring-2` đúng chuẩn accessibility (đã có)
4. **Responsive slot priority:** Học từ Linear, ưu tiên hiển thị các nav item quan trọng khi màn hình hẹp (low priority)

### 6.3 Theme generation

Linear dùng LCH color space để generate theme nhất quán. Nếu Vroom HR muốn custom theme trong tương lai, nên xem xét chuyển từ HSL → LCH để màu sắc đồng đều hơn giữa các theme.

*(Nguồn: [How we redesigned the Linear UI (part II)](https://linear.app/blog/how-we-redesigned-the-linear-ui))*

---

## 7. Tài liệu tham khảo

1. [shadcn/ui — Navigation Menu Source](https://github.com/shadcn-ui/ui/blob/b59f68ec/apps/v4/registry/new-york-v4/ui/navigation-menu.tsx)
2. [shadcn/ui — Navigation Menu Docs](https://ui.shadcn.com/docs/components/base/navigation-menu)
3. [Radix UI — NavigationMenu Primitives](https://www.radix-ui.com/primitives/docs/components/navigation-menu)
4. [Tailwind CSS — Navbar Components](https://tailwindcss.com/plus/ui-blocks/application-ui/navigation/navbars)
5. [Linear — How we redesigned the Linear UI (part II)](https://linear.app/blog/how-we-redesigned-the-linear-ui)
6. [Reverse engineering Linear — part 1: Header](https://pustelto.com/blog/reverse-engineer-linear-1-header/)
7. [Vercel Geist — Design System Introduction](https://vercel.com/geist/introduction)
8. [Vercel Geist — Colors](https://vercel.com/geist/colors)
9. [Stripe.com Navigation Tutorial](https://lokeshdhakar.com/dev-201-stripe.coms-main-navigation/)
10. [shadcn/blocks — Animated Underline Navbar](https://www.shadcn.io/blocks/navbar-animated-underline)
11. [shadcn/blocks — Hover Highlight Navbar](https://www.shadcn.io/blocks/navbar-hover-highlight)
