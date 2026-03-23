import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

function getActivityLogs() {
  return getDb().activityLogs;
}

/** List activity logs (admin only) */
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    if (payload.role !== "admin") {
      return NextResponse.json({ error: "仅管理员可查看操作日志" }, { status: 403 });
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get("projectId");
    const userId = searchParams.get("userId");
    const action = searchParams.get("action");

    const db = getDb();
    let logs = getActivityLogs();

    if (projectId) logs = logs.filter((l) => l.projectId === projectId);
    if (userId) logs = logs.filter((l) => l.userId === userId);
    if (action) logs = logs.filter((l) => l.action === action);

    // Sort newest first
    logs.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    // Enrich with user and project names
    const result = logs.slice(0, 100).map((l) => {
      const user = db.users.find((u) => u.id === l.userId);
      const project = l.projectId ? db.projects.find((p) => p.id === l.projectId) : null;
      return {
        ...l,
        userName: user?.nickname || "未知",
        projectName: project?.name || null,
        details: l.detailsJson ? JSON.parse(l.detailsJson) : null,
      };
    });

    return NextResponse.json({ logs: result });
  } catch (error) {
    console.error("List activity logs error:", error);
    return NextResponse.json({ error: "获取操作日志失败" }, { status: 500 });
  }
}
