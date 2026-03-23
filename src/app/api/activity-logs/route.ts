import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

/** List activity logs (admin only) */
export async function GET(request: NextRequest) {
  try {
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    if (payload.role !== "admin") {
      return NextResponse.json({ error: "仅管理员可查看操作日志" }, { status: 403 });
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get("projectId");
    const userId = searchParams.get("userId");
    const action = searchParams.get("action");

    const db = getDb();

    let sql = "SELECT * FROM activity_logs WHERE 1=1";
    const params: unknown[] = [];

    if (projectId) {
      sql += " AND project_id = ?";
      params.push(projectId);
    }
    if (userId) {
      sql += " AND user_id = ?";
      params.push(userId);
    }
    if (action) {
      sql += " AND action = ?";
      params.push(action);
    }

    sql += " ORDER BY created_at DESC LIMIT 100";

    const logs = db.all<Record<string, unknown>>(sql, ...params);

    // Enrich with user and project names
    const result = logs.map((l) => {
      const user = db.get<{ nickname: string }>(
        "SELECT nickname FROM users WHERE id = ?",
        l.user_id
      );
      const project = l.project_id
        ? db.get<{ name: string }>(
            "SELECT name FROM projects WHERE id = ?",
            l.project_id
          )
        : null;
      return {
        ...l,
        userName: user?.nickname || "未知",
        projectName: project?.name || null,
        details: l.details_json ? JSON.parse(l.details_json as string) : null,
      };
    });

    return NextResponse.json({ logs: result });
  } catch (error) {
    console.error("List activity logs error:", error);
    return NextResponse.json({ error: "获取操作日志失败" }, { status: 500 });
  }
}
