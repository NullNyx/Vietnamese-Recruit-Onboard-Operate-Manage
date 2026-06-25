import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const accessToken = request.cookies.get("access_token");
  const path = request.nextUrl.pathname;

  // Admin dashboard routes — require authentication
  if (
    path.startsWith("/admin") ||
    path.startsWith("/attendance") ||
    path.startsWith("/employees") ||
    path.startsWith("/gmail") ||
    path.startsWith("/leave") ||
    path.startsWith("/recruitment") ||
    path.startsWith("/settings")
  ) {
    if (!accessToken) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    return NextResponse.next();
  }

  // Employee self-service routes — require authentication
  // Backend API will return 403 if token lacks employee_id claim
  if (path.startsWith("/employee")) {
    if (!accessToken) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    return NextResponse.next();
  }

  // All other matched routes — require authentication
  if (!accessToken && path !== "/login" && path !== "/") {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all routes except:
     * - /login (auth page)
     * - /_next/ (Next.js internals)
     * - /api/ (API routes, proxied to backend)
     * - Static files (favicon, images, etc.)
     */
    "/((?!login|_next/|api/|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
