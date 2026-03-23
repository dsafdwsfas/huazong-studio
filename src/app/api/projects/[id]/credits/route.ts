import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List credit logs for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const platform = searchParams.get("platform");
    const userId = searchParams.get("userId");

    const db = getDb();
    let logs = db.creditLogs.filter((l) => l.projectId === projectId);

    if (platform) logs = logs.filter((l) => l.platform === platform);
    if (userId) logs = logs.filter((l) => l.userId === userId);

    // Sort by newest first
    logs.sort((a, b) => new Date(b.loggedAt).getTime() - new Date(a.loggedAt).getTime());

    // Enrich with user nickname
    const result = logs.map((l) => {
      const user = db.users.find((u) => u.id === l.userId);
      return { ...l, userName: user?.nickname || "未知" };
    });

    // Summary stats
    const totalAmount = logs.reduce((sum, l) => sum + l.amount, 0);
    const byPlatform: Record<string, number> = {};
    const byUser: Record<string, { name: string; amount: number }> = {};
    for (const l of logs) {
      byPlatform[l.platform] = (byPlatform[l.platform] || 0) + l.amount;
      if (!byUser[l.userId]) {
        const user = db.users.find((u) => u.id === l.userId);
        byUser[l.userId] = { name: user?.nickname || "未知", amount: 0 };
      }
      byUser[l.userId].amount += l.amount;
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
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

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
    const log = {
      id: generateId("crl"),
      userId: targetUserId,
      platform,
      amount,
      projectId,
      note: note || null,
      loggedAt: new Date().toISOString(),
    };
    db.creditLogs.push(log);

    const user = db.users.find((u) => u.id === log.userId);
    return NextResponse.json(
      { log: { ...log, userName: user?.nickname || "未知" } },
      { status: 201 }
    );
  } catch (error) {
    console.error("Create credit log error:", error);
    return NextResponse.json({ error: "登记失败" }, { status: 500 });
  }
}
