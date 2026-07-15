# Animation Recommendation — Vroom HR

> **Context:** Vroom HR dùng Next.js 14 App Router, React 18.3, Tailwind CSS 3.4, Base UI, shadcn/ui. Hiện chưa có animation library — chỉ có `tw-animate-css` (Tailwind CSS animation plugin). UI cần: micro-interactions, skeleton loading, modal/drawer transitions, staggered list animations, page transitions.

## Mục lục

- [Hiện trạng](#hiện-trạng)
- [Ứng viên so sánh](#ứng-viên-so-sánh)
- [Ma trận so sánh](#ma-trận-so-sánh)
- [Phân tích chi tiết](#phân-tích-chi-tiết)
- [Đề xuất](#đề-xuất)
- [Implementation patterns](#implementation-patterns)
- [Kế hoạch migration](#kế-hoạch-migration)

---

## Hiện trạng

| Thành phần | Trạng thái |
|---|---|
| **`tw-animate-css`** | ✅ Đã cài (v1.4.0) — CSS keyframe + transition utilities |
| **Animation library** (framer-motion, gsap, v.v.) | ❌ Chưa có |
| **Page transitions** | ❌ Mặc định Next.js — không animation |
| **Modal/Drawer** | ❌ Base UI / shadcn — mount/unmount tức thì |
| **Skeleton loading** | ✅ Có thể dùng Tailwind `animate-pulse` |
| **Micro-interactions** | ❌ Chưa có hệ thống |

### Constraint kỹ thuật

- **React 18.3** — chưa có `<ViewTransition>` component (React 19)
- **Next.js 14.2** — App Router, RSC, Server Components
- **Tailwind CSS 3.4** — CSS-first approach
- **Base UI** — headless components, cần tự quản lý animation

---

## Ứng viên so sánh

| # | Library | Approach | Bundle (gzip) |
|---|---|---|---|
| 1 | **CSS transitions + keyframes** (thuần) | CSS native | **0 KB** |
| 2 | **Motion / Framer Motion** | React component (`motion.div`) | 15–46 KB |
| 3 | **Motion (WAAPI — animate/stagger)** | Imperative + WAAPI | 3.8 KB |
| 4 | **GSAP** | Timeline imperative | 23 KB (+30 KB ScrollTrigger) |
| 5 | **AutoAnimate** | MutationObserver + WAAPI | **<3 KB** |

---

## Ma trận so sánh

| Tiêu chí | CSS thuần | Motion (full) | Motion (mini/WAAPI) | GSAP | AutoAnimate |
|---|---|---|---|---|---|
| **Bundle size** | 0 KB 🏆 | 15–46 KB | 3.8 KB | 23–53 KB | <3 KB |
| **RSC compatible** | ✅ Hoàn toàn | ⚠️ Cần `"use client"` | ✅ (imperative) | ⚠️ Cần `"use client"` | ⚠️ Cần `"use client"` |
| **Page transitions** | ⚠️ View Transitions API | ✅ AnimatePresence | ❌ | ✅ ScrollTrigger | ❌ |
| **Staggered list** | ⚠️ CSS `animation-delay` | ✅ `staggerChildren` | ✅ `stagger()` | ✅ Timeline | ✅ Tự động |
| **Modal/Drawer enter/exit** | ⚠️ Khó exit animation | ✅ AnimatePresence | ❌ | ✅ Tween | ❌ |
| **Micro-interactions** | ✅ `:hover`, `:focus` CSS | ✅ `whileHover`, `whileTap` | ⚠️ useEffect | ✅ useGSAP | ❌ |
| **Skeleton loading** | ✅ `animate-pulse` | ✅ `motion.div` | ❌ | ❌ | ❌ |
| **Layout animation** | ❌ | ✅ `layout` prop | ❌ | ✅ Flip plugin | ✅ Auto |
| **Shared elements** | ❌ | ✅ `layoutId` | ❌ | ✅ Flip | ❌ |
| **Gesture (drag, pinch)** | ❌ | ✅ `drag`, `whileHover` | ❌ | ✅ Draggable | ❌ |
| **Scroll-triggered** | ❌ | ✅ `useScroll`/`useTransform` | ✅ `inView()` | ✅ ScrollTrigger 🏆 | ❌ |
| **Prefer-reduced-motion** | ✅ `@media` | ✅ `useReducedMotion` | ⚠️ Tự làm | ⚠️ Tự làm | ✅ Mặc định |
| **TypeScript** | — | ✅✅ Excellent | ✅ Good | ⚠️ Trung bình | ✅ Good |
| **Learning curve** | Dễ | Trung bình | Dễ | Khó | **Cực dễ** 🏆 |
| **Bảo trì** | Browser native 🏆 | Active (Motion团队) | Active | Active | Đủ dùng |

### Chi tiết bundle size

| Library | Full gzip | Với tree-shaking | Ghi chú |
|---|---|---|---|
| CSS transitions | 0 KB | 0 KB | Không cần import |
| Motion (LazyMotion) | 30 KB | 15 KB | `LazyMotion` + `domAnimation` |
| Motion (full) | 46 KB | 34 KB | Import cả `motion/react` |
| Motion (WAAPI mini) | 3.8 KB | 3.8 KB | `animate()` + `stagger()` |
| GSAP core | 23 KB | 23 KB | Không tree-shake tốt |
| GSAP + ScrollTrigger | 53 KB | 30–35 KB | Plugin gộp |
| AutoAnimate | <3 KB | <3 KB | Cố định |
| `tw-animate-css` | ~1 KB | ~1 KB | Đã cài sẵn |

---

## Phân tích chi tiết

### 1. CSS transitions + keyframes (thuần) — 0 KB

**Khi nào dùng:** Mọi thứ decorative, hover effects, skeleton, loading spinner.

**Ưu điểm:**
- Zero bundle cost — không import gì
- GPU-accelerated (composite-only properties)
- Không ảnh hưởng INP/LCP/CLS
- Hoạt động với Server Component
- `prefers-reduced-motion` dễ implement

**Nhược điểm:**
- Không exit animation khi component unmount
- Không staggered (cần `animation-delay` manual)
- Không layout animation khi filter list
- Không gesture (chỉ `:hover`/`:focus`)
- Không scroll-triggered

> "CSS Animations: 0KB, ideal for micro-interactions, prefers-reduced-motion compatible"
> — Mintec, Animation Libraries & Core Web Vitals 2026

```css
/* Tốt cho: skeleton, spinner, fade-in, slide-in */
.skeleton {
  @apply animate-pulse bg-muted rounded;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}
```

### 2. Motion / Framer Motion (full) — 15–46 KB

> **Lưu ý:** `framer-motion` đã đổi tên thành `motion` từ 2024. `npm install motion` — cùng package nhưng API `motion/react`.

**Khi nào dùng:** Khi cần layout animations, AnimatePresence (exit animations), shared elements, gesture, staggered sequences phức tạp.

**Ưu điểm:**
- `AnimatePresence` — exit animations cho modal/drawer (không CSS nào làm được khi unmount)
- `layout` prop — filter list items tự động smooth
- `layoutId` — shared element transitions giữa các page
- `whileHover`/`whileTap`/`whileFocus` — micro-interactions dễ
- `useScroll`/`useTransform` — scroll animations declarative
- TypeScript support xuất sắc

**Nhược điểm:**
- Bundle lớn (15 KB lazy — tối thiểu)
- Cần `"use client"` — không dùng trong Server Component
- JavaScript main-thread — ảnh hưởng INP nếu lạm dụng
- Quá mạnh cho decorative animations (phí)

> "Do not use Framer Motion for decorative landing page animations. This is the #1 cause of high INP."
> — Mintec, Animation Libraries & Core Web Vitals 2026

```tsx
// Tối ưu bundle với LazyMotion
import { LazyMotion, domAnimation, m } from 'motion/react';

// Chỉ load 15 KB thay vì 30 KB
<LazyMotion features={domAnimation}>
  <m.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.2 }}
  />
</LazyMotion>
```

### 3. Motion WAAPI (mini) — 3.8 KB

Đây là phần lõi WAAPI của cùng package `motion`, dùng `animate()` và `stagger()` ở dạng imperative, không cần React component.

**Khi nào dùng:** Scroll reveals nhẹ, stagger effects khi bundle budget tight, không cần AnimatePresence.

```ts
import { animate, stagger, inView } from 'motion';

// Scroll reveal — 3.8 KB
inView('.section', ({ target }) => {
  animate(
    target.querySelectorAll('[data-animate]'),
    { opacity: [0, 1], y: [12, 0] },
    { delay: stagger(0.05), duration: 0.4 }
  );
});
```

**Giới hạn:** Không exit animation, không gesture, không `motion.div`. Chỉ imperative.

### 4. GSAP — 23 KB (core)

**Khi nào dùng:** ScrollTrigger (mạnh nhất ecosystem), timeline phức tạp, animation không-React (tương thích mọi framework).

**Ưu điểm:**
- ScrollTrigger là mạnh nhất cho scroll-driven
- Timeline API — kiểm soát từng frame
- Performance tốt (requestAnimationFrame tối ưu)
- Plugin ecosystem (ScrollTrigger, Flip, Text, v.v.)

**Nhược điểm:**
- API imperative — không declarative như Motion
- Không tree-shake tốt
- Bundle 23 KB core + 30 KB ScrollTrigger
- Cần `"use client"` + `useGSAP` hook cho React
- TypeScript support trung bình
- Learning curve cao

> "GSAP core: 23KB, best performance-per-feature ratio, ScrollTrigger is unbeatable."
> — Mintec 2026

### 5. AutoAnimate — <3 KB

**Khi nào dùng:** List enter/exit/reorder animation — **chỉ một dòng code**.

```tsx
import { useAutoAnimate } from '@formkit/auto-animate/react';

function EmployeeList() {
  const [parent] = useAutoAnimate();
  return <ul ref={parent}>{/* items tự động animate */}</ul>;
}
```

**Giới hạn:**
- Chỉ animate DOM change (enter/exit/reorder)
- Không custom từng element
- Không gesture, không scroll, không layout animation

---

## Đề xuất

### Chiến lược tổng thể: **CSS-first + Motion cho functional animations**

Dùng **3 tầng animation** — mỗi tầng cho một loại use case khác nhau, không competing:

```
Tầng 1: CSS transitions       → 0 KB — decorative, hover, skeleton
Tầng 2: AutoAnimate           → 3 KB — list enter/exit/reorder
Tầng 3: Motion (LazyMotion)   → 15 KB — modal/drawer, staggered, layout, page transition
```

**Tổng bundle animation: ~18 KB** (chỉ load khi cần)

### Chi tiết từng tầng

#### Tầng 1: CSS transitions (0 KB) — decorative

| Use case | Implementation |
|---|---|
| Skeleton loading | `animate-pulse` (Tailwind) + `@keyframes shimmer` |
| Hover effects | `transition-all duration-200 hover:scale-[1.02]` |
| Button press | `active:scale-95 transition-transform` |
| Fade-in section | `@keyframes fade-in-up` + `animation-fill-mode: forwards` |
| Spinner/loader | `animate-spin` (Tailwind) |
| `prefers-reduced-motion` | `@media (prefers-reduced-motion: reduce) { animation: none; }` |

#### Tầng 2: AutoAnimate (<3 KB) — list operations

| Use case | Implementation |
|---|---|
| Employee list filter | `useAutoAnimate()` trên container |
| Department accordion | `useAutoAnimate()` trên panel |
| Notification toast list | `useAutoAnimate()` trên stack |
| Sortable table rows | `useAutoAnimate()` trên tbody |
| Tag/chip add/remove | `useAutoAnimate()` trên wrapper |

#### Tầng 3: Motion LazyMotion (15 KB) — functional

| Use case | Implementation |
|---|---|
| **Modal/Drawer** enter/exit | `AnimatePresence` + `motion.div` |
| **Staggered list** | `variants` + `staggerChildren` |
| **Filter layout shift** | `layout` prop |
| **Page transitions** | View Transitions API + fallback `AnimatePresence` |
| **Shared elements** | `layoutId` (future React 19 upgrade) |
| **Micro-interactions nâng cao** | `whileHover`, `whileTap`, `whileFocus` |

### Giải thích: Tại sao không chọn GSAP?

1. **Bundle lớn** (23 KB core, 53 KB + ScrollTrigger) so với Motion LazyMotion (15 KB)
2. **API imperative** — không declarative, khó maintain với React component tree
3. **Không tree-shake** — import cái nào cũng kéo cả core
4. **Không AnimatePresence** — exit animation khi unmount phải tự xử lý
5. ScrollTrigger mạnh nhưng Vroom HR không cần scroll storytelling

GSAP chỉ phù hợp nếu sau này cần:
- Scroll-driven storytelling (landing page marketing)
- SVG animation phức tạp
- Timeline animation đồng bộ với video/audio

### Giải thích: Tại sao không dùng Motion WAAPI mini làm chính?

WAAPI mini (3.8 KB) không có:
- `AnimatePresence` — không exit animation
- `layout` — không layout animation
- `whileHover`/`whileTap` — micro-interactions phải tự xử
- Scroll hooks (`useScroll`, `useTransform`)

WAAPI mini phù hợp cho scroll reveal + stagger nhẹ, nhưng không đủ cho modal/drawer và layout transition.

---

## Implementation patterns

### Pattern 1: Modal/Drawer với AnimatePresence

```tsx
'use client';

import { AnimatePresence, m, LazyMotion, domAnimation } from 'motion/react';
import { Dialog, DialogBackdrop, DialogPanel } from '@base-ui-components/react/dialog';

// Base UI Dialog + Motion exit animation
export function AnimatedDialog({ open, onClose, children }) {
  return (
    <LazyMotion features={domAnimation}>
      <AnimatePresence>
        {open && (
          <Dialog open={open} onClose={onClose}>
            {/* Backdrop */}
            <DialogBackport
              render={
                <m.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                />
              }
            />
            {/* Panel */}
            <DialogPanel
              render={
                <m.div
                  initial={{ opacity: 0, scale: 0.95, y: -8 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -8 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                />
              }
            >
              {children}
            </DialogPanel>
          </Dialog>
        )}
      </AnimatePresence>
    </LazyMotion>
  );
}
```

### Pattern 2: Staggered list animation

```tsx
'use client';

import { m, LazyMotion, domAnimation } from 'motion/react';

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.04 },
  },
};

const item = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0 },
};

export function EmployeeCardList({ employees }) {
  return (
    <LazyMotion features={domAnimation}>
      <m.ul variants={container} initial="hidden" animate="show">
        {employees.map((emp) => (
          <m.li key={emp.id} variants={item}>
            <EmployeeCard employee={emp} />
          </m.li>
        ))}
      </m.ul>
    </LazyMotion>
  );
}
```

### Pattern 3: AutoAnimate cho list filter

```tsx
'use client';

import { useAutoAnimate } from '@formkit/auto-animate/react';
import { useState } from 'react';

export function FilterableEmployeeList({ employees }) {
  const [filter, setFilter] = useState('');
  const [listRef] = useAutoAnimate();

  const filtered = employees.filter((e) =>
    e.name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div>
      <input onChange={(e) => setFilter(e.target.value)} />
      <ul ref={listRef}>
        {filtered.map((emp) => (
          <li key={emp.id}>{emp.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Pattern 4: Page transitions (View Transitions API)

Vì đang dùng React 18, không có `<ViewTransition>` component. Dùng browser native API:

```tsx
// components/page-transition-provider.tsx
'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';

export function PageTransitionProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!document.startViewTransition) return;

    // Native View Transitions API
    // Fallback: không làm gì nếu browser không support
  }, [pathname]);

  return <div ref={ref}>{children}</div>;
}
```

**Khi nâng cấp lên React 19:** Dùng `<ViewTransition>` component native.

```tsx
// React 19 — tương lai
import { ViewTransition } from 'react';

<ViewTransition name="employee-detail" share="morph">
  <EmployeeDetail employee={employee} />
</ViewTransition>
```

### Pattern 5: CSS skeleton loading

```tsx
// components/skeleton.tsx — hoàn toàn RSC-compatible, 0 KB bundle
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 animate-pulse">
          <div className="h-4 w-1/4 bg-muted rounded" />
          <div className="h-4 w-1/3 bg-muted rounded" />
          <div className="h-4 w-1/5 bg-muted rounded" />
        </div>
      ))}
    </div>
  );
}
```

### Pattern 6: Micro-interactions với Tailwind

```tsx
// Button — 0 KB animation library
<button
  className="
    transition-all duration-150 ease-out
    hover:scale-[1.02] hover:shadow-md
    active:scale-[0.98]
    focus-visible:ring-2
  "
>
  {children}
</button>
```

### Pattern 7: Card hover animation

```tsx
// Card — CSS thuần, RSC-compatible
<div className="
  group relative
  transition-all duration-200 ease-out
  hover:-translate-y-1 hover:shadow-lg
">
  <div className="
    absolute inset-0 rounded-lg bg-primary/5
    opacity-0 transition-opacity duration-200
    group-hover:opacity-100
  " />
  <div className="relative">
    {children}
  </div>
</div>
```

### Pattern 8: prefers-reduced-motion system-wide

```css
/* globals.css */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Với Motion, dùng hook:

```tsx
'use client';
import { useReducedMotion } from 'motion/react';

function AnimatedComponent() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <m.div
      animate={prefersReducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
      transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3 }}
    />
  );
}
```

---

## Tổng kết bundle size impact

| Thành phần | Tình huống | Tác động bundle |
|---|---|---|
| CSS transitions | **Luôn luôn** — decorative, hover, skeleton | **+0 KB** |
| AutoAnimate | List filter, accordion, toast | **+3 KB** (chunk riêng) |
| Motion LazyMotion | Modal, drawer, staggered, page transition | **+15 KB** (chunk riêng) |
| **Total critical path** | First load — CSS transitions là đủ | **0 KB** |
| **Total lazy loaded** | Khi user mở modal/filter | **~18 KB** |

### So sánh với approach khác

| Approach | Total bundle | Critical path | Ghi chú |
|---|---|---|---|
| **CSS-first + AutoAnimate + Motion (lazy)** ✅ | ~18 KB | 0 KB | Khuyến nghị |
| Motion cho mọi thứ | 30–46 KB | 30–46 KB | Load ngay cả khi không cần |
| GSAP cho mọi thứ | 23–53 KB | 23–53 KB | Nặng, imperative |
| CSS + AutoAnimate | ~3 KB | 0 KB | Nhẹ nhất nhưng thiếu modal/drawer |
| CSS thuần | 0 KB | 0 KB | Không exit animation, không layout |

---

## Kế hoạch migration

### Phase 1: CSS transitions (ngay lập tức — không cần cài gì)

- [ ] Thêm `prefers-reduced-motion` reset vào `globals.css`
- [ ] Thêm utility `@keyframes fade-in-up` cho section entrance
- [ ] Apply `transition-all duration-150` vào button, card, input
- [ ] Dùng `animate-pulse` cho skeleton component
- [ ] Xóa bỏ các animation không cần thiết (giữ INP thấp)

### Phase 2: AutoAnimate (ngày 1)

- [ ] `npm install @formkit/auto-animate`
- [ ] Wrap employee list, department accordion, notification stack với `useAutoAnimate()`
- [ ] Kiểm tra tương thích với virtualized list (nếu có)

### Phase 3: Motion LazyMotion (ngày 2)

- [ ] `npm install motion`
- [ ] Tạo `AnimatedDialog` wrapper — Modal + Drawer enter/exit
- [ ] Tạo staggered list component cho dashboard cards
- [ ] Tạo `layout` animation cho filterable table (nếu cần)
- [ ] Test INP với Motion active — dùng LoAF API

### Phase 4: Page transitions (khi nâng cấp React 19)

- [ ] Nâng cấp lên React 19 + Next.js 15+
- [ ] Dùng `<ViewTransition>` component cho page morph animations
- [ ] Kết hợp `AnimatePresence` cho route transitions fallback

---

## Tài liệu tham khảo

- [Motion (Framer Motion) documentation](https://motion.dev/)
- [AutoAnimate](https://auto-animate.formkit.com/)
- [GSAP](https://gsap.com/)
- [Next.js View Transitions Guide](https://nextjs.org/docs/app/guides/view-transitions)
- [CSS vs JavaScript animation performance (MDN)](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/CSS_JavaScript_animation_performance)
- [Animation Libraries & Core Web Vitals (Mintec 2026)](https://mintec.co/blog/animaciones-web-rendimiento-core-web-vitals/)
- [Framer Motion vs Motion One vs AutoAnimate (PkgPulse 2026)](https://www.pkgpulse.com/guides/framer-motion-vs-motion-one-vs-autoanimate-2026)
- [Choosing a React Animation Library (Syncfusion 2026)](https://www.syncfusion.com/blogs/post/react-animation-libraries-comparison)
- [GSAP & Framer Motion in Next.js 15](https://buildwithumar.com/blogs/nextjs-animations-optimization)
- [Inclusively Hidden — prefers-reduced-motion best practices](https://www.scottohara.me/blog/2023/03/21/inclusively-hidden.html)
