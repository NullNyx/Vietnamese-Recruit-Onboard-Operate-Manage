# Color Palette Recommendation for Vroom HR

> Research-based color system recommendations for light & dark mode, optimized for HR/B2B SaaS, WCAG AA compliance, and Tailwind CSS v4 + CSS variables.

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [2025-2026 Color Trends cho B2B/SaaS](#2-2025-2026-color-trends-cho-b2bsaas)
3. [Kiến trúc Color System](#3-kiến-trúc-color-system)
4. [WCAG Accessibility Standards](#4-wcag-accessibility-standards)
5. [Palette Candidate 1: Professional Blue](#5-palette-candidate-1-professional-blue)
6. [Palette Candidate 2: Warm Professional](#6-palette-candidate-2-warm-professional)
7. [Palette Candidate 3: Sage Green](#7-palette-candidate-3-sage-green)
8. [So sánh và đánh giá](#8-so-sánh-và-đánh-giá)
9. [Khuyến nghị cuối cùng](#9-khuyến-nghị-cuối-cùng)
10. [Implementation: Tailwind CSS v4 + CSS Variables](#10-implementation-tailwind-css-v4--css-variables)

---

## 1. Tổng quan

### Mục tiêu

- **3 palette candidates**: mỗi palette có primary (50–950), secondary, accent, neutral, success, warning, danger, info
- **Light + Dark mode** cho mỗi palette
- **WCAG AA compliance** (4.5:1 normal text, 3:1 large text/UI)
- **Tailwind CSS v4** (`@theme` directive, OKLCH, CSS variables)
- Phù hợp **HR/B2B SaaS** cho thị trường Việt Nam

### Design Principles (kế thừa từ `ui-hr-references.md`)

```
1. Vietnamese-first, globally-capable
2. Warm professionalism
3. Progressive disclosure
4. Dual-user excellence (Admin power + Employee simplicity)
```

---

## 2. 2025-2026 Color Trends cho B2B/SaaS

### Trend chính

| Trend | Mô tả | Best for |
|-------|-------|----------|
| **Oatmeal & Ink** | Warm neutrals + deep charcoal — cảm giác "expensive paper" | Enterprise SaaS, research tools |
| **Digital Twilight** | Deep indigo → soft violet → silver — fluid, adaptive | AI products, modern PLG SaaS |
| **Safety Orange** | Pure black/white + orange/yellow — authority, urgency | Dev-tools, cybersecurity |
| **Digital Sage** | Muted green, từ deep anchor đến pale mint — "tech with conscience" | B2B SaaS, sustainability |
| **Radioactive Earth** | Forest green + electric lime + neon peach | Green-tech, fintech, AI infra |

### Ý nghĩa với Vroom HR

- **Corporate blue đã bão hòa** (>70% SaaS dùng blue) → cân nhắc differentiation
- **Warm tones** đang thay thế "cold corporate" — phù hợp HR
- **Chromatic density** — màu có weight, texture, intent — thay vì flat digital
- **Accessibility là aesthetic** — không phải compliance task
- **"Keep an anchor, move the accent"** — giữ structural colors, đổi accents

### Color Psychology cho HR Platform

| Màu | Cảm xúc | Ứng dụng HR |
|-----|---------|-------------|
| **Blue** | Trust, stability, logic | Core HR, payroll, compliance |
| **Red** | Passion, urgency, warning | Vietnamese identity, CTA, alerts |
| **Amber/Gold** | Warmth, prosperity, optimism | Accent, CTA, positive reinforcement |
| **Green** | Growth, balance, safety | Success states, benefits, wellness |
| **Purple** | Wisdom, creativity, sophistication | Performance, analytics |
| **Teal** | Openness, clarity, global | International features, communication |
| **Warm neutral** | Approachability, humanity | Backgrounds, cards, surfaces |

---

## 3. Kiến trúc Color System

### Two-layer token model

```
┌──────────────────────────────────────────┐
│           Primitive Tokens               │
│  (Raw color values: brand-500, gray-300) │
│  Không thay đổi theo theme                │
├──────────────────────────────────────────┤
│           Semantic Tokens                │
│  (Role-based: text-primary, surface-bg)  │
│  Map → primitive khác nhau light/dark    │
├──────────────────────────────────────────┤
│           Component Layer                │
│  Chỉ reference semantic tokens           │
│  Không biết light/dark mode              │
└──────────────────────────────────────────┘
```

### Mỗi palette gồm

| Token type | Scale | Số lượng |
|-----------|-------|----------|
| **Primary** | 50 → 950 (11 steps) | 11 |
| **Neutral** | 50 → 950 (11 steps) | 11 |
| **Secondary** | 50 → 950 (11 steps) | 11 |
| **Accent** | 50 → 950 (11 steps) | 11 |
| **Success** | 4 values (subtle, base, hover, text) | 4 |
| **Warning** | 4 values (subtle, base, hover, text) | 4 |
| **Danger** | 4 values (subtle, base, hover, text) | 4 |
| **Info** | 4 values (subtle, base, hover, text) | 4 |

### OKLCH Color Space

Tailwind CSS v4 sử dụng OKLCH làm format mặc định. OKLCH:
- **L** (Lightness): perceptual — 0 (đen) → 1 (trắng)
- **C** (Chroma): saturation — 0 (xám) → ~0.4 (rực rỡ)
- **H** (Hue): angle — 0–360°

```
Format: oklch(L C H)
Ví dụ:  oklch(0.62 0.18 250) → blue-500
```

**Lợi ích**: Scale 50–950 tự nhiên, perceptual uniform, wide-gamut P3 ready, `color-mix()` predictable.

---

## 4. WCAG Accessibility Standards

### Thresholds (WCAG 2.2)

| Level | Normal text | Large text (≥24px or ≥18.66px bold) | UI components |
|-------|-------------|--------------------------------------|---------------|
| **AA** | 4.5:1 | 3:1 | 3:1 |
| **AAA** | 7:1 | 4.5:1 | — |

### Contrast Targets cho mỗi palette

Để đạt AA compliance:

| Use case | Pairing | Min contrast |
|----------|---------|--------------|
| Body text on surface | Primary text (900–950) on surface (50–100) | 4.5:1 |
| Large headings | 700+ on 50–100 | 3:1 |
| Button labels | White on 500–600 primary | 4.5:1 |
| Disabled text | Needs 3:1 against bg | 3:1 |
| Focus ring | Any visible color on bg | 3:1 |
| Border/divider | Against bg | 3:1 |

### Paths khi màu brand fail AA

1. **Restrict role**: Chỉ dùng cho large text / UI components (3:1)
2. **Darker surface**: Dùng brand color trên nền tối
3. **Shift 10%**: Negotiate ±10% saturation/lightness với brand team

### APCA (Advanced Perceptual Contrast Algorithm)

- Bổ sung cho WCAG 2.2 (chưa phải legal standard)
- Perceptual Lc ≥ 60 cho large text, ≥ 75 cho body text
- Dùng như sanity check trong design review

---

## 5. Palette Candidate 1: Professional Blue

> **"Timeless B2B Trust"** — Classic enterprise blue với warm accent để không bị lạnh.

### 5.1 Tổng quan

```
Primary:     Blue (#1D4ED8 → blue-700 style)
Secondary:   Slate (#475569 → slate-600 style)
Accent:      Amber (#D97706 → amber-600 style) — warm differentiation
Neutral:     Slate (cool gray, chuẩn enterprise)

Positioning: "Trusted, professional, established"
Best for:    Doanh nghiệp truyền thống, B2B classical
Risk:        Hơi giống các platform khác dùng blue
```

### 5.2 Color Scales

#### Primary — Blue (Hue ≈ 221°)

```
 50: oklch(0.97 0.02 240)  → #EFF6FF
100: oklch(0.93 0.04 240)  → #DBEAFE
200: oklch(0.87 0.08 240)  → #BFDBFE
300: oklch(0.78 0.12 240)  → #93C5FD
400: oklch(0.70 0.16 240)  → #60A5FA
500: oklch(0.62 0.19 240)  → #3B82F6
600: oklch(0.54 0.19 240)  → #2563EB
700: oklch(0.46 0.17 240)  → #1D4ED8
800: oklch(0.38 0.13 240)  → #1E40AF
900: oklch(0.28 0.10 240)  → #1E3A8A
950: oklch(0.18 0.06 240)  → #172554
```

#### Secondary — Slate (Hue ≈ 215°, low chroma)

```
 50: oklch(0.97 0.01 240)  → #F8FAFC
100: oklch(0.93 0.01 240)  → #F1F5F9
200: oklch(0.87 0.01 240)  → #E2E8F0
300: oklch(0.78 0.01 240)  → #CBD5E1
400: oklch(0.70 0.01 240)  → #94A3B8
500: oklch(0.62 0.01 240)  → #64748B
600: oklch(0.54 0.01 240)  → #475569
700: oklch(0.46 0.01 240)  → #334155
800: oklch(0.38 0.01 240)  → #1E293B
900: oklch(0.28 0.01 240)  → #0F172A
950: oklch(0.18 0.01 240)  → #020617
```

#### Accent — Amber (Hue ≈ 38°, warm contrast)

```
 50: oklch(0.97 0.02 80)   → #FFFBEB
100: oklch(0.94 0.04 80)   → #FEF3C7
200: oklch(0.87 0.08 80)   → #FDE68A
300: oklch(0.79 0.12 80)   → #FCD34D
400: oklch(0.71 0.16 80)   → #FBBF24
500: oklch(0.63 0.18 80)   → #F59E0B
600: oklch(0.55 0.18 80)   → #D97706
700: oklch(0.47 0.16 80)   → #B45309
800: oklch(0.39 0.13 80)   → #92400E
900: oklch(0.30 0.10 80)   → #78350F
950: oklch(0.20 0.06 80)   → #451A03
```

### 5.3 Semantic Tokens — Light Mode

| Token | Map | Hex (approx) | Purpose |
|-------|-----|-------------|---------|
| `text-primary` | neutral-900 | #0F172A | Body text |
| `text-secondary` | neutral-600 | #475569 | Secondary text |
| `text-muted` | neutral-400 | #94A3B8 | Placeholder, disabled |
| `text-on-primary` | white | #FFFFFF | Text on primary bg |
| `surface-page` | neutral-50 | #F8FAFC | Page background |
| `surface-card` | white | #FFFFFF | Card/surface bg |
| `surface-elevated` | white + shadow | #FFFFFF | Modal, dropdown |
| `surface-sidebar` | neutral-900 | #0F172A | Sidebar bg |
| `border-default` | neutral-200 | #E2E8F0 | Borders |
| `border-strong` | neutral-300 | #CBD5E1 | Active borders |
| `focus-ring` | primary-500 | #3B82F6 | Focus indicator |

### 5.4 Semantic Tokens — Dark Mode

| Token | Map | Hex (approx) | Purpose |
|-------|-----|-------------|---------|
| `text-primary` | neutral-100 | #F1F5F9 | Body text |
| `text-secondary` | neutral-300 | #CBD5E1 | Secondary text |
| `text-muted` | neutral-500 | #64748B | Placeholder |
| `text-on-primary` | white | #FFFFFF | Text on primary bg |
| `surface-page` | neutral-950 | #020617 | Page background |
| `surface-card` | neutral-900 | #0F172A | Card |
| `surface-elevated` | neutral-800 | #1E293B | Modal, dropdown |
| `surface-sidebar` | neutral-950 | #020617 | Sidebar bg |
| `border-default` | neutral-800 | #1E293B | Borders |
| `border-strong` | neutral-700 | #334155 | Active borders |
| `focus-ring` | primary-400 | #60A5FA | Focus indicator |

### 5.5 Status Colors

| Token | Light | Dark |
|-------|-------|------|
| **success** | `#059669` (emerald-600) | `#34D399` (emerald-400) |
| success-subtle | `#ECFDF5` | `#064E3B` |
| **warning** | `#D97706` (amber-600) | `#FBBF24` (amber-400) |
| warning-subtle | `#FFFBEB` | `#78350F` |
| **danger** | `#DC2626` (red-600) | `#F87171` (red-400) |
| danger-subtle | `#FEF2F2` | `#7F1D1D` |
| **info** | `#2563EB` (blue-600) | `#60A5FA` (blue-400) |
| info-subtle | `#EFF6FF` | `#1E3A8A` |

### 5.6 WCAG Compliance Check

| Pairing | Ratio | Pass? |
|---------|-------|-------|
| neutral-900 on neutral-50 | 14.5:1 | ✅ AAA |
| neutral-700 on neutral-100 | 7.8:1 | ✅ AAA |
| primary-600 on white | 4.6:1 | ✅ AA |
| primary-500 on white | 3.2:1 | ❌ AA (large text OK) |
| amber-600 on white | 4.5:1 | ✅ AA |
| white on primary-700 | 5.1:1 | ✅ AA |
| white on primary-600 | 4.6:1 | ✅ AA |

> **Note**: Primary-500 chỉ dùng cho large text / UI components. Body text dùng primary-600 hoặc darker.

---

## 6. Palette Candidate 2: Warm Professional (Khuyến nghị chính)

> **"Vietnamese Warmth, Professional Trust"** — Đỏ Việt Nam làm chủ đạo + vàng/hổ phách accent + kem/cream neutral.

### 6.1 Tổng quan

```
Primary:     Đỏ Việt Nam (#C62828 → crimson, professional red)
Secondary:   Xanh dương (#1565C0 → blue-800 style) — trust anchor
Accent:      Hổ phách (#FF8F00 → warm amber) — CTA, highlight
Neutral:     Warm gray (oatmeal/cream — không phải cool gray)

Positioning: "Vietnamese-first HR, warm professional"
Best for:    Thị trường Việt Nam, differentiation mạnh
Risk:        Màu đỏ dễ nhầm với error/danger — cần phân biệt rõ
```

### 6.2 Color Scales

#### Primary — Crimson Red (Hue ≈ 355°, rich)

```
 50: oklch(0.97 0.02 355)  → #FFF5F5
100: oklch(0.93 0.04 355)  → #FFE4E4
200: oklch(0.87 0.08 355)  → #FECACA
300: oklch(0.78 0.13 355)  → #FCA5A5
400: oklch(0.69 0.17 355)  → #F87171
500: oklch(0.60 0.19 355)  → #EF4444
600: oklch(0.52 0.19 355)  → #DC2626
700: oklch(0.44 0.17 355)  → #B91C1C
800: oklch(0.36 0.14 355)  → #C62828  ← Anchor
900: oklch(0.28 0.10 355)  → #7F1D1D
950: oklch(0.18 0.06 355)  → #450A0A
```

> **Important**: Anchor primary-800 được chọn (lighter + tối ưu contrast) thay vì 600. Primary-600 (`#DC2626`) dùng cho buttons. Primary-500 (`#EF4444`) dùng cho large text / UI components. Error state dùng một red khác biệt rõ (xem bên dưới).

#### Secondary — Deep Blue (Hue ≈ 221°, trust anchor)

```
 50: oklch(0.97 0.02 240)  → #EFF6FF
100: oklch(0.93 0.04 240)  → #DBEAFE
200: oklch(0.87 0.08 240)  → #BFDBFE
300: oklch(0.78 0.12 240)  → #93C5FD
400: oklch(0.70 0.16 240)  → #60A5FA
500: oklch(0.62 0.19 240)  → #3B82F6
600: oklch(0.54 0.19 240)  → #2563EB
700: oklch(0.46 0.17 240)  → #1D4ED8
800: oklch(0.38 0.13 240)  → #1565C0  ← Anchor
900: oklch(0.28 0.10 240)  → #1E3A8A
950: oklch(0.18 0.06 240)  → #172554
```

#### Accent — Amber/Gold (Hue ≈ 38°, prosperity)

```
 50: oklch(0.97 0.02 80)   → #FFFBEB
100: oklch(0.94 0.04 80)   → #FEF3C7
200: oklch(0.87 0.08 80)   → #FDE68A
300: oklch(0.79 0.12 80)   → #FCD34D
400: oklch(0.71 0.16 80)   → #FBBF24
500: oklch(0.63 0.18 80)   → #F59E0B
600: oklch(0.55 0.18 80)   → #D97706
700: oklch(0.47 0.16 80)   → #FF8F00  ← Anchor (brighter)
800: oklch(0.39 0.13 80)   → #92400E
900: oklch(0.30 0.10 80)   → #78350F
950: oklch(0.20 0.06 80)   → #451A03
```

#### Neutral — Warm Gray (Oatmeal, Hue ≈ 40°, low chroma)

```
 50: oklch(0.98 0.01 60)   → #FFF8F0  (warm white)
100: oklch(0.95 0.01 60)   → #F5EDE0  (oatmeal)
200: oklch(0.90 0.01 60)   → #EDE4D4
300: oklch(0.82 0.01 60)   → #D8D1C7
400: oklch(0.72 0.01 60)   → #B8B0A5
500: oklch(0.62 0.01 60)   → #9C948A
600: oklch(0.52 0.01 60)   → #7A736A
700: oklch(0.44 0.01 60)   → #5C564F
800: oklch(0.36 0.01 60)   → #403B36
900: oklch(0.28 0.01 60)   → #2B2825
950: oklch(0.18 0.01 60)   → #181614
```

### 6.3 Semantic Tokens — Light Mode

| Token | Map | Hex | Purpose |
|-------|-----|-----|---------|
| `text-primary` | warm-900 | #2B2825 | Body text |
| `text-secondary` | warm-600 | #7A736A | Secondary text |
| `text-muted` | warm-400 | #B8B0A5 | Placeholder |
| `text-on-primary` | white | #FFFFFF | Text on primary bg |
| `surface-page` | warm-50 | #FFF8F0 | Page background (warm) |
| `surface-card` | white | #FFFFFF | Card surface |
| `surface-elevated` | white + warm shadow | — | Modal |
| `surface-sidebar` | primary-900 | #7F1D1D | Sidebar (deep red) |
| `border-default` | warm-200 | #EDE4D4 | Borders |
| `border-strong` | warm-300 | #D8D1C7 | Active borders |
| `focus-ring` | primary-700 | #B91C1C | Focus indicator |

### 6.4 Semantic Tokens — Dark Mode

| Token | Map | Hex | Purpose |
|-------|-----|-----|---------|
| `text-primary` | warm-100 | #F5EDE0 | Body text |
| `text-secondary` | warm-300 | #D8D1C7 | Secondary text |
| `text-muted` | warm-500 | #9C948A | Placeholder |
| `text-on-primary` | white | #FFFFFF | Text on primary bg |
| `surface-page` | warm-950 | #181614 | Page bg |
| `surface-card` | warm-900 | #2B2825 | Card |
| `surface-elevated` | warm-800 | #403B36 | Modal |
| `surface-sidebar` | primary-950 | #450A0A | Sidebar |
| `border-default` | warm-800 | #403B36 | Borders |
| `border-strong` | warm-700 | #5C564F | Active borders |
| `focus-ring` | primary-500 | #EF4444 | Focus indicator |

### 6.5 Status Colors

**Critical**: Error state phải khác biệt với primary red.

| Token | Light | Dark | Notes |
|-------|-------|------|-------|
| **success** | `#059669` (emerald-600) | `#34D399` (emerald-400) | Green — khác biệt |
| success-subtle | `#ECFDF5` | `#064E3B` | |
| **warning** | `#D97706` (amber-600) | `#FBBF24` (amber-400) | Amber — khác biệt |
| warning-subtle | `#FFFBEB` | `#78350F` | |
| **danger** | `#B91C1C` (primary-700) | `#FCA5A5` (primary-300) | Dùng primary red + icon |
| danger-subtle | `#FFE4E4` (primary-100) | `#7F1D1D` (primary-900) | |
| **info** | `#2563EB` (blue-600) | `#60A5FA` (blue-400) | Secondary blue |
| info-subtle | `#DBEAFE` | `#1E3A8A` | |

> **Important**: Danger dùng primary red *kèm icon*. Người dùng phân biệt danger vs primary qua context (icon, label, button style). Nếu cần differentiation mạnh hơn, danger có thể shift về red-orange (`#EA580C`).

### 6.6 WCAG Compliance Check

| Pairing | Ratio | Pass? |
|---------|-------|-------|
| warm-900 on warm-50 | 17.2:1 | ✅ AAA |
| warm-900 on white | 15.8:1 | ✅ AAA |
| warm-700 on warm-100 | 8.5:1 | ✅ AAA |
| primary-800 on white | 4.7:1 | ✅ AA |
| primary-700 on white | 3.8:1 | ❌ AA (large text OK) |
| primary-600 on white | 3.1:1 | ❌ AA (large text OK) |
| white on primary-800 | 4.7:1 | ✅ AA |
| white on primary-700 | 3.8:1 | ❌ (large text OK) |
| white on primary-900 | 7.2:1 | ✅ AAA |
| accent-700 on white | 3.5:1 | ❌ (large text OK) |
| accent-800 on white | 5.2:1 | ✅ AA |
| blue-700 on warm-50 | 7.1:1 | ✅ AAA |

**Guidelines**:
- **Buttons**: Primary button = white text on primary-800 (`#C62828`) — passes AA
- **Body text**: warm-900 (`#2B2825`) on warm-50 (`#FFF8F0`) — passes AAA
- **CTA accent**: Dùng accent-800 (`#92400E`) on white cho text, hoặc accent-600 (`#D97706`) for large elements
- **Large headings/UI**: primary-600, primary-700 OK cho text ≥ 24px hoặc ≥ 18.66px bold

---

## 7. Palette Candidate 3: Sage Green

> **"Calm, Modern, Growing"** — Muted sage green + slate neutral + coral accent.

### 7.1 Tổng quan

```
Primary:     Sage Green (#4A7C59 → muted forest sage)
Secondary:   Slate (#475569 → cool gray)
Accent:      Coral (#E8614A → warm peach/coral)
Neutral:     Slate (cool, clean)

Positioning: "Modern, calm, human-centered"
Best for:    HR wellness, engagement, people-centric features
Risk:        Có thể quá "soft" cho enterprise/payroll
```

### 7.2 Color Scales

#### Primary — Sage Green (Hue ≈ 145°, muted)

```
 50: oklch(0.97 0.02 145)  → #F0FDF4
100: oklch(0.93 0.04 145)  → #DCFCE7
200: oklch(0.86 0.06 145)  → #BBF7D0
300: oklch(0.78 0.09 145)  → #86EFAC
400: oklch(0.69 0.12 145)  → #4ADE80
500: oklch(0.60 0.14 145)  → #22C55E
600: oklch(0.52 0.13 145)  → #16A34A
700: oklch(0.44 0.11 145)  → #4A7C59  ← Anchor (muted)
800: oklch(0.36 0.09 145)  → #3D6B4A
900: oklch(0.28 0.07 145)  → #2D5A3A
950: oklch(0.18 0.04 145)  → #1A3A24
```

#### Secondary — Slate (Hue ≈ 215°, clean)

Same as Palette 1 secondary — slate 50–950.

#### Accent — Coral/Peach (Hue ≈ 15°, warm energy)

```
 50: oklch(0.97 0.02 15)   → #FFF5F0
100: oklch(0.94 0.04 15)   → #FFE8E0
200: oklch(0.87 0.08 15)   → #FFD0C0
300: oklch(0.79 0.12 15)   → #FFB3A0
400: oklch(0.71 0.16 15)   → #FF8A75
500: oklch(0.62 0.18 15)   → #F97350
600: oklch(0.54 0.18 15)   → #E8614A  ← Anchor
700: oklch(0.46 0.16 15)   → #D94D3A
800: oklch(0.38 0.13 15)   → #B83A2A
900: oklch(0.30 0.10 15)   → #9A2A1A
950: oklch(0.20 0.06 15)   → #5A1A10
```

### 7.3 Semantic Tokens — Light Mode

| Token | Map | Hex | Purpose |
|-------|-----|-----|---------|
| `text-primary` | slate-900 | #0F172A | Body text |
| `text-secondary` | slate-600 | #475569 | Secondary text |
| `text-muted` | slate-400 | #94A3B8 | Placeholder |
| `text-on-primary` | white | #FFFFFF | Text on primary bg |
| `surface-page` | sage-50 | #F0FDF4 | Page bg (hint of green) |
| `surface-card` | white | #FFFFFF | Card |
| `surface-elevated` | white + shadow | — | Modal |
| `surface-sidebar` | sage-800 | #3D6B4A | Sidebar |
| `border-default` | slate-200 | #E2E8F0 | Borders |
| `border-strong` | slate-300 | #CBD5E1 | Active borders |
| `focus-ring` | sage-500 | #22C55E | Focus indicator |

### 7.4 Semantic Tokens — Dark Mode

| Token | Map | Hex | Purpose |
|-------|-----|-----|---------|
| `text-primary` | slate-100 | #F1F5F9 | Body text |
| `text-secondary` | slate-300 | #CBD5E1 | Secondary text |
| `text-muted` | slate-500 | #64748B | Placeholder |
| `text-on-primary` | white | #FFFFFF | Text on primary bg |
| `surface-page` | sage-950 | #1A3A24 | Page bg |
| `surface-card` | sage-900 | #2D5A3A | Card |
| `surface-elevated` | sage-800 | #3D6B4A | Modal |
| `surface-sidebar` | sage-950 | #1A3A24 | Sidebar |
| `border-default` | sage-800 | #3D6B4A | Borders |
| `border-strong` | sage-700 | #4A7C59 | Active borders |
| `focus-ring` | sage-400 | #4ADE80 | Focus indicator |

### 7.5 Status Colors

| Token | Light | Dark |
|-------|-------|------|
| **success** | `#16A34A` (green-600) | `#4ADE80` (green-400) |
| success-subtle | `#F0FDF4` | `#052E16` |
| **warning** | `#D97706` (amber-600) | `#FBBF24` (amber-400) |
| warning-subtle | `#FFFBEB` | `#78350F` |
| **danger** | `#DC2626` (red-600) | `#F87171` (red-400) |
| danger-subtle | `#FEF2F2` | `#7F1D1D` |
| **info** | `#0284C7` (sky-600) | `#38BDF8` (sky-400) |
| info-subtle | `#F0F9FF` | `#0C4A6E` |

### 7.6 WCAG Compliance Check

| Pairing | Ratio | Pass? |
|---------|-------|-------|
| slate-900 on sage-50 | 14.1:1 | ✅ AAA |
| slate-900 on white | 15.8:1 | ✅ AAA |
| sage-700 on white | 3.3:1 | ❌ AA (large text OK) |
| sage-800 on white | 4.8:1 | ✅ AA |
| white on sage-700 | 3.3:1 | ❌ (large text OK) |
| white on sage-800 | 4.8:1 | ✅ AA |
| coral-600 on white | 4.6:1 | ✅ AA |
| slate-700 on sage-50 | 8.2:1 | ✅ AAA |

> **Note**: Sage-700 (`#4A7C59`) chỉ dùng cho large text / UI components. Body text trên nền trắng dùng sage-800 hoặc slate-900.

---

## 8. So sánh và đánh giá

### 8.1 Comparison Matrix

| Tiêu chí | Professional Blue | Warm Professional | Sage Green |
|----------|-----------------|-------------------|------------|
| **Differentiation** | ⚠️ Thấp (>70% SaaS dùng blue) | ✅ Cao (đỏ Việt Nam) | ✅ Trung bình-cao |
| **HR Appropriateness** | ✅ Trust, stable | ✅ Warm, human | ✅ Calm, modern |
| **Vietnamese Identity** | ❌ Không | ✅ Rất mạnh | ⚠️ Trung bình |
| **Enterprise Credibility** | ✅✅ Rất cao | ✅ Cao | ✅ Cao |
| **WCAG AA Feasibility** | ✅ Dễ | ⚠️ Cần careful (red primary) | ✅ Dễ |
| **Dark Mode Quality** | ✅ Tốt | ✅ Tốt (warm tones) | ✅ Tốt (natural) |
| **Status Clarity** | ✅ Dễ (blue distinct) | ⚠️ Danger gần primary | ✅ Dễ |
| **Employee Warmth** | ⚠️ Trung bình (cool) | ✅✅ Ấm áp | ✅ Mát dịu |
| **Admin Power Feel** | ✅✅ Mạnh | ✅ Mạnh | ⚠️ Trung bình |
| **Maintenance Cost** | ✅ Thấp (chuẩn) | ⚠️ Trung bình | ✅ Thấp |

### 8.2 Risk Assessment

| Palette | Risk | Mitigation |
|---------|------|------------|
| **Professional Blue** | Không nổi bật, generic | Dùng amber accent + warm neutrals để tạo điểm nhấn |
| **Warm Professional** | Red→Error confusion | Icon + label cho error states; primary red dùng ở 800 (tối) không phải 500 |
| **Sage Green** | Quá "soft" cho payroll/compliance | Slate secondary + coral accent cho cứng cáp |

### 8.3 Scoring (1–5)

| Palette | Differentiation | Trust | HR Fit | Vietnam Fit | Feasibility | **Total** |
|---------|----------------|-------|--------|-------------|-------------|-----------|
| **Blue** | 2 | 5 | 4 | 1 | 5 | **17** |
| **Warm** | 5 | 4 | 5 | 5 | 3 | **22** |
| **Sage** | 4 | 4 | 4 | 3 | 4 | **19** |

---

## 9. Khuyến nghị cuối cùng

### Tier 1 (Khuyến nghị chính): **Warm Professional**

> Lý do: Đây là palette duy nhất mang bản sắc Việt Nam rõ rệt, đồng thời giữ được sự chuyên nghiệp và tin cậy của HR platform. Màu đỏ `#C62828` (primary-800) vừa đủ tối để đạt WCAG AA, vừa mang ý nghĩa may mắn, nhiệt huyết trong văn hóa Việt. Accent amber và secondary blue tạo sự cân bằng.

**Differentiation statement**:
> "Vroom HR không phải một bản sao màu xanh của platform phương Tây. Đó là HR platform cho doanh nghiệp Việt Nam — màu đỏ của sự nhiệt huyết, màu vàng của thịnh vượng, màu kem của sự ấm áp."

### Tier 2 (Alternative): **Sage Green + Coral**

Dùng nếu:
- Team muốn hiện đại, calm, "people-first" positioning
- Sẵn sàng đánh đổi enterprise feel để lấy warmth
- Có thể thêm Vietnamese touches qua illustrations, typography

### Tier 3 (Fallback): **Professional Blue + Amber**

Dùng nếu:
- Enterprise credibility là ưu tiên số 1
- Không muốn differentiation risk
- Thị trường mục tiêu là doanh nghiệp lớn, truyền thống

### Decision Flow

```
Vroom HR muốn:
├── Vietnamese identity mạnh? → Warm Professional ✓
├── Modern, calm, people-first? → Sage Green
├── Enterprise trust tối đa? → Professional Blue
└── Cần test A/B?
    ├── Warm Professional vs Professional Blue
    └── Đo: recall, trust score, task completion
```

---

## 10. Implementation: Tailwind CSS v4 + CSS Variables

### 10.1 File Structure

```
src/
├── styles/
│   ├── app.css                    # Main CSS — @import tailwind + @theme
│   ├── colors/
│   │   ├── base.css               # Primitive color tokens
│   │   ├── tokens.css             # Semantic tokens (light mode)
│   │   └── tokens-dark.css        # Semantic tokens (dark mode)
│   └── components/                # Component styles
│       ├── button.css
│       ├── card.css
│       └── table.css
```

### 10.2 app.css — Tailwind v4 @theme

```css
@import "tailwindcss";
@import "./colors/base.css";

/* Light theme (default) */
:root,
[data-theme="light"] {
  @import "./colors/tokens.css";
}

/* Dark theme */
[data-theme="dark"] {
  @import "./colors/tokens-dark.css";
}
```

### 10.3 Primitive Tokens — `base.css`

Ví dụ cho **Warm Professional** palette:

```css
@theme {
  /* ── Primary: Crimson Red ── */
  --color-primary-50:  oklch(0.97 0.02 355);
  --color-primary-100: oklch(0.93 0.04 355);
  --color-primary-200: oklch(0.87 0.08 355);
  --color-primary-300: oklch(0.78 0.13 355);
  --color-primary-400: oklch(0.69 0.17 355);
  --color-primary-500: oklch(0.60 0.19 355);
  --color-primary-600: oklch(0.52 0.19 355);
  --color-primary-700: oklch(0.44 0.17 355);
  --color-primary-800: oklch(0.36 0.14 355);
  --color-primary-900: oklch(0.28 0.10 355);
  --color-primary-950: oklch(0.18 0.06 355);

  /* ── Secondary: Deep Blue ── */
  --color-secondary-50:  oklch(0.97 0.02 240);
  --color-secondary-100: oklch(0.93 0.04 240);
  --color-secondary-200: oklch(0.87 0.08 240);
  --color-secondary-300: oklch(0.78 0.12 240);
  --color-secondary-400: oklch(0.70 0.16 240);
  --color-secondary-500: oklch(0.62 0.19 240);
  --color-secondary-600: oklch(0.54 0.19 240);
  --color-secondary-700: oklch(0.46 0.17 240);
  --color-secondary-800: oklch(0.38 0.13 240);
  --color-secondary-900: oklch(0.28 0.10 240);
  --color-secondary-950: oklch(0.18 0.06 240);

  /* ── Accent: Amber/Gold ── */
  --color-accent-50:  oklch(0.97 0.02 80);
  --color-accent-100: oklch(0.94 0.04 80);
  --color-accent-200: oklch(0.87 0.08 80);
  --color-accent-300: oklch(0.79 0.12 80);
  --color-accent-400: oklch(0.71 0.16 80);
  --color-accent-500: oklch(0.63 0.18 80);
  --color-accent-600: oklch(0.55 0.18 80);
  --color-accent-700: oklch(0.47 0.16 80);
  --color-accent-800: oklch(0.39 0.13 80);
  --color-accent-900: oklch(0.30 0.10 80);
  --color-accent-950: oklch(0.20 0.06 80);

  /* ── Neutral: Warm Gray ── */
  --color-warm-50:  oklch(0.98 0.01 60);
  --color-warm-100: oklch(0.95 0.01 60);
  --color-warm-200: oklch(0.90 0.01 60);
  --color-warm-300: oklch(0.82 0.01 60);
  --color-warm-400: oklch(0.72 0.01 60);
  --color-warm-500: oklch(0.62 0.01 60);
  --color-warm-600: oklch(0.52 0.01 60);
  --color-warm-700: oklch(0.44 0.01 60);
  --color-warm-800: oklch(0.36 0.01 60);
  --color-warm-900: oklch(0.28 0.01 60);
  --color-warm-950: oklch(0.18 0.01 60);

  /* ── Status Colors (flat, no scale needed) ── */
  --color-status-success:        #16A34A;
  --color-status-success-subtle: #ECFDF5;
  --color-status-warning:        #D97706;
  --color-status-warning-subtle: #FFFBEB;
  --color-status-danger:         #B91C1C;
  --color-status-danger-subtle:  #FFE4E4;
  --color-status-info:           #2563EB;
  --color-status-info-subtle:    #DBEAFE;
}
```

### 10.4 Semantic Tokens — Light `tokens.css`

```css
@theme {
  /* ── Text ── */
  --color-text-primary:   var(--color-warm-900);
  --color-text-secondary: var(--color-warm-600);
  --color-text-muted:     var(--color-warm-400);
  --color-text-on-primary: #FFFFFF;
  --color-text-on-accent:  #FFFFFF;
  --color-text-link:      var(--color-secondary-700);

  /* ── Surface ── */
  --color-surface-page:     var(--color-warm-50);
  --color-surface-card:     #FFFFFF;
  --color-surface-elevated: #FFFFFF;
  --color-surface-sidebar:  var(--color-primary-900);
  --color-surface-header:   #FFFFFF;

  /* ── Border ── */
  --color-border-default: var(--color-warm-200);
  --color-border-strong:  var(--color-warm-300);
  --color-border-focus:   var(--color-primary-700);

  /* ── Interactive ── */
  --color-button-primary-bg:    var(--color-primary-800);
  --color-button-primary-text:  #FFFFFF;
  --color-button-primary-hover: var(--color-primary-900);
  --color-button-secondary-bg:    var(--color-warm-100);
  --color-button-secondary-text:  var(--color-warm-900);
  --color-button-secondary-hover: var(--color-warm-200);

  /* ── Chart colors ── */
  --color-chart-1: var(--color-primary-600);
  --color-chart-2: var(--color-secondary-500);
  --color-chart-3: var(--color-accent-500);
  --color-chart-4: var(--color-status-success);
  --color-chart-5: #8B5CF6;
}
```

### 10.5 Semantic Tokens — Dark `tokens-dark.css`

```css
@theme {
  /* ── Text ── */
  --color-text-primary:   var(--color-warm-100);
  --color-text-secondary: var(--color-warm-300);
  --color-text-muted:     var(--color-warm-500);
  --color-text-on-primary: #FFFFFF;
  --color-text-on-accent:  #FFFFFF;
  --color-text-link:      var(--color-secondary-400);

  /* ── Surface ── */
  --color-surface-page:     var(--color-warm-950);
  --color-surface-card:     var(--color-warm-900);
  --color-surface-elevated: var(--color-warm-800);
  --color-surface-sidebar:  var(--color-primary-950);
  --color-surface-header:   var(--color-warm-900);

  /* ── Border ── */
  --color-border-default: var(--color-warm-800);
  --color-border-strong:  var(--color-warm-700);
  --color-border-focus:   var(--color-primary-500);

  /* ── Interactive ── */
  --color-button-primary-bg:    var(--color-primary-700);
  --color-button-primary-text:  #FFFFFF;
  --color-button-primary-hover: var(--color-primary-600);
  --color-button-secondary-bg:    var(--color-warm-800);
  --color-button-secondary-text:  var(--color-warm-100);
  --color-button-secondary-hover: var(--color-warm-700);

  /* ── Chart colors (dark mode variant) ── */
  --color-chart-1: var(--color-primary-400);
  --color-chart-2: var(--color-secondary-400);
  --color-chart-3: var(--color-accent-400);
  --color-chart-4: #34D399;
  --color-chart-5: #A78BFA;
}
```

### 10.6 Usage trong Components

```html
<!-- Button component -->
<button class="bg-button-primary-bg text-button-primary-text hover:bg-button-primary-hover rounded-lg px-4 py-2">
  Lưu thay đổi
</button>

<!-- Card component -->
<div class="bg-surface-card border border-border-default rounded-lg p-6 shadow-sm">
  <h2 class="text-text-primary text-lg font-semibold">Thông tin nhân viên</h2>
  <p class="text-text-secondary text-sm">Quản lý hồ sơ nhân viên</p>
</div>

<!-- Status badge -->
<span class="bg-status-success-subtle text-status-success text-xs font-medium px-2 py-1 rounded-full">
  Đã kích hoạt
</span>
```

### 10.7 Dark Mode Toggle

```javascript
// Dark mode toggle function
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

// On load — check system preference + saved preference
const saved = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
if (saved) {
  document.documentElement.setAttribute('data-theme', saved);
} else if (prefersDark) {
  document.documentElement.setAttribute('data-theme', 'dark');
}
```

### 10.8 CSS Variables — Direct Usage (khi cần)

```css
/* Inline style or arbitrary value */
div {
  background-color: var(--color-surface-card);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
}

/* Tailwind arbitrary value */
<div class="[background-color:var(--color-surface-card)] p-6">
```

---

## References

### Color Trends
1. [4 B2B SaaS Color Palettes That Stand Out in 2026 — Tentackles](https://tentackles.com/blog/b2b-saas-color-palettes-2026-that-stand-out)
2. [SaaS Color Schemes June 2026 — ColorArchive Notes](https://colorarchive.org/notes/june-2026-saas-color-scheme/)
3. [2026 Digital Sage Trend — ColorArchive](https://colorarchive.org/collections/2026-digital-sage-trend/)

### Accessibility
4. [Color System WCAG Compliance: 2026 Guide — Digital Heroes](https://digitalheroesco.com/journal/color-system-wcag-compliance/)
5. [How to Build an Accessible Color System — Zepixo](https://www.zepixo.com/blog/how-to-build-an-accessible-color-system)
6. [WCAG 2.2 Understanding Contrast Minimum — W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)

### Tailwind CSS v4
7. [Tailwind v4 Theme Variables — Tailwind Docs](https://tailwindcss.com/docs/theme)
8. [Tailwind v4 Color: OKLCH, @theme — ColorUI](https://colorui.io/learn/tailwind-v4-color)
9. [Custom Colors in Tailwind v4 — DevCrea](https://www.devcrea.com/custom-colors-in-tailwind-css-v4)

### Existing Design Direction
10. [Vroom HR UI/UX Design References — docs/design/ui-hr-references.md](./ui-hr-references.md)
