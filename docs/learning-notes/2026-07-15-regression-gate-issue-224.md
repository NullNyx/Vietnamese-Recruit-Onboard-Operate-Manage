# Task

Chạy regression gate browser cho HR và Employee Account theo issue #224, ở desktop 1280px và mobile 390px.

# What I changed

- Sửa lỗi cú pháp JSX trong `frontend/src/components/data-table.tsx` khiến Next.js trả HTTP 500 ngay cả ở `/login`.
- Làm Ctrl+K chịu được cả `k` và `K` từ browser event bằng `event.key.toLowerCase()`.
- Cấu hình project mobile Playwright chạy Chromium mobile emulation, không phụ thuộc WebKit binary có sẵn trên máy.
- Sửa browser assertion Employee Account để kiểm tra hamburger theo đúng viewport thay vì đòi mobile control trên desktop.
- Lưu screenshot evidence: `docs/learning-notes/assets/issue-224/hr-1280.png` và `docs/learning-notes/assets/issue-224/employee-390.png`.

# The real problem

Regression gate không thể chạy vì một nhánh JSX error state thiếu dấu `}` làm toàn bộ frontend compile fail. Sau khi sửa, browser test còn bộc lộ hai giả định không bền: keyboard event có thể có `event.key` viết hoa, và test mobile control được chạy trong cả project desktop.

# Why this solution

Giữ thay đổi nhỏ ở đúng seam: sửa parser error, chuẩn hóa keyboard comparison, buộc project mobile dùng Chromium emulation và làm assertion phụ thuộc viewport thật. Flow vẫn kiểm tra external behavior qua accessible role/name, không kiểm tra private component internals.

# Production shape

Playwright chạy với `E2E_BASE_URL`, `E2E_HR_STORAGE_STATE` và `E2E_EMPLOYEE_STORAGE_STATE`. Kết quả thực tế ngày 2026-07-15:

- `hr-desktop` 1280px: pass search bằng Ctrl+K, dialog name/description, focus input, Escape và focus return.
- `hr-mobile` 390px: pass cùng keyboard/accessibility flow.
- `employee-desktop` 1280px: pass named account/search controls và xác nhận hamburger hidden.
- `employee-mobile` 390px: pass named account/search/hamburger controls.
- Tổng: `4 passed (4.0s)`.
- Console error được thu trong từng test và cả bốn flow đều pass `consoleErrors.errors` rỗng.
- Vitest được cấu hình loại trừ `frontend/e2e/**` để Playwright spec không bị Vitest import nhầm.
- Full Vitest: 380/381 test pass; một test recruitment inbox timeout có sẵn ngoài scope (`recruitment-inbox-actions-ui.test.tsx`).
- TypeScript vẫn có 2 lỗi fixture có sẵn trong `job-application-actions.test.tsx` (`intent`, `has_cv`). Backend full suite cũng có các regression interview có sẵn về `calendar_event_id`; không thuộc browser UX scope.
- DataTable loading/error/empty filter được kiểm tra bởi `frontend/src/components/data-table.test.tsx`; browser flow không giả lập backend state để tránh biến regression seam thành test implementation.

Lệnh chạy:

```bash
cd frontend
E2E_BASE_URL=http://localhost:3000 \
E2E_HR_STORAGE_STATE=/tmp/vroom-hr.json \
E2E_EMPLOYEE_STORAGE_STATE=/tmp/vroom-employee.json \
pnpm test:e2e
```

# Other possible approaches

1. Cài WebKit bằng `pnpm exec playwright install webkit` và giữ iPhone 12 project nguyên bản. Phù hợp khi CI có cache browser đầy đủ và cần kiểm tra engine WebKit thật.
2. Chỉ chạy browser flow trên desktop rồi dùng Vitest để kiểm tra mobile class/conditional rendering. Phù hợp khi không có browser binary hoặc mobile emulation, nhưng không đủ để phát hiện lỗi hierarchy và accessible behavior ở viewport 390px.
3. Tách test thành hai file riêng cho desktop và mobile. Phù hợp khi mỗi viewport có hành vi nghiệp vụ khác nhau đáng kể; hiện tại cùng một contract nên conditional assertion ít trùng lặp hơn.

# Why I did not choose those alternatives

WebKit chưa được cài trong môi trường hiện tại, nên Chromium mobile emulation cho kết quả 390px lặp lại được mà không thêm dependency tải ngoài. Chỉ dùng Vitest sẽ bỏ qua browser focus, responsive layout và console evidence. Không tách file vì flow Employee chỉ khác ở visibility của hamburger; test hiện tại biểu đạt đúng contract đó.

# Key concepts to learn

- Một lỗi parse ở shared component có thể làm mọi browser route fail trước khi auth được kiểm tra.
- `KeyboardEvent.key` nên được chuẩn hóa khi contract không phụ thuộc chữ hoa/thường.
- Responsive assertion phải gắn với viewport, không gắn với tên test.
- Browser regression evidence nên gồm kết quả, console assertion và screenshot dễ truy xuất.

# Common mistakes

- Kết luận UI pass khi dev server thực tế đang trả 500.
- Dùng device profile yêu cầu browser engine chưa cài mà không kiểm tra project config.
- Đòi control chỉ có trên mobile trong test desktop.
- Chỉ kiểm tra screenshot mà bỏ qua accessible name, focus và console.

# Small example

```ts
if ((page.viewportSize()?.width ?? 0) <= 768) {
  await expect(page.getByRole("button", { name: "Mở menu" })).toBeVisible();
} else {
  await expect(page.getByRole("button", { name: "Mở menu" })).toBeHidden();
}
```

# How to think about this next time

Trước khi đánh giá UX, xác nhận app compile và route mở được. Sau đó chạy cùng một flow trên từng viewport, kiểm tra semantics/focus/console, rồi lưu evidence. Nếu test fail vì môi trường (browser binary) hoặc vì assertion sai scope, sửa seam kiểm thử; nếu fail vì UI behavior, sửa production code và chạy lại từ đầu.
