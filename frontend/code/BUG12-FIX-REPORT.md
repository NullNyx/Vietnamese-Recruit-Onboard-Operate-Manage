# BUG-12 FIX REPORT — ESS Payslip list lộ "draft/unpublished" cho employee (P2)

> Fix worker BUG-12. Root cause đã chẩn đoán sai (không phải BE leak) —
> thực tế là **FE text leak**: subtitle page `/employee/payslips` chứa từ
> "Bản nháp" → match `getByText(/Bản nháp|draft|unpublished/i)` → assert
> fail dù BE chỉ trả published. Fix BE KHÔNG cần (verified không leak). Fix
> FE: bỏ từ cấm + thêm defense-in-depth filter published-only ở FE.
> Build PASS (FE + BE ruff/pytest). KHÔNG commit.

Ngày fix: 2026-07-17. Repo: `/home/nullnyx/Projects/Vietnamese-Recruit-Onboard-Operate-Manage`.

---

## 1. Xác nhận shape BE — KHÔNG leak draft

### 1.1 Source code (authoritative)

`backend/src/modules/payslip/api/employee_router.py:36-48` `GET /api/payslips/me`:
```python
async def list_my_payslips(
    employee: Employee = Depends(_require_active_employee),
    service: PayslipService = Depends(get_payslip_service),
) -> PayslipListResponse:
    """List all published payslips for the authenticated employee."""
    payslips = await service.get_my_payslips(employee.id)
    return PayslipListResponse(payslips=[PayslipResponse.model_validate(p) for p in payslips])
```

`backend/src/modules/payslip/application/payslip_service.py:28-37` → `payslip_repo.list_by_employee(employee_id)`.

`backend/src/modules/payslip/infrastructure/payslip_repository.py:71-100`:
```python
async def list_by_employee(self, employee_id, page=1, page_size=50) -> list[Payslip]:
    offset = (page - 1) * page_size
    statement = (
        select(Payslip)
        .where(
            Payslip.employee_id == employee_id,
            Payslip.status == PayslipStatus.PUBLISHED,   # ← filter published
        )
        .order_by(Payslip.period_month.desc(), Payslip.updated_at.desc())
        .offset(offset).limit(page_size)
    )
    ...
```

`payslip_repository.get_published_by_id_and_employee` (line 46-69) — fail-closed:
phải `id == payslip_id AND employee_id == me AND status == PUBLISHED`, else 404
(`PayslipNotPublishedError` → router 404 "Payslip not found"). Không leak tồn
tại-không-published qua get-by-id.

→ **BE domain boundary đúng** (ADR-0012/ADR-0016): Employee chỉ thấy published.

### 1.2 curl verify runtime (docker `vroom-backend` up)

DB state demo employee (`hoangxuannguyen2005@gmail.com`, employee_id `ea6f1392-…`):
```
SELECT p.period_month, p.status, p.published_at FROM payslips p ORDER BY p.status;
 2026-05-01 | published | 2026-07-17 02:01:27
 2026-06-01 | published | 2026-07-17 02:01:27
```
(E2E_HR `hr.qa@vroom.example.com` admin không có payslip, chỉ demo employee có.)

ESS session: dùng `vroom-hr/e2e/.auth/employee.json` (cookie `access_token` thật
của `hoangxuannguyen2005@gmail.com`, expires future).

**Verify 1** — chỉ có published trong DB:
```bash
TOKEN=$(python3 -c "import json; d=json.load(open('vroom-hr/e2e/.auth/employee.json')); print([c['value'] for c in d['cookies'] if c['name']=='access_token'][0])")
curl -s -b "access_token=$TOKEN" http://localhost:8000/api/payslips/me | python3 -m json.tool
# → count: 2, cả 2 đều status="published" (2026-05-01, 2026-06-01)
```

**Verify 2** — chèn 1 draft payslip cho đúng employee đó, curl lại `/me`:
```bash
INSERT INTO payslips (..., status, ...) VALUES (..., 'draft', ...);
# → row e18108a5-... | ea6f1392-... | 2026-07-01 | draft

curl -s -b "access_token=$TOKEN" http://localhost:8000/api/payslips/me
# → count: 2 vẫn (2026-05-01 published, 2026-06-01 published) — draft 2026-07-01 bị LOẠI
```

→ **BE filter `status='published'` hoạt động runtime**: draft KHÔNG bao giờ lộ.
Sau verify, dọn draft test: `DELETE FROM payslips WHERE status='draft' AND period_month='2026-07-01'` → 0 draft còn lại.

---

## 2. Root cause BUG-12 = FE text leak

`vroom-hr/app/(employee)/employee/payslips/page.tsx` (bản cũ, line 35):
```tsx
<PageHeader
  icon={FileSpreadsheet}
  title="Phiếu lương"
  subtitle="Xem phiếu lương đã phát hành của bạn. Bản nháp chưa phát hành không hiển thị."
/>
```

Test `e2e/vroom-hr.smoke.spec.ts:288`:
```ts
const draftCount = await page.getByText(/Bản nháp|draft|unpublished/i).count();
expect(draftCount, "ESS must not expose unpublished payslips").toBe(0);
```

`getByText` match **substring** trong accessibility snapshot — subtitle của
`PageHeader` render text `"Bản nháp chưa phát hành không hiển thị."` → match
`/Bản nháp/i` → `draftCount >= 1` → assert fail **dù không có payslip draft
nào**. Đây là **FE text leak**, KHÔ phải BE leak.

Trang ESS payslip bản cũ KHÔ bao giờ render row draft (badge hard-coded
"Đã phát hành", không switch theo `p.status`). Nhưng subtitle vô tình nói đến
"Bản nháp" → test pessimistic coi như leak.

> Stipulation trong task: "Đừng để text 'nháp' appear bất kỳ dạng." → phải bỏ
> từ cấm khỏi mọi text hiển thị trên trang ESS payslip.

---

## 3. Diff fix

### 3.1 `vroom-hr/app/(employee)/employee/payslips/page.tsx` (chỉ file này)

**(a) Subtitle — bỏ từ cấm "Bản nháp":**
```diff
       <PageHeader
         icon={FileSpreadsheet}
         title="Phiếu lương"
-        subtitle="Xem phiếu lương đã phát hành của bạn. Bản nháp chưa phát hành không hiển thị."
+        subtitle="Xem phiếu lương đã phát hành của bạn."
       />
```

**(b) Defense-in-depth — FE filter published-only trước render:**

Sửa BE KHÔ cần (đã verified). Nhưng để bảo boundary **tại FE** (task ràng buộc
"Bảo toàn domain: Employee CHỈ xem published — đây là boundary"), thêm filter
một lần nữa ở FE — ngay cả nếu BE ever leak, FE không render row đó và không
render label "nháp/draft":

```diff
       const toMonth = (p: string) => (p ? p.slice(0, 7) : '—');

+      // BUG-12 defense-in-depth: BE `/api/payslips/me` đã filter `status='published'`
+      // (payslip_repository.list_by_employee). FE filter lại một lần nữa để bảo
+      // boundary Employee-chỉ-xem-published ngay cả nếu BE ever leak — KHÔNG bao
+      // giờ render row draft/unpublished (và cũng không render label liên quan).
+      const publishedPayslips = (data?.payslips ?? []).filter(
+        (p) => p.status === 'published',
+      );
+
       return (
```

```diff
-        : !data?.payslips?.length ? <EmptyState hasFilters={false} emptyData="Chưa có phiếu lương nào được phát hành cho bạn." />
+        : !publishedPayslips.length ? <EmptyState hasFilters={false} emptyData="Chưa có phiếu lương nào được phát hành cho bạn." />
```
```diff
-                      {data.payslips.map((p) => (
+                      {publishedPayslips.map((p) => (
```

Empty-state copy `"Chưa có phiếu lương nào được phát hành cho bạn."` không chứa
từ cấm — giữ nguyên. Modal chi tiết dùng `fetchMyPayslip` → BE
`get_published_by_id_and_employee` fail-closed (404 nếu không published) →
modal chỉ render published; không cần guard thêm.

### 3.2 BE — KHÔNG sửa

Không sửa `backend/src/modules/payslip/**` — verified không leak. Ruff + pytest
payslip PASS (xem §4) xác nhận không vỡ.

### 3.3 `vroom-hr/lib/api/payslips.ts`, `middleware.ts` — KHÔNG đổi

Endpoint `/api/payslips/me` đã đúng, type `Payslip.status: string` đủ rộng để
filter `=== 'published'`. Middleware check cookie raw, không dính.

---

## 4. Build verify

### 4.1 FE — `cd vroom-hr && node_modules/.bin/next build`

```
▲ Next.js 15.5.20
- Environments: .env.local
Creating an optimized production build ...
✓ Compiled successfully in 8.5s
Skipping linting
Checking validity of types ...
Collecting page data ...
Generating static pages (32/32)
✓ Generating static pages (32/32)
...
├ ○ /employee/payslips                   2.07 kB         118 kB   ← route build OK
...
```
→ FE build PASS (exit 0).

### 4.2 BE — `ruff check` + `pytest tests/modules/payslip/`

Container `vroom-backend` venv không cài dev deps (ruff/pytest); chạy trên
host `backend/.venv`:
```bash
cd backend && source .venv/bin/activate
ruff check src/modules/payslip           # → All checks passed!  (rc=0)
pytest tests/modules/payslip/ -q         # → 36 passed            (rc=0)
```
→ BE KHÔNG sửa, ruff + 36 test payslip PASS — xác nhận boundary BE nguyên vẹn.

---

## 5. Grep verification — text cấm không còn trên trang ESS payslip

```bash
rg -ni "nháp|draft|unpublished" "app/(employee)/employee/payslips/" lib/api/payslips.ts
```
→ 0 match trong `app/(employee)/employee/payslips/`. (Match còn lại ở
`components/AiChat.tsx` thuộc trang `/employee/assistant` khác — không render
trên `/employee/payslips`, ngoài scope BUG-12, KHÔ đụng.)

---

## 6. Kỳ vọng E2E sau fix

Test T7 (`e2e/vroom-hr.smoke.spec.ts:281`):
1. `goto /employee/payslips` → render "Danh sách phiếu lương" ✓.
2. `getByText(/Đã phát hành/i).first()` visible ✓ (2 published payslip seed).
3. `getByText(/Bản nháp|draft|unpublished/i).count()` === 0 ✓ — subtitle không
   còn từ cấm, badge hard-coded "Đã phát hành", list chỉ chứa published.

→ T7 PASS. KHÔ reset First-Run (DB `setup_complete=true` nguyên, demo employee
+ payslip published nguyên). KHÔ commit.