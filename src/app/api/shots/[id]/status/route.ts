import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/auth";
import { getDb } from "@/lib/db-store";

const VALID_STATUSES = [
  "pending_upload",
  "pending_review",
  "needs_revision",
  "revised_pending_review",
  "approved",
  "delivered",
];

/** Update shot status */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: shotId } = await params;
    const authHeader = request.headers.get("authorization");
    const token = authHeader?.replace("Bearer ", "");
    if (!token) return NextResponse.json({ error: "未登录" }, { status: 401 });

    const payload = await verifyToken(token);
    if (!payload) return NextResponse.json({ error: "登录已过期" }, { status: 401 });

    const { status, assigneeId } = await request.json();

    const db = getDb();
    const shot = db.shots.find((s) => s.id === shotId);
    if (!shot) return NextResponse.json({ error: "镜头不存在" }, { status: 404 });

    const now = new Date().toISOString();

    // Update status
    if (status) {
      if (!VALID_STATUSES.includes(status)) {
        return NextResponse.json({ error: "无效的状态" }, { status: 400 });
      }

      // Permission check: only admin/director can approve
      if (
        (status === "approved" || status === "needs_revision") &&
        payload.role !== "admin" &&
        payload.role !== "director"
      ) {
        return NextResponse.json(
          { error: "需要导演或管理员权限才能审批" },
          { status: 403 }
        );
      }

      shot.status = status;
    }

    // Update assignee
    if (assigneeId !== undefined) {
      if (payload.role !== "admin" && payload.role !== "director") {
        return NextResponse.json(
          { error: "需要导演或管理员权限才能分配任务" },
          { status: 403 }
        );
      }
      shot.assigneeId = assigneeId;
    }

    shot.updatedAt = now;

    // Log activity
    db.projects.forEach((p) => {
      if (p.id === shot.projectId) p.updatedAt = now;
    });

    return NextResponse.json({ shot });
  } catch (error) {
    console.error("Update shot status error:", error);
    return NextResponse.json({ error: "更新失败" }, { status: 500 });
  }
}
