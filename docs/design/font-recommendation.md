# Font Recommendation — Vroom HR

> **Context:** Vroom HR là nền tảng HR B2B cho doanh nghiệp Việt Nam. UI có nhiều bảng dữ liệu (datagrid), form, dashboard, và text dài tiếng Việt. Font chữ cần support tiếng Việt đầy đủ, đọc tốt ở small size, có variable font, và pair được giữa heading/body/label.

## Mục lục

- [Font hiện tại: Public Sans](#font-hiện-tại-public-sans)
- [Ứng viên so sánh](#ứng-viên-so-sánh)
- [Ma trận so sánh](#ma-trận-so-sánh)
- [Phân tích chi tiết](#phân-tích-chi-tiết)
- [Đề xuất](#đề-xuất)
- [Kế hoạch migration](#kế-hoạch-migration)

---

## Font hiện tại: Public Sans

| Thuộc tính | Giá trị |
|---|---|
| **Glyph count** | 645 (Latin-only theo thiết kế gốc) |
| **Variable font** | ✅ wght 100–900 |
| **x-height** | 1,034 / 1,000 UPM (thấp nhất trong các ứng viên) |
| **Vietnamese subset** | ✅ Có trên Google Fonts (`vietnamese`) |
| **Trạng thái bảo trì** | ❌ **Không còn được phát triển (unmaintained)** |

**Rủi ro:** Public Sans đã bị USWDS (U.S. Web Design System) tuyên bố ngừng phát triển. Repo GitHub [ghi rõ](https://github.com/uswds/public-sans):

> "Public Sans as a font is not currently being actively developed or maintained."

Site `public-sans.digital.gov` đã redirect vào tháng 6/2026. Vì vậy bất kỳ lỗi Vietnamese glyph nào cũng sẽ không được fix. Đây là rủi ro lớn cho một HR platform dùng tiếng Việt hàng ngày.

Hiện tại project load Public Sans với 4 static weights (300, 400, 500, 600) — không dùng variable font, làm tăng dung lượng network.

---

## Ứng viên so sánh

Các font được đánh giá:

1. **Inter** — rsms — Google Fonts
2. **Plus Jakarta Sans** — Tokotype — Google Fonts
3. **Manrope** — Mikhail Sharanda — Google Fonts
4. **DM Sans** — Colophon Foundry — Google Fonts
5. **Satoshi** — Indian Type Foundry — Fontshare
6. **Figtree** — Erik Kennedy — Google Fonts

---

## Ma trận so sánh

| Tiêu chí | Public Sans ⚠️ | Inter ✅ | Plus Jakarta Sans ✅ | Satoshi ❌ | Figtree ❌ | DM Sans ⚠️ | Manrope ✅ |
|---|---|---|---|---|---|---|---|
| **Vietnamese glyphs** | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ | ✅ |
| **Variable font** | ✅ wght | ✅ wght+opsz | ✅ wght | ✅ wght | ✅ wght | ✅ wght+opsz | ✅ wght |
| **x-height** | Thấp (1034) | Cao (1118) | Trung bình | Trung bình | Trung bình | Trung bình | Trung bình |
| **Weight range** | 100–900 | 100–900 | 200–800 | 300–900 | 300–900 | 100–1000 | 200–800 |
| **Italic** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Design for screen** | Trung bình | ✅ Tối ưu | Tốt | Tốt | Tốt | Tốt | Tốt |
| **Bảo trì** | ❌ Ngừng | ✅ Active | ✅ Active | ✅ Active | ✅ Active | ✅ Active | ✅ Active |
| **Google Fonts** | ✅ | ✅ | ✅ | ❌ (Fontshare) | ✅ | ✅ | ✅ |
| **License** | SIL OFL | SIL OFL | SIL OFL | ITF FFL | SIL OFL | SIL OFL | SIL OFL |
| **Dung lượng (var)** | ~59 KB | ~334 KB | ~100 KB | ~80 KB | ~70 KB | ~120 KB | ~80 KB |
| **Phù hợp HR B2B** | ⚠️ | ✅✅ | ✅✅ | ❌ | ❌ | ⚠️ | ✅ |

### Chú thích

- **Vietnamese glyphs ✅** = Có subset `vietnamese` trên Google Fonts.
- **Vietnamese glyphs ❌** = Không có subset `vietnamese`.
- **Vietnamese glyphs ⚠️** = Có `latin-ext` nhưng không có `vietnamese` subset riêng.

---

## Phân tích chi tiết

### 1. Public Sans — ⚠️ Cần thay thế khẩn cấp

| Ưu điểm | Nhược điểm |
|---|---|
| Nhẹ (59 KB static, ~25 KB variable) | **Không còn bảo trì** |
| Có Vietnamese subset | x-height thấp, khó đọc small size |
| Tabular figures (tnum) | Không có italic variable? ❌ (có italic riêng) |
| Neutral, chuyên nghiệp | Thiết kế cho USWDS, không optimize cho screen |
| | Glyph count thấp (645) — thiếu nhiều ký tự Latin mở rộng |

### 2. Inter — ✅ Mạnh nhất cho UI/Data-heavy

| Thuộc tính | Giá trị |
|---|---|
| **Designed for** | Màn hình máy tính (screen-first) |
| **x-height** | 1,118 / 1,000 UPM — **cao nhất** → đọc tốt ở small size |
| **Weight range** | 100–900 (full spectrum) |
| **Variable axes** | `wght` 100–900 + `opsz` 14–32 |
| **Glyph count** | **2,926** — rộng nhất trong tất cả font so sánh |
| **OpenType features** | Tabular figures (tnum), slashed zero, stylistic sets (ss01-ss03) |
| **Vietnamese issues** | Từng có bug diacritic overlap ở ExtraLight/Light (issue #3579, #883). Đã fix ở Inter v4+ (2024), cần kiểm tra kỹ weight nhẹ. |
| **Used by** | Figma, GitLab, Mozilla, NASA, ISO, Unity |

Phù hợp cho: datagrid, form, dashboard, UI label — mọi thứ cần đọc nhanh và chính xác.

**Lưu ý:** Inter phổ biến đến mức "có thể bị nhàm" (looks like 30% of the SaaS internet). Cần phối hợp màu sắc, spacing, và brand elements để tạo khác biệt.

### 3. Plus Jakarta Sans — ✅ Tốt cho HR/B2B cần warmth

| Thuộc tính | Giá trị |
|---|---|
| **Design** | Geometric sans-serif pha humanist — ấm áp hơn Inter |
| **Weight range** | 200–800 (hẹp hơn Inter) |
| **Vietnamese support** | Được thêm chính thức từ v2.400 (12/2020) |
| **Variable font** | ✅ wght + italic variable |
| **Character** | Softer terminals, rounder counters, dễ tiếp cận |
| **x-height** | Cao, nhưng không bằng Inter |

Phù hợp cho: HR tech, education tech, platform cần cảm giác "thân thiện, con người".

> "Plus Jakarta Sans is the warmest of the three. It carries a slightly humanist tilt, with softer terminals and rounder counters."
> — [pravinkumar.co, B2B Webflow comparison 2026](https://www.pravinkumar.co/blog/inter-geist-plus-jakarta-sans-webflow-b2b-2026)

### 4. Manrope — ✅ Lựa chọn thay thế tốt

| Thuộc tính | Giá trị |
|---|---|
| **Design** | Geometric sans-serif, modern, polished |
| **Weight range** | 200–800 |
| **Vietnamese** | ✅ `vietnamese` subset |
| **Variable font** | ✅ wght (200–800) |
| **Italic** | ❌ **Không có italic** |
| **Subsets** | cyrillic, cyrillic-ext, greek, latin, latin-ext, vietnamese |

**Thiếu italic** là vấn đề lớn cho UI (italic dùng cho emphasis, foreign words, etc.). Manrope phù hợp hơn cho marketing/landing page, không lý tưởng cho toàn bộ UI product.

Phù hợp: Heading font kết hợp Inter làm body.

### 5. Satoshi — ❌ Không support tiếng Việt

- 504 glyphs — không đủ Latin Extended cho tiếng Việt
- Chỉ có trên Fontshare, không có trên Google Fonts
- License ITF FFL (free cho commercial, nhưng khác ecosystem)
- **Dealbreaker:** không thể dùng làm font chính cho HR platform tiếng Việt

### 6. Figtree — ❌ Không support tiếng Việt

- Chỉ có `latin` + `latin-ext`
- Có issue report về Vietnamese diacritic display problems (#30)
- **Dealbreaker:** giống Satoshi

### 7. DM Sans — ⚠️ Thiếu Vietnamese subset chính thức

| Thuộc tính | Giá trị |
|---|---|
| **Weight range** | 100–1000 (rộng nhất!) |
| **Variable axes** | `wght` + `opsz` 9–40 (optical size) |
| **Vietnamese** | ❌ Không có `vietnamese` subset |
| **Design** | Low-contrast geometric, elegant |
| **Derived from** | Poppins (ITF) |

Thiếu Vietnamese subset chính thức có nghĩa là các ký tự như ế, ề, ệ, ữ, ự có thể render sai hoặc dùng fallback font. Rủi ro cao.

---

## Đề xuất

### Lựa chọn A (Khuyến nghị chính): **Inter** cho mọi thứ

Dùng Inter làm single font family cho cả body, heading, và label.

```
Font: Inter (variable, wght 100–900 + opsz 14–32)
Subset: latin + vietnamese
Weights dùng: 400 (body), 500 (label), 600–700 (heading)
Variable: ✅ Một file cho mọi weight
```

**Lý do:**
1. **x-height cao nhất** — đọc tốt nhất ở 14–16px (dashboard, datagrid, form)
2. **Designed for screen** — không phải print-to-screen adaptation
3. **Vietnamese subset** — có trên Google Fonts
4. **Tabular figures** — datagrid, số liệu HR (lương, ngày tháng) căn chỉnh chuẩn
5. **Opsz axis** — tự động tối ưu cho từng kích thước (14px cho UI vs 32px cho heading)
6. **2926 glyphs** — coverage rộng nhất, an toàn cho mọi ký tự tiếng Việt
7. **Cộng đồng lớn** — bug được fix nhanh, tài liệu nhiều

**Rủi ro cần kiểm tra:**
- Test kỹ các tổ hợp diacritic tiếng Việt ở weight Light (200–300) trước khi deploy
- Inter đang rất phổ biến — design cần bù đắp bằng màu sắc, spacing, icon để không bị "generic"

### Lựa chọn B (HR-friendly): **Plus Jakarta Sans** heading + **Inter** body

Pair font để tạo cá tính riêng cho Vroom HR.

```
Heading: Plus Jakarta Sans (variable wght 200–800)
Body:     Inter (variable wght 100–900 + opsz 14–32)
Label:    Inter (500 weight)
Subset:   latin + vietnamese cho cả hai
```

**Lý do:**
1. Plus Jakarta Sans mang warmth, phù hợp HR platform — "cảm giác con người"
2. Inter đảm bảo readability cho datagrid, form, dashboard
3. Cả hai đều có Vietnamese subset
4. Cả hai đều variable font, tối ưu dung lượng
5. Tạo visual hierarchy rõ ràng giữa heading và body

**Lưu ý kỹ thuật:**
- Cần check x-height match giữa hai font (Inter x-height cao hơn → có thể cần điều chỉnh line-height)
- Dùng CSS variable: `--font-heading` và `--font-sans`
- Total payload: ~100 KB (Plus Jakarta Sans var) + ~80 KB (Inter var subset) = ~180 KB

### Lựa chọn C (Tiết kiệm): **Inter** + **Public Sans** (giữ nguyên heading)

Không khuyến nghị do Public Sans unmaintained.

---

## Bảng so sánh xếp hạng

| Hạng | Font | Điểm | Lý do |
|---|---|---|---|
| 🥇 | **Inter** | 9.5/10 | Screen-first, x-height cao, Vietnamese đầy đủ, variable wght+opsz, active |
| 🥈 | **Plus Jakarta Sans** | 8.5/10 | Warm, HR-phù hợp, Vietnamese tốt, variable font, thiếu weight 100 và 900 |
| 🥉 | **Manrope** | 7/10 | Vietnamese tốt, variable font, nhưng thiếu italic — chỉ phù hợp làm heading |
| 4 | DM Sans | 6/10 | Weight range rộng + opsz, nhưng thiếu Vietnamese subset |
| 5 | Public Sans ⚠️ | 5/10 | Vietnamese có, nhưng unmaintained, x-height thấp |
| 6 | Satoshi | 3/10 | Đẹp nhưng không support tiếng Việt |
| 7 | Figtree | 2/10 | Không support tiếng Việt + diacritic bugs |

---

## So sánh pair font phổ biến cho B2B SaaS

| Pair | Phù hợp | Ghi chú |
|---|---|---|
| **Inter (single)** | ✅✅ Mọi B2B SaaS | An toàn, tối ưu, hơi generic |
| Plus Jakarta Sans + Inter | ✅✅ HR, Education, Healthcare | Warm + functional |
| **Manrope + Inter** | ✅ Marketing-heavy B2B | Manrope thiếu italic |
| Space Grotesk + Inter | ✅ Tech/Dev tools | Hơi lạnh cho HR |
| Figtree + Inter | ❌ | Figtree không support tiếng Việt |

---

## Kế hoạch migration (gợi ý)

### Giai đoạn 1: Chọn font và test

1. Cài font thử nghiệm (Inter / Plus Jakarta Sans)
2. Test Vietnamese rendering ở tất cả weight:
   - Các tổ hợp: ứ, ừ, ử, ữ, ự, ế, ề, ể, ễ, ệ, ố, ồ, ổ, ỗ, ộ, ấ, ầ, ẩ, ẫ, ậ, ắ, ằ, ẳ, ẵ, ặ
   - Đặc biệt ở weight Light (200–300) nếu dùng
3. Test readability ở 14px, 16px trên datagrid và form
4. Test trên Windows (ClearType) và macOS

### Giai đoạn 2: Cập nhật code

1. Sửa `frontend/src/app/layout.tsx` — thay `Public_Sans` import
2. Sửa `frontend/tailwind.config.ts` — cập nhật `fontFamily` config
3. Chuyển từ static weights sang variable font để giảm dung lượng
4. Nếu chọn pair font: thiết lập CSS variable cho heading và body riêng

### Giai đoạn 3: QA

1. So sánh screenshot trước/sau ở các màn hình chính
2. Check Cumulative Layout Shift (CLS) với font-display: swap
3. Check dung lượng font bundle

---

## Tài liệu tham khảo

- [Inter font family](https://rsms.me/inter/) — Rasmus Andersson
- [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans) — Tokotype
- [Manrope](https://fonts.google.com/specimen/Manrope) — Mikhail Sharanda
- [Public Sans (unmaintained)](https://github.com/uswds/public-sans) — USWDS
- [Satoshi](https://www.fontshare.com/fonts/satoshi) — Indian Type Foundry
- [Figtree](https://github.com/erikdkennedy/figtree/issues/30) — Vietnamese support issue
- [B2B SaaS Typography Guide 2026](https://brand-generator.com/blog/typography-guide-saas)
- [Inter vs Geist vs Plus Jakarta Sans for B2B](https://www.pravinkumar.co/blog/inter-geist-plus-jakarta-sans-webflow-b2b-2026)
- [Inter vs Manrope Comparison](https://fontswiki.com/comparisons/inter-font-family-vs-manrope-font-family)
- [Google Fonts — Vietnamese fonts list](https://vietrick.com/font-chu-tieng-viet-dep-tren-google-fonts/)
