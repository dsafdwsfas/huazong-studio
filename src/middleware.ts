import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";

const PUBLIC_PATHS = ["/api/auth/login", "/api/auth/register", "/api/auth/send-code"];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip public API routes
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Protect /api/* routes
  if (pathname.startsWith("/api/")) {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");

    if (!token) {
      return NextResponse.json({ error: "未登录" }, { status: 401 });
    }

    try {
      const secret = process.env.JWT_SECRET;
      if (!secret) {
        return NextResponse.json(
          { error: "Server configuration error" },
          { status: 500 }
        );
      }
      await jwtVerify(token, new TextEncoder().encode(secret), {
        issuer: "huazong-studio",
      });
      return NextResponse.next();
    } catch {
      return NextResponse.json({ error: "登录已过期" }, { status: 401 });
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*"],
};
