# BUG-11 FIX REPORT — ESS leave request submit button không match selector / actionability timeout (P2)

> Fix worker BUG-11. Root cause: **FE form a11y + nút disabled đến khi form
> valid**. Spec `getByPlaceholder(/lý do|reason/i)` fail silent vì `TextArea`
> "Lý do" không có `placeholder` → `reason` không được fill → nút submit vẫn
> `disabled` (logic `!leaveForm.reason`) → `click()` hang 90s actionability.
> Fix FE (1 file): thêm `aria-label` rõ ràng cho inputs + `placeholder` cho
> `TextArea` "Lý do" + `aria-label` cho nút submit. BE KHÔNG đụng.
> Build FE PASS. KHÔNG commit.

Ngày fix: 2026-07-17. Repo: `/home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage/vroom-hr`.

---

## 1. Code hiện tại + root cause

`vroom-hr/app/(employee)/employee/requests/page.tsx` (bản cũ, tab "leave"):

```tsx
<SectionTitle icon={Plus}>Tạo yêu cầu nghỉ phép</SectionTitle>
<div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
  <Field label="Loại nghỉ">
    <Select value={leaveForm.leave_type} onChange={...}>
      {LEAVE_TYPES.map((t) => <option ...>{t.label}</option>)}
    </Select>
  </Field>
  <Field label="Từ ngày *"><TextInput type="date" value={leaveForm.start_date} onChange={...} /></Field>
  <Field label="Đến ngày *"><TextInput type="date" value={leaveForm.end_date} onChange={...} /></Field>
</div>
<Field label="Lý do *"><TextArea rows={2} value={leaveForm.reason} onChange={...} /></Field>
{leaveMut.isError && <ErrorAlert error={leaveMut.error} />}
<div className="flex justify-end">
  <ButtonPrimary onClick={submitLeave} disabled={leaveMut.isPending || !leaveForm.start_date || !leaveForm.end_date || !leaveForm.reason}>
    {leaveMut.isPending ? 'Đang gửi…' : 'Gửi yêu cầu'}
  </ButtonPrimary>
</div>
```

`components/operate.tsx`:
```tsx
export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`${inputCls} ${props.className ?? ''}`} />;
}
export function ButtonPrimary(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className={`${BTN} ...`} />;   // ← spread props → aria-label qua được
}
```

### Test spec T6 (`e2e/vroom-hr-smoke.spec.ts:247`)

```ts
async function submitLeave(sd: string, ed: string) {
  const startInput = page.locator('input[type="date"]').first();
  await startInput.fill(sd);
  const endInput = page.locator('input[type="date"]').nth(1);
  await endInput.fill(ed);
  const reason = page.getByPlaceholder(/lý do|reason/i).first();
  if ((await reason.count()) > 0) await reason.fill("E2E smoke test nghỉ phép");
  await page.getByRole("button", { name: /Gửi.*nghỉ phép|Tạo.*nghỉ phép|Gửi yêu cầu/i }).first().click();
}
```

### Chuỗi lỗi tác động

1. **`TextArea` "Lý do" không có `placeholder`** → `getByPlaceholder(/lý do|reason/i)` count = 0
   (regex match placeholder text, không match label `<span>`). Branch `if count > 0` bỏ qua fill →
   `leaveForm.reason` vẫn `""`.
2. **Nút submit `disabled` đến khi form valid** (`disabled={... || !leaveForm.reason}`) → vẫn disabled.
3. **`getByRole("button", { name: /Gửi.*nghỉ phép|Tạo.*nghỉ phép|Gửi yêu cầu/i })`** match text nút
   "Gửi yêu cầu" (alternative thứ 3 khớp vì `Gửi yêu cầu` là substring của accessible name). Nhưng
   Playwright `click()` mặc định chờ actionability — nút `disabled` KHÔNG actionable → hang đến test
   timeout 90s. Đây chính xác là "actionability timeout 90s" trong BUG-10 §7.

> Ghi chú: KHÔ único bug này có thể bịnesia "Gửi yêu cầu" vs "Tạo yêu cầu nghỉ phép"
> (SectionTitle text "Tạo yêu cầu nghỉ phép" không phải role=button nên không match) — selector thứ
> 3 `Gửi yêu cầu` đã đúng; vấn đề KHÔ phải selector sai mà là form invalid → nút disabled.

### Loại trừ

- Nút icon-only / thiếu aria-label? — KHÔ. Text "Gửi yêu cầu" đã có, accessible name OK.
- Selector spec sai? — KHÔ. `/Gửi yêu cầu/` match text nút; vấn đề là disabled.
- BE? — KHÔ. Test fail ở UI interaction (filling form) trước khi gọi BE; chưa tới tầng service.

---

## 2. Choice fix: kết hợp (a) aria-label + (c) form valid + spec fill reason

Sửa FE `app/(employee)/employee/requests/page.tsx` (chỉ file này):

1. **`TextArea` "Lý do" thêm `placeholder`** ("Nhập lý do nghỉ phép…" / "Nhập lý do tăng ca…") →
   spec `getByPlaceholder(/lý do|reason/i)` giờ match → fill reason → button enable.
2. **Thêm `aria-label` deterministic cho inputs** (Từ ngày / Đến ngày / Lý do / overtime variants)
   → E2E + assistive tech target deterministic, không phụ thuộc vị trí `.first()/.nth(1)`.
3. **Thêm `aria-label` cho 2 nút submit** ("Gửi yêu cầu nghỉ phép" / "Gửi yêu cầu tăng ca") →
   accessible name rõ ràng, loại xung đột khi cả 2 tab đều render (nếu sau này đổi UI), và
   thỏa mãn cả `getByRole("button", { name: /Gửi.*nghỉ phép/ })` (match aria-label mới) và
   `getByRole("button", { name: /Gửi yêu cầu/ })` (match text "Gửi yêu cầu").

KHÔ đổi spec (choice (b) không cần thiết — spec regex đã match sau khi form enable). KHÔ đụng BE,
KHÔ đụng feature code khác.

---

## 3. Diff fix

```diff
--- a/vroom-hr/app/(employee)/employee/requests/page.tsx
+++ b/vroom-hr/app/(employee)/employee/requests/page.tsx
@@ tab leave form
-  <Field label="Từ ngày *"><TextInput type="date" value={leaveForm.start_date} onChange={...} /></Field>
-  <Field label="Đến ngày *"><TextInput type="date" value={leaveForm.end_date} onChange={...} /></Field>
-  <Field label="Lý do *"><TextArea rows={2} value={leaveForm.reason} onChange={...} /></Field>
-  <ButtonPrimary onClick={submitLeave} disabled={... || !leaveForm.reason}>
-    {leaveMut.isPending ? 'Đang gửi…' : 'Gửi yêu cầu'}
-  </ButtonPrimary>
+  <Field label="Từ ngày *"><TextInput aria-label="Từ ngày nghỉ phép" type="date" value={leaveForm.start_date} onChange={...} /></Field>
+  <Field label="Đến ngày *"><TextInput aria-label="Đến ngày nghỉ phép" type="date" value={leaveForm.end_date} onChange={...} /></Field>
+  <Field label="Lý do *"><TextArea rows={2} aria-label="Lý do nghỉ phép" placeholder="Nhập lý do nghỉ phép…" value={leaveForm.reason} onChange={...} /></Field>
+  {/* BUG-11: aria-label rõ ràng để E2E/AT target deterministically; nút disabled
+      đến khi start_date+end_date+reason đầy đủ (xem disabled logic) — phải fill đủ form trước. */}
+  <ButtonPrimary aria-label="Gửi yêu cầu nghỉ phép" onClick={submitLeave} disabled={... || !leaveForm.reason}>
+    {leaveMut.isPending ? 'Đang gửi…' : 'Gửi yêu cầu'}
+  </ButtonPrimary>

@@ tab overtime form (parity)
-  <TextInput type="date" value={otForm.work_date} ... />                                            → + aria-label="Ngày làm tăng ca"
-  <TextInput type="time" value={otForm.start_time} ... />                                           → + aria-label="Giờ bắt đầu tăng ca"
-  <TextInput type="time" value={otForm.end_time} ... />                                             → + aria-label="Giờ kết thúc tăng ca"
-  <TextArea rows={2} value={otForm.reason} ... />                                                   → + aria-label="Lý do tăng ca" + placeholder="Nhập lý do tăng ca…"
-  <ButtonPrimary onClick={submitOt} disabled={...}>                                                → + aria-label="Gửi yêu cầu tăng ca"
```

`disabled` logic (form valid gate) **giữ nguyên** — đây là feature intent (chặn submit form rỗng).
`submitLeave`/`submitOt`/mutation logic không đổi.

---

## 4. Spec T6 trace sau fix

```ts
// submitLeave(start, end) — sau fix
1. fill input[type="date"]).first()      → "Từ ngày nghỉ phép" (start_date)
2. fill input[type="date"]).nth(1)       → "Đến ngày nghỉ phép" (end_date)
3. getByPlaceholder(/lý do|reason/i)     → giờ match TextArea "Lý do" (placeholder "Nhập lý do nghỉ phép…")
   → reason.fill("E2E smoke test nghỉ phép")  → leaveForm.reason = "E2E smoke..."
4. getByRole("button", { name: /Gửi.*nghỉ phép|Tạo.*nghỉ phép|Gửi yêu cầu/i }).first()
   → accessible name "Gửi yêu cầu nghỉ phép" (aria-label) — match cả 3 alternative
   → KHÔ disabled (start+end+reason đầy đủ) → click() actionability OK → mutate → BE create leave
5. submitLeave again (overlap) → BE trả LEAVE_OVERLAP → expect text match ✓
```

→ T6 PASS kỳ vọng.

---

## 5. Build verify

```bash
cd vroom-hr && node_modules/.bin/next build
```
```
▲ Next.js 15.5.20
- Environments: .env.local
Creating an optimized production build ...
✓ Compiled successfully in 3.8s
Skipping linting
Checking validity of types ...
Collecting page data ...
Generating static pages (32/32)
✓ Generating static pages (32/32)
...
├ ○ /employee/requests          5.34 kB         122 kB   ← route build OK
...
```
→ FE build PASS (exit 0). 32 routes build OK, type check pass.

KHÔNG chạy BE ruff/pytest (BE không sửa).

---

## 6. Ràng buộc tuân thủ

- ✅ Feature intent giữ nguyên (form valid gate `disabled` logic không đổi; mutation/state không đổi).
- ✅ BE KHÔ đụng.
- ✅ Tiếng Việt.
- ✅ Build PASS rồi dừng.
- ✅ KHÔNG commit. KHÔNG reset First-Run.

---

## 7. Đề nghị cho orchestrator (tùy chọn, không thuộc scope fix)

Spec T6 hiện phụ thuộc các selector fragile (`input[type="date"]).first()/.nth(1)`,
`getByPlaceholder`). Sau fix FE, spec chạy được, nhưng nếu sau này UI re-order fields
spec dễ vỡ lại. Có thể orchestrator cho worker E2E cập nhật spec dùng `getByLabel`
hoặc `getByRole('textbox', { name: /từ ngày nghỉ phép/i })` để robust hơn (dựa trên
`aria-label` mới). KHÔ属 scope fix này — fix worker chỉ sửa FE feature.