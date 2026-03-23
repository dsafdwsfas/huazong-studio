import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { generateId } from "@/lib/id";
import { getDb } from "@/lib/db-store";

/** List annotations for an asset */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: assetId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;

    const db = getDb();
    const annotations = db.all<Record<string, unknown>>(
      "SELECT * FROM annotations WHERE asset_id = ? ORDER BY created_at DESC",
      assetId
    );

    const enriched = annotations.map((ann) => {
      const annotator = db.get<{ nickname: string }>(
        "SELECT nickname FROM users WHERE id = ?",
        ann.annotator_id
      );

      const replies = db.all<Record<string, unknown>>(
        "SELECT * FROM annotation_replies WHERE annotation_id = ? ORDER BY created_at ASC",
        ann.id
      ).map((r) => {
        const replyUser = db.get<{ nickname: string }>(
          "SELECT nickname FROM users WHERE id = ?",
          r.user_id
        );
        return { ...r, userName: replyUser?.nickname || "未知" };
      });

      return {
        ...ann,
        annotatorName: annotator?.nickname || "未知",
        replies,
      };
    });

    return NextResponse.json({ annotations: enriched });
  } catch (error) {
    console.error("List annotations error:", error);
    return NextResponse.json({ error: "获取批注失败" }, { status: 500 });
  }
}

/** Create annotation */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: assetId } = await params;
    const auth = await requireAuth(request);
    if ("error" in auth) return auth.error;
    const { payload } = auth;

    // Only admin and director can annotate
    if (payload.role !== "admin" && payload.role !== "director") {
      return NextResponse.json({ error: "需要导演或管理员权限" }, { status: 403 });
    }

    const { canvasDataJson, textComment, frameTimestampMs } = await request.json();

    if (!textComment && !canvasDataJson) {
      return NextResponse.json({ error: "请输入批注内容" }, { status: 400 });
    }

    const db = getDb();
    const now = new Date().toISOString();
    const annotationId = generateId("ann");

    db.run(
      `INSERT INTO annotations (id, asset_id, canvas_data_json, text_comment, annotator_id, status, frame_timestamp_ms, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, 'unresolved', ?, ?, ?)`,
      annotationId,
      assetId,
      canvasDataJson || null,
      textComment || "",
      payload.sub,
      frameTimestampMs || null,
      now,
      now
    );

    const annotation = db.get<Record<string, unknown>>(
      "SELECT * FROM annotations WHERE id = ?",
      annotationId
    );

    // Find the project_id for activity log via asset -> shot -> project
    const assetInfo = db.get<{ shot_id: string }>(
      "SELECT shot_id FROM assets WHERE id = ?",
      assetId
    );
    const shotInfo = assetInfo
      ? db.get<{ project_id: string }>(
          "SELECT project_id FROM shots WHERE id = ?",
          assetInfo.shot_id
        )
      : null;

    // Activity log
    db.run(
      "INSERT INTO activity_logs (id, user_id, project_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
      generateId("log"),
      payload.sub,
      shotInfo?.project_id || null,
      "create_annotation",
      JSON.stringify({ annotationId, assetId }),
      now
    );

    return NextResponse.json({ annotation }, { status: 201 });
  } catch (error) {
    console.error("Create annotation error:", error);
    return NextResponse.json({ error: "创建批注失败" }, { status: 500 });
  }
}
