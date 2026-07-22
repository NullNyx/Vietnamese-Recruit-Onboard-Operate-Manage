import createMiddleware from 'next-intl/middleware';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { routing } from './i18n/routing';

// Create the next-intl middleware for locale detection + redirect
const intlMiddleware = createMiddleware(routing);

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // Let API routes pass through unchanged
  if (path.startsWith('/api/')) {
    return NextResponse.next();
  }

  // Static files: let through
  if (path.match(/\.(svg|png|jpg|jpeg|gif|webp|ico)$/) || path.startsWith('/_next/')) {
    return NextResponse.next();
  }

  // Step 1: Run next-intl middleware FIRST — handles locale detection and prefix redirects
  // (e.g. /login → /vi/login, / → /vi/, /en/dashboard → stays)
  const intlResponse = intlMiddleware(request);

  // If next-intl redirected, return its response immediately
  // (we'll auth-check on the redirected URL on the next request)
  if (intlResponse.status === 302 || intlResponse.status === 307 || intlResponse.status === 308) {
    return intlResponse;
  }

  // Step 2: After locale prefix is handled, extract locale from path for auth redirects
  const locale = path.match(/^\/(vi|en)/)?.[1] || routing.defaultLocale;

  // Auth check — uses current path (which already has locale prefix at this point)
  const refreshToken = request.cookies.get('refresh_token');
  const mustChangePassword = request.cookies.get('must_change_password')?.value === 'true';

  // Must change password → force redirect
  if (mustChangePassword && !path.includes('/change-password')) {
    return NextResponse.redirect(new URL(`/${locale}/change-password`, request.url));
  }

  // Protected routes
  const protectedPaths = [
    '/dashboard', '/recruitment', '/onboarding', '/employees',
    '/attendance', '/requests', '/payroll', '/gmail', '/settings', '/employee',
  ];
  const pathWithoutLocale = path.replace(/^\/(vi|en)/, '') || '/';
  const isProtected = protectedPaths.some((p) => pathWithoutLocale.startsWith(p));

  if (isProtected && !refreshToken) {
    return NextResponse.redirect(new URL(`/${locale}/login`, request.url));
  }

  return intlResponse;
}

export const config = {
  matcher: [
    '/((?!api/|_next/|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)',
  ],
};
