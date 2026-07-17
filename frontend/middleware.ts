import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const accessToken = request.cookies.get("access_token");
  const mustChangePassword = request.cookies.get("must_change_password")?.value === "true";
  const path = request.nextUrl.pathname;

  // Must change password → force redirect to /change-password
  if (mustChangePassword && path !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }

  // Protected routes — require authentication
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
    if (!accessToken) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Employee routes — only for non-admin (enforced by BE, but redirect early)
    // Admin routes — only for admin
    // The actual role gate is enforced by the BE; we just check auth here
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
