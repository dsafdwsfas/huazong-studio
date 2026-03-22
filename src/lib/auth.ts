import { SignJWT, jwtVerify } from "jose";

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || "huazong-dev-secret-change-in-production"
);

const JWT_ISSUER = "huazong-studio";
const JWT_EXPIRATION = "7d";

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
    .sign(JWT_SECRET);
}

export async function verifyToken(token: string): Promise<JWTPayload | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET, {
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
