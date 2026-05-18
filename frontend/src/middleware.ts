import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/", "/login", "/register"];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const isPublic = PUBLIC_PATHS.includes(pathname) || pathname.startsWith("/_next");
  if (isPublic) return NextResponse.next();

  // Token presence is checked client-side; middleware handles cookie-based auth if added later.
  // For now, pass through (client-side redirect handles unauthenticated users).
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
