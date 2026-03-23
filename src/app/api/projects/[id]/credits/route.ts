import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List credit logs for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const { searchParams } = new URL(request.url);
    const platform = searchParams.get("platform");
    const userId = searchParams.get("userId");

    const db = getDb();

    let sql = "SELECT * FROM credit_logs WHERE project_id = ?";
    const params_arr: unknown[] = [projectId];

    if (platform) {
      sql += " AND platform = ?";
      params_arr.push(platform);
    }
    if (userId) {
      sql += " AND user_id = ?";
      params_arr.push(userId);
    }

    sql += " ORDER BY logged_at DESC";

    const logs = db.all<Record<string, unknown>>(sql, ...params_arr);

    // Enrich with user nickname
    const result = logs.map((l) => {
      const user = db.get<{ nickname: string }>(
        "SELECT nickname FROM users WHERE id = ?",
        l.user_id
      );
      return { ...l, userName: user?.nickname || "未知" };
    });

    // Summary stats
    const totalAmount = logs.reduce((sum, l) => sum + (l.amount as number), 0);
    const byPlatform: Record<string, number> = {};
    const byUser: Record<string, { name: string; amount: number }> = {};
    for (const l of logs) {
      const plat = l.platform as string;
      const uid = l.user_id as string;
      const amt = l.amount as number;
      byPlatform[plat] = (byPlatform[plat] || 0) + amt;
      if (!byUser[uid]) {
        const user = db.get<{ nickname: string }>(
          "SELECT nickname FROM users WHERE id = ?",
          uid
        );
        byUser[uid] = { name: user?.nickname || "未知", amount: 0 };
      }
      byUser[uid].amount += amt;
    }

    return NextResponse.json({
      logs: result,
      summary: { totalAmount, byPlatform, byUser },
    });
  } catch (error) {
    console.error("List credit logs error:", error);
    return NextResponse.json({ error: "获取积分记录失败" }, { status: 500 });
  }
}

/** Create credit log */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { platform, amount, note, userId } = await request.json();
    if (!platform) return NextResponse.json({ error: "请选择平台" }, { status: 400 });
    if (!amount || amount <= 0) return NextResponse.json({ error: "请输入消耗数量" }, { status: 400 });

    // Only admin/director can log credits for other users
    let targetUserId = payload.sub;
    if (userId && userId !== payload.sub) {
      if (payload.role !== "admin" && payload.role !== "director") {
        return NextResponse.json({ error: "只有管理员或导演可以为他人登记积分" }, { status: 403 });
      }
      targetUserId = userId;
    }

    const db = getDb();
    const now = new Date().toISOString();
    const logId = generateId("crl");

    db.run(
      "INSERT INTO credit_logs (id, user_id, platform, amount, project_id, note, logged_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
      logId,
      targetUserId,
      platform,
      amount,
      projectId,
      note || null,
      now
    );

    const log = db.get<Record<string, unknown>>(
      "SELECT * FROM credit_logs WHERE id = ?",
      logId
    );

    const user = db.get<{ nickname: string }>(
      "SELECT nickname FROM users WHERE id = ?",
      targetUserId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_credit_log",
      JSON.stringify({ logId, platform, amount, targetUserId }),
      now
    );

    return NextResponse.json(
      { log: { ...log, userName: user?.nickname || "未知" } },
      { status: 201 }
    );
  } catch (error) {
    console.error("Create credit log error:", error);
    return NextResponse.json({ error: "登记失败" }, { status: 500 });
  }
}
