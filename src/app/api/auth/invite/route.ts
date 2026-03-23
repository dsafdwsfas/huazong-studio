import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** Generate invite codes (admin only) */
export async function POST(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    if (payload.role !== "admin") {
      return NextResponse.json({ error: "需要管理员权限" }, { status: 403 });
    }

    const { count = 1 } = await request.json().catch(() => ({}));
    const db = getDb();
    const codes: string[] = [];
    const now = new Date().toISOString();

    for (let i = 0; i < Math.min(count, 20); i++) {
      const code = generateId().slice(0, 8).toUpperCase();
      const invId = generateId("inv");
      db.run(
        "INSERT INTO invite_codes (id, code, created_by, used_by, used_at, expires_at, created_at) VALUES (?, ?, ?, NULL, NULL, NULL, ?)",
        invId,
        code,
        payload.sub,
        now
      );
      codes.push(code);
    }

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      null,
      "generate_invite_codes",
      JSON.stringify({ count: codes.length }),
      now
    );

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
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    if (payload.role !== "admin") {
      return NextResponse.json({ error: "需要管理员权限" }, { status: 403 });
    }

    const db = getDb();
    const inviteCodes = db.all<Record<string, unknown>>(
      "SELECT code, used_by, created_at FROM invite_codes ORDER BY created_at DESC"
    );

    return NextResponse.json({
      codes: inviteCodes.map((c) => ({
        code: c.code,
        used: !!c.used_by,
        createdAt: c.created_at,
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
