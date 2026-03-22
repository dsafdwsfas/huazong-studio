import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** Generate invite codes (admin only) */
export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) {
      return NextResponse.json({ error: "未登录" }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== "admin") {
      return NextResponse.json({ error: "需要管理员权限" }, { status: 403 });
    }

    const { count = 1 } = await request.json().catch(() => ({}));
    const db = getDb();
    const codes: string[] = [];

    for (let i = 0; i < Math.min(count, 20); i++) {
      const code = generateId().slice(0, 8).toUpperCase();
      db.inviteCodes.push({
        id: generateId("inv"),
        code,
        createdBy: payload.sub,
        usedBy: null,
        usedAt: null,
        expiresAt: null,
        createdAt: new Date().toISOString(),
      });
      codes.push(code);
    }

    return NextResponse.json({ codes });
  } catch (error) {
    console.error("Invite error:", error);
    return NextResponse.json(
      { error: "生成邀请码失败" },
      { status: 500 }
    );
  }
}

/** List invite codes (admin only) */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) {
      return NextResponse.json({ error: "未登录" }, { status: 401 });
    }

    const payload = await verifyToken(token);
    if (!payload || payload.role !== "admin") {
      return NextResponse.json({ error: "需要管理员权限" }, { status: 403 });
    }

    const db = getDb();
    return NextResponse.json({
      codes: db.inviteCodes.map((c) => ({
        code: c.code,
        used: !!c.usedBy,
        createdAt: c.createdAt,
      })),
    });
  } catch (error) {
    console.error("List invites error:", error);
    return NextResponse.json(
      { error: "获取邀请码失败" },
      { status: 500 }
    );
  }
}
