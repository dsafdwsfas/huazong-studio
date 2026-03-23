import { SignJWT, jwtVerify } from "jose";
import { NextRequest, NextResponse } from "next/server";

function getJwtSecret(): Uint8Array {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error(
      "JWT_SECRET environment variable must be set. " +
        "Generate one with: openssl rand -base64 32"
    );
  }
  return new TextEncoder().encode(secret);
}

const JWT_ISSUER = "huazong-studio";
const JWT_EXPIRATION = "24h";

export interface JWTPayload {
  sub: string; // user ID
  role: string;
  nickname: string;
}

export async function createToken(payload: JWTPayload): Promise<string> {
  return new SignJWT(payload as unknown as Record<string, unknown>)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuer(JWT_ISSUER)
    .setIssuedAt()
    .setExpirationTime(JWT_EXPIRATION)
    .sign(getJwtSecret());
}

export async function verifyToken(token: string): Promise<JWTPayload | null> {
  try {
    const { payload } = await jwtVerify(token, getJwtSecret(), {
      issuer: JWT_ISSUER,
    });
    return {
      sub: payload.sub as string,
      role: payload.role as string,
      nickname: payload.nickname as string,
    };
  } catch {
    return null;
  }
}

/**
 * Extract and verify auth token from request.
 * Returns payload or error response.
 */
export async function requireAuth(
  request: NextRequest
): Promise<{ payload: JWTPayload } | { error: NextResponse }> {
  const authHeader = request.headers.get("authorization");
  const token = authHeader?.replace("Bearer ", "");
  if (!token) {
    return { error: NextResponse.json({ error: "未登录" }, { status: 401 }) };
  }
  const payload = await verifyToken(token);
  if (!payload) {
    return { error: NextResponse.json({ error: "登录已过期" }, { status: 401 }) };
  }
  return { payload };
}
