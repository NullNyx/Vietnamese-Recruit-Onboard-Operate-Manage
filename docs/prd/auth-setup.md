# PRD — Auth/Setup surface

## Problem Statement

HR Space không thể đi vào luồng làm việc chính nếu chưa có lớp nền xác thực và khởi tạo instance. Ở trạng thái fresh install, hệ thống cần cho người dùng tạo SUPER_ADMIN đầu tiên, cấu hình Organization, rồi mới vào được app shell. Sau đó, mỗi lần mở app phải có login ổn định, session cookie rõ ràng, và cơ chế thoát/khôi phục phiên đúng chuẩn.

Hiện tại, auth/setup không chỉ là tiện ích kỹ thuật. Nó là cửa ngõ bắt buộc cho toàn bộ surface còn lại. Nếu lớp nền này lệch scope, mọi surface phía sau đều sai từ gốc: org scope, audit actor, permission, và app entry point.

## Solution

Xây Auth/Setup thành surface nền đầu tiên của HR Space.

Luồng chuẩn:
1. Fresh install vào setup wizard.
2. SUPER_ADMIN đầu tiên được tạo bằng username/password.
3. Organization được cấu hình trong cùng wizard.
4. Setup hoàn tất thì khóa route setup.
5. Người dùng đăng nhập qua username/password.
6. Hệ thống set cookie-based JWT session.
7. Sau login, app mở vào Today/Command Center.
8. Logout thu hồi session server-side.
9. Refresh gia hạn session bằng refresh token rotation.
10. `/auth/me` trả identity và role để app shell dựng trạng thái.

Surface này không dùng Google OAuth cho app login. Gmail OAuth là integration riêng, tách khỏi login app.

## User Stories

1. As an HR, I want to create the first SUPER_ADMIN during initial setup, so that the instance can be bootstrapped without manual DB intervention.
2. As an HR, I want to configure Organization during initial setup, so that the app knows org name and timezone from day one.
3. As an HR, I want setup to lock after completion, so that I cannot accidentally re-run first-time bootstrap on a live instance.
4. As a SUPER_ADMIN, I want to sign in with username and password, so that I can access HR Space without external identity providers.
5. As an HR_ADMIN, I want to sign in with username and password, so that I can access admin-capable surfaces securely.
6. As an HR_STAFF, I want to sign in with username and password, so that I can work with assigned items after authentication.
7. As an authenticated HR, I want session tokens stored in HttpOnly cookies, so that browser-side script cannot read session secrets.
8. As an authenticated HR, I want access token renewal to happen through refresh rotation, so that long sessions remain secure.
9. As an authenticated HR, I want logout to revoke current session server-side, so that a logged-out browser cannot keep using stale tokens.
10. As an authenticated HR, I want `/auth/me` to return current identity and role, so that the app shell can hydrate user state after refresh.
11. As an unauthenticated visitor, I want to be redirected to login, so that protected surfaces are not exposed.
12. As a freshly installed tenant, I want setup to be the first visible flow, so that I can complete bootstrap before using the product.
13. As an HR, I want to land on Today after login, so that I immediately see the work queue entry point rather than a generic dashboard.
14. As an HR, I want invalid credentials to fail safely, so that the system does not leak account existence or session state.
15. As an HR, I want repeated failed logins to trigger temporary lockout, so that brute-force attempts are slowed down.
16. As a SUPER_ADMIN, I want the first admin username to be immutable after creation, so that the initial identity cannot be silently re-keyed.
17. As an HR, I want password rules to be explicit and consistent, so that I know what is required before submitting setup or login-related flows.
18. As an HR, I want org configuration and auth state to survive reloads, so that I do not have to repeat bootstrap or sign-in on every page change.
19. As an HR, I want session expiry to be handled predictably, so that I can re-authenticate without data loss in the current screen.
20. As a system owner, I want app auth separated from Gmail integration auth, so that core login never depends on Google availability.

## Implementation Decisions

- Auth/Setup is the first mandatory foundation surface before any work-focused surface becomes meaningful.
- App login uses username/password, not Google OAuth.
- Session model uses cookie-based JWT with access and refresh cookies.
- Refresh uses rotation semantics; stale replay must revoke the family.
- Setup wizard creates the first SUPER_ADMIN and captures Organization configuration in one first-run flow.
- Setup route is one-time and locked after completion.
- The post-login landing state is Today/Command Center, not a generic homepage.
- App shell depends on `/auth/me` for identity hydration and route guarding.
- Password policy is enforced consistently across setup and future auth-related writes.
- Brute-force protection and audit logging are part of the auth boundary, not a later addon.
- Gmail OAuth stays out of this surface; it belongs to integration auth, not app auth.
- Backend work stays inside identity/setup boundary and shared permission/session plumbing.
- Frontend work stays inside login page, setup wizard, and app-shell guard/hydration.
- Main seam: one backend auth/setup boundary and one frontend shell guard seam.

## Testing Decisions

- Tests must verify external behavior only: route responses, cookie behavior, redirects, and state transitions.
- Backend tests should cover setup bootstrap, first admin creation, login success/failure, refresh rotation, logout revocation, `/auth/me`, and setup lock after completion.
- Backend tests should also cover lockout behavior and replay protection if those rules are included in the slice.
- Frontend tests should cover unauthenticated redirect, setup-first flow, successful login redirect to Today, and persistence of authenticated shell state after reload.
- Good tests here assert browser-observable outcomes and session state, not internal implementation details.
- Prior art should follow existing service-first and route-level test style in backend modules, plus browser QA for the auth/setup screens when UI is touched.

## Out of Scope

- Gmail OAuth and mailbox integration auth.
- Work, Inbox, People, Documents, Contracts, Templates, AI, Reports, Notes, Audit, and Admin user management beyond first-run setup.
- Self-service password reset and recovery flows beyond what is needed for the initial auth foundation.
- Multi-tenant support.
- Invite flows for HR_ADMIN / HR_STAFF.
- Social login, SSO, and bearer-token login.
- Any redesign of Today / Work surfaces beyond the landing redirect after login.

## Further Notes

- ADR 0030 is the primary auth decision source.
- ADR 0028 and 0029 freeze API shape and contracts around `/auth/*` and `/setup/*`.
- This PRD is intentionally foundation-first because every other surface depends on org scope, session state, and actor identity.
- The product entry point after auth should be Today / Command Center, not a dashboard page.
- Downstream slices can assume authenticated HR actor, cookie session, and setup-complete instance state.
