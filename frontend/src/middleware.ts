import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname, origin } = request.nextUrl;
  const accessToken = request.cookies.get("access_token");

  // Static assets and public routes — always allow
  if (
    pathname.startsWith("/_next/") ||
    pathname.startsWith("/api/") ||
    pathname === "/favicon.ico" ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/setup") ||
    /\.(svg|png|jpg|jpeg|gif|webp|ico|css|js)$/.test(pathname)
  ) {
    return NextResponse.next();
  }

  // Setup status check — redirect if incomplete or already done
  try {
    const res = await fetch(`${origin}/api/setup/status`);
    if (res.ok) {
      const { setup_complete } = await res.json();
      if (!setup_complete) {
        return NextResponse.redirect(new URL("/setup", origin));
      }
    }
  } catch {
    // Backend unreachable → fall through to auth check
  }

  // Authenticated routes require token
  if (!accessToken) {
    return NextResponse.redirect(new URL("/login", origin));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/|api/|login|setup|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
