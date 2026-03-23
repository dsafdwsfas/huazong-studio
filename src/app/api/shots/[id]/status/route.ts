import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
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
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const { status, assigneeId } = await request.json();

    const db = getDb();
    const shot = db.get<Record<string, unknown>>(
      "SELECT * FROM shots WHERE id = ?",
      shotId
    );
    if (!shot) return NextResponse.json({ error: "镜头不存在" }, { status: 404 });

    const now = new Date().toISOString();
    const sets: string[] = ["updated_at = ?"];
    const params_arr: unknown[] = [now];

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

      sets.push("status = ?");
      params_arr.push(status);
    }

    // Update assignee
    if (assigneeId !== undefined) {
      if (payload.role !== "admin" && payload.role !== "director") {
        return NextResponse.json(
          { error: "需要导演或管理员权限才能分配任务" },
          { status: 403 }
        );
      }
      sets.push("assignee_id = ?");
      params_arr.push(assigneeId);
    }

    params_arr.push(shotId);
    db.run(`UPDATE shots SET ${sets.join(", ")} WHERE id = ?`, ...params_arr);

    // Update project updated_at
    db.run(
      "UPDATE projects SET updated_at = ? WHERE id = ?",
      now,
      shot.project_id
    );

    const updated = db.get<Record<string, unknown>>(
      "SELECT * FROM shots WHERE id = ?",
      shotId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      shot.project_id as string,
      "update_shot_status",
      JSON.stringify({ shotId, status, assigneeId }),
      now
    );

    return NextResponse.json({ shot: updated });
  } catch (error) {
    console.error("Update shot status error:", error);
    return NextResponse.json({ error: "更新失败" }, { status: 500 });
  }
}
