import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List shots for a project */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const project = db.get<Record<string, unknown>>(
      "SELECT * FROM projects WHERE id = ?",
      projectId
    );
    if (!project) return NextResponse.json({ error: "项目不存在" }, { status: 404 });

    const shots = db.all<Record<string, unknown>>(
      "SELECT * FROM shots WHERE project_id = ? ORDER BY sort_order ASC",
      projectId
    );

    // Enrich with assets and annotation counts
    const enriched = shots.map((shot) => {
      const latestAsset = db.get<Record<string, unknown>>(
        "SELECT * FROM assets WHERE shot_id = ? ORDER BY created_at DESC LIMIT 1",
        shot.id
      );

      const assetCount =
        db.get<{ cnt: number }>(
          "SELECT COUNT(*) as cnt FROM assets WHERE shot_id = ?",
          shot.id
        )?.cnt ?? 0;

      const unresolvedAnnotations =
        db.get<{ cnt: number }>(
          `SELECT COUNT(*) as cnt FROM annotations a
           JOIN assets ast ON a.asset_id = ast.id
           WHERE ast.shot_id = ? AND a.status != 'resolved'`,
          shot.id
        )?.cnt ?? 0;

      const assignee = shot.assignee_id
        ? db.get<{ nickname: string }>(
            "SELECT nickname FROM users WHERE id = ?",
            shot.assignee_id
          )
        : null;

      return {
        ...shot,
        latestAsset: latestAsset || null,
        assetCount,
        unresolvedAnnotations,
        assigneeName: assignee?.nickname || null,
      };
    });

    return NextResponse.json({ shots: enriched, project });
  } catch (error) {
    console.error("List shots error:", error);
    return NextResponse.json({ error: "获取镜头失败" }, { status: 500 });
  }
}

/** Create a single shot */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: projectId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    const db = getDb();
    const { sceneDescription, dialogue, durationSeconds, cameraAngle } =
      await request.json();

    const existingCount =
      db.get<{ cnt: number }>(
        "SELECT COUNT(*) as cnt FROM shots WHERE project_id = ?",
        projectId
      )?.cnt ?? 0;

    const nextNumber = existingCount + 1;
    const now = new Date().toISOString();
    const shotId = generateId("sht");

    db.run(
      `INSERT INTO shots (id, project_id, shot_number, scene_description, dialogue, duration_seconds, camera_angle, status, assignee_id, sort_order, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_upload', NULL, ?, ?, ?)`,
      shotId,
      projectId,
      nextNumber,
      sceneDescription || "",
      dialogue || null,
      durationSeconds || null,
      cameraAngle || null,
      nextNumber,
      now,
      now
    );

    // Update project updated_at
    db.run("UPDATE projects SET updated_at = ? WHERE id = ?", now, projectId);

    const shot = db.get<Record<string, unknown>>(
      "SELECT * FROM shots WHERE id = ?",
      shotId
    );

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      projectId,
      "create_shot",
      JSON.stringify({ shotId, shotNumber: nextNumber }),
      now
    );

    return NextResponse.json({ shot }, { status: 201 });
  } catch (error) {
    console.error("Create shot error:", error);
    return NextResponse.json({ error: "创建镜头失败" }, { status: 500 });
  }
}
