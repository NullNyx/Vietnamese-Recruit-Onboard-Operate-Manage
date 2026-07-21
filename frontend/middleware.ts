import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const refreshToken = request.cookies.get("refresh_token");
  const mustChangePassword = request.cookies.get("must_change_password")?.value === "true";
  const path = request.nextUrl.pathname;

  // Must change password → force redirect to /change-password
  if (mustChangePassword && path !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }

  // Protected routes — require authentication
  // We check the refresh_token cookie (7-day lifetime) instead of access_token
  // (15-min JWT). The access_token is a session cookie that may contain an
  // expired JWT; the client-side apiFetch will transparently refresh it via
  // POST /api/auth/refresh. Checking refresh_token avoids the double-login
  // problem where the middleware redirected to /login before the client had
  // a chance to refresh.
  const protectedPaths = [
    "/dashboard",
    "/recruitment",
    "/onboarding",
    "/employees",
    "/attendance",
    "/requests",
    "/payroll",
    "/gmail",
    "/settings",
    "/employee",
  ];

  const isProtected = protectedPaths.some((p) => path.startsWith(p));

  if (isProtected) {
    if (!refreshToken) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // The actual auth + role gate is enforced by the BE; the client-side
    // apiFetch + useAuthGuard handle token refresh and role-based redirect.
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all routes except:
     * - /login (auth page)
     * - /setup (first-run bootstrap)
     * - /change-password (forced first-login password change)
     * - /_next/ (Next.js internals)
     * - /api/ (API routes)
     * - Static files (favicon, images, etc.)
     */
    "/((?!login|setup|change-password|_next/|api/|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
