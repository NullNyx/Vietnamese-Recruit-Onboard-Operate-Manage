# 10 — Fix permission test T13: employee access to admin dashboard

**What to build:** Investigate and fix `vroom-hr.smoke.spec.ts` test T13 (Employee permission check). Currently when an Employee accesses `/dashboard` (admin page), they are NOT redirected or shown a forbidden page — meaning the backend/frontend doesn't properly restrict admin routes.

**Blocked by:** None (independent)

**Status:** ready-for-agent

**Acceptance criteria:**
- [ ] Investigate: Employee có nên bị chặn truy cập `/dashboard` không?
  - Nếu **có** (bug cần fix):
    - Backend: check role-based access cho `/api/*` admin endpoints trả về 403
    - Frontend: redirect employee từ `/dashboard` về `/employee/dashboard`
    - Test T13 pass
  - Nếu **không** (test sai expectation):
    - Update test expectation — employee có thể xem dashboard nhưng không edit được
- [ ] Check xem có permission middleware/guard nào ở frontend không
- [ ] Check backend role-based access control cho admin routes
- [ ] Báo cáo investigation result
- [ ] Implement fix hoặc update test

## Instructions
1. Investigate trước: `src/modules/identity/api/admin_router.py` + frontend middleware
2. Quyết định: fix permission hay fix test
3. Commit trực tiếp lên main
4. Dùng skill implement
5. Báo cáo kết quả + rationale
